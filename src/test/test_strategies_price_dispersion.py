import unittest
from unittest.mock import patch
from intrinio_sdk.rest import ApiException
from data_provider import intrinio_data
from exception.exceptions import ValidationError, DataError
from strategies.low_price_dispersion_strategy import LowPriceDispersionStrategy

class TestStrategiesPriceDispersion(unittest.TestCase):
    

    def test_init_no_tickers(self):
        with self.assertRaises(ValidationError):
            LowPriceDispersionStrategy(None, 2020, 2, 1)

    def test_init_empty_ticker_list(self):
        with self.assertRaises(ValidationError):
            LowPriceDispersionStrategy([], 2020, 2, 1)

    def test_init_too_few_tickers(self):
        with self.assertRaises(ValidationError):
            LowPriceDispersionStrategy(['AAPL'], 2020, 2, 1)

    def test_init_enough_tickers(self):
        LowPriceDispersionStrategy(['1', '2'], 2020, 1, 1)

    def test_api_exception(self):
        with patch.object(intrinio_data.company_api, 'get_company_historical_data',
            side_effect=ApiException("Not Found")):

            strategy = LowPriceDispersionStrategy(['1', '2'], 2020, 2, 1)
            
            with self.assertRaises(DataError):
                strategy.__load_financial_data__()