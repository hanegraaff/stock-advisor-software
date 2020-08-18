"""test_script.py

A general purpose test script. Nothing to see here.
"""
import argparse
import logging
import logging
from datetime import datetime, timedelta, time
from datetime import date, time
import pandas_market_calendars as mcal
import pandas as pd

from support import logging_definition, util, constants
from connectors import connector_test, intrinio_data, td_ameritrade
from strategies.macd_crossover_strategy import MACDCrossoverStrategy
from strategies.price_dispersion_strategy import PriceDispersionStrategy
from model.ticker_list import TickerList
from model.positions import Positions
from model.pportfolio import Portfolio
from support import constants, util
from support.configuration import Configuration
from services.portfolio_manager import PortfolioManager
from services.broker_new import Broker
from exception.exceptions import ValidationError

#
# Main script
#

log = logging.getLogger()


def main():
    '''
        Main testing script
    '''
    try:

        #test_portfolio_manager()
        #test_broker()
        test_read_transactions()

    except Exception as e:
        log.error("Could run script, because, %s" % (str(e)))
        raise e


def test_read_transactions():
    '''
        test the ability to read historical transaction
    '''
    recent_transactions = td_ameritrade.list_recent_transactions()
    print(util.format_dict(recent_transactions))


def test_broker():
    '''
        Tests the broker and its features
    '''
    portfolio_dict = {
        "portfolio_id": "58c390ec-d64e-11ea-89bf-acbc329ef75f",
        "portfolio_type": "CURRENT_PORTFOLIO",
        "creation_date": "2020-08-04T12:30:57.322597+00:00",
        "price_date": "2020-08-03",
        "last_updated": "2020-08-04T12:30:57.588363+00:00",
        "open_positions": [
            {
                "ticker_symbol": "VZ",
                "ls_indicator": "LONG",
                "strategy_name": "MACD_CROSSOVER",
                "current_price": 57.24,
                "quantity": 0,
                "pnl": 0
            },
            {
                "ticker_symbol": "TRV",
                "ls_indicator": "LONG",
                "strategy_name": "MACD_CROSSOVER",
                "current_price": 114.4,
                "quantity": 0,
                "pnl": 0
            },
            {
                "ticker_symbol": "BA",
                "ls_indicator": "LONG",
                "strategy_name": "PRICE_DISPERSION",
                "current_price": 162.27,
                "quantity": 0,
                "pnl": 0
            }
        ]
    }

    portfolio = Portfolio.from_dict(portfolio_dict)

    broker = Broker()
    broker.reconcile_portfolio(portfolio)


def test_portfolio_manager():
    '''
        Tests the portfolio manager and its features
    '''
    ticker_list = TickerList.from_local_file(
        "%s/djia30.json" % (constants.APP_DATA_DIR))

    config = Configuration.try_from_s3(
        constants.STRATEGY_CONFIG_FILE_NAME, 'sa')

    #macd_strategy = MACDCrossoverStrategy.from_configuration(config, 'sa')
    macd_strategy = MACDCrossoverStrategy(
        ticker_list, date(2020, 6, 16), 0.0016, 12, 26, 9)
    macd_strategy.generate_recommendation()
    #macd_strategy.display_results()

    #pd_strategy = PriceDispersionStrategy.from_configuration(config, 'sa')
    pd_strategy = PriceDispersionStrategy(
        ticker_list, '2020-06', date(2020, 6, 16), 3)
    pd_strategy.generate_recommendation()
    #pd_strategy.display_results()

    recommendation_list = [macd_strategy.recommendation_set, pd_strategy.recommendation_set]

    pman = PortfolioManager()

    portfolio = pman.create_new_portfolio(recommendation_list, 3)
    #print(util.format_dict(portfolio.model))

    pd_strategy.recommendation_set.model['securities_set'].pop()

    pman.update_portfolio(portfolio, recommendation_list, None, 3)
    print(util.format_dict(portfolio.model))

    portfolio.reprice(util.get_business_date(constants.BUSINESS_DATE_DAYS_LOOKBACK, 
                            constants.BUSINESS_DATE_CUTOVER_TIME))

    print(util.format_dict(portfolio.model))



def test_position_from_dict():
    '''
        Tests the creation of a positions object initialized 
        using a dictionary 
    '''
    positions_dict = {
        "positions_id": "123",
        "positions_type": "OPEN_POSITIONS",
        "creation_date": "2020-06-23T12:30:47.271203+00:00",
        "price_date": "2020-06-23",
        "last_updated": "2020-06-23T12:30:47.271203+00:00",
        "positions": [{
            "ticker_symbol": "AAPL",
            "ls_indicator": "LONG",
            "strategy_name": "MACD_CROSSOVER",
            "current_price": 0,
            "quantity": 100,
            "pnl": 100,
            "open": {
                "price": 100,
                "date": None,
                "order_id": "1234",
                "order_status": None, 
                "reason": "RECOMMENDATION"
            }
        }]
    }

    positions = Positions.from_dict(positions_dict)

    positions.validate_model()


if __name__ == "__main__":
    main()
