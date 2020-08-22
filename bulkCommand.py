from requests import Request, Session, Response
import time
import collections
import datetime
import json
import logging
import hmac
import hashlib
import os
import urllib

from ftxBulkOrder import FtxClient
from dotenv import load_dotenv

from typing import Optional, Dict, Any, List
from colorprint import ColorPrint
from colorama import Fore, Back, Style, init

path = './keys.env'
load_dotenv(dotenv_path=path, verbose=True)

logging.basicConfig(level=logging.INFO, format=(
    Fore.BLUE + '[+] ' + Style.RESET_ALL + '%(message)s '))


def process_command(ftx, userInput):
    # dispatcher = {'instrument': ,
    #               'fatfinger': ,
    #               'buy': place_order,
    #               'sell': ,
    #               'alias': ,
    #               'tp': place_conditional_order,
    #               'trail': ,
    #               'close':,
    #               'cancel': cancel_orders,
    #               'position': ,
    #               'order': get_open_orders}

    commands = collections.deque()

    for input in userInput.split(";"):
        # [buy 1 @8500, sell 1 @8600]
        commands.append(input.strip())

    while commands:
        currCommand = commands.popleft().split(" ")

        ######################
        # -PLACING ORDER
        ######################
        if currCommand[0] == "buy" or currCommand[0] == "sell":
            ftx.place_order_cleanup(currCommand)
        ######################
        # -PLACING CONDITIONAL ORDER
        ######################
        elif currCommand[0] == "stop" or currCommand[0] == "tp" or currCommand[0] == "trail":

            ftx.place_conditional_order_cleanup(currCommand)
        ######################
        # -SHOW OPEN ORDERS
        ######################
        elif currCommand[0] == "order":
            market = currCommand[1] if len(currCommand) > 1 else None

            if market:
                ftx.get_open_orders(market)
            elif not market and ftx.market:
                ftx.get_open_orders(ftx.market)
            else:
                cp.red(f'Missing market to grab open orders, please reset instrument')
        ######################
        # -CANCEL ORDERS
        ######################
        elif currCommand[0] == "cancel":
            # diff types of cancel
            if ftx.market is not None:
                ftx.cancel_orders(ftx.market)
            else:
                cp.red(f'Missing market to delete orders, please reset instrument')
        ######################
        # -LOCKING INSTRUMENT
        ######################
        elif currCommand[0] == "instrument":
            if len(currCommand) < 2:
                cp.green(f'Current MARKET: {ftx.market}')
            elif currCommand[1]:
                ftx.market = currCommand[1].upper()
                cp.green(f'Assign new MARKET: {ftx.market}')
        ######################
        # -SET FATFINGER:
        ######################
        elif currCommand[0] == "fatfinger":
            if len(currCommand) > 1:
                if float(currCommand[1]):
                    ftx.fatFinger = currCommand[1]
                    cp.green(f'fatFinger set: {ftx.fatFinger}')
                else:
                    cp.red(
                        f'Please input only digits for fatfinger: {currCommand[1]}')
            else:
                cp.red(f'Missing the value for fatfinger')
        ######################
        # -SHOW OPEN POSITIONS
        ######################
        elif currCommand[0] == "position":
            market = currCommand[1] if len(currCommand) > 1 else None

            ftx.get_position(name=market)

        else:
            pass

        # creating alias


def main(ftx):
    input("Welcome to FTX bot, please start by creating your market... press enter to continue")
    input("Set your market by typing: instrument NAME")
    input("Please set your limit size fatfinger for this market: fatfinger SIZE")
    input("Type /help for list of commands")
    while True:
        # main program
        try:
            while True:

                userInput = input('Command: ')
                break
            if userInput == 'q':
                break
            else:
                process_command(ftx, userInput)
        except Exception as e:
            cp.red(f'Exception in calling main() {e}')


if __name__ == '__main__':
    cp = ColorPrint()
    ftx = FtxClient()
    try:
        main(ftx)
    except Exception as ex:
        cp.red(ex.args)
    finally:
        exit()


"""
instrument XTZ-PERP
fatfinger 2
buy 1 1
tp 1 @1 sell @
stop 1 @1
buy 1
sell 1
cancel  # cancel all orders
order   # showing only open orders, not trigger orders

position  # current position
position XTZ-PERP
"""
