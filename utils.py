from datetime import datetime, timedelta
from pytz import utc, timezone
import requests as req


# Gets the contents of an URL.
def get_data(url):
	data = None

	try:
		# Define headers.
		headers = req.utils.default_headers()
		headers.update({ 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'})
		
		# Fetch the data.
		resp = req.get(url)
		# Convert the data in to JSON.
		data = resp.json()
	except Exception as e:
		pass

	return data	


def datetime_to_timestamp(date_str):
	timestamp = None

	try:
		# Convert date string into utc datetime object.
		utc_time = utc.localize(datetime.strptime(date_str, "%Y-%m-%d"))
		# Convert the datetime into timestamp.
		timestamp = int(utc_time.timestamp())
	except Exception as e:
		pass

	return timestamp


def add_hour(date_str):
	timestamp = None
	
	try:
		# Convert date string into datetime object.
		utc_time = utc.localize(datetime.strptime(date_str, "%Y-%m-%d"))
		# Add an hour to the input date.
		utc_time_plus_hour = utc_time + timedelta(hours=1)
		# Convert the datetime into timestamp.
		timestamp = int(utc_time_plus_hour.timestamp())
	except Exception as e:
		pass

	return timestamp 

