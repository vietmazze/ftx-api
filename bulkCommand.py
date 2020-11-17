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
import numpy as np
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

    commands = collections.deque()

    for input in userInput.split(";"):
        # [buy 1 @8500, sell 1 @8600]
        commands.append(input.strip())

    while commands:
        currCommand = commands.popleft().split(" ")
        try:
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
                    cp.red(
                        f'Missing market to grab open orders, please reset instrument')

            ######################
            # -CANCEL ORDERS
            ######################
            elif currCommand[0] == "cancel":
                cancel_type = currCommand[1] if len(currCommand) >= 2 else None
                conditional_id = currCommand[2] if len(
                    currCommand) >= 3 else None
                # diff types of cancel

                if ftx.market is not None:
                    if cancel_type:
                        if cancel_type == "conditional":
                            if conditional_id:
                                ftx.cancel_orders(
                                    market_name=ftx.market, conditional_id=conditional_id)
                            else:
                                ftx.cancel_orders(
                                    market_name=ftx.market, conditional_orders=True)
                        elif cancel_type == "limit":
                            ftx.cancel_orders(
                                market_name=ftx.market, limit_orders=True)
                        elif cancel_type.isnumeric():
                            ftx.cancel_orders(
                                market_name=ftx.market, cancel_id=cancel_type)
                    else:
                        ftx.cancel_orders(market_name=ftx.market)
                else:
                    cp.red(
                        f'Missing market to delete orders, please reset instrument')
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
                    if currCommand[1]:
                        ftx.fatFinger = float(currCommand[1])
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

            ######################
            # - SPLITTING ORDERS
            # ! split [sell] [0.1] into [10] from [11288] to [11355]
            ######################
            elif currCommand[0] == "split":
                side = currCommand[1] if len(currCommand) > 1 else None
                size = currCommand[2] if len(currCommand) > 2 else None
                total = float(currCommand[4]) if len(currCommand) > 4 else None
                start = float(currCommand[6]) if len(currCommand) > 6 else None
                end = float((currCommand[8])) if len(currCommand) > 7 else None
                limitOrder = currCommand[9] if len(currCommand) > 8 else None
                if len(currCommand) > 8:
                    order_list = split_equal_parts(start, end, total)
                    size = float(size) / total
                    cp.green(order_list)
                    if not None in (side, size, total, start, end):

                        if side == "buy" or side == "sell":
                            while total > 0 and len(order_list) > 0:

                                ftx.place_order_cleanup(
                                    [side, float(size), str(order_list.pop())])
                                total -= 1
                        elif side == "stop" or side == "tp" or side == "trail":

                            while total > 0 and len(order_list) > 0:
                                price = str(order_list.pop())

                                ftx.place_conditional_order_cleanup(
                                    [side, float(size), price, limitOrder, price])
                                total -= 1
                    else:
                        cp.red(
                            f'One of the values in split order is missing, please check your command: \n {currCommand}')

                else:
                    cp.red(
                        f'Split order requires all 9 words typed out, please check your command: \n {currCommand}')

            #######################
            # - HELP COMMAND
            #######################

            elif currCommand[0] == "help" or currCommand[0] == "/help":
                show_command()

            else:
                cp.red(
                    f'Error in process_command, please use only one of those command option: buy,sell,order,cancel,position,split')

        except Exception as e:
            cp.red(
                f'Error in process_command, please restart your program:  {currCommand}  \n  {e} ')

######################################
# - Calculation for splitting order
######################################


def split_equal_parts(start, end, total):
    price = [start]
    avg_price = round((end - start) / total, 4)

    while total > 2:
        curr = (start + avg_price)
        price.append(curr)
        start = curr
        total -= 1
    price.append(end)
    return price


######################################
# - Commands for bot
######################################
def show_command():
    cp.green(f"""
            [instrument] [XTZ-PERP]
            [fatfinger] [#]
            market order - [type] [size] - buy 1000
            limit order - [type] [size] [price] - buy 1 @1
            stop market - [type] [size] [price] - stop 1 @1
            stop limit - [type] [size] [price] [side] [limitPrice] - stop 1 @1 sell @1
            take profit market - [type] [size] [price] - tp 1 @1
            take profit limit - [type] [size] [price] [side] [limitPrice] - tp 1 @1 sell @1
            split order - split [type] [size] into [total] from [price 1] to [price 2] - split [sell] [0.1] into [10] from [11288] to [11355]
            cancel - cancel all orders
            order - show all limit and stops open order
            position  - show all current positions
            position [market] - show specific market""")


def main(ftx):
    input("Welcome to FTX bot, please start by creating your market... press enter to continue")
    while True:
        # main program

        try:
            while True:

                userInput = input('Command: ')
                break
            if userInput == 'quit':
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
[instrument] [XTZ-PERP]
[fatfinger] [#]
market order - [type] [size] - buy 1000
limit order - [type] [size] [price] - buy 1 @1
stop market - [type] [size] [price] - stop 1 @1
stop limit - [type] [size] [price] [side] [limitPrice] - stop 1 @1 sell @1
take profit market - [type] [size] [price] - tp 1 @1
take profit limit - [type] [size] [price] [side] [limitPrice] - tp 1 @1 sell @1
cancel - cancel all orders
order - show all limit and stops open order
position  - show all current positions
position [market] - show specific market

"""
