"""Author: Mark Hanegraaff -- 2020
"""

import logging
from connectors import td_ameritrade
from exception.exceptions import ValidationError, TradeError
from model.pportfolio import Portfolio
from support import util

log = logging.getLogger()


class PortfolioManager():
    """
        A data structure representing a set of positions.
        Positions are created and maintained by the Portfolio Manager service.
    """

    broker = Broker()


    def create_new_portfolio(self, recommendation_list: list, portfolio_size: int):
        '''
            Creates a new portfolio based on an existing set of recommendations.
            Securities are selected using a round robin approach.

            Returns
            -------
            A new instance of a portfolio
        '''
        pass

    def update_portfolio(self, portfolio: object, recommendation_list: list, stop_loss: object):
        '''
            Updates the contents of a portfolio based on a recommendation list
            and a stop loss object.

            Returns
            -------
            An updated portfolio instance
        '''
        pass


    def reconcile_portfolio(self, portfolio: object):
        '''
            Compares the current portfolio with the current positions recorded
            in the Brokerage account. Returns true if symbol and quantity match,
            otherwise returns false.

            Parameters
            ----------
            broker_positions : dict
                Current positions fetched from the brokerage account

            current_portfolio : object
                Current Portfolio object
        '''



    def materialize_portfolio(self, portfolio: object):
        '''
            Materializes the portfolio by executing all necessary trades
            to to create matching positions
        '''
        pass