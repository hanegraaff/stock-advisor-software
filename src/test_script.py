"""test_script.py

A general purpose test script. Nothing to see here.
"""
import argparse
import logging
from datetime import datetime

from support import logging_definition
from connectors import connector_test, intrinio_data

#
# Main script
#

log = logging.getLogger()

try:
    #intrinio_data.API_KEY = 'xxx'
    connector_test.test_all_connectivity()
except Exception as e:
    log.error("Could run script, because, %s" % (str(e)))
