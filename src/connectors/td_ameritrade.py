"""Author: Mark Hanegraaff -- 2020
"""

import requests
import os
import json
import logging
from datetime import datetime
import random
import string
#import pytz
import dateutil.parser as parser
from datetime import timedelta
from exception.exceptions import ValidationError, TradeError
from support import util


log = logging.getLogger()

missing_variables = []

TD_ACCESS_TOKEN = ""

# 5 second timeout for each request
REQUEST_TIMEOUT = 8


def AUTH_HEADER():
    '''
        Generates a standard authentication header used for TD Ameritrade api calls
    '''
    if TD_ACCESS_TOKEN == "":
        return None
    else:
        return {'Authorization': 'Bearer %s' % TD_ACCESS_TOKEN}


def generate_tag():
    '''
        Generates a two character random string used to tag orders
    '''
    chars = list(string.ascii_lowercase)
    chars += list(string.ascii_uppercase)
    chars += ["%d" % i for i in range(0, 9)]

    return "%s%s" % (random.choice(chars), random.choice(chars))


def td_authenticate(func):
    """
        A Decorator that fetches an access token if one does not exist.
        Used to simplify other methods that interact with the TD Apis
    """
    def wrapper(*args, **kwargs):
        if TD_ACCESS_TOKEN == "":
            login()
        return func(*args, **kwargs)
    return wrapper


def __validate_response(url: str, response: object):
    '''
        validates a request's status code and throws a TradeError
        if not a 200 or 201
    '''
    if response.status_code not in (200, 201):
        raise TradeError("Invalid response while calling %s: %s" %
                         (url, response.text), None, response)


def request(method: str, url: str, params: dict, payload: dict):
    '''
        Value add wrapper around the "request" method. Add auth header, timeout,
        and throws an exception if the response is not valid

        Parameters
        ----------
        method : str
            the HTTP method (GET, PUT, etc) of the request
        url : str
            URL of the API
        params : dict
            request parameters
        payload : dict
            request payload (data)
    '''
    try:
        r = requests.request(method, url, params=params, json=payload,
                             headers=AUTH_HEADER(), timeout=REQUEST_TIMEOUT)
    except Exception as e:
        raise TradeError("Could not execute POST to %s" % url, e, None)

    __validate_response(url, r)

    try:
        response = r.json()
        log.debug("API Response: %s" % util.format_dict(response))
        return (r.headers, response)
    except:
        log.debug("API Response: None")
        return (r.headers, {})


def get_credentials():
    '''
        Read the TD Credentials from the environment or throws an exception
    '''
    def read_from_env(env_name: str):
        '''
            reads a TD credential variable from the environment.
            If not found add it to the "missing" list to improve
            the error message.
        '''
        try:
            return os.environ.get(env_name)
        except Exception:
            missing_variables.append(env_name)

    missing_variables.clear()

    td_account_id = read_from_env('TDAMERITRADE_ACCOUNT_ID')
    td_client_id = read_from_env('TDAMERITRADE_CLIENT_ID')
    td_refresh_token = read_from_env('TDAMERITRADE_REFRESH_TOKEN')

    if len(missing_variables) > 0:
        raise ValidationError("Could not read TDAmeritrade credentials from environment. Missing %s" % str(
            missing_variables), None)

    return (td_account_id, td_client_id, td_refresh_token)


def login():
    '''
        Calls the https://api.tdameritrade.com/v1/oauth2/token Api and
        requests a temporary access token, effectively logging into TDAmeritrade
    '''
    (td_account_id, td_client_id, td_refresh_token) = get_credentials()

    auth_url = 'https://api.tdameritrade.com/v1/oauth2/token'

    log.info("Generating TDAmeritrade refresh token")
    try:
        creds_response = requests.post(auth_url, data={
            'grant_type': 'refresh_token',
            'refresh_token': td_refresh_token,
            'client_id': '%s@AMER.OAUTHAP' % td_client_id
        }, timeout=REQUEST_TIMEOUT
        )
    except Exception as e:
        raise TradeError("Could not execute POST to %s" % auth_url, e, None)

    __validate_response(auth_url, creds_response)

    global TD_ACCESS_TOKEN
    TD_ACCESS_TOKEN = creds_response.json()['access_token']

'''
    TD Ameritrade APIs
    Users of this module must use these methods
'''


@td_authenticate
def equity_market_open(current_time: datetime):
    '''
        Calls the https://api.tdameritrade.com/v1/marketdata/equity/hours Api
        and returns true if the Equities market is open during the specified time
    '''
    params = {
        'date': current_time.strftime("%Y-%m-%d")
    }

    #current_time = pytz.utc.localize(current_time)

    market_hours = request(
        'GET', 'https://api.tdameritrade.com/v1/marketdata/equity/hours', params=params, payload=None)[1]

    try:
        open_time = parser.parse(market_hours['equity']['EQ'][
                                 'sessionHours']['regularMarket'][0]['start'])
        close_time = parser.parse(market_hours['equity']['EQ'][
                                  'sessionHours']['regularMarket'][0]['end'])
    except Exception:
        return market_hours['equity']['equity']['isOpen']

    return open_time.timestamp() <= current_time.timestamp() <= close_time.timestamp()


