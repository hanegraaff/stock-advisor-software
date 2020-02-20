import unittest
from datetime import datetime
from unittest.mock import patch
from exception.exceptions import ValidationError
from strategies.portfolio import Portfolio

class TestStrategiesPortfolio(unittest.TestCase):


    '''
        Exception/Validation testing
    '''

    def test_invalid_parameters(self):
        with self.assertRaises(ValidationError):
            Portfolio(datetime.now(), datetime.now(), 'x', [])
            Portfolio(datetime.now(), datetime.now(), None, [])
            Portfolio(datetime.now(), None, None, [])
            Portfolio(None, None, None, [])

    def test_valid_parameters(self):
        Portfolio(datetime.now(), datetime.now(), 'x', ['AAPL', 'INTC'])

    def test_invalid_dict(self):
        with self.assertRaises(ValidationError):
            Portfolio.from_dict({
                'x' : 'y'
            })

    def test_valid_dict(self):
        d = {
            'portfolio_id': 'xxx',
            'creation_date': '2020-02-18T01:59:59Z',
            'data_date': '2019-01-18T01:59:59Z',
            'strategy_name': 'sname',
            'portfolio':[
                'AAPL', 'V', 'CSCO'
            ]
        }

        p = Portfolio.from_dict(d)

        self.assertEqual(p.portfolio_id, d['portfolio_id'])
        self.assertEqual(p.creation_date.year, 2020)
        self.assertEqual(p.creation_date.month, 2)
        self.assertEqual(p.creation_date.day, 18)
        self.assertEqual(p.creation_date.hour, 1)
        self.assertEqual(p.creation_date.minute, 59)
        self.assertEqual(p.creation_date.second, 59)

        self.assertEqual(p.data_date.year, 2019)
        self.assertEqual(p.data_date.month, 1)
        self.assertEqual(p.data_date.day, 18)
        self.assertEqual(p.data_date.hour, 1)
        self.assertEqual(p.data_date.minute, 59)
        self.assertEqual(p.data_date.second, 59)

        self.assertEqual(d['strategy_name'], p.strategy_name)
        self.assertListEqual(p.portfolio, ['AAPL', 'V', 'CSCO'])

    def test_valid_datadate_yyyy_mm_dd(self):
        d = {
            'portfolio_id': 'xxx',
            'creation_date': '2020-02-18T01:59:59Z',
            'data_date': '2019-01-18',
            'strategy_name': 'sname',
            'portfolio':[
                'AAPL', 'V', 'CSCO'
            ]
        }

        p = Portfolio.from_dict(d)

        self.assertEqual(p.data_date.year, 2019)
        self.assertEqual(p.data_date.month, 1)
        self.assertEqual(p.data_date.day, 18)
        self.assertEqual(p.data_date.hour, 0)
        self.assertEqual(p.data_date.minute, 0)
        self.assertEqual(p.data_date.second, 0)

        # now test that data date can be converted back to string
        d = p.to_dict()
        self.assertEqual(d['data_date'], "2019-01-18T00:00:00")


    def test_valid_dictionary(self):
        p = Portfolio(datetime(2020, 6, 5, 12, 30, 0), datetime(2019, 4, 3, 12, 30, 0), 'x', ['AAPL', 'INTC'])
        self.assertDictEqual(p.to_dict(), {
            'portfolio_id': p.portfolio_id, 
            'creation_date': '2020-06-05T16:30:00+00:00', 
            'data_date': '2019-04-03T12:30:00', 
            'strategy_name': 'x', 
            'portfolio': ['AAPL', 'INTC']
        })

