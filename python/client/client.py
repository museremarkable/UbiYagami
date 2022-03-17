import os
import sys
path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(path)
from argparse import ArgumentParser
import multiprocessing

import h5py
from enum import IntEnum
from connection.order_type import OrderTick
from connection.pollable_queue import PollableQueue
import socket
import json
import struct
import pathlib
import os
import pandas as pd
import time
from utils.wirte_logger import get_logger
import asyncio
from asyncio import AbstractEventLoop, StreamReader, StreamWriter
from connection.tcp_client import ClientTCP
import numpy as np
from data_type import OrderType, DirectionType, OperationType, Order, Quote, Trade
import logging
logger = logging.getLogger()
handler = logging.FileHandler('./ClientLogFile.log')
logging.basicConfig(level=logging.DEBUG)
formatter = logging.Formatter('%(asctime)s  %(name)s  %(levelname)s: %(message)s')
logger.addHandler(handler)
handler.setFormatter(formatter)
import datetime
import contextlib
from functools import partial
import psutil
import pysnooper
import gc
@contextlib.contextmanager
def record_time():
    try:
        start_time = datetime.datetime.now()
        logger.info('start: {}'.format(start_time))
        yield
    finally:
        logger.info('this code text need time: {}'.format(datetime.datetime.now() - start_time))


def read_binary_order_temp_file(data_file_path):
    struct_fmt = '=iiidii' # 
    struct_len = struct.calcsize(struct_fmt)
    struct_unpack = struct.Struct(struct_fmt).unpack_from
    results = []
    with open(data_file_path, "rb") as f:
        while True:
            data = f.read(struct_len)
            if not data: break
            s = struct_unpack(data)
            results.append(Order(s[0], s[1], DirectionType(s[2]), s[3], s[4], OrderType(s[5])))
    return results

class data_read:
    def __init__(self, data_file_path, client_id):

        self.trade_list = [[]] * 10
        # client_id used to identify different client server
        self.client_id = client_id
        self.all_page = []
        self.data_file_path = data_file_path

        
    # process all data, alter that then trans these data

    def data_read_mp(self, curr_stock_id):
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
        #logger.info("读文件进程的内存使用：" , psutil.Process(os.getpid()).memory_info().rss)
        #logger.info("读文件进程的内存使用：%.4f GB" % (psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024 / 1024) )

        data_page_number = order_id_mtx.shape[0]
        data_row_number = order_id_mtx.shape[1]
        data_column_number = order_id_mtx.shape[2]        
        per_stock_page_number = data_page_number // 10
        logger.info("page number is %d" % data_page_number)
        logger.info("data row number is%d" % data_row_number)
        logger.info("data column number is %d" % data_column_number)
        logger.info("per stock has %d page" % per_stock_page_number)
        #data transform
        #this implementation only works for small data(100x10x10 0.06 per stock 100x100x100 35s per stock, 100x1000x1000 1240s per stock, it's unaccecptable)
        logger.info("begin to process data")
        #print(curr_stock_id)
        logger.info("proceesing stock %d" % (curr_stock_id + 1))
        indexes = [i * 10 + curr_stock_id for i in range(0, per_stock_page_number)]
        curr_order_id_page = order_id_mtx[indexes,].reshape(-1).astype(np.int32)
        curr_direction_page = direction_mtx[indexes,].reshape(-1).astype(np.int32)
        curr_price_page = price_mtx[indexes,].reshape(-1).astype(np.int32)
        curr_volumn_page = volume_mtx[indexes,].reshape(-1).astype(np.int32)
        curr_type_page = type_mtx[indexes,].reshape(-1).astype(np.int32)
        curr_order_page = np.transpose([curr_order_id_page, curr_direction_page, curr_price_page, curr_volumn_page, curr_type_page])
        del curr_order_id_page
        del curr_direction_page
        del curr_price_page
        del curr_volumn_page
        del curr_type_page
        gc.collect()
        logger.info('排序前的内存使用：%.4f GB' % (psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024 / 1024) )
        curr_order_page = curr_order_page[curr_order_page[:, 0].argsort()] 
        #self.all_page.append(curr_order_page)
        logger.info('排序后的内存使用：%.4f GB' % (psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024 / 1024) )

        #temp_file_path = self.data_file_path + '/team-3/' + 'temp' + str(curr_stock_id + 1)
        
        logger.info(str(os.getpid())+'to list前的内存使用：%.4f GB' % (psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024 / 1024) )
        #res = curr_order_page.tolist()
        logger.info('to_list后的内存使用：%.4f GB' % (psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024 / 1024) )

        return (curr_stock_id, curr_order_page)
    
