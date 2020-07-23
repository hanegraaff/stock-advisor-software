"""Author: Mark Hanegraaff -- 2020
"""

import logging
import uuid
from copy import deepcopy
from datetime import datetime
from connectors import td_ameritrade
from exception.exceptions import ValidationError, TradeError
from model.pportfolio import Portfolio
from services.broker import Broker
from support import util
import itertools

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
            Securities are selected by sorting the recommendations and selecting
            securities using a round robin. This is done to ensure the selection process
            is deterministic.

            Parameters
            ----------
            recommendation_list: list
                The list of SecurityRecommendationSets used to construct the portfolio
            portfolio_size: int
                The number of recommended securities to include in the portfolio
            
            Returns
            ----------
            A new instance of a portfolio
        '''

        def more_recommendations():
            '''
                returns true if there are any recommendations left. Useful when the
                portfolio size exceeds the available recommendations
            '''
            for strategy_name in recommendation_dict.keys():
                if len(recommendation_dict[strategy_name]) > 0:
                    return True

            return False

        if portfolio_size <= 0:
            raise ValidationError("Portfolio must contain at least one security", None)

        create_time = util.datetime_to_iso_utc_string(datetime.now())

        new_portfolio_dict = {
            "portfolio_id": str(uuid.uuid1()),
            "portfolio_type": "CURRENT_PORTFOLIO",
            "creation_date": create_time,
            "last_updated": create_time,
            "open_positions": []
        }

        #{strategy_name: securities_set}
        recommendation_dict = {}

        for rec in recommendation_list:
            recommendation_dict[rec.model['strategy_name']] = deepcopy(rec.model['securities_set'])

        strategies = itertools.cycle(sorted(recommendation_dict.keys()))

        remaining_items = portfolio_size

        for next_strategy in strategies:
            try:
                next_recommendation = recommendation_dict[next_strategy].pop()['ticker_symbol']
                remaining_items -= 1

                new_portfolio_dict['open_positions'].append({
                    "ticker_symbol": next_recommendation,
                    "ls_indicator": "LONG",
                    "strategy_name": next_strategy,
                    "quantity": 0,
                    "pnl": 0
                })

                if remaining_items <= 0:
                    break
            except IndexError:
                if not more_recommendations():
                    return Portfolio.from_dict(new_portfolio_dict)
            except Exception as e:
                raise ValidationError("Error while assembling new portfolio", e)
        
        return Portfolio.from_dict(new_portfolio_dict)


    def update_portfolio(self, portfolio: object, recommendation_list: list, stop_loss: object):
        '''
            Updates the contents of a portfolio based on a recommendation list
            and a stop loss object.

            1) Remove securities from portfolio that are not in recommendation List
            2) Create a candidate list made up recommendations - portfolio securities
            3) Select random items from the candidate list and update portfolio

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