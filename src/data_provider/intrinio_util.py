from datetime import datetime
from datetime import timedelta
import calendar
from exception.exceptions import ValidationError

def get_year_date_range(year : int, extend_by_days : int):
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
    raise ValidationError("Invalid extend_by_days. Must between 0 and 350", None)

  start = datetime(year, 1, 1)
  end = datetime(year, 12, 31) +  timedelta(days=extend_by_days)
  return(date_to_string(start), date_to_string(end))


def get_month_date_range(year : int, month : int):
      
    """
      returns the first and last date of the month

      E.g.
        2018, 1 -> ('2018-01-01', '2018-01-31')

      Parameters
      ----------
      year : int
        the year in question
      month : int
        the month in question
      
      Returns
      -----------
      A tuple of strings containing the start and end date.
    """
    __validate_year__(year)

    if month not in range(1, 13):
      raise ValidationError("Invalid month. Must be between 0 and 12" + str(month), None)
      
    (x, last_date) = calendar.monthrange(year,month)

    start = datetime(year, month, 1)
    end = datetime(year, month, last_date) 

    return(start, end)


def get_month_date_range_str(year : int, month : int):

    (start, end) = get_month_date_range(year, month)

    return(date_to_string(start), date_to_string(end))

def date_to_string(date : object):
  """
    returns a string representation of a date that is usable by the intrinio API

    Parameters
    ----------
    date : object
      the date in question

    Returns
    ----------
    A string formatted as YYYY-MM-DD. This is the format used by most Intrinio APIs
  """    
  return date.strftime("%Y-%m-%d")


def __validate_year__(year):
    if year < 2000:
      raise ValidationError("Invalid Year. Must be >= 2000", None)