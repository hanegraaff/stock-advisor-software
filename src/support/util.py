"""Author: Mark Hanegraaff -- 2019
"""
import json
import os
from exception.exceptions import FileSystemError

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