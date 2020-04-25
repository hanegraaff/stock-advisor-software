import argparse
import logging
from datetime import datetime
from model.recommendation_set import SecurityRecommendationSet 
from support import constants, util, logging_definition
from model.portfolio import Portfolio
from exception.exceptions import AWSError
from service_support import portfolio_mgr_svc
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
    parser.add_argument("-app_namespace", help="Application namespace used to identify AWS resources", type=str, required=True)
    parser.add_argument("-portfolio_size", help="Number of securties that will be part of the portfolio", type=int, required=True)

    args = parser.parse_args()

    app_ns = args.app_namespace
    portfolio_size = args.portfolio_size

    return (app_ns, portfolio_size)

try:
    (app_ns, portfolio_size) = parse_params()

    log.info("Application Parameters")
    log.info("-app_namespace: %s" % app_ns)
    log.info("-portfolio_size: %d" % portfolio_size)

    (current_portfolio, sr) = portfolio_mgr_svc.get_service_inputs(app_ns)

    log.info("Loaded recommendation set id: %s" % sr.model['set_id'])

    if current_portfolio == None:
        log.info("Creating new portfolio")
        current_portfolio = Portfolio()
        current_portfolio.create_empty_portfolio(sr)
    else:
        log.info("Repricing portfolio")
        current_portfolio.reprice(datetime.now())


    (updated_portfolio, updated) = portfolio_mgr_svc.update_portfolio(current_portfolio, sr, portfolio_size)

    log.info("updated portfolio: %s" % util.format_dict(updated_portfolio.to_dict()))

    log.info("Saving updated portfolio")
    updated_portfolio.save_to_s3(app_ns)
    
    portfolio_mgr_svc.publish_current_returns(updated_portfolio, updated, app_ns)


except Exception as e:
    log.error("Could not run Portfolio Manager, because: %s" % str(e))
    #raise e