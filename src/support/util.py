"""Author: Mark Hanegraaff -- 2019
"""
import json
from datetime import datetime
import pytz
import os
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



def format_dict(dict_string : dict):
    """
        formats a dictionary so that it can be printed to console

        Parameters
        ------------
        dict_string : dictionary to be formatted
        
    """
    return json.dumps(dict_string, indent=4)



def date_to_iso_string(date : datetime):
    '''
        Converts a date object into an 8601 string usin local timezone
    '''
    if date == None: return "None"

    try:
        return date.astimezone().isoformat()
    except Exception as e:
        raise ValidationError("Could not convert date to string", e)

def date_to_iso_utc_string(date : datetime):
    '''
        Converts a date object into an 8601 string using UTC
    '''
    if date == None: return "None"

    try:
        return date.astimezone(pytz.UTC).isoformat()
    except Exception as e:
        raise ValidationError("Could not convert date to string", e)

def trunc(date : datetime):
    '''
        truncates a date object and removes the time component
    '''
    return date.replace(hour=0, minute=0, second=0, microsecond=0)


