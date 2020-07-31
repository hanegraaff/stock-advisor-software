"""Author: Mark Hanegraaff -- 2020
"""

import logging
import uuid
import random
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
                returns True if there are any recommendations left. Useful when the
                portfolio size exceeds the available recommendations
            '''
            for strategy_name in recommendation_dict.keys():
                if len(recommendation_dict[strategy_name]) > 0:
                    return True
            return False
        
        def contains_security(ticker_symbol: str):
            for position in new_portfolio_dict['open_positions']:
                if position['ticker_symbol'] == ticker_symbol:
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
            recommendation_dict[rec.model['strategy_name']] = rec.get_security_list()

        strategies = itertools.cycle(sorted(recommendation_dict.keys()))

        remaining_items = portfolio_size

        for next_strategy in strategies:
            try:
                next_security = recommendation_dict[next_strategy].pop()

                if contains_security(next_security):
                    continue
                remaining_items -= 1
                new_portfolio_dict['open_positions'].append({
                    "ticker_symbol": next_security,
                    "ls_indicator": "LONG",
                    "strategy_name": next_strategy,
                    "current_price": 0,
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


    def update_portfolio(self, portfolio: object, recommendation_list: list, stop_loss: object, desired_portfolio_size: int):
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
        def unwind_non_recommended_positions():
            '''
                Mark any positions that are no longer recommended so that they
                may be unwound by the Broker object
            '''
            for position in portfolio.model['open_positions']:
                if (position['ticker_symbol'], position['strategy_name']) not in all_recommended_securities:
                    sell_securities.append(position['ticker_symbol'])

            for sell_security in sell_securities:
                portfolio.unwind_position(sell_security, 'RECOMMENDATION')
        
        def generate_portfolio_candidates():
            '''
                Returns the candidates that can be added to the portfolio.
                "All Recommended Securities - Portfolio securities"
            '''
            portfolio_candidates = deepcopy(all_recommended_securities)

            for position in portfolio.model['open_positions']:
                ptuple = (position['ticker_symbol'], position['strategy_name'])
                if ptuple in portfolio_candidates:
                    portfolio_candidates.remove(ptuple)
            
            return portfolio_candidates

        def resize_portfolio(portfolio_candidates: list):
            '''
                Adds or removes positions from the portfolio to ensure that it is
                of the desired size. When removing positions, remove those with
                the lowest PNL
            '''

            remaining_positions = desired_portfolio_size - portfolio.get_active_position_count()
            if remaining_positions > len(portfolio_candidates):
                remaining_positions = len(portfolio_candidates)
            
            if remaining_positions == 0:
                return
            elif remaining_positions > 0:
                for i in range(remaining_positions):

                    random_security = random.choice(portfolio_candidates)

                    portfolio.model['open_positions'].append({
                        "ticker_symbol": random_security[0],
                        "ls_indicator": "LONG",
                        "strategy_name": random_security[1],
                        "current_price": 0,
                        "quantity": 0,
                        "pnl": 0
                    })

                    portfolio_candidates.remove(random_security)
            else:
                # remove positions with the lowest PNL
                positions_pnl = []
                for position in portfolio.model['open_positions']:
                    if 'pending_command' not in position:
                        positions_pnl.append((position['ticker_symbol'], position['pnl']))

                sorted_pnl = sorted(positions_pnl, reverse=True, key=lambda x: x[1])

                for i in range(abs(remaining_positions)):
                    removed_ticker = sorted_pnl.pop()[0]
                    portfolio.unwind_position(removed_ticker, 'PORTFOLIO_RESIZE')
        
        sell_securities = []
        all_recommended_securities = []
            
        for recommendation_set in recommendation_list:
            all_recommended_securities += [(security, recommendation_set.model['strategy_name']) for security in recommendation_set.get_security_list()]

        unwind_non_recommended_positions()
        portfolio_candidates = generate_portfolio_candidates()
        resize_portfolio(portfolio_candidates)

        portfolio.validate_model()


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