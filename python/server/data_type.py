import enum
import struct


class DirectionType(enum.Enum):
    """
    the trading direction of the order: buy side / sell side;
    """
    BUY = 1
    SELL = -1


class OrderType(enum.Enum):
    """
    Totally 6 types of order;
    """
    LIMIT_ORDER = 0                             #限价申报 limit order
    COUNTER_PARTY_BEST_PRICE_ORDER = 1          #对手方最优价格申报 best price of opposite side
    OUR_BEST_PRICE_ORDER = 2                    #本方最优价格申报   best price of own side
    TOP_FIVE_INS_TRANS_REMAIN_CANCEL_ORDER = 3  #最优五档即时成交剩余撤销申报 fill within the top 5 optimal price, cancel the remaining
    IMMEDIATE_TRANS_REMAIN_CANCEL_ORDER = 4     #即时成交剩余撤销申报 immidiate order, cancel the remaining
    FULL_DEAL_OR_CANCEL_ORDER = 5               #全额成交或撤销申报 full deal or cancel


class Order:
    """
    Order type used for transferring;
    """

    __slots__ = ['stk_code','order_id','direction','price','volume','type']
    def __init__(self, stk_code, order_id, direction, price, volume, type):
        self.stk_code = stk_code
        self.order_id = order_id
        self.direction = direction
        self.price = price
        self.volume = volume
        self.type = type

    def to_suborder(self):
        """
        convert into SubOrder type;
        """
        return SubOrder(self.order_id, self.direction, self.price, self.volume)
        
    def to_minorder(self):
        """
        convert into MinOrder type;
        """
        return MinOrder(self.order_id, self.volume)
    



class SubOrder:
    """
    A Order type used inside the order book operations;
    """
    __slots__ = ['order_id','direction','price','volume']
    def __init__(self, order_id, direction, price, volume):
        self.order_id = order_id
        self.direction = direction
        self.price = price
        self.volume = volume

    def to_minorder(self):
        """
        convert into MinOrder type
        """
        return MinOrder(self.order_id, self.volume)


class MinOrder:
    """
    A order type that is stored in the order link, only contents minimum order info taking up less memory.
    """
    __slots__ = ['order_id','volume']
    def __init__(self, order_id, volume):
        self.order_id = order_id
        self.volume = volume


class Quote:
    """"
    A date type used to quote feed from exchange to traders
    The trader can use these quotes to reconstruct their local order book (optional)
    """
    def __init__(self, stk_code, order_id, price, volume, operation):
        self.stk_code = stk_code
        self.order_id = order_id
        self.price = price
        self.volume = volume
        self.operation = operation


class OperationType(enum.Enum):
    """
    A type used as update instructions to reconstruct the local order book;
    """
    NEW_BID = 0
    NEW_ASK = 1
    AMEND_BID = 2
    AMEND_ASK = 3
    REMOVE_BID = 4
    REMOVE_ASK = 5


class Trade:
    """
    A data type that contains transaction informations;
    """
    def __init__(self, stk_code, bid_id, ask_id, price, volume):
        self.stk_code = stk_code
        self.bid_id = bid_id
        self.ask_id = ask_id
        self.price = price
        self.volume = volume

    def to_bytes(self):
        return struct.pack("=iiidi", self.stk_code, self.bid_id, self.ask_id, self.price, self.volume)
