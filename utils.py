from datetime import datetime, timedelta, date, timezone
import requests as req
import json
import time
from dateutil import parser, tz
import pandas as pd


# Testing purposes only.
def load_file(filename):
    content = "";

    with open('./' + filename) as f:
        content = f.read()
        content = content.replace("'", "\"")

    return json.loads(content)


def form_url(crypto_currency, fiat_currency, start_datetime, end_datetime):
	url_data = {'url': '', 'error': ''} 

	# Take only the date part of the datetime.
	start_timestamp = datetime_to_timestamp(start_datetime[0:10])
	end_timestamp = datetime_to_timestamp(end_datetime[0:10])

	if start_timestamp != None and end_timestamp != None:
		# Check out that the timestamps are in correct order, ie. start_timestamp is smaller. Check also that the dates are not the same.
		if start_timestamp < end_timestamp:
			from_timestamp = start_timestamp
			to_timestamp = end_timestamp
		elif end_timestamp < start_timestamp:
			from_timestamp = end_timestamp
			to_timestamp = start_timestamp
		else: # Both are the same date
			url_data['error'] = "Dates can't be the same."

		# Add one hour to the to_timestamp.
		to_timestamp = add_hour(to_timestamp)
	else:
		url_data['error'] = "Start or end date, or both, are invalid. Dates must be in form '2021-12-31'."

	# If there's no errors.
	if len(url_data['error']) == 0:
		url_data['url'] = f"https://api.coingecko.com/api/v3/coins/{crypto_currency}/market_chart/range?vs_currency={fiat_currency}&from={int(from_timestamp)}&to={int(to_timestamp)}"

	return url_data


# Calculate the distance between midnight timestamp and price timestamp.
def absolute_distance(midnight_timestamp, price_timestamp):
	# Data (price_timestamp) from the coingecko-API is in milliseconds.
	midnight_timestamp = midnight_timestamp * 1000

	return abs(int(midnight_timestamp) - int(price_timestamp))


# Find the currency price of the day, which is as close the midnight as possible.
# If the previous day's last price is closer to midnight than the actual day's price, the previous day's price, if available, will be used.
def get_midnight_price(date_str, day_prices, prev_day_prices):
	columns = ["Timestamp", "Price"]
	# Get the midnight timestamp of the day in question, ie. "2021-12-24 00:00:00"
	midnight_timestamp = datetime_to_timestamp(date_str)

	# If there is not data from the previous day of the day in question (date_str).
	if prev_day_prices is None:
		prices_arr = pd.DataFrame(day_prices, columns=columns)
	else:
		day_prices_arr = pd.DataFrame(day_prices, columns=columns)
		prev_day_prices_arr = pd.DataFrame(prev_day_prices, columns=columns)
		# Combine the above two dataframes as one.
		prices_arr = pd.concat([day_prices_arr, prev_day_prices_arr])

	# Calculate the distance between the midnight timestamp and the price time stamp of the row, and set its to TimeDistance column.
	prices_arr['TimeDistance'] = prices_arr.apply(lambda x: absolute_distance(midnight_timestamp, x['Timestamp']), axis=1)

	minarg = prices_arr["TimeDistance"].idxmin()
	closest_to_midnight_price =  prices_arr.iloc[minarg]

	return closest_to_midnight_price['Price']


# Gets the distinct dates ("2021-12-24") from the currency prices data. 
def get_days(currency_data):
	prices = currency_data['prices']
	dates = []

	for pr in prices:
		price_timestamp = pr[0]
		price_date = timestamp_to_date(price_timestamp)
		
		if price_date not in dates:
			dates.append(price_date)

	return dates

# Creates a dictionary with input dates as keys. Every key has an empty list attached to it.
# Example: { "2021-12-24": [], "2021-12-25": [] }
def create_price_date_dict(dates):
	price_date_dict	= {}

	for d in dates:
		if d not in price_date_dict:
			price_date_dict[d] = []

	return price_date_dict


def organize_prices_by_date(price_date_dict, prices):
	price_date_dict = {}

	for pr in prices:
		date_str = timestamp_to_date(pr[0])

		if date_str in price_date_dict:
			price_date_dict[date_str].append(pr)
		else: # This shouldn't happen, if everything else before is done correctly.
			price_date_dict[date_str] = []
			price_date_dict[date_str].append(pr)

	return price_date_dict