def print_error(value):
    logger.info("Error reason: ", value)

def write_data2file(args):
    curr_stock_id = args[0]
    curr_order_page = args[1]
    temp_file_path = '/data/team-3/' + 'temp' + str(curr_stock_id + 1)
    with open(temp_file_path, 'wb') as f:
        f.write(b''.join(map(lambda x: struct.pack("=iiidii", int(curr_stock_id), int(x[0]), int(x[1]), x[2], int(x[3]), int(x[4])), curr_order_page)))
        f.close()
    logger.info(str(os.getpid())+ '写入的内存使用：%.4f GB' % (psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024 / 1024) )
    del curr_order_page

def make_batches(size, batch_size):
    nb_batch = int(np.ceil(size / float(batch_size)))
    return [(i * batch_size, min(size, (i + 1) * batch_size)) for i in range(0, nb_batch)]






class Client:
    """
    read order from file, send order to exchange, (receive result from  exchanger? is it essential?)
    """

    def __init__(self, client_id, data_file_path, res_file_path):

        self.trade_list = [[]] * 10
        # client_id used to identify different client server
        self.client_id = client_id
        #self.all_page = []
        self.data_file_path = data_file_path
        self.res_file_path = res_file_path
        self.hook_mtx = h5py.File(data_file_path + '/' + "hook.h5", 'r')['hook']
        self.hook_position = [0] * 10
        
    # process all data, alter that then trans these data
    '''
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
        logger.info("page number is %d" % data_page_number)
        logger.info("data row number is%d" % data_row_number)
        logger.info("data column number is %d" % data_column_number)
        logger.info("per stock has %d page" % per_stock_page_number)
        #data transform
        #this implementation only works for small data(100x10x10 0.06 per stock 100x100x100 35s per stock, 100x1000x1000 1240s per stock, it's unaccecptable)
        logger.info("begin to process data")
        for curr_stock_id in range(10):
            #print(curr_stock_id)
            logger.info("proceesing stock %d" % (curr_stock_id + 1))
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
            #self.all_page.append(curr_order_page)
            #temp_file_path = self.data_file_path + '/' + 'temp' + str(curr_stock_id + 1)
            temp_file_path = '/data/team-3/' + 'temp' + str(curr_stock_id + 1)
            with open(temp_file_path, 'wb') as f:
                f.write(b''.join(map(lambda x: struct.pack("=iiidii", int(curr_stock_id + 1), int(x[0]), int(x[1]), x[2], int(x[3]), int(x[4])),curr_order_page)))
            # asynchronous send data
            #await self.communicate_with_server(curr_order_page, hook_mtx, curr_stock_id, res_file_path)
    '''
    #async def communicate_with_server(self, send_queue, receive_queue):
        """
        communicate all data with server
        why use async not multiprocess
        """
        
       
             
        
    async def put_single_stock_to_server(self, stock_id, send_queue):
        """
        put data in a queue
        """
        logger.info("start put orderid of stock %d in queue" % (stock_id + 1))
        temp_file_path = '/data/team-3/' + 'temp' + str(stock_id + 1)
        
        #temp_file_path = self.data_file_path + '/' + 'temp' + str(stock_id + 1)
        order_list = read_binary_order_temp_file(temp_file_path)
        for index in range(len(order_list)):
            order_id = order_list[index].order_id
            price = order_list[index].price
            direction = DirectionType(order_list[index].direction)
            volume = order_list[index].volume
            type = OrderType(order_list[stock_id].type) 
            if await self.order_is_need_to_tans(order_id, stock_id):              
                if index % 20 == 1:
                # a stock hook 1000 6 230 5
                    await asyncio.sleep(1)
                await send_queue.put(order_list[index])
                #
                # 
                
                
                logger.debug(order_list[index])
                logger.debug("put order_id %d of stock %d in send_queue(index is %d)" % (order_id, stock_id + 1, index))
                #!!!!! only for test
                #await send_queue.get()
                #await asyncio.sleep(1)
            
            else:             
                tempdata = Order(stock_id + 1, int(order_id), direction, 0, 0, type)
                send_queue.put(tempdata)
                logger.debug("put no nned to use order_id %d of stock %d in send_queue" % (order_id, stock_id))
                #!!!!! only for test
                #await send_queue.get()
                #await asyncio.sleep(1)
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
                    logger.debug("corresponding stock %d 's tradelist is not enough when stock %d order_id %d inquire hook" % ( target_stk_code,stock_id, order_id))
                    logger.debug("current stock %d 's trade_list length is %d" % (target_stk_code, len(self.trade_list[stock_id])))
                    await asyncio.sleep(1)
                else:
                    if self.trade_list[target_stk_code][target_trade_idx - 1] < arg:
                        self.hook_position[stock_id] += 1
                        return True
                    else:
                        self.hook_position[stock_id] += 1
                        return False

            # if self.trade_list[target_stk_code][target_trade_idx - 1] < arg:
            #     self.hook_position[stock_id] += 1
            #     return True
            # else:
            #     self.hook_position[stock_id] += 1
            #     return False
        else:
            #if order id is bigger than the current hook order_id, we need to add hook position to make it <= hook order id
            while(self.hook_mtx[stock_id][self.hook_position[stock_id]][0] < order_id):
                logger.debug("order_id %d of stock %d is larger than corresponding hook position %d" %(order_id, stock_id, self.hook_mtx[stock_id][self.hook_position[stock_id]][0]))
                self.hook_position[stock_id] += 1
            if order_id == self.hook_mtx[stock_id][self.hook_position[stock_id]][0]:
                target_stk_code = self.hook_mtx[stock_id][self.hook_position[stock_id]][1]
                target_trade_idx = self.hook_mtx[stock_id][self.hook_position[stock_id]][2]
                arg = self.hook_mtx[stock_id][self.hook_position[stock_id]][3]
                while True:
                    if len(self.trade_list[stock_id]) < target_trade_idx:
                        logger.debug("corresponding stock %d 's tradelist is not enough when stock %d order_id %d inquire hook" %(target_stk_code, stock_id, order_id))
                        logger.debug("current stock %d 's trade_list length is %d" % (target_stk_code, len(self.trade_list[stock_id])))
                        await asyncio.sleep(1)
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
    async def communicate_to_server(self, send_queue, receive_queue):
        #loop = asyncio.get_event_loop()
        Client_run = ClientTCP(receive_queue, send_queue)
        stock_1_task = asyncio.create_task(
            self.put_single_stock_to_server(0, send_queue))
        stock_2_task = asyncio.create_task(
            self.put_single_stock_to_server(1, send_queue))
        stock_3_task = asyncio.create_task(
            self.put_single_stock_to_server(2, send_queue))
        stock_4_task = asyncio.create_task(
            self.put_single_stock_to_server(3, send_queue))        
        stock_5_task = asyncio.create_task(
            self.put_single_stock_to_server(4, send_queue))
        stock_6_task = asyncio.create_task(
            self.put_single_stock_to_server(5, send_queue))
        stock_7_task = asyncio.create_task(
            self.put_single_stock_to_server(6, send_queue))
        stock_8_task = asyncio.create_task(
            self.put_single_stock_to_server(7, send_queue))
        stock_9_task = asyncio.create_task(
            self.put_single_stock_to_server(8, send_queue))
        stock_10_task = asyncio.create_task(
            self.put_single_stock_to_server(9, send_queue))
        receive_task = asyncio.create_task(
            self.read_trade_data_from_queue(receive_queue))
        communicate_task = asyncio.create_task(
            Client_run.run_main())
        ret = await asyncio.gather(stock_1_task, stock_2_task, stock_3_task, stock_4_task, stock_5_task, stock_6_task, stock_7_task, stock_8_task, stock_9_task, stock_10_task, receive_task, communicate_task)       
        logger.info("in the communicate server", send_queue)
        
        #loop.run_until_complete(Client_run.run_main())
        #loop.close()
        
    async def read_trade_data_from_queue(self, receive_queue):
        #read data from trade data
        while True:
            #!!!!! only for test
            #await receive_queue.put(Trade(1, 1, 1, 1, 1))
            #await asyncio.sleep(1)
            if receive_queue.empty():
                await asyncio.sleep(1)
            else:
                trade_item = receive_queue.get()
        
                        #self.trade_list[trade_item.stock_id].append(trade_item)
                stock_id = trade_item.stk_code
                volume = trade_item.volume 
                logger.info("get trade result of stock %d while volume is %d" % (stock_id, trade_item))
                self.trade_list[stock_id].append(volume)
                res_path = self.res_file_path + '/' + 'trade' + str(stock_id)
                with open(res_path, 'wb') as f:
                    f.write(b''.join(trade_item.to_bytes()))
            #!!!!!! just for test!!!!
            

    # def store_all_trade(self, stock_id):
    #     res_file_path = self.res_file_path + '/' + 'trade' + str(stock_id)
    #     with open(res_file_path, 'wb') as f:
    #         f.write(b''.join(map(lambda x: x.to_bytes(), self.trade_list[stock_id])))
