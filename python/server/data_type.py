import enum
import struct

class BuySide(enum.Enum):
    BUY = 1
    SELL = -1

class DirectionType(enum.Enum):
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

    def to_suborder(self):
        return SubOrder(self.order_id, self.direction, self.price, self.volume)
        
    def to_minorder(self):
        return MinOrder(self.order_id, self.volume)

class SubOrder:
    def __init__(self, order_id, direction, price, volume):
        self.order_id = order_id
        self.direction = direction
        self.price = price
        self.volume = volume

    def to_minorder(self):
        return MinOrder(self.order_id, self.volume)

class MinOrder:
    """
    A order type that is stored in the order link, only contents minimum order info.
    """
    def __init__(self, order_id, volume):
        self.order_id = order_id
        self.volume = volume

class Trade:
    def __init__(self, stk_code, bid_id, ask_id, price, volume):
        self.stk_code = stk_code
        self.bid_id = bid_id
        self.ask_id = ask_id
        self.price = price
        self.volume = volume

    def to_bytes(self):
        return struct.pack("=iiidi", self.stk_code, self.bid_id, self.ask_id, self.price, self.volume)