# Gets the contents of an URL.
def get_data(url):
	data = None

	try:
		# Define headers.
		headers = req.utils.default_headers()
		headers.update({ 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'})
		
		# Fetch the data.
		resp = req.get(url)
		# Convert the data into JSON.
		data = resp.json()
	except Exception as e:
		pass

	return data	


def datetime_to_timestamp(date_str):
	timestamp = None

	try:
		date_time = parser.parse(date_str)
		timestamp = date_time.replace(tzinfo=timezone.utc).timestamp()
	except Exception as e:
		print

	return timestamp


def timestamp_to_date(timestamp):
	date_time = None

	try:
		# Convert date string into datetime object.
		# date_time = parser.parse(str(timestamp))
		date_time = datetime.fromtimestamp(timestamp)
		# date_time = utc.localize(datetime.fromtimestamp(timestamp))
		date_time = date_time.strftime("%Y-%m-%d")
	except Exception as e:
		# Data from the coingecko-API is in milliseconds.
		try:
			# Convert date string into datetime object.
			timestamp = int(timestamp) / 1000
			date_time = datetime.fromtimestamp(timestamp)
			date_time = date_time.astimezone(timezone.utc).strftime("%Y-%m-%d")		
		except Exception as ee:
			pass

	return date_time


def add_hour(timestamp):
	hour_later = None
	
	try:
		date_str = timestamp_to_date(timestamp)
		# Convert date string into datetime object.
		date_time = parser.parse(date_str)
		# Switch to UTC time and add an hour to the input date.
		date_time_plus_hour = date_time.replace(tzinfo=timezone.utc) + timedelta(hours=1)		
		# Convert the datetime into timestamp.
		hour_later = int(date_time_plus_hour.timestamp())
	except Exception as e:
		pass

	return hour_later 


def get_highest_trading_volume(data):
	# Get the volumes data.
	total_volumes = data['total_volumes']
	# Create a Pandas dataframe from the volumes data.
	volumes = pd.DataFrame(total_volumes, columns=["Date", "Volume"])

	maxarg = volumes["Volume"].idxmax()
	highest_volume = volumes.iloc[maxarg]
	highest_volume_date = timestamp_to_date(highest_volume['Date'])

	return highest_volume_date, highest_volume['Volume']


# Find the longest bearish (downward) trend from the midnight currency prices of the chosen date range.
def find_longest_bearish_trend(data):
	# Get a list of dates (2021-12-24) between the from and to -dates of the range.
	days = get_days(data)
	# Create a dictionary, where keys are distinct dates of the date ranges, and for every key, there's an empty list.
	price_date_dict = create_price_date_dict(days)
	# Append all the prices of a specific date to price_date_dict, ie. date: [[timestamp1, price1], [timestamp2, price2]].
	organized_prices = organize_prices_by_date(price_date_dict, data['prices'])

	midnight_prices = {}
	prev_date = None
	prev_price = None
	longest_bearish_trend = 0
	bearish_length = 0

	# Iterate through each date and date's available prices, in order to find the bearish trends, ie. the maximum amount of days,
	# when the midnight/closest to midnight price of the currency was lower than previous day's same price.
	for date_str in organized_prices:
		# If previous date haven't been set yet, set it.
		if prev_date is None:
			# There are no data from the previous date at this point.
			prev_day_prices = None
		else:
			prev_day_prices = organized_prices[prev_date]

		# Get all the available prices for the date in question.
		day_prices = organized_prices[date_str]
		# Get the day's price which is closest to the midnight.
		midnight_price = get_midnight_price(date_str, day_prices, prev_day_prices)

		# Set the previous date.
		prev_date = date_str

		# No calculations to be made on the first round of iteration.
		if prev_price is None:
			prev_price = float(midnight_price)
		else:
			# If midnight prices is smaller than previous day's midnight price, increase the bearish trend length counter.
			if float(midnight_price) < float(prev_price):
				bearish_length += 1

				# If current bearish length is longer than the current longest trend, update the longest bearish trend length.
				if bearish_length > longest_bearish_trend:
					longest_bearish_trend = bearish_length
			else:
				bearish_length = 0

			# Set the previous price to the midnight price in question.
			prev_price = float(midnight_price)

	return longest_bearish_trend

