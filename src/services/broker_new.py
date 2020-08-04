"""Author: Mark Hanegraaff -- 2020
"""

import logging
import time
from datetime import datetime
import dateutil.parser as parser
from connectors import td_ameritrade
from exception.exceptions import ValidationError, TradeError
from support import util

log = logging.getLogger()


class Broker():
    '''
        The Broker class is responsible for ensuring that positions in the brokerage account
        match those of the Portfolio's desired state.

        Specifically, this class used in the following scenarios

        1) When a new portfolio is selected, it will perform all trades necessary to materilize it,
            meaning that the broker positions will match those of the Portfolio's desired state.

        2) When a portfolio is still current, it will update its details (purchase price, quantity, etc)
            based on the contents of the brokerage account.
    '''

    def reconcile_portfolio(self, broker_positions: dict, current_portfolio: object):
        '''
            Compares the current portfolio with the current positions recorded
            in the Brokerage account. Returns true if symbol and quantity match,
            otherwise returns false.

            Parameters
            ----------
            broker_positions : dict
                Current positions fetched from the brokerage account

            current_portfolio : object
                Current Portfolio object
        '''

        # flatten portfolio into two lists that can be easily compared
        portfolio_list = [(sec['ticker_symbol'], sec['quantity'])
                          for sec in current_portfolio.model['current_portfolio']['securities']]
        portfolio_list.sort(key=lambda s: s[0])

        positions_list = [(sec, broker_positions['equities'][sec]['longQuantity'])
                          for sec in broker_positions['equities'].keys()]
        positions_list.sort(key=lambda s: s[0])

        if len(portfolio_list) != len(positions_list):
            return False

        # First verify that sets are the same
        for i in range(0, len(portfolio_list)):
            if portfolio_list[i] != positions_list[i]:
                return False

        return True

    def synchronize_portfolio(self, broker_positions: dict, current_portfolio: object):
        '''
            Matches the state of the supplied portfolio object with that of the
            latest positions listed in the brokerage account. This method is useful
            when recovering from errors since the brokerage account is the ultimately
            the source of truth.

            Parameters
            ----------
            broker_positions : dict
                Current positions fetched from the brokerage account

            current_portfolio : object
                Current Portfolio object
        '''
        def get_broker_position(ticker: str):
            try:
                return broker_positions['equities'][ticker]
            except Exception:
                return None

        for sec in current_portfolio.model['current_portfolio']['securities']:
            position = get_broker_position(sec['ticker_symbol'])

            if (position != None):
                sec['trade_state'] = 'FILLED'
                sec['purchase_price'] = position['averagePrice']
                sec['quantity'] = position['longQuantity']

        current_portfolio.validate_model()

    def cancel_all_open_orders(self):
        '''
            Cancels any open orders that are in a cancelable state.
            This is useful when handing errors where the service needs to exit
            but there are still open trades out there.
        '''
        def try_cancel_oder(order_id):
            '''
                Cancels an order, but does not
            '''
            try:
                td_ameritrade.cancel_order(order_id)
            except TradeError as te:
                log.warning("Could not cancel oder %s, because: %s" %
                            (order_id, str(te)))
        log.info("Attempting to cancel all open orders")

        recent_oders = td_ameritrade.list_recent_orders()

        for order_id in recent_oders.keys():
            order = recent_oders[order_id]

            if order['cancelable']:
                log.info("Cancelling %s, in state: %s" %
                         (order_id, order['status']))
                try_cancel_oder(order_id)

    def _generate_trade_instructions(self, broker_positions: dict, new_portfolio: object):
        '''
            Generates two sets of trade instruction based on the current broker positions 
            and new portfolio. Specifically, it will generate sell instructions for any
            position not in the portfolio, and a buy positions for every portfolio item
            in an unfulfilled state

            Returns
            -------
            A tuple containing a list of sell instructions an a list of buy instructions

            ([ticker, shares_qty], [ticker])

            Note that the buy instructions do not contain a share quantity. This is determined immediately
            before trading based on the available cash, after sell positions are unwound.
        '''
        sell_list = []

        if 'equities' in broker_positions:
            position_tickers = broker_positions['equities'].keys()
        else:
            position_tickers = []

        for ticker in position_tickers:
            if new_portfolio.get_position(ticker) == None:
                sell_list.append(
                    (ticker, broker_positions['equities'][ticker]['longQuantity']))

        buy_list = []
        for sec in new_portfolio.model['current_portfolio']['securities']:
            if sec['ticker_symbol'] not in position_tickers:
                buy_list.append(sec['ticker_symbol'])

        return (sell_list, buy_list)

    def trade(self, action: str, trade_instructions: list, new_portfolio: dict):
        '''
            Executes all trades for the supplied list and action (BUY/SELL).
            'new_portfolio' is optional and if supplied, will be updated
            the details of the transaction.

            Parameters
            ----------
            action: str
                Trade action (BUY or SELL)
            trade_instructions: list
                list of tuples (ticker, shares_amt) that must be traded.
            new_portfolio: Portfolio
                Optional portfolio object. When buying securities it will
                be updated with the trade details.
        '''
        def fill_order(order_id: str, quantity: int, purchase_time: str):
            '''
                If the order is a BUY, then update the portfolio with the
                details of the trade.
            '''
            if order_id in order_ids:
                order_ids.remove(order_id)

            if new_portfolio is None or action == 'SELL':
                return

            for sec in new_portfolio.model['current_portfolio']['securities']:
                if sec['order_id'] == order_id:
                    sec['purchase_date'] = util.datetime_to_iso_utc_string(
                        parser.parse(purchase_time))
                    sec['trade_state'] = 'FILLED'
                    sec['quantity'] = quantity
                    break

        def track_order(ticker: str, order_id: str):
            '''
                associates the supplied order ID with a specific security listed
                in the portfolio
            '''
            order_ids.append(order_id)

            if new_portfolio is None or action == 'SELL':
                return

            new_portfolio.get_position(ticker)['order_id'] = order_id
        #
        # Executes all trades
        #

        log.info("About to %s: %s" % (action, str(trade_instructions)))

        order_ids = []

        if (len(trade_instructions) == 0):
            log.info("There are no securities to be traded")
            return True

        for (ticker, quantity) in trade_instructions:
            try:
                log.info("Placing order: %s %.2f %s" %
                         (action, quantity, ticker))
                order_id = td_ameritrade.place_order(
                    action, ticker, quantity, 'SHARES')
                track_order(ticker, order_id)
            except TradeError as te:
                log.warning("Could not execute order, because: %s" % str(te))
                order_ids.append('ERROR')

        #
        # Wait for trades to complete and update portfolio accordingly
        #
        for i in range(0, 5):
            log.info("Waiting for all trades to execute")
            recent_orders = td_ameritrade.list_recent_orders()

            completed = True
            for order_id in recent_orders.keys():
                status = recent_orders[order_id]['status']
                close_time = recent_orders[order_id]['closeTime']

                log.debug("Order %s is in %s state" % (order_id, status))
                if close_time is None:
                    log.info("Order %s is not completed" % order_id)
                    completed = False
                elif status == 'FILLED':
                    log.info(
                        "Order %s was filled and will no longer be tracked" % order_id)
                    fill_order(order_id, recent_orders[order_id][
                               'quantity'], recent_orders[order_id]['closeTime'])
                else:
                    log.info("Order %s completed with an error state" %
                             order_id)
                    if order_id in order_ids:
                        order_ids.remove(order_id)

            if completed:
                log.info("All orders are closed.")
                break
            else:
                log.info(
                    "One or more orders are still being processed. Sleeping for 1 minute")
                time.sleep(60)

        if len(order_ids) == 0:
            log.info("All securities were succefully [%s] traded" % action)
            return True
        else:
            log.info("%d security could not be [%s] traded"
                     % (len(order_ids), action))
            return False

    def materialize_portfolio(self, broker_positions: dict, portfolio: object):
        '''
            Materializes the porfolio by executing the trades necessary to do so.
            Specifically:

            1) Sell all securities not in the portfolio
            2) Buy all existing securities not already owned
        '''

        (sell_trades, buy_trades) = self._generate_trade_instructions(
            broker_positions, portfolio)

        if len(sell_trades) > 0:
            if (self.trade('SELL', sell_trades, None) == False):
                log.warning(
                    "There was error unwinding positions. Portfolio could not be materialized")
                raise TradeError(
                    "Could not unwind (sell) all positions from portfolio", None, None)

        '''
            Get the cash available for trading and split it evenly acorss all securities
            to be bought.
        '''
        if len(buy_trades) > 0:
            current_broker_positions = td_ameritrade.positions_summary()
            try:
                available_cash = current_broker_positions[
                    'cash']['cashAvailableForTrading']
            except KeyError:
                available_cash = 0

            # trade 90% of available cash
            trade_dollar_amount = (available_cash / len(buy_trades)) * 0.9

            buy_instructions = []
            for buy_ticker in buy_trades:
                latest_price = td_ameritrade.get_latest_equity_price(
                    buy_ticker)

                shares = int(trade_dollar_amount / latest_price)

                if shares > 0:
                    buy_instructions.append((buy_ticker, shares))
                else:
                    log.warning(
                        "Will not purchase %s, because there aren't enough funds" % buy_ticker)

            if len(buy_instructions) == 0:
                log.warning("Could not afford to purchase any securities")
                return

            if self.trade('BUY', buy_instructions, portfolio) == False:
                log.warning(
                    "There was an error adding positions to the portoflio. Portfolio could not be materialized")
        else:
            log.info("There are no securities to buy")
