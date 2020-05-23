"""Author: Mark Hanegraaff -- 2020

This module initializes the logger, so that it can produce consistent logging
across all services
"""
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')