async run

if __name__ == "__main__":
    # input list
    parser = ArgumentParser()
    parser.add_argument("-f", "--filepath",  help="data file folder path")
    parser.add_argument("-r", "--respath",  help="result folder path")
    parser.add_argument("-c", "--client_id",  help="client_id, which is 1 or 2")
    args = parser.parse_args()    
    logger.info("===============begin to read data==============")
    send_queue = asyncio.Queue()
    receive_queue = asyncio.Queue()
    Trade_Server = Client(int(args.client_id), args.filepath, args.respath)
    data_file_path = args.filepath
    with record_time():
        order_data = data_read(data_file_path, 1)
        batch_size = 4
        query_list = make_batches(10,batch_size)
        # order_data.data_read()
        # order_id_mtx,direction_mtx, price_mtx, volume_mtx, type_mtx, per_stock_page_number = order_data.data_read()
        # final_func = partial(mpread,order_id_mtx=order_id_mtx,direction_mtx=direction_mtx, price_mtx=price_mtx, volume_mtx=volume_mtx, type_mtx=type_mtx, per_stock_page_number=per_stock_page_number)
        # order_data.data_read_mp(0)
        for start, end in query_list:
            pool = multiprocessing.Pool(batch_size)
            for curr_stock_id in range(start,end):
                pool.apply_async(order_data.data_read_mp, args=(curr_stock_id, ),callback=write_data2file, error_callback=print_error)
            pool.close()
            pool.join()
    #Trade_Server.data_read()
    logger.info("begin to use asyncio")
    #asyncio.get_event_loop().run_until_complete(Trade_Server.communicate_with_server(send_queue, receive_queue))
    asyncio.run(Trade_Server.communicate_to_server(send_queue, receive_queue))
    #loop = asyncio.get_event_loop()
    #Client_run = ClientTCP(order_queue, response_queue)
    #loop.run_until_complete(Trade_Server.communicate_with_server(send_queue, receive_queue))
    #loop.close()
#todo暂时把接受数据与写文件解耦，后续tcp部分完成后和tcp部分写到一起
    #for i in range(10):
    #   Trader_Server.store_all_trade(i + 1)
