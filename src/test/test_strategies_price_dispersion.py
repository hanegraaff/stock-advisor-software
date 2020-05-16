import unittest
from unittest.mock import patch
from intrinio_sdk.rest import ApiException
from data_provider import intrinio_data
from datetime import datetime
from exception.exceptions import ValidationError, DataError
from strategies.price_dispersion_strategy import PriceDispersionStrategy


class TestStrategiesPriceDispersion(unittest.TestCase):

    def test_init_no_tickers(self):
        with self.assertRaises(ValidationError):
            PriceDispersionStrategy(None, 2020, 2, 1)

    def test_init_empty_ticker_list(self):
        with self.assertRaises(ValidationError):
            PriceDispersionStrategy([], 2020, 2, 1)

    def test_init_too_few_tickers(self):
        with self.assertRaises(ValidationError):
            PriceDispersionStrategy(['AAPL'], 2020, 2, 1)

    def test_init_enough_tickers(self):
        PriceDispersionStrategy(['1', '2'], 2020, 1, 1)

    def test_api_exception(self):
        with patch.object(intrinio_data.company_api, 'get_company_historical_data',
                          side_effect=ApiException("Not Found")):

            strategy = PriceDispersionStrategy(['1', '2'], 2020, 2, 1)

            with self.assertRaises(DataError):
                strategy.__load_financial_data__()
