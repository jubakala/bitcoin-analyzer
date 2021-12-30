# bitcoin-analyzer
A tool to analyze Bitcoin market value for a given date range.

Demo: https://jubakala-bitcoin-analyzer.herokuapp.com/

This app has been tested only with Python 3.8 in macOS Big Sur version 11.5.1.


# Create virtual environment.
$ python3 -m venv venv

# Activate the virtual environment.
$ source venv/bin/activate

# Install dependencies. (The process may recommend to upgrade pip, but it can be ignored this time.)
$ python3 -m pip install -r requirements.txt

# Run the app.
$ flask run
or 
$ python3 app.py

The app prompts the local url where it runs. Should be http://127.0.0.1:5000. Copy and paste the url to your favourite browser and you're good to test the app!

# To run the tests (optional):
$ python3 tests.py