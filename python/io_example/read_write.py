import h5py
import struct

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

def read_order_from_file(self, order_id_path, direction_path, price_path, volume_path, type_path):
    order_id_mtx = h5py.File(order_id_path, 'r')['order_id']
    direction_mtx = h5py.File(direction_path, 'r')['direction']
    price_mtx = h5py.File(price_path, 'r')['price']
    volume_mtx = h5py.File(volume_path, 'r')['volume']
    type_mtx = h5py.File(type_path, 'r')['type']
    x = 10
    y = 100
    z = 77
    return Order(x%10 + 1,
                order_id_mtx[x,y,z],
                DirectionType(direction_mtx[x,y,z]),
                price_mtx[x,y,z],
                volume_mtx[x,y,z],
                OrderType(type_mtx[x,y,z]))

def dump_trade(trade_list):
    with open("Ans", 'wb') as f:
        f.write(b''.join(map(lambda x: x.to_bytes(), trade_list)))

