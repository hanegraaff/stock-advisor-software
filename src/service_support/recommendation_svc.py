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

def from_yyyymmdd(datestr):
    '''
        Converts a parameter string in yyyy/mm/dd format to a date object

        Returns
        ----------
        A datetime object with the converted date
    '''
    try:
        return datetime.strptime(datestr, '%Y/%m/%d')
    except Exception:
        raise ValidationError("%s is invalid. Expecting 'yyyy/mm/dd' format" % datestr, None)

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