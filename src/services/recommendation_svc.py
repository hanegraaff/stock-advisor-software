"""Author: Mark Hanegraaff -- 2020

This module contains supporting logic for reccomendation service script.
It exists solely so that the code may be tested. otherwise it would
be organized along with the service itself.
"""
import logging
from connectors import aws_service_wrapper
from support import constants
import dateutil.parser as parser

log = logging.getLogger()


def notify_new_recommendation(notification_list: list, app_ns: str):
    '''
        Sends an SNS notification indicating that a new recommendation has been generated

        Parameters
        ----------
        notification_list: list
            List of new SecurityRecommendationSet objects that require notifications
        app_ns: str
            The application namespace supplied to the command line
            used to identify the appropriate CloudFormation exports
    '''
    if notification_list == None or len(notification_list) == 0:
        return

    message = ""
    sns_topic_arn = aws_service_wrapper.cf_read_export_value(
        constants.sns_app_notifications_topic_arn(app_ns))
    subject = "New Stock Recommendation Available"

    for recommendation_set in notification_list:
        formatted_ticker_message = ""

        for security in recommendation_set.model['securities_set']:
            formatted_ticker_message += "Ticker Symbol: %s\n" % security[
                'ticker_symbol']

        message += "A New Stock Recommendation is available for the following trading strategy %s\n" % recommendation_set.model[
            'strategy_name']
        message += "\n"
        message += formatted_ticker_message

        message += "\n\n"

    log.info("Publishing Recommendation set to SNS topic: %s" %
             sns_topic_arn)
    aws_service_wrapper.sns_publish_notification(
        sns_topic_arn, subject, message)
