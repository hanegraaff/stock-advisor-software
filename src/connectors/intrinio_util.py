"""Author: Mark Hanegraaff -- 2020

  A module containing date utilities that are useful when interacting
  with the Intrinio SDK
"""

from datetime import date, datetime, timedelta
import calendar
from exception.exceptions import ValidationError


def get_year_date_range(year: int, extend_by_days: int):
    """
      returns the first and last day of the supplied year formatted in a way
      that can be supplied to the Intrinion SDK

      For example:
        2018 -> ('2018-01-01', '2019-12-31')

      the end date can be extended by "extend_by_days"
      For example:
        (2018, 10) -> ('2018-01-01', '2019-01-10')

      Parameters
      ----------
      year : int
        the year in question
      extend_by_days : int
        number of days by which to extend the end date period.

      Returns
      -----------
      A tuple of strings containing the start and end date.
    """
    __validate_year__(year)

    if extend_by_days < 0 or extend_by_days > 350:
        raise ValidationError(
            "Invalid extend_by_days. Must between 0 and 350", None)

    start = date(year, 1, 1)
    end = date(year, 12, 31) + timedelta(days=extend_by_days)
    return(date_to_string(start), date_to_string(end))


def get_month_period_range(period: object):
    """
      returns the first and last date of the month as dates given the 
      Pandas period.

      E.g.
        Period('2018-01', 'M') -> ('2018-01-01', '2018-01-31')

      Returns
      -------
      A tuple of strings containing the start and end date.
    """
    __validate_year__(period.year)

    start = date(period.year, period.month, 1)
    end = date(period.year, period.month, period.day)

    return(start, end)


def get_month_date_range(year: int, month: int):
    """
      returns the first and last date of the month as dates

      E.g.
        2018, 1 -> ('2018-01-01', '2018-01-31')

      Returns
      -----------
      A tuple of strings containing the start and end date.
    """
    __validate_year__(year)

    if month not in range(1, 13):
        raise ValidationError(
            "Invalid month. Must be between 0 and 12" + str(month), None)

    last_date = calendar.monthrange(year, month)[1]

    start = datetime(year, month, 1)
    end = datetime(year, month, last_date)

    return(start, end)


def get_month_date_range_str(year: int, month: int):
    """
      returns the first and last date of the month as strings.
      See the get_month_date_range function above for more detail
    """

    (start, end) = get_month_date_range(year, month)

    return(date_to_string(start), date_to_string(end))


def date_to_string(date: date):
    """
      returns a string representation of a date that is usable by the intrinio API

      Returns
      ----------
      A string formatted as YYYY-MM-DD. This is the format used by most Intrinio APIs
    """
    return date.strftime("%Y-%m-%d")


def __validate_year__(year):
    if year < 2000:
        raise ValidationError("Invalid Year. Must be >= 2000", None)
