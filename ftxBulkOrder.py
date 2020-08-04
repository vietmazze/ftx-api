from requests import Request, Session, Response
import time
import collections
import datetime
import json
import logging
import hmac
import hashlib
import os
from dotenv import load_dotenv
import urllib
from typing import Optional, Dict, Any, List
from colorprint import ColorPrint
from colorama import Fore, Back, Style, init
path = './keys.env'
load_dotenv(dotenv_path=path, verbose=True)

logging.basicConfig(level=logging.INFO, format=(
    Fore.BLUE + '[+] ' + Style.RESET_ALL + '%(message)s '))


class FtxClient:
    _ENDPOINT = 'https://ftx.com/api/'
    markets = {
        "ATOM": "ATOM-PERP",
        "XTZ": "XTZ-PERP",
        "BTC": "BTC-PERP",
        "ETH": "ETH-PERP"

    }

    def __init__(self, subaccount_name=None) -> None:
        self._session = Session()
        self._api_key = os.getenv('FTX_HUNTER_KEY')
        self._api_secret = os.getenv('FTX_HUNTER_SECRET')
        self._subaccount_name = "hunter-api"
        self.logger = logging.getLogger(__name__)
        self.cp = ColorPrint()
        self.market = ""

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('GET', path, params=params)

    def _post(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('POST', path, json=params)

    def _request(self, method: str, path: str, **kwargs) -> Any:
        request = Request(method, self._ENDPOINT + path, **kwargs)
        # Apply hash to keys
        self._sign_request(request)
        # Send the request, similar to req.get() or req.post()
        response = self._session.send(request.prepare())
        # Clean up response
        result = self._process_response(response)
        return result

    def _sign_request(self, request: Request) -> None:
        ts = int(time.time() * 1000)
        prepared = request.prepare()
        signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode(
        )

        if prepared.body:
            signature_payload += prepared.body
        signature = hmac.new(self._api_secret.encode(),
                             signature_payload, 'sha256').hexdigest()
        request.headers['FTX-KEY'] = self._api_key
        request.headers['FTX-SIGN'] = signature
        request.headers['FTX-TS'] = str(ts)
        if self._subaccount_name:
            request.headers['FTX-SUBACCOUNT'] = urllib.parse.quote(
                self._subaccount_name)

    def _process_response(self, response: Response) -> Any:
        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            raise
        else:
            if not data['success']:
                raise Exception(data['error'])
            return data['result']

    def get_account_info(self) -> dict:
        return self._get(f'account')

    def list_markets(self) -> List[dict]:
        return self._get('markets')

    def cancel_orders(self, market_name: str = None, conditional_orders: bool = False,
                      limit_orders: bool = False) -> dict:
        try:
            result = self._delete(f'orders', {'market': market_name,
                                              'conditionalOrdersOnly': conditional_orders,
                                              'limitOrdersOnly': limit_orders,
                                              })

            self.cp.green(f"{result}")
        except Exception as e:
            self.cp.red(
                f'Exception when calling cancel_orders: \n {e}')

    def get_open_orders(self, market: str = None) -> List[dict]:
        try:
            result = self._get(f'orders', {'market': market})
            self.cp.green(f'{result}')
            for item in result:
                self.cp.green(f"""{item['type']} order is in placed: 
                            market: {item['market']}, 
                            size: {item['size']},
                            price: {item['price']}, 
                            side: {item['side']},
                            clientId: {item['clientId']},
                            id: {item['id']}""")

        except Exception as e:
            self.cp.red(
                f'Exception when calling get_open_orders: \n {e}')

    def place_order(self, market: str, side: str, price: float, size: float, type: str = 'limit',
                    clientId: str = None, reduce_only: bool = False, ioc: bool = False, post_only: bool = False) -> dict:
        try:
            result = self._post('orders', {'market': market,
                                           'side': side,
                                           'price': price,
                                           'size': size,
                                           'type': type,
                                           'reduceOnly': reduce_only,
                                           'ioc': ioc,
                                           'postOnly': post_only,
                                           'clientId': clientId,
                                           })
            self.cp.green(f"""{result['type']} order has been created: 
                          clientId - {result['clientId']}, 
                          market: {result['market']}, 
                          size: {result['size']},
                          price: {result['price']}, 
                          side: {result['side']}""")

        except Exception as e:
            self.cp.red(f'Exception when calling place_order: \n {e}')

    def place_conditional_order(
            self, market: str, side: str, size: float, type: str,
            trigger_price: float = None, clientId: str = None, limit_price: float = None, reduce_only: bool = False, cancel: bool = True,
            trail_value: float = None) -> dict:
        """
        To send a Stop Market order, set type='stop' and supply a trigger_price
        To send a Stop Limit order, also supply a limit_price
        To send a Take Profit Market order, set type='trailing_stop' and supply a trigger_price
        To send a Trailing Stop order, set type='trailing_stop' and supply a trail_value
        """
        assert type in ('stop', 'take_profit', 'trailing_stop')
        assert type not in ('stop', 'take_profit') or trigger_price is not None, \
            'Need trigger prices for stop losses and take profits'
        assert type not in ('trailing_stop',) or (trigger_price is None and trail_value is not None), \
            'Trailing stops need a trail value and cannot take a trigger price'

        try:
            result = self._post('conditional_orders',
                                {'market': market, 'side': side, 'triggerPrice': trigger_price,
                                 'size': size, 'reduceOnly': reduce_only, 'type': type,
                                 'cancelLimitOnTrigger': cancel, 'orderPrice': limit_price, 'clientId': clientId})
            self.cp.green(f"""{result['type']} order has been created: 
                          market: {result['market']}, 
                          size: {result['size']},
                          price: {result['triggerPrice']}, 
                          side: {result['side']}""")
            self.cp.green(f'{result}')
        except Exception as e:
            self.cp.red(
                f'Exception when calling place_conditional_order: \n {e}')


def process_command(ftx, userInput):
    dispatcher = {'instrument':,
                  'fatfinger':,
                  'buy': place_order,
                  'sell':,
                  'alias':,
                  'tp': place_conditional_order,
                  'trail':,
                  'close': ,
                  'cancel': cancel_orders,
                  'position':,
                  'order': get_open_orders}

    # seperate by comma - diff call
    # seperate by each order - one call
    commands = collections.deque()
    for input in userInput.split(","):
        commands.append(input)

    while commands:
        command_one, command_two = commands.popleft()
        dispatcher[command_one](command_two)
    # set fatfinger
    # if command_one == "fatfinger":
        # send to fatfinger function
    # locking instrument

    # creating alias

    # placing orders

    # cancel orders

    # show open orders

    # show open positions


def main(ftx):
    while True:
        # main program

        while True:
            userInput = input('Command: ')
            break
        if userInput == 'q':
            break
        else:
            result = process_command(ftx, userInput)


if __name__ == '__main__':
    cp = ColorPrint()
    ftx = FtxClient()
    try:
        main(ftx)
    except Exception as ex:
        cp.red(ex.args)
    finally:
        exit()