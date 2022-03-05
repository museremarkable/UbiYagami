from sqlalchemy import func
from connection.connection import ServerTCP
import enum
import h5py
import struct

class BuySide(enum.Enum):
    BUY = 1
    SELL = -1

class OrderType(enum.Enum):
    LIMIT_ORDER = 0 #限价申报
    COUNTER_PARTY_BEST_PRICE_ORDER = 1#对手方最优价格申报
    OUR_BEST_PRICE_ORDER = 2#本方最优价格申报
    TOP_FIVE_INS_TRANS_REMAIN_CANCEL_ORDER = 3#最优五档即时成交剩余撤销申报
    IMMEDIATE_TRANS_REMAIN_CANCEL_ORDER = 4#即时成交剩余撤销申报
    FULL_DEAL_OR_CANCEL_ORDER = 5#全额成交或撤销申报

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
    data structure to store record
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
    """
    all matching operation is accomplished in this class
    """
    def __init__(self):
        self.order_books = {}
        self.curr_order_id = 0
        self.curr_trade_id = 0
        print("test")

    "fun parameter is not determined, just for temporary"
    def add_order(self, str_code, order_id, price, volume, direction):
        """
        Add an order
        :param str_code     股票的代码
        :order_id           order ID
        :param price        当前order的bid/ask的价格
        :param volume       当前order的bid/ask的数量
        :param direction    order是买入还是卖出        
        :return The order and the list of trades.
                Empty list if there is no matching.
        """
        pass
    def cancel_order(self, order_id, str_code):
        """
        Cancel order
        :param order_id     order ID
        :param str_code     股票代码
        :return The order if the cancellation is successful
        """
        pass
    def amend_order(self, order_id, str_code, amended_price, amended_volume):
        """
        Amend an order
        :param order_id         order ID
        :param str_code         股票代码
        :param amended_price    Amended price, defined as zero if market order
        :param amended_volume   Amended order quantity
        :return The order and the list of trades.
                Empty list if there is no matching.
        """
        pass


    