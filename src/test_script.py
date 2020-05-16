"""test_script.py

A general purpose test script. Nothing to see here.
"""
import argparse
import logging
from datetime import datetime
import dateutil.parser as parser
from support import logging_definition, util
from connectors import td_ameritrade
from services.broker import Broker
from model.portfolio import Portfolio

#
# Main script
#

log = logging.getLogger()

try:


    '''pfolio = Portfolio.from_s3('sa')
    positions = td_ameritrade.positions_summary()

    b = Broker()
    (sell_instructions, buy_instructions) = b._generate_trade_instructions(positions, pfolio)
    log.info((sell_instructions, buy_instructions))

    b.synchronize_portfolio(positions, pfolio)
    b.cancel_all_open_orders()

    b.materialize_portfolio(positions, pfolio)'''

    date_str = '2020-05-11T16:10:30+0000'

    print(date_str)
    print(util.date_to_iso_utc_string(parser.parse(date_str)))


except Exception as e:
    logging.error("Could run script, because, %s" % (str(e)))
    raise e
