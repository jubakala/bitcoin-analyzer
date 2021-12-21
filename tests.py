import unittest
from unittest import TestCase
from utils import datetime_to_timestamp, add_hour, get_data


class ApiTest(TestCase):
	def test_datetime_to_timestamp(self):
		timestamp = datetime_to_timestamp("2020-01-01")
		expected = 1577836800

		self.assertEqual(timestamp, expected)


	def test_datetime_to_timestamp_invalid_input(self):
		timestamp = datetime_to_timestamp("12345678")

		self.assertIsNone(timestamp)


	def test_add_hour(self):
		# Add an hour to '2021-01-01'.
		added_timestamp = add_hour("2021-01-01")
		expected = 1609462800

		self.assertEqual(added_timestamp, expected)


	def test_add_hour_invalid_input(self):
		added_timestamp = add_hour("87654321")

		self.assertIsNone(added_timestamp)


	def test_get_data_by_url(self):
		crypto_currency = "bitcoin"
		fiat_currency = "eur"
		start_date = "1577836800"
		end_date = "1609376400"

		url = f"https://api.coingecko.com/api/v3/coins/{crypto_currency}/market_chart/range?vs_currency={fiat_currency}&from={start_date}&to={end_date}"
		json_data = get_data(url)

		self.assertTrue('prices' in json_data)


	def test_get_data_by_url_invalid_url(self):
		crypto_currency = "scroogecoin"
		fiat_currency = "eur"
		start_date = "this_is_a_date"
		end_date = "another_date"

		url = f"https://api.coingecko.com/api/v3/coins/{crypto_currency}/market_chart/range?vs_currency={fiat_currency}&from={start_date}&to={end_date}"
		json_data = get_data(url)

		self.assertTrue('prices' in json_data)
		self.assertEqual(len(json_data['prices']), 0)


if __name__ == '__main__':
    unittest.main()