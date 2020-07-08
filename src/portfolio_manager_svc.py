"""Author: Mark Hanegraaff -- 2020
    Portfolio Manager Main Script

    Complete documentation can be found here:
    https://github.com/hanegraaff/stock-advisor-software
"""

import argparse
import logging
import traceback
from datetime import datetime
from model.recommendation_set import SecurityRecommendationSet
from support import constants, util, logging_definition
from connectors import connector_test, td_ameritrade, aws_service_wrapper
from model.portfolio import Portfolio
from exception.exceptions import AWSError
from services import portfolio_mgr_svc
from services.broker import Broker
from support import util

log = logging.getLogger()


def parse_params():
    """
        Parse command line parameters

        Returns
        ----------
        A tuple containing the application paramter values
    """

    description = """ Executes trades and maintains a portfolio based on the output
                  of the recommendation service
              """

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-app_namespace", help="Application namespace used to identify AWS resources", type=str, required=True)
    parser.add_argument(
        "-portfolio_size", help="Number of securties that will be part of the portfolio", type=int, required=True)

    args = parser.parse_args()

    app_ns = args.app_namespace
    portfolio_size = args.portfolio_size

    if portfolio_size <= 0:
        log.error("Portfolio Size (-portfolio_size) must be a positive number")
        exit(-1)

    return (app_ns, portfolio_size)


def main():
    """
        Main function of this script
    """
    try:
        #(app_ns, portfolio_size) = parse_params()
        (app_ns, portfolio_size) = ('sa', 3)

        log.info("Application Parameters")
        log.info("-app_namespace: %s" % app_ns)
        log.info("-portfolio_size: %d" % portfolio_size)

        # test all connectivity upfront, so if there any issues
        # the problem becomes more apparent
        connector_test.test_all_connectivity()

        (current_portfolio,
         security_recommendation) = portfolio_mgr_svc.get_service_inputs(app_ns)

        log.info("Loaded recommendation set id: %s" %
                 security_recommendation.model['set_id'])

        if current_portfolio is None:
            log.info("Creating new portfolio")
            current_portfolio = Portfolio(None)
            current_portfolio.create_empty_portfolio(security_recommendation)
        else:
            log.info("Repricing portfolio")
            current_portfolio.reprice(datetime.now())

        (updated_portfolio, updated) = portfolio_mgr_svc.update_portfolio(
            current_portfolio, security_recommendation, portfolio_size)

        # See if there is anything that needs to be traded
        market_open = td_ameritrade.equity_market_open(datetime.now())

        if market_open == True:
            broker = Broker()
            broker.cancel_all_open_orders()

            log.info("Market is open. Looking for trading opportunities")
            current_positions = td_ameritrade.positions_summary()

            try:
                if broker.reconcile_portfolio(current_positions, updated_portfolio) == False:
                    log.info(
                        "Portfolio is not in sync with brokerage account positions. Positions will be rebalanced")

                broker.materialize_portfolio(
                    current_positions, updated_portfolio)
            finally:
                updated_positions = td_ameritrade.positions_summary()
                broker.synchronize_portfolio(
                    updated_positions, updated_portfolio)

                updated_portfolio.recalc_returns()
                broker.cancel_all_open_orders()
        else:
            log.info("Market is closed. Nothing to trade")

        log.info("updated portfolio: %s" %
                 util.format_dict(updated_portfolio.to_dict()))

        log.info("Saving updated portfolio")
        updated_portfolio.save_to_s3(
            app_ns, constants.S3_PORTFOLIO_OBJECT_NAME)

        portfolio_mgr_svc.publish_current_returns(
            updated_portfolio, updated, app_ns)

    except Exception as e:
        stack_trace = traceback.format_exc()
        log.error("Could run script, because: %s" % (str(e)))
        log.error(stack_trace)

        aws_service_wrapper.notify_error(e, "Portfolio Manager Service",
                                         stack_trace, app_ns)

if __name__ == "__main__":
    main()
