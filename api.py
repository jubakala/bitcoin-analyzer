import flask
from flask import request, jsonify


app = flask.Flask(__name__)
app.config["DEBUG"] = True


@app.route('/', methods=["GET"])
def home():
	return "<h1>Hello, World!</h1>"


@app.route('/bitcoin/<start>/<end>', methods=["GET"])
def bitcoin(start_date, end_date):
	return jsonify({"start": start_date, "end": end_date})


app.run()