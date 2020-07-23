import bitmex
import os
import time
import datetime
import json
import logging
import os
import asyncio
import sys
import argparse
from colorprint import ColorPrint
from os.path import join, dirname
from dotenv import load_dotenv, find_dotenv
from ftxOrder import FtxClient


path = './keys.env'
load_dotenv(dotenv_path=path, verbose=True)

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger('LOGGER_NAME')

# process new buy/sell order


def connection(subaccount_name="hunter-api"):
    ftx = FtxClient(subaccount_name)
    return ftx


def process_new_order(ftx, market, side, price, orderQty, type, clientId, stopPx, targetPx):
    cp.yellow("Process order started")
    clientId = f'{type}_{clientId}'
    market = ftx.markets.get(market)
    if type == "limit" or type == "market":

        ftx.place_order(market, side, price, orderQty, type, clientId)

    elif type == "stop":
        ftx.place_conditional_order(
            market, side, orderQty, type, stopPx, clientId)
    elif type == "take_profit":
        ftx.place_conditional_order(
            market, side, orderQty, type, targetPx, clientId)


def process_append_order(ftx, clientId, type, price, stopPx, targetPx, orderQty):
    cp.yellow("Appending orders started")
    clientId = f'{type}_{clientId}'
    if ordType == "limit":

        ftx.modify_order(clientId, price, orderQty)
    elif ordType == "stop":
        ftx.modify_condtional_order(clientId, stopPx, orderQty)
    elif type == "take_profit":
        ftx.modify_conditional_order(clientId, targetPx, orderQty)


def process_get_order(ftx, market, ordType):
    cp.yellow("Get orders started")
    if ordType == "limit":
        ftx.get_open_orders(ftx.markets.get(market))
    if ordType == "stop":
        ftx.get_open_conditional_orders(ftx.markets.get(market))


def process_delete_all_order(ftx, market):
    cp.yellow("Delete all orders started")
    market_name = ftx.markets.get(market)
    ftx.cancel_orders(market_name=market_name)


def parse_args():
    # Create parse:
    parser = argparse.ArgumentParser(prog='ftxClient',
                                     description='Process orders through FTX API',
                                     usage='ftx -letter [amount]')
    parser.add_argument('-t', '--type', type=str, dest='type',
                        help="Choose API endpoint", choices=['get', 'create', 'conditional' 'append', 'delete'])
    # arguments to pass in create_bulk_order

    order_opts = parser.add_argument_group(
        'Flags for creating orders \n APPEND: -t append -id profit_order# -qty -e -sl -tp \n CREATE: ')
    order_opts.add_argument('-m', '--market', type=str,
                            dest='market', help="Market name", default="None")
    order_opts.add_argument('-s', '--side', type=str,
                            dest='side', help="Buy/Sell", choices=['buy', 'sell'], default="buy")
    order_opts.add_argument('-o', '--orderType', type=str, dest='orderType',
                            help="Choose order type", choices=['limit', 'market', 'stop', 'take_profit', 'trailing_stop'], default="limit")
    order_opts.add_argument('-qty', '--quantity', type=float,
                            dest='quantity', help="Quantity", nargs='?', const=0)
    order_opts.add_argument('-e', '--entry', type=float,
                            dest='entry', help="Entry price for limit order only", nargs='?', const=0)
    order_opts.add_argument('-sl', '--stoploss', type=float,
                            dest='stoploss', help="Stoploss price entry", nargs='?', const=0)
    order_opts.add_argument('-tp', '--targetpoint',
                            type=float, dest='targetpoint', help="Target point entry", nargs='?', const=0)
    order_opts.add_argument('-id', '--clientId', type=str,
                            dest='clientId', help="Order Id for the order", default="0")

    # arguments to pass in append_order

    # arguments to pass in get_order
    get_order_opts = parser.add_argument_group(
        'Flags for getting current orders.')

    # arguments to pass in cancel_all_order
    cancel_order_opts = parser.add_argument_group(
        'Flags for cancel all orders.')

    return parser.parse_args()


def main():
    cp.blue("Starting order")
    args = parse_args()
    # arguments getting passed in

    endpoint = args.type.upper()
    market = args.market.upper()
    side = args.side
    ordType = args.orderType  # trailingStop.. is the S needed?
    orderQty = args.quantity
    price = args.entry if args.entry else None
    stopPx = args.stoploss if args.stoploss else None
    targetPx = args.targetpoint if args.targetpoint else None
    clientId = args.clientId

    cp.blue(
        f'{side}, {ordType}, {orderQty}, {price}, {stopPx}, {targetPx},{clientId}')
    # establish connection
    ftx = connection()
    # Transfer args to specify api Endpoint
    if endpoint == "CREATE":
        process_new_order(ftx, market, side, price, orderQty,
                          ordType, clientId, stopPx, targetPx)
    elif endpoint == "GET":
        process_get_order(ftx, market, ordType)
    elif endpoint == "APPEND":
        process_append_order(ftx, clientId, ordType, price,
                             stopPx, targetPx, orderQty)
    elif endpoint == "DELETE":
        process_delete_all_order(ftx, market)


if __name__ == '__main__':
    cp = ColorPrint()
    try:
        main()
    except Exception as ex:
        cp.red(ex.args)
    finally:
        exit()


# python ftxClient.py -t create -m xtz -s buy -o limit -qty 1 -e 3.01 -id 100
# python ftxClient.py -t create -m xtz -s sell -o stop -qty 1 -sl 2.05 -id 100
# python ftxClient.py -t create -m xtz -s sell -o take_profit -qty 1 -tp 5 -id 100


# GET ORDERS
# python ftxClient.py -t get -m xtz -o stop
# python ftxClient.py -t get -m xtz

# Delete orders
# python ftxClient.py -t delete -m xtz
