"""Author: Mark Hanegraaff -- 2020
"""
import json
from datetime import datetime, date
import pytz
import os
import pandas as pd
from datetime import datetime, timedelta, time
import pandas_market_calendars as mcal
from exception.exceptions import ValidationError, FileSystemError


def create_dir(dirname):
    """
        Creates the report directory if not already present
    """
    try:
        if not os.path.exists(dirname):
            os.makedirs(dirname)
    except Exception as e:
        raise FileSystemError("Can't create directory: %s" % dirname, e)


def format_dict(dict_string: dict):
    """
        formats a dictionary so that it can be printed to console

        Parameters
        ------------
        dict_string : dictionary to be formatted

    """
    return json.dumps(dict_string, indent=4)


def datetime_to_iso_utc_string(date: datetime):
    '''
        Converts a date object into an 8601 string using UTC
    '''
    if date is None:
        return "None"

    try:
        return date.astimezone(pytz.UTC).isoformat()
    except Exception as e:
        raise ValidationError("Could not convert date to string", e)


def get_business_date(days_offset: int, cutover_time: time):
    '''
        Returs the current business by comparing the current date with the
        'NYSE' market calendar. The cutover time is used to determine the time
        in the day when the business date will cutover.

        For example if today is "06/19/2020 13:00:00" and the cutover time 
        is "17:00:00" it will return a value of "06/18/2020"

        Parameters
        ----------
        days_offset: int
            The number of days of offset the results. E.g. 0 will
            return the current date and 1 will return the next, and
            -1 will return the previous.
        cutover_time: time
            the business date cutover time.

    '''
    nyse_cal = mcal.get_calendar('NYSE')

    days_offset *= -1

    utcnow = pd.Timestamp.utcnow()
    utcnow_with_delta = utcnow - \
        pd.Timedelta(timedelta(days=days_offset))
    market_calendar = nyse_cal.schedule(
        utcnow_with_delta - timedelta(days=10), utcnow_with_delta + timedelta(days=10))

    market_calendar['market_close'] = market_calendar['market_close'].map(lambda d: pd.Timestamp(d.year, d.month,
                                                                                                 d.day, cutover_time.hour, cutover_time.minute, cutover_time.second).tz_localize('UTC'))
    market_calendar = market_calendar[market_calendar.market_close < (
        utcnow_with_delta)]

    try:
        return market_calendar.index[-1].to_pydatetime().date()
    except Exception as e:
        raise ValidationError("Could not retrieve Business Date", e)


def get_business_date_offset(business_date: date, days_offset: int):
    '''
        Returns the business date offest by 'days_offset' business date.

        For example, the day before the observed 4th of July will return
        the following Monday:

        (2020/07/02, 1) -> 2020/07/06

        if the business date is not valid, the method will throw a ValidationError
    '''

    nyse_cal = mcal.get_calendar('NYSE')

    if days_offset > 0:
        market_calendar = nyse_cal.schedule(
            business_date, business_date + timedelta(days=int(days_offset * 1.5)))
    else:
        market_calendar = nyse_cal.schedule(
            business_date + timedelta(days=int(days_offset * 1.5)), business_date)
        # reverse the calendar order
        market_calendar = market_calendar.iloc[::-1]

    # if business_date is not valid, raise an exception
    try:
        market_calendar.index.get_loc(business_date)
    except Exception as e:
        raise ValidationError("Cannot offset %s by %d days because %s is not a valid business date" % (
            business_date, days_offset, business_date), e)

    return market_calendar.index[abs(days_offset)].to_pydatetime().date()