@td_authenticate
def positions_summary():
    '''
        calls the https://api.tdameritrade.com/v1/accounts/{ACCOUNT_ID} Api and
        summarizes the positions that are returned in the response nto a dictionary
        like this:

        {
            "equities": {
                "SYMBOL":{
                    "longQuantity": 1.0,
                    "averagePrice": 120,
                    "marketValue": 120
                }
            },
            "cash" : {
                "cashAvailableForTrading": 1000,
            }
        }

    '''
    def equities(response_dict: dict):
        '''
            Summarizes the "equities" portion of the response
        '''
        equity_dict = {}
        try:
            for equity in response_dict['securitiesAccount']['positions']:
                if equity['instrument']['assetType'] == 'EQUITY':
                    symbol = equity['instrument']['symbol']
                    equity_dict[symbol] = {}
                    equity_dict[symbol][
                        'longQuantity'] = equity['longQuantity']
                    equity_dict[symbol][
                        'averagePrice'] = equity['averagePrice']
                    equity_dict[symbol]['marketValue'] = equity['marketValue']
        except Exception:
            return {}

        return equity_dict

    def cash(response_dict: dict):
        '''
            Summarizes the "cash" portion of the response
        '''
        try:
            return {
                "cashAvailableForTrading": response_dict['securitiesAccount']['currentBalances']['cashAvailableForTrading']
            }
        except Exception:
            return {
                "cashAvailableForTrading": 0
            }

    td_account_id = get_credentials()[0]

    acct_response = request('GET', 'https://api.tdameritrade.com/v1/accounts/%s' %
                            td_account_id, params={'fields': ['positions']}, payload=None)[1]

    if acct_response['securitiesAccount']['type'] != 'CASH':
        raise ValidationError(
            "TDAmeritrade cccount must be a CASH account", None)

    position_summary = {
        "equities": equities(acct_response),
        "cash": cash(acct_response)
    }

    return position_summary


@td_authenticate
def place_order(action: str, symbol: str, quantity: float, quantity_type: str):
    '''
        Calls the https://api.tdameritrade.com/v1/accounts/{ORDER_ID}/orders API and
        places a simple (single leg) Market order (BUY/SELL) valid through the day for the specified
        symbol and dollar amount.

        Returns the order id as extracted from the location header. If the order ID
        cannot be found, it will return a the two character tag which was randomly
        generated during this call

    '''

    if quantity_type not in ['SHARES', 'DOLLARS', 'ALL_SHARES']:
        raise ValidationError(
            "Invalid quantity type supplied: %s" % quantity_type, None)

    if (action) not in ('BUY', 'SELL'):
        raise ValidationError(
            "Invalid trading actions supplied: %s" % action, None)

    td_account_id = get_credentials()[0]

    tag = generate_tag()

    order = {
        "orderType": "MARKET",
        "session": "NORMAL",
        "duration": "DAY",
        "orderStrategyType": "SINGLE",
        "orderLegCollection": [
            {
                "instruction": action,
                "quantity": quantity,
                "quantityType": quantity_type,
                "instrument": {
                    "assetType": "EQUITY",
                    "symbol": symbol
                }
            }
        ],
        "tag": tag
    }

    headers = request('POST', 'https://api.tdameritrade.com/v1/accounts/%s/orders' %
                      td_account_id, None, order)[0]

    # fetch the order id from the headers, This is where it's stored
    # https://api.tdameritrade.com/v1/accounts/{ACCT_ID}/orders/{ORDER_ID}'
    # --> {ORDER_ID}
    try:
        order_id = str(headers['Location'].rsplit('/', 1)[-1])
    except:
        order_id = tag

    return order_id


@td_authenticate
def cancel_order(order_id: str):
    '''
        Calls the https://api.tdameritrade.com/v1/accounts/{ACCOUNT_ID}/orders/{ORDER_ID}
        and cancels the order.
    '''

    td_account_id = get_credentials()[0]
    request('DELETE', 'https://api.tdameritrade.com/v1/accounts/%s/orders/%s' %
            (td_account_id, order_id), None, None)


@td_authenticate
def list_recent_orders():
    '''
        Calls the 'https://api.tdameritrade.com/v1/accounts/{ACCOUNT_ID}/orders' API and
        returns the orders for the past day, and summarizes them in a dictionary
        like this:

        {
            "activityType": "'EXECUTION' or 'ORDER_ACTION'",
            "executionType": "'FILL'",
            "quantity": 0,
            "orderRemainingQuantity": 0,
            "executionLegs": [
                {
                "legId": 0,
                "quantity": 0,
                "mismarkedQuantity": 0,
                "price": 0,
                "time": "string"
                }
            ]
            }

        {
            "orderId": {
                "status": "CANCELED",
                "symbol": "SPY",
                "quantity": 8.0,
                "closeTime": "2020-05-04T03:21:04+0000",
                "tag": "AA_myuser",
                "cancelable": False
            },
        }
    '''
    recent_orders = {}
    td_account_id = get_credentials()[0]

    params = {
        'fromEnteredTime': (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
        'toEnteredTime': (datetime.now().strftime("%Y-%m-%d")),
    }

    order_list = request('GET', 'https://api.tdameritrade.com/v1/accounts/%s/orders' %
                         td_account_id, params=params, payload=None)[1]
    
    for order in order_list:
        order_id = str(order['orderId'])
        recent_orders[order_id] = {}

        recent_orders[order_id]['status'] = order['status']
        recent_orders[order_id]['symbol'] = order[
            'orderLegCollection'][0]['instrument']['symbol']
        recent_orders[order_id]['quantity'] = order[
            'orderLegCollection'][0]['quantity']
        try:
            close_time = order['closeTime']
        except:
            close_time = None
        recent_orders[order_id]['closeTime'] = close_time
        recent_orders[order_id]['tag'] = order['tag']
        recent_orders[order_id]['cancelable'] = order['cancelable']

    return recent_orders


@td_authenticate
def get_latest_equity_price(ticker: str):
    '''
        Calls thehttps://api.tdameritrade.com/v1/marketdata/{symbol}/quotes
        and cancels the order.
    '''

    r = request('GET', 'https://api.tdameritrade.com/v1/marketdata/%s/quotes' %
            ticker, None, None)[1]
    
    return r[ticker]['lastPrice']