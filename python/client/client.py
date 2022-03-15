from asyncore import poll
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
from asyncio import AbstractEventLoop, StreamReader, StreamWriter
from argparse import ArgumentParser
import numpy as np

from python.data_type import OrderType, DirectionType, OperationType, Order, Quote, Trade

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
    # todo： 做好解析之后还回去。

    def __init__(self, ip: str, port: int):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(3)
        self._socket.connect((ip, port))
        self.data_queue = PollableQueue()
        self._is_running = True
        # todo: write a function to read data file
        self.log = get_logger(__name__, filename='streaming_client')
        # write a log ?
        # self.log

    def close(self):
        self._is_running = False

    def start_streaming(self):
        incomplete_frame = b''
        while self._is_running:
            try:
                data = incomplete_frame + self._socket.recv(self.BUF_SIZE)
            except socket.timeout:
                if is_in_trading_day_session_trading_hour():
                    self.log.debug('Sending Heart Beat...Plz Check Streaming Data Availability!')
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
        self.all_page = []
        self.data_file_path = data_file_path
        self.res_file_path = res_file_path
        self.hook_mtx = h5py.File(data_file_path + '/' + "hook.h5", 'r')['hook']
        self.hook_position = [0] * 10
    
    # process all data, alter that then trans these data
    def data_read(self):
        """
        read all data from file
        """
        order_id_path = self.data_file_path +'/'+ "order_id" + str(self.client_id) + ".h5"
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
        per_stock_page_number = data_page_number // 10
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
    async def communicate_with_server(self, send_queue, receive_queue):
        """
        communicate all data with server
        why use async not multiprocess
        """
        
        stock_1_task = asyncio.create_task(
            self.communicate_single_stock_with_server(0, send_queue))
        stock_2_task = asyncio.create_task(
            self.communicate_single_stock_with_server(1, send_queue))
        stock_3_task = asyncio.create_task(
            self.communicate_single_stock_with_server(2, send_queue))
        stock_4_task = asyncio.create_task(
            self.communicate_single_stock_with_server(3, send_queue))        
        stock_5_task = asyncio.create_task(
            self.communicate_single_stock_with_server(4, send_queue))
        stock_6_task = asyncio.create_task(
            self.communicate_single_stock_with_server(5, send_queue))
        stock_7_task = asyncio.create_task(
            self.communicate_single_stock_with_server(6, send_queue))
        stock_8_task = asyncio.create_task(
            self.communicate_single_stock_with_server(7, send_queue))
        stock_9_task = asyncio.create_task(
            self.communicate_single_stock_with_server(8, send_queue))
        stock_10_task = asyncio.create_task(
            self.communicate_single_stock_with_server(9, send_queue))
        receive_task = asyncio.create_task(
            self.read_trade_data_from_queue(receive_queue)
            )
        ret = await asyncio.gather(stock_1_task, stock_2_task, stock_3_task, stock_4_task, stock_5_task, stock_6_task, stock_7_task, stock_8_task, stock_9_task, stock_10_task, receive_task)            
        
    async def communicate_single_stock_with_server(self, stock_id, send_queue):
        """
        put data in a queue
        """
        print("start put orderid %d of stock %d in queue")
        
        for i in range(len(self.all_page[stock_id])):
            if self.order_is_need_to_tans(i, stock_id):
                direction = DirectionType(self.all_page[stock_id][i][1])
                price = self.all_page[stock_id][i][2]
                volume = self.all_page[stock_id][i][3]
                type = OrderType(self.all_page[stock_id][i][4])
                tempdata = Order(stock_id, i, direction, price, volume, type)
                    #here need to add some to avoid 
                    #if corresponding trade_list number is 
                if i % 20 == 1:
                # a stock hook 1000 6 230 5
                    await asyncio.sleep(2)
                await send_queue.put(tempdata)
            
            
            else:
                direction = DirectionType(self.all_page[stock_id][i][1])
                type = OrderType(self.all_page[stock_id][i][4])
                tempdata = Order(stock_id, i, direction, 0, 0, type)
                await send_queue.put(tempdata)
            #only trans order_id and stock_id, other parameter is 0

   


    async def order_is_need_to_tans(self, order_id, stock_id):
        """
        use to determine whther this order need to send
        """
        if order_id < self.hook_mtx[stock_id][self.hook_position[stock_id]][0]:
            # if this order id is smaller than the first hook orderid, definetely need to send

            return True
        elif order_id == self.hook_mtx[stock_id][self.hook_position[stock_id]][0]:
            # if this order id is in hook matrix, begin to see if volume is smaller than arg
            target_stk_code = self.hook_mtx[stock_id][self.hook_position[stock_id]][1]
            target_trade_idx = self.hook_mtx[stock_id][self.hook_position[stock_id]][2]
            #todo: here need to use asyncio.Event to resolve condition when trader_list length is shorter than target_trade_idx
            arg = self.hook_mtx[stock_id][self.hook_position[stock_id]][3]
            while True:
                if len(self.trade_list[stock_id]) < target_trade_idx:
                    print("corresponding stock %d 's tradelist is not enough when stock %d order_id %d inquire hook")
                    print("stock %d wait 10 seconds")
                    await asyncio.sleep(3)
                else:
                    break
            
            if self.trade_list[target_stk_code][target_trade_idx - 1] < arg:
                self.hook_position[stock_id] += 1
                return True
            else:
                self.hook_position[stock_id] += 1
                return False
        else:
            #if order id is bigger than the current hook order_id, we need to add hook position to make it <= hook order id
            while(self.hook_mtx[stock_id][self.hook_position[stock_id]][0] > order_id):
                self.hook_position[stock_id] += 1
            if order_id == self.hook_mtx[stock_id][self.hook_position[stock_id]][0]:
                target_stk_code = self.hook_mtx[stock_id][self.hook_position[stock_id]][1]
                target_trade_idx = self.hook_mtx[stock_id][self.hook_position[stock_id]][2]
                arg = self.hook_mtx[stock_id][self.hook_position[stock_id]][3]
                while True:
                    if len(self.trade_list[stock_id]) < target_trade_idx:
                        print("corresponding stock %d 's tradelist is not enough when stock %d order_id %d inquire hook" %(target_stk_code, stock_id, order_id))
                        print("stock %d wait 3 seconds" % (stock_id))
                        await asyncio.sleep(3)
                    else:
                        break
                if self.trade_list[target_stk_code][target_trade_idx - 1] < arg:
                    self.hook_position[stock_id] += 1
                    return True
                else:
                    self.hook_position[stock_id] += 1
                    return False
            else:
                return True               
    async def read_trade_data_from_queue(self, receive_queue):
        #read data from trade data
        while True:
            trade_item = await reveive_queue.get()
            if trade_item is None:
                await asyncio.sleep(1)
            else:
                self.trade_list[trade_item.stock_id].append(trade_item)          
            
            

    def store_all_trade(self, stock_id):
        res_file_path = self.res_file_path + '/' + 'trade' + str(stock_id)
        with open(res_file_path, 'wb') as f:
            f.write(b''.join(map(lambda x: x.to_bytes(), self.trade_list[stock_id])))
parser = ArgumentParser()
parser.add_argument("-f", "--filepath",  help="data file folder path")
parser.add_argument("-r", "--respath",  help="result folder path")
parser.add_argument("-c", "--client_id",  help="client_id, which is 1 or 2")
args = parser.parse_args()
send_queue = asyncio.Queue()
reveive_queue = asyncio.Queue()
Trader_Server = Client(args.client_id)
Trader_Server.data_read(args.filepath, args.respath)
asyncio.run(Trader_Server.communicate_with_server(send_queue, reveive_queue))
#todo暂时把接受数据与写文件解耦，后续tcp部分完成后和tcp部分写到一起
for i in range(10):
    Trader_Server.store_all_trade(i + 1)
