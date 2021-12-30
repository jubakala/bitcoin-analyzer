from datetime import datetime, timedelta, date, timezone
import requests as req
import json
# import time
from dateutil import parser, tz
import pandas as pd


# Testing purposes only.
def load_file(filename):
    """
    A function to load data from json-file.

    Parameters
    ----------
    filename : string
        Path to the file to be read

    Returns
    -------
    dict
        Contents of the json-file as a dictionary.
    """    
    
    content = ""

    with open('./' + filename) as f:
        content = f.read()
        content = content.replace("'", "\"")

    return json.loads(content)


def form_url(crypto_currency, fiat_currency, start_datetime, end_datetime):
    """
    A function that forms a url for CoinGecko API: /coins/{id}/market_chart/range endpoint.
    Parameters for the url are FIAT currency and start & end dates for the date range. Id is the crypto currency id.

    Parameters
    ----------
    crypto_currency : string
        Id of the crypto currency to be fetched date of.
    fiat_currency : string
        Abbreviation of the FIAT currency the crypto currency values are compared to. For example eur => EURO.
    start_datetime : date string
        Start date for the date range in form of year-month-day => 2021-12-30
    end_datetime : date string
        End date for the date range in form of year-month-day => 2021-12-30        

    Returns
    -------
    dict
        Contents of a JSON-reply from the API containing cryptocurrency data, or an error message.
    """    
    url_data = {'url': '', 'error': ''} 

    # Take only the date part of the datetime.
    start_timestamp = datetime_to_timestamp(start_datetime[0:10])
    end_timestamp = datetime_to_timestamp(end_datetime[0:10])

    if start_timestamp != end_timestamp:
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
    else:
        url_data['error'] = "Start and end dates can't be the same!"

    return url_data


def absolute_distance(midnight_timestamp, price_timestamp):
    """
    Calculate the distance between midnight timestamp and price timestamp.

    Parameters
    ----------
    midnight_timestamp : string
        Midnight timestamp of a date.
    price_timestamp : string
        Timestamp of a specific timestamp for a cryptocurrency price.

    Returns
    -------
    int
        Returns the absolute difference ie. distance between the two timestamp parameters.
    """    
    # Data (price_timestamp) from the coingecko-API is in milliseconds.
    midnight_timestamp = midnight_timestamp * 1000

    return abs(int(midnight_timestamp) - int(price_timestamp))


def get_midnight_price(date_str, day_prices, prev_day_prices):
    """
    Find the currency price of the day, which is as close the midnight as possible.
    If the previous day's last price is closer to midnight than the actual day's price, the previous day's price, if available, will be used.

    Parameters
    ----------
    date_string : string
        Midnight datetime of the day in question.
    day_prices : dict
        All the currency prices of the day in question.
    prev_day_prices : dict
        All the currency prices of the previous day. These are considered since it's possible that the previous days last prices is closer
        to the midnight than the actual day's first price.

    Returns
    -------
    float
        Returns the currency value that is closest to midnight of the day in question.
    """    
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
    """
    Gets all the distinct dates ("2021-12-24") from the currency prices data. 

    Parameters
    ----------
    currency_data : dict
        All the timepoints of the date range with currency timestamps and values.

    Returns
    -------
    list
        Returns the list of distinct dates of the date range.
    """
    prices = currency_data['prices']
    dates = []

    for pr in prices:
        price_timestamp = pr[0]
        price_date = timestamp_to_date(price_timestamp)
        
        if price_date not in dates:
            dates.append(price_date)

    return dates


def create_price_date_dict(dates):
    """
    Creates a dictionary with input dates as keys. Every key has an empty list attached to it.

    Parameters
    ----------
    dates : list
        List of date strings.

    Returns
    -------
    dict
        A dictionary with dates as keys, and an empty list for each key. Example: { "2021-12-24": [], "2021-12-25": [] }
    """    
    price_date_dict    = {}

    for d in dates:
        # If date is not yet as a key of the dictionary, add it.
        if d not in price_date_dict:
            price_date_dict[d] = []

    return price_date_dict


def organize_prices_by_date(price_date_dict, prices):
    """
    Creates a dictionary with input dates as keys. Every key of the dictionary has a list of the fiat currency prices with timestamps of that date.

    Parameters
    ----------
    price_date_dict : dict
        A dictionary with input dates as keys. Every key has an empty list attached to it. Created in create_price_dict -function.
    prices : dict
        A dictionary of timestamps and the fiat currency prices of that point in time.

    Returns
    -------
    dict
        A dictionary with dates as keys, and a list with all the timestamp fiat currency pairs of the date.
    """    
    price_date_dict = {}

    for pr in prices:
        date_str = timestamp_to_date(pr[0])

        if date_str in price_date_dict:
            price_date_dict[date_str].append(pr)
        else: # This shouldn't happen, if everything else before is done correctly.
            price_date_dict[date_str] = []
            price_date_dict[date_str].append(pr)

    return price_date_dict


def get_data(url):
    """
    Makes a http request to the API endpoint of url and gets the returned data.

    Parameters
    ----------
    url : string
        The url of the API endpoint to be called

    Returns
    -------
    dict
        JSON data returned by the API as a dictionary.
    """        
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
    """
    Converts datetime string to UTC timestamp. Timestamp is time in seconds.

    Parameters
    ----------
    date_str : string
        Date as a string to be converted. Date is formatted like 2021-12-31.

    Returns
    -------
    int
        The input date as seconds timestamp.
    """    
    timestamp = None

    try:
        date_time = parser.parse(date_str)
        timestamp = date_time.replace(tzinfo=timezone.utc).timestamp()
    except Exception as e:
        print

    return timestamp


