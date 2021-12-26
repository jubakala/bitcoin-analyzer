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


def add_hour(date_str):
	timestamp = None
	
	try:
		# Convert date string into datetime object.
		date_time = parser.parse(date_str)
		# Switch to UTC time and add an hour to the input date.
		date_time_plus_hour = date_time.replace(tzinfo=timezone.utc) + timedelta(hours=1)		
		# Convert the datetime into timestamp.
		timestamp = int(date_time_plus_hour.timestamp())
	except Exception as e:
		pass

	return timestamp 

