from cProfile import run
import imp
import tarfile
from python.connection.connection import ClientTCP
import h5py
from enum import IntEnum
from python.connection.order_type import OrderTick
from python.connection.pollable_queue import PollableQueue
import socket
import json
import struct
import pathlib
import os
import pandas as pd
import time
from python.utils.wirte_logger import get_logger
import asyncio
from argparse import ArgumentParser
import numpy as np
from data_type import OrderType, DirectionType, OperationType, Order, Quote, Trade
from functools import reduce
from operator import add
#from python.server.server import BuySide, OrderType
#from server.server import Order

def is_in_trading_day_session_trading_hour(now: pd.Timestamp = None):
    if now is None:
        now = pd.Timestamp.now(tz='Asia/Shanghai')
    now_ = now.strftime("%H:%M:%S,%f")
    s1 = "09:00:00"
    e1 = "10:15:00"
    s2 = "10:30:00"
    e2 = "11:30:00"
    s3 = "13:30:00"
    e3 = "15:00:00"
    rslt_ix = sorted([now_, s1, e1, s2, e2, s3, e3]).index(now_)
    if rslt_ix % 2 == 0:
        return False
    else:
        return True


class Operation(IntEnum):
    HEARTBEAT = 0
    KEEPALIVE = 1
    KEEPALIVE_FAIL = 2
    INFO = 3


class OrderStreamClient:
    BUF_SIZE = 2 << 20
    order_tick_shema = OrderTick()
    # todo:完善

    def __init__(self, ip:str, port:int):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(3)
        self._socket.connect((ip, port))
        self.data_queue = PollableQueue()
        self._is_running = True
        # todo: write a function to read data file
        self._load_symbol_map()
        self.log = get_logger(__name__, filename='streaming_client')
        # write a log ?
        # self.log


    def _load_symbol_map(self):
        # todo:  看看这里应该怎么写
        # path = pathlib.Path(__file__)
        path = os.getcwd()
        pass

    def close(self):
        self._is_running = False

    def start_streaming(self):
        incomplete_frame = b''
        while self._is_running:
            try:
                data = incomplete_frame + self._socket.recv(self.BUF_SIZE)
            except socket.timeout:
                if is_in_trading_day_session_trading_hour():
                    self.msg_bot.msg2fs('Sending Heart Beat...Plz Check Streaming Data Availability!')
                self.heartbeat()
                continue
            except BaseException as e:
                self.log.error(f'got error: {e}')
                time.sleep(1)  # 避免不断报错
                continue

        frames = data.split(b'\r\n')
        for frame in frames:
            if frame:  # 不考虑 b'' 的情况
                if frame.endswith(b'}') and len(frame) > 8:
                    try:
                        payload = frame[8:]
                        # self.data_queue.put(order_tick)
                    except BaseException as e:
                        self.log.error(f'{e}, received {frame}')
                    incomplete_frame = b''
                else:
                    self.log.debug(f'received incomplete frame: {frame}')
                    incomplete_frame = frame

        self.log.warning('socket is closing!')
        self._socket.close()
        self.log.warning('socket closed')


    def keep_alive(self):
        self._socket.send()
        # todo: 活的时候要发什么

    def keep_alive_fail(self):
        self._socket.send()
        # todo:死了发什么

    def heartbeat(self):
        self._socket.send(self._generate_msg(operation=Operation.HEARTBEAT, body={'time': int(time.time()*1000)}))
        self.log.info()

    @staticmethod
    def _generate_msg(operation: Operation, body: dict) -> bytes:
        return struct.pack('!ii', 1, operation) + json.dumps(body).encode() + b'\r\n'




