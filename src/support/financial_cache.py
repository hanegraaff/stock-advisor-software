"""Author: Mark Hanegraaff -- 2019
"""
from io import BytesIO
import atexit
from diskcache import Cache
from support import util, constants
from exception.exceptions import ValidationError
import logging

log = logging.getLogger()

class FinancialCache():
    """
        A Disk based database containing an offline version of financial
        data and used as a cache 
    """
    
    def __init__(self, path, **kwargs):
        '''
            Initializes the cache

            Parameters
            ----------
            path : str
            The path where the cache will be located

            max_cache_size_bytes : int (kwargs)
            (optional) the maximum size of the cache in bytes
            
            Returns
            -----------
            A tuple of strings containing the start and end date of the fiscal period
        '''

        try:
            max_cache_size_bytes = kwargs['max_cache_size_bytes']
        except KeyError:
            # default max cache is 4GB
            max_cache_size_bytes = 4e9

        util.create_dir(path)
        
        try:
            self.diskCache = Cache(path, size_limit=int(max_cache_size_bytes))
        except Exception as e:
            raise ValidationError('invalid max cache size', e)

        log.debug("Cache was initialized: %s" % path)

    def write(self, key : str, value : object):
        """
            Writes an object (value) to the cache using the supplied key
        """
        if (key == "" or key is None) or (value == "" or value is None):
            return

        self.diskCache[key] = value

    def read(self, key):
        """
            Reads an object (value) to the cache given the supplied key
            and returns None if it cannot be found

            Returns
            ----------
            The object in question, or None if they key is not present
        """
        try:
            return self.diskCache[key]
        except KeyError:
            log.debug("%s not found inside cache" % key)
            return None


@atexit.register
def shutdownCache():
    log.debug("Shutting down cache")
    cache.diskCache.close()


cache = FinancialCache(constants.FINANCIAL_DATA_DIR)