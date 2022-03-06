from sqlalchemy import func
from connection.connection import ServerTCP
import enum
import h5py
import struct
from data_type import Order, MinOrder, Trade, OrderType, DirectionType

class BookBase:
    def __init__(self):
        pass

    def push_back():
        pass

    def pull_in():
        pass

class OrderLink:
    """
    The link list of orders under each price level
    """
    def __init__(self):
        pass
    def insert_order(self, minorder: MinOrder):
        """
        for order type 
        LIMIT_ORDER, 
        OUR_BEST_PRICE_ORDER
        """
        pass

    def match_order(self, size):
        """
        Match order from lower order_id to higher until the size is all filled. 
        Otherwise, return the size remain to fill after consuming all the available orders on the link
        : size      the size of to fill
        : return1    number of volume remained to fill for this coming order
        : return2   list of transaction detail in Trade type
        """
        pass
        remain = 0
        ls_trade = []
        return remain, ls_trade

    def amend_order(self, order_id, diff):
        pass

    def cancel_order(self, order_id):
        pass

class OrderBook:
    """
    data structure to store record
    to be defined, just for demo , will write in altree ?
    """
    def __init__(self):
        self.bids = {}
        self.asks = {}
        self.order_id_map = {}
    
    def _get_price_level(self, price):
        pass

    def handle_order_limit(self, order: Order):
        pass

    def handle_order_counter_side_optimal(self, ):
        pass

    def handle_order_own_side_optimal(self, ):
        pass

    def handle_order_best_five(self, ):
        pass

    def handle_order_immediate_transact(self, ):
        pass

    def handle_order_full_deal(self, ):
        pass



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


    