class Client:
    """
    read order from file, send order to exchange, (receive result from  exchanger? is it essential?)
    """

    def __init__(self, client_id, data_file_path, res_file_path):

        self.trade_list = [[]] * 10
        # client_id used to identify different client server
        self.client_id = client_id
        self.all_page = [[]] * 10
        self.data_file_path = data_file_path
        self.res_file_path = res_file_path
        self.hook_mtx = h5py.File(data_file_path + '/' + "hook.h5", 'r')['hook']
        self.hook_position = [0] * 10
    
    # process all data, alter that then trans these data
    def data_read(self):
        """
        read all data from file
        """
        order_id_path = self.data_file_path +'/'+ "order" + str(self.client_id) + ".h5"
        direction_path = self.data_file_path + '/'+ "direction" + str(self.client_id) + ".h5"
        price_path = self.data_file_path + '/'+ "price" + str(self.client_id) + ".h5"
        volume_path = self.data_file_path + '/'+ "volume" + str(self.client_id) + ".h5"
        type_path = self.data_file_path + '/'+ "type" + str(self.client_id) + ".h5"

        order_id_mtx = h5py.File(order_id_path, 'r')['order_id']
        direction_mtx = h5py.File(direction_path, 'r')['direction']
        price_mtx = h5py.File(price_path, 'r')['price']
        volume_mtx = h5py.File(volume_path, 'r')['volume']
        type_mtx = h5py.File(type_path, 'r')['type']
        

        data_page_number = order_id_mtx.shape[0]
        data_row_number = order_id_mtx.shape[1]
        data_column_number = order_id_mtx.shape[2]        
        per_stock_page_number = data_page_number / 10
        #data transform
        #this implementation only works for small data(100x10x10 0.06 per stock 100x100x100 35s per stock, 100x1000x1000 1240s per stock, it's unaccecptable)
        for curr_stock_id in range(10):
            #print(curr_stock_id)
            curr_order_id_page = order_id_mtx[curr_stock_id].reshape(-1)
            curr_direction_page = direction_mtx[curr_stock_id].reshape(-1)
            curr_price_page = price_mtx[curr_stock_id].reshape(-1)
            curr_volumn_page = volume_mtx[curr_stock_id].reshape(-1)
            curr_type_page = type_mtx[curr_stock_id].reshape(-1)
            for i in range(1, per_stock_page_number):
                temp_order_id_page = order_id_mtx[i * 10 + curr_stock_id].reshape(-1)
                temp_direction_page = direction_mtx[i * 10 + curr_stock_id].reshape(-1)
                temp_price_page = price_mtx[i * 10 + curr_stock_id].reshape(-1)
                temp_volume_page = volume_mtx[i * 10 + curr_stock_id].reshape(-1)
                temp_type_page = type_mtx[i * 10 + curr_stock_id].reshape(-1)
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
            self.all_page.append(curr_order_page)
            
            # asynchronous send data
            #await self.communicate_with_server(curr_order_page, hook_mtx, curr_stock_id, res_file_path)
    async def communicate_with_server(self):
        """
        communicate all data with server
        """
        """
        stock_1_task = asyncio.create_task(
            self.communicate_single_stock_with_server(0))
        stock_2_task = asyncio.create_task(
            self.communicate_single_stock_with_server(1))
        stock_3_task = asyncio.create_task(
            self.communicate_single_stock_with_server(2))
        stock_4_task = asyncio.create_task(
            self.communicate_single_stock_with_server(3))        
        stock_5_task = asyncio.create_task(
            self.communicate_single_stock_with_server(4))
        stock_6_task = asyncio.create_task(
            self.communicate_single_stock_with_server(5))
        stock_7_task = asyncio.create_task(
            self.communicate_single_stock_with_server(6))
        stock_8_task = asyncio.create_task(
            self.communicate_single_stock_with_server(7))
        stock_9_task = asyncio.create_task(
            self.communicate_single_stock_with_server(8))
        stock_10_task = asyncio.create_task(
            self.communicate_single_stock_with_server(9))
        ret = await asyncio.gather(stock_1_task, stock_2_task, stock_3_task, stock_4_task, stock_5_task, stock_6_task, stock_7_task, stock_8_task, stock_9_task, stock_10_task)            
        """
    async def communicate_single_stock_with_server(self, stock_id) -> list:
        """
        input is one stock data and stock id, communicate with two server , get the trade and then write it into corresponding trade file
        """
        """
        每次传输一个order class的数据
        首先根据stock_id读入对应的股票数据， 然后按order_id顺序进行传输。 
        传输时，首先在hook矩阵中判断是否需要传输，(func order_id_need_to_trans)
        不需要：除stock_id和order_id外其它参数全部置0
        需要：json文件格式传输

        """
        """
        EXAMPLE:  trade1传输的stock1的order_id
        """
        data_length = self.all_page[stock_id].shape[0]
        if self.order_is_need_to_tans(order_id, stock_id):
            #here begin trans corresponding order_id
            #to do
            #todo 当接收到传回的结果后，需要将其append到对应的self.trade_list中

            
            print("todo")
        else:
            print("Todo")
            #only trans order_id and stock_id, other parameter is 0
            #to do 
    def order_is_need_to_tans(self, order_id, stock_id):
        if self.order_id < self.hook_mtx[stock_id][self.hook_position[stock_id]][0]:
            return True
        elif self.order_id == self.hook_mtx[stock_id][self.hook_position[stock_id]][0]:
            target_stk_code = self.hook_mtx[stock_id][self.hook_position[stock_id]][1]
            target_trade_idx = self.hook_mtx[stock_id][self.hook_position[stock_id]][2]
            arg = self.hook_mtx[stock_id][self.hook_position[stock_id]][3]
            if self.trade_list[target_stk_code][target_trade_idx - 1] < arg:
                self.hook_position[stock_id] += 1
                return True
            else:
                self.hook_position[stock_id] += 1
                return False
        else:
            while(self.hook_mtx[stock_id][self.hook_position[stock_id]][0] > self.order_id):
                self.hook_position[stock_id] += 1
            if self.order_id == self.hook_mtx[stock_id][self.hook_position[stock_id]][0]:
                target_stk_code = self.hook_mtx[stock_id][self.hook_position[stock_id]][1]
                target_trade_idx = self.hook_mtx[stock_id][self.hook_position[stock_id]][2]
                arg = self.hook_mtx[stock_id][self.hook_position[stock_id]][3]
                if self.trade_list[target_stk_code][target_trade_idx - 1] < arg:
                    self.hook_position[stock_id] += 1
                    return True
                else:
                    self.hook_position[stock_id] += 1
                    return False
            else:
                return True                 
            


            
            
            
    def dump_trade(self, stock_id):
        """
        read trade_list, tans every trade into a 12 byte 
        :param trade_list       结果        
        :param save_path        the folder path where res save
        :return none
        """
        res_file_path = self.res_file_path + '/' + 'trade' + str(stock_id)
        with open(res_file_path, 'wb') as f:
            f.write(b''.join(map(lambda x: x.to_bytes(), self.trade_list[stock_id])))


parser = ArgumentParser()
parser.add_argument("-f", "--file",  help="data file folder path")
parser.add_argument("-r", "--res",  help="result folder path")
parser.add_argument("-c", "--client_id",  help="client_id, which is 1 or 2")
args = parser.parse_args()

Trader_Server = Client(args[2])
Trader_Server.data_read(args[0], args[1])
asyncio.run(Trader_Server.communicate_with_server())
#todo暂时把接受数据与写文件解耦，后续tcp部分完成后和tcp部分写到一起
for i in range(10):
    Trader_Server.dump_trade(i)
