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
from connectors import connector_test, intrinio_data
from strategies.macd_crossover_strategy import MACDCrossoverStrategy
from strategies.price_dispersion_strategy import PriceDispersionStrategy
from model.ticker_list import TickerList
from model.positions import Positions
from model.pportfolio import Portfolio
from support import constants, util
from support.configuration import Configuration
from services.portfolio_manager import PortfolioManager
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
        ticker_list = TickerList.from_local_file(
            "%s/djia30.json" % (constants.APP_DATA_DIR))

        config = Configuration.try_from_s3(
            constants.STRATEGY_CONFIG_FILE_NAME, 'sa')

        macd_strategy = MACDCrossoverStrategy.from_configuration(config, 'sa')
        #macd_strategy = MACDCrossoverStrategy(
        #    ticker_list, date(2020, 6, 16), 0.0016, 12, 16, 9)
        macd_strategy.generate_recommendation()
        #macd_strategy.display_results()

        pd_strategy = PriceDispersionStrategy.from_configuration(config, 'sa')
        #pd_strategy = PriceDispersionStrategy(
        #    ticker_list, '2020-06', date(2020, 5, 16), 3)
        pd_strategy.generate_recommendation()
        #pd_strategy.display_results()

        '''positions_dict = {
            "positions_id": "123",
            "positions_type": "OPEN_POSITIONS",
            "creation_date": "2020-06-23T12:30:47.271203+00:00",
            "last_updated": "2020-06-23T12:30:47.271203+00:00",
            "positions": [{
                "ticker_symbol": "AAPL",
                "ls_indicator": "LONG",
                "strategy_name": "MACD_CROSSOVER",
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

        positions.validate_model()'''

        pman = PortfolioManager()

        portfolio = pman.create_new_portfolio([macd_strategy.recommendation_set, pd_strategy.recommendation_set], 3 )

        print(util.format_dict(portfolio.model))
        print(util.format_dict(pd_strategy.recommendation_set.model))

    except Exception as e:
        log.error("Could run script, because, %s" % (str(e)))
        #raise e

if __name__ == "__main__":
    main()
