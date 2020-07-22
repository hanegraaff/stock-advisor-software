"""Author: Mark Hanegraaff -- 2020
"""
import logging
import random
import dateutil.parser as parser
from tzlocal import get_localzone
from datetime import datetime, date
from connectors import aws_service_wrapper
from exception.exceptions import ValidationError, AWSError
from model.pportfolio import Portfolio
from model.recommendation_set import SecurityRecommendationSet
from connectors import aws_service_wrapper
from support import util, constants

log = logging.getLogger()

"""
This module contains supporting logic for the portfolio manager script.
It exists solely so that the code may be tested. otherwise it would
be organized along with the service itself.
"""


def get_service_inputs(app_ns: str):
    '''
        Returns the required inputs for the portfolio manager service given
        the application namespace used to identify the appropriate cloud resources.

        Returns
        ----------
        A tuple containing a list of recommendation sets
        and current Portfolio objects.
    '''

    business_date = util.get_business_date(
        constants.BUSINESS_DATE_DAYS_LOOKBACK, constants.BUSINESS_DATE_CUTOVER_TIME)

    log.info("Using business date of: %s" % business_date)

    recommendation_list = []

    log.info("Loading latest recommendations")
    pd_recommendation_set = SecurityRecommendationSet.from_s3(
        app_ns, constants.S3_PRICE_DISPERSION_RECOMMENDATION_SET_OBJECT_NAME)
    if pd_recommendation_set.is_current(business_date):
        recommendation_list.append(pd_recommendation_set)
    else:
        log.warn("%s is no longer current and will not be used" % pd_recommendation_set.model_name)

    macd_recommendation_set = SecurityRecommendationSet.from_s3(
        app_ns, constants.S3_MACD_CROSSOVER_RECOMMENDATION_SET_OBJECT_NAME)
    if macd_recommendation_set.is_current(business_date):
        recommendation_list.append(macd_recommendation_set)
    else:
        log.warn("%s is no longer current and will not be used" % macd_recommendation_set.model_name)

    if len(recommendation_list) == 0:
        raise ValidationError("No recommendation sets could be used")
    try:
        log.info("Loading current portfolio")
        pfolio = Portfolio.from_s3(app_ns, constants.S3_PORTFOLIO_OBJECT_NAME)
    except AWSError as e:
        if e.resource_not_found():
            pfolio = None
        else:
            raise e

    return (pfolio, recommendation_list)


def update_portfolio(current_portfolio: object, recommendation_set: object, portfolio_size: int):
    '''
        Updates the portolio based on the recommendation set.

        1) When a portfolio is empty, then create a new one
        2) When a portfolio is stale (based on an old recommendation), rebalance it.
        3) Else, do nothing.

        Returns
        -------
        A tuple containing the updated portfolio (copy) and a boolean flag indicating
        whether positions were updated (and should be traded)
    '''
    def select_random_portfolio(portfolio_size: int):
        '''
            selects a randmon subset of the security set and creates
            a portfolio out out it.
        '''
        security_set = updated_portfolio.model['securities_set']

        # portfolio size cannot be larger than the available securitues
        # in the recommendation
        if len(security_set) < portfolio_size:
            portfolio_size = len(security_set)

        if not 'current_portfolio' in updated_portfolio.model:
            updated_portfolio.model['current_portfolio'] = {}

        updated_portfolio.model['current_portfolio']['securities'] = []

        for _ in range(0, portfolio_size):
            random_security = random.choice(security_set)

            updated_portfolio.model['current_portfolio']['securities'].append({
                "ticker_symbol": random_security['ticker_symbol'],
                "quantity": 0,
                "purchase_date": None,
                "purchase_price": 0,
                "current_price": random_security['current_price'],
                "current_returns": 0,
                "trade_state": "UNFILLED",
                "order_id": None
            }
            )

            security_set.remove(random_security)

    if portfolio_size <= 0:
        raise ValidationError("Portfolio Size must be a positive number", None)

    updated_portfolio = current_portfolio.copy()

    updated = False
    pfolio_set_id = current_portfolio.model['set_id']
    rec_set_id = recommendation_set.model['set_id']

    if current_portfolio.is_empty():
        log.info("Portfolio is empty, selecting a new one")
        select_random_portfolio(portfolio_size)
        updated = True

    elif pfolio_set_id != rec_set_id:
        log.info("Recommendation set has changed, rebalancing portfolio")
        updated_portfolio = Portfolio(None)
        updated_portfolio.create_empty_portfolio(recommendation_set)
        select_random_portfolio(portfolio_size)
        updated = True
    else:
        log.info("Portfolio is still current. No rebalancing necessary")

    updated_portfolio.validate_model()

    return (updated_portfolio, updated)


def publish_current_returns(updated_portfolio: object, updated: bool, app_ns: str):
    '''
        publishes current returns as a SNS notifcation, given an updated portfolio
    '''

    sns_topic_arn = aws_service_wrapper.cf_read_export_value(
        constants.sns_app_notifications_topic_arn(app_ns))
    subject = "Portfolio Update - "

    if updated == True:
        subject = "Stock Advisor Update - New Portfolio was created"
    else:
        subject = "Stock Advisor Update - Portfolio Returns"

    creation_date = parser.parse(updated_portfolio.model['creation_date'])
    price_date = parser.parse(updated_portfolio.model['price_date'])

    message = "Portfolio was created on: %s\n" % datetime.strftime(
        creation_date.astimezone(get_localzone()), '%Y/%m/%d %I:%M %p (%Z)')
    message += "Price date is: %s\n\n" % datetime.strftime(
        price_date, '%Y/%m/%d')
    for security in updated_portfolio.model['current_portfolio']['securities']:
        message += "Symbol: %s\n" % security['ticker_symbol']
        message += "Purchase Price: %.2f\n" % security[
            'purchase_price']
        message += "Current Price: %.2f (%+d%%)\n" % (
            security['current_price'], round(security['current_returns'] * 100))
        message += "\n"

    log.info("Publishing portfolio update to SNS topic: %s" % sns_topic_arn)
    aws_service_wrapper.sns_publish_notification(
        sns_topic_arn, subject, message)