def timestamp_to_date(timestamp):
    """
    Converts timestamp into UTC datetime string. Timestamp may be in seconds or milliseconds.

    Parameters
    ----------
    timestamp : int
        Timestamp in seconds or milliseconds.

    Returns
    -------
    string
        Converted datetime string. Formatted like 2021-12-30.
    """        
    date_time = None

    try:
        # Convert date string into datetime object.
        date_time = datetime.fromtimestamp(timestamp)
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
    """
    Add an hour to the input timestamp.

    Parameters
    ----------
    timestamp : int
        Timestamp in seconds.

    Returns
    -------
    int
        Timestamp which time is an hour later than the input timestamp.
    """
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


def downward_only(data):
    """
    Check if the midnight prices of the date range are decreasing each date.

    Parameters
    ----------
    data : dict
        Currency data from the CoinGecko API endpoint containing timestamp and the FIAT currency value of that timestamp.

    Returns
    -------
    boolean
        Returns True, if each FIAT currency value is smaller than the previous price. Data is ordered by timestamp in asceding order.
    """    
    prices = data['prices']
    prices_df = pd.DataFrame(prices, columns=["Timestamp", "Price"])

    # Ensure that data is sorted by the date, ascending.
    prices_df = prices_df.sort_values(by="Timestamp", ascending=True)
    # Take only the prices column and transform it to a list.
    prices_arr = prices_df['Price'].tolist()

    # Check if each prices is smaller than the price preceding it.
    is_downward_only = all(ii > jj for ii, jj in zip(prices_arr, prices_arr[1:]))

    return is_downward_only


def get_highest_trading_volume(data):
    """
    Finds the date with the highest trading volume of the chosen date range.

    Parameters
    ----------
    data : dict
        Currency data from the CoinGecko API endpoint containing all the data from the date range.

    Returns
    -------
    date string
        Returns the date of the highest trading volume.
    float
        Returns the highest trading volume in FIAT currency of the chosen date range.
    """        
    # Get the volumes data.
    total_volumes = data['total_volumes']
    # Create a Pandas dataframe from the volumes data.
    volumes = pd.DataFrame(total_volumes, columns=["Date", "Volume"])

    # Find the index with the maximum volume of the data.
    maxarg = volumes["Volume"].idxmax()
    highest_volume = volumes.iloc[maxarg]
    highest_volume_date = timestamp_to_date(highest_volume['Date'])

    return highest_volume_date, highest_volume['Volume']


def get_midnight_prices(data):
    """
    Gets a list of dates formatted like 2021-12-30, and the FIAT currency price closest to midnight available.

    Parameters
    ----------
    data : dict
        Currency data from the CoinGecko API endpoint containing all the data from the date range.

    Returns
    -------
    dict
        Dictionary with date as a key, and the FIAT currency value closest to midnight.
    """
    days = get_days(data)
    # Create a dictionary, where keys are distinct dates of the date ranges, and for every key, there's an empty list.
    price_date_dict = create_price_date_dict(days)
    # Append all the prices of a specific date to price_date_dict, ie. date: [[timestamp1, price1], [timestamp2, price2]].
    organized_prices = organize_prices_by_date(price_date_dict, data['prices'])

    midnight_prices = {}
    prev_date = None

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

        midnight_prices[date_str] = midnight_price

        # Set the previous date.
        prev_date = date_str        

    return midnight_prices


def get_days_to_by_and_sell(data):
    """
    Gets the best day to sell and buy crypto currency, of the date range. 

    Parameters
    ----------
    data : dict
        Currency data from the CoinGecko API endpoint containing all the data from the date range.

    Returns
    -------
    string
        The date of date range where the currency price is the smallest on the date range. If prices go downward through the date range, returns "Don't buy"
    string
        The date of date range where the currency price is the largest on the date range. If prices go downward through the date range, returns "Don't sell"
    """    
    if downward_only(data):
        date_to_buy = "Don't buy"
        date_to_sell = "Don't sell"
    else:
        midnight_prices = get_midnight_prices(data)
        prices = pd.DataFrame.from_dict(midnight_prices, orient='index', columns=["Price"])
        
        # Find the lowest price, ie. date to buy.
        date_to_buy = prices["Price"].idxmin()

        # Find the highest price, ie. date to sell.
        date_to_sell = prices["Price"].idxmax()

    return date_to_buy, date_to_sell


def find_longest_bearish_trend(data):
    """
    Find the longest bearish (downward) trend from the midnight currency prices of the chosen date range.

    Parameters
    ----------
    data : dict
        Currency data from the CoinGecko API endpoint containing all the data from the date range.

    Returns
    -------
    int
        Length of the longest bearish (downward) trend of the chosen date range.
    """    
    midnight_prices = get_midnight_prices(data)

    longest_bearish_trend = 0
    bearish_length = 0
    prev_price = None

    # Iterate through each date and date's available prices, in order to find the bearish trends, ie. the maximum amount of days,
    # when the midnight/closest to midnight price of the currency was lower than previous day's same price.
    for date_str in midnight_prices:
        midnight_price = midnight_prices[date_str]

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

