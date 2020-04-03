from datetime import datetime, timedelta
from cloud import aws_service_wrapper
from exception.exceptions import ValidationError, FileSystemError    
from support import constants
from support import util
import logging

log = logging.getLogger()

"""
This module contains supporting logic for reccomendation service script.
It exists solely so that the code may be tested. otherwise it would
be organized along with the service itself.
"""

def validate_environment(environment : str):
    """
        Validates the supplied enviornment against allowed values, and returns
        the uppercase value of it.
    """

    environment = environment.upper()
    allowed_values = ['TEST', 'PRODUCTION']
    
    if environment in allowed_values:
        return environment
    else: 
        raise ValidationError("invalid environment value. Expected values are %s" % allowed_values, None)

def validate_price_date(price_date_str : str):
    '''
        Converts the price date string in yyyy/mm/dd format to a date object.
        Raises a ValidationError if the date could not be parsed or if
        it's in the future.

        Returns
        ----------
        A datetime object with the converted date
    '''
    try:
        price_date = datetime.strptime(price_date_str, '%Y/%m/%d')
    except Exception:
        raise ValidationError("%s is invalid. Expecting 'yyyy/mm/dd' format" % price_date_str, None)
    
    if price_date > datetime.now():
        raise ValidationError("Price date cannot be in the future", None)

    return price_date

    
def validate_commandline_parameters(year : int, month  : int, current_price_date : datetime):
    '''
        Validates command line parameters and throws an exception
        if they are not properly set.
    '''
    if (year < 2000 or (month not in range(1, 13))):
        raise ValidationError("Parameters out of range", None)

    if datetime(year, month, 1) >= current_price_date:
        raise ValidationError("Price Date must be in future compared to analysis period", None)

def compute_analysis_period(current_price_date : datetime):
    '''
        Computes the period of instead of reading them from the commmand line.
        The analysis period is simply the month before the current_price_date 
        
        Returns
        ----------
        a tuple, (year, month) based on the supplied current_price_date
    '''
    
    last_month = datetime(current_price_date.year, current_price_date.month, 1) - timedelta(days=1)
    return (last_month.year, last_month.month)