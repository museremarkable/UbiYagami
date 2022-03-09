import imp
from connection.connection import ClientTCP
import h5py
import struct
import time
import asyncio
from argparse import ArgumentParser
import numpy as np
from data_type import OrderType, DirectionType, OperationType, Order, Quote, Trade
#from python.server.server import BuySide, OrderType
#from server.server import Order


class Client:
    """
    read order from file, send order to exchange, (receive result from  exchanger? is it essential?)
    """
    def __init__(self, client_id):
        self.trade_list = []
        # client_id used to identify different client server
        self.client_id = client_id
        self.curr_order_page = np.array
    
    
    # asynchronous process data, 10 stock, when have already read one stock then send this stock to server, on the same time process next stock data
    async def data_read(self, data_file_path, res_file_path):
        """
        发送order, 生成结果
        :param data_file_path    数据存放文件夹
        :param res_file_path     结果存放位置      
        :return status, 存结果
        """
        order_id_path = data_file_path +'/'+ "order" + str(self.client_id) + ".h5"
        direction_path = data_file_path + '/'+ "direction" + str(self.client_id) + ".h5"
        price_path = data_file_path + '/'+ "price" + str(self.client_id) + ".h5"
        volume_path = data_file_path + '/'+ "volume" + str(self.client_id) + ".h5"
        type_path = data_file_path + '/'+ "type" + str(self.client_id) + ".h5"

        order_id_mtx = h5py.File(order_id_path, 'r')['order_id']
        direction_mtx = h5py.File(direction_path, 'r')['direction']
        price_mtx = h5py.File(price_path, 'r')['price']
        volume_mtx = h5py.File(volume_path, 'r')['volume']
        type_mtx = h5py.File(type_path, 'r')['type']
        hook_mtx = h5py.File(data_file_path + '/' + "hook.h5", 'r')['hook']

        data_page_number = order_id_mtx.shape[0]
        data_row_number = order_id_mtx.shape[1]
        data_column_number = order_id_mtx.shape[2]        
        per_stock_page_number = data_page_number / 10
        #data transform
        #this implementation only works for small data(100x10x10 0.06 per stock 100x100x100 35s per stock, 100x1000x1000 1240s per stock, it's unaccecptable)
        for curr_stock_id in range(10):
            #print(curr_stock_id)
            curr_order_id_page = np.array(order_id_mtx)[curr_stock_id].flatten()
            curr_direction_page = np.array(direction_mtx)[curr_stock_id].flatten()
            curr_price_page = np.array(price_mtx)[curr_stock_id].flatten()
            curr_volumn_page = np.array(volume_mtx)[curr_stock_id].flatten()
            curr_type_page = np.array(type_mtx)[curr_stock_id].flatten()
            for i in range(1, per_stock_page_number):
                print(i)
                temp_order_id_page = np.array(order_id_mtx)[i * 10 + curr_stock_id].flatten()
                temp_direction_page = np.array(direction_mtx)[i * 10 + curr_stock_id].flatten()
                temp_price_page = np.array(price_mtx)[i * 10 + curr_stock_id].flatten()
                temp_volume_page = np.array(volume_mtx)[i * 10 + curr_stock_id].flatten()
                temp_type_page = np.array(type_mtx)[i * 10 + curr_stock_id].flatten()
                curr_order_id_page = np.concatenate((curr_order_id_page,temp_order_id_page))
                curr_direction_page = np.concatenate((curr_direction_page, temp_direction_page))
                curr_price_page = np.concatenate((curr_price_page, temp_price_page))
                curr_volumn_page = np.concatenate((curr_volumn_page, temp_volume_page))
                curr_type_page = np.concatenate((curr_type_page, temp_type_page))
                # time_end=time.time()         
                # print('totally cost',time_end-time_start)
            #convert 2d matrix data to 1d array
            # curr_order_id_page = curr_order_id_page.flatten()
            # curr_direction_page = curr_direction_page.flatten()
            # curr_price_page = curr_price_page.flatten()
            # curr_volumn_page = curr_volumn_page.flatten()
            # curr_type_page = curr_type_page.flatten()
            # curr_order_page is a 2d matrix (5000x5), coresponding order_id, direction, price, volumn, type corresponding one stock
            curr_order_page = np.transpose([curr_order_id_page, curr_direction_page, curr_price_page, curr_volumn_page, curr_type_page])
            # sort curr_order_page by order_id
            curr_order_page = curr_order_page[curr_order_page[:, 0].argsort()] 
            print(curr_order_id_page.shape)
            print(curr_order_page.shape)
            
            # asynchronous send data
            await self.communicate_with_server(curr_order_page, hook_mtx, curr_stock_id, res_file_path)

    async def communicate_with_server(self, curr_order_page, hook , stock_id, save_path) -> list:
        """
        input is one stock data and stock id, communicate with two server , get the trade and then write it into corresponding trade file
        """
        self.trade_list = ClientTCP(curr_order_page, stock_id, hook)
        self.dump_trade(self.trade_list, save_path, stock_id)


    def dump_trade(self, trade_list, save_path, stock_id):
        """
        read trade_list, tans every trade into a 12 byte 
        :param trade_list       结果        
        :param save_path        the folder path where res save
        :return none
        """
        res_file_path = save_path + '/' + str(stock_id)
        with open(res_file_path, 'wb') as f:
            f.write(b''.join(map(lambda x: x.to_bytes(), trade_list)))


parser = ArgumentParser()
parser.add_argument("-f", "--file",  help="data file folder path")
parser.add_argument("-r", "--res",  help="result folder path")
parser.add_argument("-c", "--client_id",  help="client_id, which is 1 or 2")
args = parser.parse_args()

Trader_Server = Client(args[2])
Trader_Server.data_read(args[0], args[1])

