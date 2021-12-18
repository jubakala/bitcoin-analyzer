import flask

app = flask.Flask(__name__)
app.config["DEBUG"] = True


@app.route('/', methods=["GET"])
def home():
	return "<h1>Hello, World!</h1>"


app.run()