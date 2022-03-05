import imp
from connection import ClientTCP
import h5py
from python.server import BuySide, OrderType
from server import Order


class client:
    """
    read order from file, send order to exchange, (receive result from  exchanger? is it essential?)
    """
    def __init__(self):
        self.trade_list = []
    def result_generate(self, data_file_path, res_file_path):
        """
        发送order, 生成结果
        :param data_file_path    数据存放文件夹
        :param res_file_path     结果存放位置      
        :return status, 存结果
        """
        pass


    def read_order_from_file(self, order_id_path, direction_path, price_path, volume_path, type_path):
        """
        发送order, 生成结果
        :param order_id_path 
        :param direction_path     
        :param price_path     
        :param volume_path     
        :param type_path

        :return a Order class
        """
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
                    BuySide(direction_mtx[x,y,z]),
                    price_mtx[x,y,z],
                    volume_mtx[x,y,z],
                    OrderType(type_mtx[x,y,z]))

    def dump_trade(trade_list):
        """
        生成结果
        :param trade_list 结果         
        :return none
        """
        with open("Ans", 'wb') as f:
            f.write(b''.join(map(lambda x: x.to_bytes(), trade_list)))