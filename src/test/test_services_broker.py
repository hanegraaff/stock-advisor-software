"""Author: Mark Hanegraaff -- 2020
    Testing class for the services.broker module
"""
import unittest
import botocore
from copy import deepcopy
from connectors import td_ameritrade
from exception.exceptions import TradeError
from unittest.mock import patch
from model.portfolio import Portfolio
from services.broker import Broker


class TestBroker(unittest.TestCase):

    """
        Testing class for the services.broker module
    """

    base_portfolio = {
        "portfolio_id": "2485a5e6-8e18-11ea-ab08-0e8077acf87d",
        "set_id": "8937aa02-8c29-11ea-92af-0a98cddf4637",
        "creation_date": "2020-05-04T15:01:33.131964+00:00",
        "price_date": "2020-05-05T00:00:00+00:00",
        "securities_set": [],
        "current_portfolio": {
            "securities": [
                {
                    "ticker_symbol": "BA",
                    "quantity": 0,
                    "purchase_date": None,
                    "purchase_price": 1.0,
                    "current_price": 1.0,
                    "current_returns": 0.0,
                    "trade_state": "UNFILLED",
                    "order_id": None
                },
                {
                    "ticker_symbol": "GE",
                    "quantity": 0,
                    "purchase_date": None,
                    "purchase_price": 1.0,
                    "current_price": 1.0,
                    "current_returns": 0.0,
                    "trade_state": "UNFILLED",
                    "order_id": None
                },
                {
                    "ticker_symbol": "XOM",
                    "quantity": 0,
                    "purchase_date": None,
                    "purchase_price": 1.0,
                    "current_price": 1.0,
                    "current_returns": 0.0,
                    "trade_state": "UNFILLED",
                    "order_id": None
                }
            ]
        }
    }

    base_positions = {
        'equities': {
            'BA': {
                'longQuantity': 1.0,
                'averagePrice': 10.0,
                'marketValue': 10.0
            },
            'GE': {
                'longQuantity': 1.0,
                'averagePrice': 10.0,
                'marketValue': 10.0
            },
            'XOM': {
                'longQuantity': 1.0,
                'averagePrice': 10.0,
                'marketValue': 10.0
            }

        },
        'cash': {
            'cashAvailableForTrading': 100
        }
    }

    '''
        reconcile_portfolio tests
    '''

    def test_reconcile_portfolio_matching(self):
        portfolio = deepcopy(self.base_portfolio)

        # this is the bare minimum required to reconcile the portfolio
        for sec in portfolio['current_portfolio']['securities']:
            sec['quantity'] = 1
            sec['trade_state'] = 'FILLED'

        portfolio = Portfolio.from_dict(portfolio)
        broker = Broker()
        self.assertTrue(broker.reconcile_portfolio(
            self.base_positions, portfolio))

    def test_reconcile_portfolio_fewer_positions(self):
        pfolio = deepcopy(self.base_portfolio)
        pos = deepcopy(self.base_positions)

        del pfolio['current_portfolio']['securities'][0]

        with patch.object(td_ameritrade, 'login', return_value=None):

            portfolio = Portfolio.from_dict(pfolio)
            broker = Broker()
            self.assertFalse(broker.reconcile_portfolio(pos, portfolio))

    def test_reconcile_portfolio_mismatching_ticker(self):
        pfolio = deepcopy(self.base_portfolio)
        pos = deepcopy(self.base_positions)

        pfolio['current_portfolio']['securities'][0]['ticker_symbol'] = 'XXX'

        with patch.object(td_ameritrade, 'login', return_value=None):
            portfolio = Portfolio.from_dict(pfolio)
            broker = Broker()
            self.assertFalse(broker.reconcile_portfolio(pos, portfolio))

    def test_reconcile_portfolio_mismatching_quantity(self):
        pfolio = deepcopy(self.base_portfolio)

        pfolio['current_portfolio']['securities'][0]['quantity'] = 999

        portfolio = Portfolio.from_dict(pfolio)
        broker = Broker()
        self.assertFalse(broker.reconcile_portfolio(
            self.base_positions, portfolio))

    '''
        Synchronize Portfolio tests
    '''

    def test_synchronize_portfolio_all_positions_filled(self):
        portfolio = Portfolio.from_dict(self.base_portfolio)
        broker = Broker()
        broker.synchronize_portfolio(self.base_positions, portfolio)

        for sec in portfolio.model['current_portfolio']['securities']:
            self.assertEqual(sec['trade_state'], 'FILLED')
            self.assertEqual(sec['purchase_price'],
                             self.base_positions['equities'][sec['ticker_symbol']]['averagePrice'])

    def test_synchronize_portfolio_no_boker_positions_filled(self):
        portfolio = Portfolio.from_dict(self.base_portfolio)
        broker = Broker()
        broker.synchronize_portfolio({'equities': {},
                                      'cash': {
            'cashAvailableForTrading': 100
        }
        }, portfolio)

        for sec in portfolio.model['current_portfolio']['securities']:
            self.assertEqual(sec['trade_state'], 'UNFILLED')

    def test_synchronize_portfolio_all_extra_broker_positions(self):
        portfolio = Portfolio.from_dict(self.base_portfolio)
        positions = deepcopy(self.base_positions)
        broker = Broker()
        broker.synchronize_portfolio(positions, portfolio)

        positions['equities']['XXX'] = {
            'longQuantity': 1.0,
            'averagePrice': 10.0,
            'marketValue': 10.0
        }

        for sec in portfolio.model['current_portfolio']['securities']:
            self.assertEqual(sec['trade_state'], 'FILLED')
            self.assertEqual(sec['purchase_price'],
                             positions['equities'][sec['ticker_symbol']]['averagePrice'])

    def test_synchronize_portfolio_all_extra_portfolio_positions(self):
        portfolio = Portfolio.from_dict(self.base_portfolio)

        broker = Broker()
        broker.synchronize_portfolio(self.base_positions, portfolio)

        portfolio.model['current_portfolio']['securities'].append(
            {
                "ticker_symbol": "XXX",
                "quantity": 1,
                "purchase_date": None,
                "purchase_price": 1.0,
                "current_price": 1.0,
                "current_returns": 0.0,
                "trade_state": "UNFILLED",
                "order_id": None
            }
        )

        self.assertEqual(portfolio.get_position('XXX')
                         ['trade_state'], 'UNFILLED')

    '''
        generate_test_instructions tests
    '''

    def test_generate_test_instructions_no_positions(self):
        portfolio = Portfolio.from_dict(self.base_portfolio)
        broker = Broker()
        (sell_list, buy_list) = broker._generate_trade_instructions({}, portfolio)

        self.assertListEqual(sell_list, [])
        self.assertListEqual(buy_list, ['BA', 'GE', 'XOM'])

    def test_generate_test_instructions_with_sells(self):
        portfolio = deepcopy(self.base_portfolio)
        del portfolio['current_portfolio']['securities'][2]
        del portfolio['current_portfolio']['securities'][1]

        portfolio = Portfolio.from_dict(portfolio)

        broker = Broker()
        (sell_list, buy_list) = broker._generate_trade_instructions(
            self.base_positions, portfolio)

        self.assertListEqual(sell_list, [('GE', 1), ('XOM', 1)])
        self.assertListEqual(buy_list, [])

    def test_generate_test_instructions_with_buys(self):
        positions = deepcopy(self.base_positions)
        del positions['equities']['GE']
        del positions['equities']['XOM']

        portfolio = Portfolio.from_dict(self.base_portfolio)

        broker = Broker()
        (sell_list, buy_list) = broker._generate_trade_instructions(
            positions, portfolio)

        self.assertListEqual(sell_list, [])
        self.assertListEqual(buy_list, ['GE', 'XOM'])

    def test_generate_test_instructions_nothing_to_do(self):
        portfolio = Portfolio.from_dict(self.base_portfolio)
        broker = Broker()
        (sell_list, buy_list) = broker._generate_trade_instructions(
            self.base_positions, portfolio)

        self.assertListEqual(sell_list, [])
        self.assertListEqual(buy_list, [])

    '''
        cancel_all_open_orders tests
    '''

    def test_cancel_all_open_orders_num_calls(self):
        '''
            Test that given a list of orders, some cancelable, some not,
            that only the cancelable ones are being considered
        '''
        with patch.object(td_ameritrade, 'cancel_order', return_value=None) as mock_cancel_order, \
                patch.object(td_ameritrade, 'list_recent_orders', return_value={
                    "order-1": {
                        "status": "FILLED",
                        "symbol": "BA",
                        "quantity": 1,
                        "closeTime": "2020-05-04T03:21:04+0000",
                        "tag": "AA_myuser",
                        "cancelable": False
                    },
                    "order-2": {
                        "status": "WORKING",
                        "symbol": "BA",
                        "quantity": 1,
                        "closeTime": None,
                        "tag": "AA_myuser",
                        "cancelable": True
                    },
                    "order-3": {
                        "status": "WORKING",
                        "symbol": "BA",
                        "quantity": 1,
                        "closeTime": None,
                        "tag": "AA_myuser",
                        "cancelable": True
                    },
                }):

            broker = Broker()
            broker.cancel_all_open_orders()

            self.assertEqual(mock_cancel_order.call_count, 2)

    def test_cancel_all_open_orders_with_exception(self):
        '''
            Test that given a list of orders, some cancelable, some not,
            that only the cancelable ones are being considered
        '''
        with patch.object(td_ameritrade, 'cancel_order', side_effect=TradeError("SomeError", None, None)), \
                patch.object(td_ameritrade, 'list_recent_orders', return_value={
                    "order-1": {
                        "status": "FILLED",
                        "symbol": "BA",
                        "quantity": 1,
                        "closeTime": "2020-05-04T03:21:04+0000",
                        "tag": "AA_myuser",
                        "cancelable": True
                    }
                }):

            broker = Broker()
            broker.cancel_all_open_orders()

    '''
        materialize_portfolio tests
    '''

    def test_materialize_portfolio_cannot_sell(self):
        with patch.object(Broker, '_generate_trade_instructions', return_value=([('BA', 3)], [])), \
                patch.object(Broker, 'trade', return_value=False):

            broker = Broker()

            # Since I am patching "_generate_trade_instructions" these parameters
            # don't really matter
            with self.assertRaises(TradeError):
                broker.materialize_portfolio(
                    self.base_positions, self.base_portfolio)

    def test_materialize_portfolio_no_cash_to_buy(self):
        '''
            Tests that when there is no cash to buy trades, no trading will
            be attempted
        '''
        with patch.object(Broker, '_generate_trade_instructions', return_value=([], ['BA', 'AAPL', 'MSFT'])), \
                patch.object(td_ameritrade, 'positions_summary', return_value={
                    "equities": {},
                    "cash": {
                        "cashAvailableForTrading": 1,
                    }
                }), \
                patch.object(td_ameritrade, 'get_latest_equity_price', return_value=100), \
                patch.object(Broker, 'trade', return_value=True) as mock_trade:

            broker = Broker()

            broker.materialize_portfolio(
                self.base_positions, self.base_portfolio)
            self.assertEqual(mock_trade.call_count, 0)

    '''
        trade tests
    '''

    def test_trade_nothing_to_sell(self):
        '''
            Tests that when there is nothing to trade, 'trade' will still
            return true
        '''
        sell_positions = []

        broker = Broker()
        self.assertTrue(broker.trade('SELL', sell_positions, None))

    def test_trade_sell_single_security(self):

        sell_positions = [('BA', 1.0)]

        with patch.object(td_ameritrade, 'place_order', return_value='order-xxx'), \
                patch.object(td_ameritrade, 'list_recent_orders', return_value={
                    "order-xxx": {
                        "status": "FILLED",
                        "symbol": "BA",
                        "quantity": 1,
                        "closeTime": "2020-05-04T03:21:04+0000",
                        "tag": "AA_myuser"
                    },
                }):

            broker = Broker()
            self.assertTrue(broker.trade('SELL', sell_positions, None))

    def test_trade_buy_single_security(self):

        buy_positions = [('BA', 1.0)]

        portfolio = deepcopy(self.base_portfolio)
        del portfolio['current_portfolio']['securities'][2]
        del portfolio['current_portfolio']['securities'][1]

        portfolio = Portfolio.from_dict(portfolio)

        with patch.object(td_ameritrade, 'place_order', return_value='order-xxx'), \
                patch.object(td_ameritrade, 'list_recent_orders', return_value={
                    "order-xxx": {
                        "status": "FILLED",
                        "symbol": "BA",
                        "quantity": 1,
                        "closeTime": "2020-05-04T03:21:04+0000",
                        "tag": "AA_myuser"
                    },
                }):

            broker = Broker()
            self.assertTrue(broker.trade('BUY', buy_positions, portfolio))

            pos = portfolio.get_position('BA')
            self.assertEqual(pos['trade_state'], 'FILLED')
            self.assertEqual(pos['quantity'], 1)
            self.assertIsNotNone(pos['purchase_date'])

    def test_trade_buy_multiple_securities(self):

        buy_positions = [('BA', 1.0), ('GE', 1.0), ('XOM', 1.0)]

        # portfolio has 3 positions
        portfolio = deepcopy(self.base_portfolio)

        portfolio = Portfolio.from_dict(portfolio)

        with patch.object(td_ameritrade, 'place_order', side_effect=[
                'order-1', 'order-2', 'order-3']), \
                patch.object(td_ameritrade, 'list_recent_orders', return_value={
                    "order-1": {
                        "status": "FILLED",
                        "symbol": "BA",
                        "quantity": 1,
                        "closeTime": "2020-05-04T03:21:04+0000",
                        "tag": "AA_myuser"
                    },
                    "order-2": {
                        "status": "FILLED",
                        "symbol": "GE",
                        "quantity": 1,
                        "closeTime": "2020-05-04T03:21:04+0000",
                        "tag": "AA_myuser"
                    },
                    "order-3": {
                        "status": "FILLED",
                        "symbol": "XOM",
                        "quantity": 1,
                        "closeTime": "2020-05-04T03:21:04+0000",
                        "tag": "AA_myuser"
                    },
                }):

            broker = Broker()
            self.assertTrue(broker.trade('BUY', buy_positions, portfolio))

            pos = portfolio.get_position('BA')
            self.assertEqual(pos['trade_state'], 'FILLED')
            self.assertEqual(pos['quantity'], 1)
            self.assertIsNotNone(pos['purchase_date'])

            pos = portfolio.get_position('GE')
            self.assertEqual(pos['trade_state'], 'FILLED')
            self.assertEqual(pos['quantity'], 1)
            self.assertIsNotNone(pos['purchase_date'])

            pos = portfolio.get_position('XOM')
            self.assertEqual(pos['trade_state'], 'FILLED')
            self.assertEqual(pos['quantity'], 1)
            self.assertIsNotNone(pos['purchase_date'])

    def test_trade_buy_multiple_securities_with_exception(self):

        buy_positions = [('BA', 1.0), ('GE', 1.0), ('XOM', 1.0)]

        # portfolio has 3 positions
        portfolio = deepcopy(self.base_portfolio)

        portfolio = Portfolio.from_dict(portfolio)

        with patch.object(td_ameritrade, 'place_order', side_effect=[
                'order-1', 'order-2', TradeError("Some Error", None, None)]), \
                patch.object(td_ameritrade, 'list_recent_orders', return_value={
                    "order-1": {
                        "status": "FILLED",
                        "symbol": "BA",
                        "quantity": 1,
                        "closeTime": "2020-05-04T03:21:04+0000",
                        "tag": "AA_myuser"
                    },
                    "order-2": {
                        "status": "FILLED",
                        "symbol": "GE",
                        "quantity": 1,
                        "closeTime": "2020-05-04T03:21:04+0000",
                        "tag": "AA_myuser"
                    }
                }):

            broker = Broker()
            self.assertFalse(broker.trade('BUY', buy_positions, portfolio))

    def test_trade_buy_failed_trades(self):

        buy_positions = [('BA', 1.0), ('GE', 1.0), ('XOM', 1.0)]

        # portfolio has 3 positions
        portfolio = deepcopy(self.base_portfolio)

        portfolio = Portfolio.from_dict(portfolio)

        with patch.object(td_ameritrade, 'place_order', side_effect=[
                'order-1', 'order-2', 'order-3']), \
                patch.object(td_ameritrade, 'list_recent_orders', return_value={
                    "order-1": {
                        "status": "FILLED",
                        "symbol": "BA",
                        "quantity": 1,
                        "closeTime": "2020-05-04T03:21:04+0000",
                        "tag": "AA_myuser"
                    },
                    "order-2": {
                        "status": "FILLED",
                        "symbol": "GE",
                        "quantity": 1,
                        "closeTime": "2020-05-04T03:21:04+0000",
                        "tag": "AA_myuser"
                    },
                    "order-3": {
                        "status": "UNKNOWN",
                        "symbol": "XOM",
                        "quantity": 1,
                        "closeTime": "2020-05-04T03:21:04+0000",
                        "tag": "AA_myuser"
                    },
                }):

            broker = Broker()
            self.assertTrue(broker.trade('BUY', buy_positions, portfolio))

            pos = portfolio.get_position('BA')
            self.assertEqual(pos['trade_state'], 'FILLED')
            self.assertEqual(pos['quantity'], 1)
            self.assertIsNotNone(pos['purchase_date'])

            pos = portfolio.get_position('GE')
            self.assertEqual(pos['trade_state'], 'FILLED')
            self.assertEqual(pos['quantity'], 1)
            self.assertIsNotNone(pos['purchase_date'])

            pos = portfolio.get_position('XOM')
            self.assertEqual(pos['trade_state'], 'UNFILLED')
            self.assertEqual(pos['quantity'], 0)
            self.assertIsNone(pos['purchase_date'])
