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

    def __init__(self, subaccount_name=None) -> None:
        self._session = Session()
        self._api_key = os.getenv('FTX_HUNTER_KEY')
        self._api_secret = os.getenv('FTX_HUNTER_SECRET')
        self._subaccount_name = "hunter-api"
        self.cp = ColorPrint()
        self.market = None
        self.orderSide = None
        self.fatFinger = None

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('GET', path, params=params)

    def _post(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('POST', path, json=params)

    def _delete(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('DELETE', path, json=params)

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
            if result is None:
                self.cp.green(f'No orders available for {market}')
            else:
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

    def get_positions(self, show_avg_price: bool = False) -> List[dict]:
        try:
            return self._get('positions', {'showAvgPrice': show_avg_price})
        except Exception as e:
            self.cp.red(f'Exception when calling get_positions: \n {e}')

    def get_position(self, name: str, show_avg_price: bool = False) -> dict:
        try:
            if name:
                try:
                    result = next(
                        filter(lambda x: x['future'] == name, self.get_positions(show_avg_price)), None)
                    self.cp.green(f"""Current position:
                                    market: {result['future']},
                                    entryPrice: {result['entryPrice']},
                                    estimatedLiquidationPrice: {result['estimatedLiquidationPrice']},
                                    initialMarginRequirement: {result['initialMarginRequirement']},
                                    longOrderSize: {result['longOrderSize']},
                                    maintenanceMarginRequirement: {result['maintenanceMarginRequirement']}
                                    netSize: {result['netSize']},
                                    openSize: {result['openSize']},
                                    realizedPnl: {result['realizedPnl']},
                                    shortOrderSize: {result['shortOrderSize']},
                                    side: {result['side']},
                                    size: {result['size']},
                                    unrealizedPnl:{result['unrealizedPnl']}""")
                except Exception as e:
                    self.cp.red(f'Cannot find the position with: {name}')

            else:
                result = self.get_positions()
                for item in result:
                    self.cp.green(f"""Current position:
                                market: {item['future']},
                                entryPrice: {item['entryPrice']},
                                estimatedLiquidationPrice: {item['estimatedLiquidationPrice']},
                                initialMarginRequirement: {item['initialMarginRequirement']},
                                longOrderSize: {item['longOrderSize']},
                                maintenanceMarginRequirement: {item['maintenanceMarginRequirement']}
                                netSize: {item['netSize']},
                                openSize: {item['openSize']},
                                realizedPnl: {item['realizedPnl']},
                                shortOrderSize: {item['shortOrderSize']},
                                side: {item['side']},
                                size: {item['size']},
                                unrealizedPnl:{item['unrealizedPnl']}""")

        except Exception as e:
            self.cp.red(f'Exception when calling get_position: \n {e}')

    def place_order(self, market: str, side: str, size: float, type: str = 'limit',
                    price: float = None, clientId: str = None, reduce_only: bool = False, ioc: bool = False, post_only: bool = False) -> dict:
        # cp.green(f'Place Order: {market},{side}, {size}, {price}, {type}')
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
            triggerPrice: float = None, clientId: str = None, limit_price: float = None, reduce_only: bool = True, cancel: bool = True,
            trail_value: float = None) -> dict:
        """
        To send a Stop Market order, set type='stop' and supply a trigger_price
        To send a Stop Limit order, also supply a limit_price
        To send a Take Profit Market order, set type='trailing_stop' and supply a trigger_price
        To send a Trailing Stop order, set type='trailing_stop' and supply a trail_value
        """
        assert type in ('stop', 'takeProfit', 'trailingStop')
        assert triggerPrice is not None, \
            self.cp.red('Need trigger prices for stop losses and take profits')
        assert type not in ('trailingStop',) or (triggerPrice is None and trail_value is not None), \
            self.cp.red(
                'Trailing stops need a trail value and cannot take a trigger price')

        try:
            result = self._post('conditional_orders',
                                {'market': market, 'side': side, 'triggerPrice': triggerPrice,
                                 'size': size, 'reduceOnly': reduce_only, 'type': type,
                                 'cancelLimitOnTrigger': cancel, 'orderPrice': limit_price, 'clientId': clientId})
            self.cp.green(f"""{result['type']} order has been created:
                              market: {result['market']},
                              size: {result['size']},
                              triggerPrice: {result['triggerPrice']},
                              side: {result['side']}""")

        except Exception as e:
            self.cp.red(
                f'Exception when calling place_conditional_order: \n {e}')

    """ Clean up order before placing """

    def place_order_cleanup(self, currCommand):
        side = currCommand[0] if len(currCommand) > 0 else None
        ftx.orderSide = side
        size = currCommand[1] if len(currCommand) > 1 else None

        if len(currCommand) > 2:
            if "@" in currCommand[2]:
                price = currCommand[2].replace('@', '')
            else:
                price = currCommand[2]
        else:
            price = None

        type = "limit" if len(currCommand) > 2 else "market"

        if size:
            if size < self.fatFinger:
                if price and type == "limit":

                    self.place_order(market=self.ftx.market, side=side,
                                     size=size, price=price, type=type)
                else:

                    self.place_order(
                        market=self.ftx.market, side=side, size=size, type=type)
            else:
                self.cp.red(
                    f'Size order exceeds fatfinger: {self.fatFinger}, unable to place order')
        else:
            self.cp.red(
                f'Error in placing order, missing size or price entry.')

    """ Clean up conditional order before placing """

    def place_conditional_order_cleanup(self, currCommand):
        """Setting proper type name to send"""
        type = currCommand[0] if len(currCommand) > 0 else None
        if type == "tp":
            type = "takeProfit"
        if type == "trail":
            type = "trailingStop"

        """ Assign command to price,size"""
        if len(currCommand) > 2:
            if "@" in currCommand[2]:
                price = currCommand[2].replace('@', '')
            else:
                price = currCommand[2]
        else:
            price = None

        size = currCommand[1] if len(currCommand) > 1 else None

        if self.orderSide is not None:
            side = "buy" if self.orderSide == "sell" else "sell"
        elif len(currCommnand) > 3:
            side = currCommand[3]
        else:
            self.cp.red(
                f'Error in placing conditional order,need to assign a side order')

        limitPrice = currCommand[4] if len(currCommand) > 4 else None

        """Sending market or limit conditional order"""
        if size and size < self.fatFinger:
            if price:
                if limitPrice:
                    self.place_conditional_order(
                        market=self.market, side=side, size=size, triggerPrice=price, limit_price=limitPrice, type=type)
                else:
                    self.place_conditional_order(
                        market=self.market, side=side, size=size, triggerPrice=price, type=type)
            else:
                self.cp.red(
                    f'Error in placing conditional order,need trigger price and/or limitPrice')
        else:
            self.cp.red(
                f'Error in placing conditional order,need size order or exceeds fatFinger: {self.fatFinger}')
