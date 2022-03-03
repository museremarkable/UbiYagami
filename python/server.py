from sqlalchemy import func
from connection import ServerTCP
import enum
import h5py
import struct

class BuySide(enum.Enum):
    BUY = 1
    SELL = -1


class Order:
    def __init__(self, stk_code, order_id, direction, price, volume, type):
        self.stk_code = stk_code
        self.order_id = order_id
        self.direction = direction
        self.price = price
        self.volume = volume
        self.type = type

class Trade:
    def __init__(self, stk_code, bid_id, ask_id, price, volume):
        self.stk_code = stk_code
        self.bid_id = bid_id
        self.ask_id = ask_id
        self.price = price
        self.volume = volume

    def to_bytes(self):
        return struct.pack("=iiidi", self.stk_code, self.bid_id, self.ask_id, self.price, self.volume)

class OrderBook:
    """
    to be defined, just for demo , will write in altree ?
    """
    def __init__(self):
        self.bids = {}
        self.asks = {}
        self.order_id_map = {}


    """
    this part can rewrite in cython for further performance improment ?
    """
class MatchingEngine:
    def __init__(self):
        self.order_books = {}
        self.curr_order_id = 0
        self.curr_trade_id = 0
        print("test")

    "fun parameter is not determined, just for temporary"
    def add_order(self, order):
        pass
    def cancel_order(self, order):
        pass
    def amend_order(self, order):
        pass


    