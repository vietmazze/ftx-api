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
from ftxOrder import FtxCLient


path = './keys.env'
load_dotenv(dotenv_path=path, verbose=True)

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger('LOGGER_NAME')

# process new buy/sell order


def connection(self, subaccount_name):
    ftx = FtxClient(subaccount_name)
    return ftx


def process_new_order(ftx: FtxCLient, market, side, price, type, clientId, stopPx, targetPx):
    cp.yellow("Process order started")
    if type == "limit" or type == "market":
        ftx.place_order(market, side, price, size, type, clientId)

    elif type == "stop":
        ftx.place_conditional_order(
            market, side, size, type=ordType, trigger_price=stopPx, clientId=clientId)
    elif type == "take_profit":
        ftx.place_conditional_order(market, side, size, type=ordType, targetPx, clientId=clientId)
    elif type == "trailing":

        # Edit current order
        #ftx.place_conditional_order(market=market,side=side,size=sizeSL,trigger_price = trigger_price_stoploss,type = typeStop)

        #ftx.place_conditional_order(market=market,side=side,size=sizeTP,trigger_price = trigger_price_tp,type = typeTP)

        # placing stoploss - STOP MARKET
        # typeStop = 'stop'
        # market=ftx.markets.get('XTZ')
        # side = "sell"
        # trigger_price_stoploss = 1.75
        # sl_clientId = 'stoploss_order2'
        # sizeSL = 1

        # #placing target point - TAKE PROFIT MARKET
        # typeTP = "take_profit"
        # market = ftx.markets.get('XTZ')
        # side = "sell"
        # trigger_price_tp = 4.5
        # tp_clientId = 'targetpoint_order4'
        # sizeTP = 1


def process_append_order(ftx: FtxCLient, orderID, origClOrdID, ordType, price, stopPx, targetPx, orderQty):
    cp.yellow("Connecting to API orders")


def process_get_order(ftx: FtxCLient,):
    cp.yellow("Connecting to API orders")


def process_delete_all_order(ftx: FtxCLient,):
    cp.yellow("Connecting to API orders")


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
                            help="Choose order type", choices=['limit', 'market', 'stop', 'take_profit', 'trailing'], default="limit")
    order_opts.add_argument('-qty', '--quantity', type=int,
                            dest='quantity', help="Quantity", nargs='?', const=0)
    order_opts.add_argument('-e', '--entry', type=int,
                            dest='entry', help="Entry price for limit order only", nargs='?', const=0)
    order_opts.add_argument('-sl', '--stoploss', type=int,
                            dest='triggerPrice', help="Stoploss price entry", nargs='?', const=0)
    order_opts.add_argument('-tp', '--targetpoint',
                            type=int, dest='targetpoint', help="Target point entry", nargs='?', const=0)
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
    price = args.entry
    stopPx = args.stoploss
    targetPx = args.targetpoint
    clientId = args.clientId

    cp.blue(
        f'{side}, {ordType}, {orderQty}, {price}, {stopPx}, {targetPx},{orderID}')
    # establish connection
    ftx = connection()

    # Transfer args to specify api Endpoint
    if endpoint == "CREATE":
        process_new_order(ftx, market, side, price, type=ordType, size, clientId, stopPx, targetPx)
    elif endpoint == "GET":
        process_get_order()
    elif endpoint == "APPEND":
        process_append_order()
    elif endpoint == "DELETE":
        process_delete_all_order()


if __name__ == '__main__':
    cp = ColorPrint()
    try:
        main()
    except Exception as ex:
        cp.red(ex.args)
    finally:
        exit()
