import os
import flask
from flask import request, jsonify, render_template
from utils import get_data, find_longest_bearish_trend, form_url, get_highest_trading_volume, get_days_to_by_and_sell


app = flask.Flask(__name__, 
	static_url_path='',
	static_folder='static/',
	template_folder='templates')

app.config["DEBUG"] = False


@app.route('/', methods=["GET"])
def home():
	# Render the home page.
	return render_template("index.html")


@app.route('/favicon.ico')
def favicon():
	return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico',mimetype='image/vnd.microsoft.icon')


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
		# If there were errors, return them.
		return url_data


if __name__ == '__main__':
	app.run()
