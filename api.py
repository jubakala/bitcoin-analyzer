import flask
from flask import request, jsonify
from utils import datetime_to_timestamp, add_hour, get_data, load_file, timestamp_to_date, get_days, create_price_date_dict, organize_prices_by_date, get_midnight_price, find_longest_bearish_trend, form_url, get_highest_trading_volume, downward_only, get_midnight_prices, get_days_to_by_and_sell


app = flask.Flask(__name__)
app.config["DEBUG"] = True


@app.route('/', methods=["GET"])
def home():
	return "<h1>Hello, World!</h1>"


@app.route('/coins/<crypto_currency>/<fiat_currency>/<start_date>/<end_date>', methods=["GET"])
def bitcoin(crypto_currency, fiat_currency, start_date, end_date):
	# Form the API url. Contains also possible error messages.
	url_data = form_url(crypto_currency, fiat_currency, start_date, end_date)
		
	if len(url_data['error']) == 0:
		# Get data by date range from coingecko.com.
		data = get_data(url_data['url'])

		if 'error' not in data:
			# Find the longest bearish trend.
			longest_bearish_trend = find_longest_bearish_trend(data)
			# Find the date with the highest trading volume.
			highest_volume_date, highest_volume = get_highest_trading_volume(data)

			# Find the days to buy and sell.
			date_to_buy, date_to_sell = get_days_to_by_and_sell(data)

			return jsonify({"trends": { 
					"longest_bearish_trend": longest_bearish_trend 
				}, 
				"volumes": { 
					"highest_volume_date": highest_volume_date, 
					"highest_volume": highest_volume 
				},
				"buy_sell": {
					"date_to_buy": date_to_buy,
					"date_to_sell": date_to_sell
				}
			})
		else:
			# If there were errors, return them.
			return data
	else:
		pass	


app.run()