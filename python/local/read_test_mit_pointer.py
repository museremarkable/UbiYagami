import os
import itertools
import sys

from pexpect import EOF
from data_type import Order, Trade, OrderType
path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(path)
#from client.client import Client
import h5py
import asyncio
import numpy as np
import asyncio
import struct
import multiprocessing
import time
from argparse import ArgumentParser
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
        print('start: {}'.format(start_time))
        yield
    finally:
        print('this code text need time: {}'.format(datetime.datetime.now() - start_time))

from http import client
import logging
import h5py
import struct
logger = logging.getLogger()
handler = logging.FileHandler('./ClientLogFile.log')
logging.basicConfig(level=logging.DEBUG)
formatter = logging.Formatter('%(asctime)s  %(name)s  %(levelname)s: %(message)s')
logger.addHandler(handler)

def read_answer_from_file(data_file_path):
    struct_fmt = '=iiidi' #
    struct_len = struct.calcsize(struct_fmt)
    struct_unpack = struct.Struct(struct_fmt).unpack_from
    results = []
    with open(data_file_path, "rb") as f:
        while True:
            data = f.read(struct_len)
            if not data: break
            s = struct_unpack(data)
            results.append(s[4])
    return results


def read_binary_mit_pointer(data_file_path, start): #read 100 lines from starting point
    struct_fmt = '=iiidii' #
    struct_len = struct.calcsize(struct_fmt)
    struct_unpack = struct.Struct(struct_fmt).unpack_from
    results = []
    starting_byte = start * struct_len
    with open(data_file_path, "rb") as f:
        f.seek(starting_byte)
        for i in range(100):
            data = f.read(struct_len)
            if not data:
                break
            s = struct_unpack(data)
            results.append(Order(s[0] + 1, s[1], s[2], s[3], s[4], s[5]))
    return results

def read_binary_order_temp_file(data_file_path):
    struct_fmt = '=iiidii' #
    struct_len = struct.calcsize(struct_fmt)
    struct_unpack = struct.Struct(struct_fmt).unpack_from
    results = []

    with open(data_file_path, "rb") as f:
        while True:
            data = f.read(struct_len)
            if not data: 
                break
            s = struct_unpack(data)
            results.append(Order(s[0] + 1, s[1], s[2], s[3], s[4], s[5]))
    return results

def order_is_need_to_trans(order_id, stock_id, hook_mtx, hook_position, trade_lists,Order_Data):
    # 当该股票的order_id小于hook的值时，不需要判断，直接跳过
    if order_id < hook_mtx[stock_id][hook_position[stock_id]][0]:
        return False
    # 等于hook的order_id时，需要开始判断
    elif order_id == hook_mtx[stock_id][hook_position[stock_id]][0]:
        # logger.info("order_id %d of stock %d is hooked up" % (order_id, stock_id + 1))
        # logger.info("now target_stk_code %d 's tar_trade_idx is %d, while, tradelsits length is %d" % (target_stk_code, target_trade_idx, len(trade_lists[stock_id])))
        target_stk_code = hook_mtx[stock_id][hook_position[stock_id]][1]
        target_trade_idx = hook_mtx[stock_id][hook_position[stock_id]][2]
        arg = hook_mtx[stock_id][hook_position[stock_id]][3]
        if len(trade_lists[target_stk_code - 1]) < target_trade_idx:
            #logger.debug("corresponding stock %d 's tradelist is not enough when stock %d order_id %d inquire hook")
            # 跳过不管
            return True
        #此特殊id符合发送条件
        if trade_lists[target_stk_code - 1][target_trade_idx - 1] < arg:
            hook_position[stock_id] += 1
            logger.debug("put order %d of stock %d in queue" % (order_id, stock_id))
            #send_queue.put(Order_Data)
            print("put queue!!!")
            #发送后继续发送该股票
            return False
        #不符合发送条件
        else:
            #压0发送
            hook_position[stock_id] += 1
            print("noqueue")
            # send_queue.put(Order(Order_Data.str_code, Order_Data.order_id, Order_Data.direction, 0, 0, Order_Data.type))
            #继续发这个股票
            return False
    #order_id 大于hook
    else:
        #必须让hookposition比orderid大
        while(hook_mtx[stock_id][hook_position[stock_id]][0] < order_id):
            hook_position[stock_id] += 1
        #当移动使得order_id和hook中orderid相等
        if order_id == hook_mtx[stock_id][hook_position[stock_id]][0]:
            target_stk_code = hook_mtx[stock_id][hook_position[stock_id]][1]
            target_trade_idx = hook_mtx[stock_id][hook_position[stock_id]][2]
            arg = hook_mtx[stock_id][hook_position[stock_id]][3]
            while True:
                #开始判断
                if len(trade_lists[target_stk_code - 1]) < target_trade_idx:
                    #logger.debug("corresponding stock %d 's tradelist is not enough when stock %d order_id %d inquire hook" %(target_stk_code, stock_id, order_id))
                    #logger.debug("stock %d wait 1 seconds" % (stock_id))
                    return True
                #tradelist符合条件
                else:
                    break
            #符合发送条件
            if trade_lists[target_stk_code - 1][target_trade_idx - 1] < arg:
                hook_position[stock_id] += 1
                # send_queue.put(Order_Data)
                print("put queue")
                return False
            #不符合发送条件
            else:
                hook_position[stock_id] += 1
                # send_queue.put(Order(Order_Data.str_code, Order_Data.order_id, Order_Data.direction, 0, 0, Order_Data.type))
                print("put no queue")
                return False
        #order_id小于hookposition
        else:
            return True

@pysnooper.snoop(output="trans_loop.log")
def order_is_need_to_trans_watch(order_id, stock_id, hook_mtx, hook_position, trade_lists,Order_Data):
    # 当该股票的order_id小于hook的值时，不需要判断，直接跳过
    if order_id < hook_mtx[stock_id][hook_position[stock_id]][0]:
        return False
    # 等于hook的order_id时，需要开始判断
    elif order_id == hook_mtx[stock_id][hook_position[stock_id]][0]:
        logger.info("order_id %d of stock %d is hooked up" % (order_id, stock_id + 1))
        # logger.info("now target_stk_code %d 's tar_trade_idx is %d, while, tradelsits length is %d" % (target_stk_code, target_trade_idx, len(trade_lists[stock_id])))
        target_stk_code = hook_mtx[stock_id][hook_position[stock_id]][1]
        target_trade_idx = hook_mtx[stock_id][hook_position[stock_id]][2]
        arg = hook_mtx[stock_id][hook_position[stock_id]][3]
        if len(trade_lists[target_stk_code - 1]) < target_trade_idx:
            #logger.debug("corresponding stock %d 's tradelist is not enough when stock %d order_id %d inquire hook")
            # 跳过不管
            return True
        #此特殊id符合发送条件
        if trade_lists[target_stk_code - 1][target_trade_idx - 1] < arg:
            hook_position[stock_id] += 1
            logger.debug("put order %d of stock %d in queue" % (order_id, stock_id))
            #send_queue.put(Order_Data)
            print("put queue!!!")
            #发送后继续发送该股票
            return False
        #不符合发送条件
        else:
            #压0发送
            hook_position[stock_id] += 1
            print("noqueue")
            # send_queue.put(Order(Order_Data.str_code, Order_Data.order_id, Order_Data.direction, 0, 0, Order_Data.type))
            #继续发这个股票
            return False
    #order_id 大于hook
    else:
        #必须让hookposition比orderid大
        while(hook_mtx[stock_id][hook_position[stock_id]][0] < order_id):
            hook_position[stock_id] += 1
        #当移动使得order_id和hook中orderid相等
        if order_id == hook_mtx[stock_id][hook_position[stock_id]][0]:
            target_stk_code = hook_mtx[stock_id][hook_position[stock_id]][1]
            target_trade_idx = hook_mtx[stock_id][hook_position[stock_id]][2]
            arg = hook_mtx[stock_id][hook_position[stock_id]][3]
            while True:
                #开始判断
                if len(trade_lists[target_stk_code - 1]) < target_trade_idx:
                    #logger.debug("corresponding stock %d 's tradelist is not enough when stock %d order_id %d inquire hook" %(target_stk_code, stock_id, order_id))
                    #logger.debug("stock %d wait 1 seconds" % (stock_id))
                    return True
                #tradelist符合条件
                else:
                    break
            #符合发送条件
            if trade_lists[target_stk_code - 1][target_trade_idx - 1] < arg:
                hook_position[stock_id] += 1
                # send_queue.put(Order_Data)
                print("put queue")
                return False
            #不符合发送条件
            else:
                hook_position[stock_id] += 1
                # send_queue.put(Order(Order_Data.str_code, Order_Data.order_id, Order_Data.direction, 0, 0, Order_Data.type))
                print("put no queue")
                return False
        #order_id小于hookposition
        else:
            return True



def put_data_in_queue(hook_mtx, client_id, trade_lists):
    logger.info("COMMUNICATE PROCESS: CLIENT_ID %d " % (client_id))
    # append squares of mylist to queue
    '''
    for i in range(10):
        temp_file_path = data_file_path + '/' + 'temp' + str(i + 1)
        order_list = read_binary_order_temp_file(temp_file_path)
        for i in range(len(order_list)):
    '''
    #hook_mtx = h5py.File(data_file_path + '/' + "hook.h5", 'r')['hook']
    hook_position = [0] * 10
    order_list = []
    curr_order_position = [0] * 10
    #asyncio.run(put_in_queue(data_file_path, send_queue, hook_mtx, hook_position, trade_lists))
    stock_id = 0
    cnt = 0
   
    hook_current_positon = hook_mtx[:, 0, 0]
    hook_current_index = [0] * 10
    curr_order_position = [0] * 10
    while not np.all(np.array(curr_order_position) == -1):
        stock_id %= 10
        batch_size = 100
        temp_file_path = 'temp/' + 'temp' + str(stock_id + 1)
        
        stock_size = 1000000
        # order_list = read_binary_order_temp_file(temp_file_path)
        # print('当前进程的内存使用：',psutil.Process(os.getpid()).memory_info().rss)
        # print('当前进程的内存使用：%.4f GB' % (psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024 / 1024) )

        order_list = read_binary_mit_pointer(temp_file_path, curr_order_position[stock_id])
        if not order_list:
            curr_order_position[stock_id] = -1
            break

        order_vol = len(order_list)
        
        if(order_vol<100):
            stock_size = curr_order_position[stock_id]+len(order_list)
        #order list that only containes order[stock_id][cur:cur+100]
        last_order_position = curr_order_position[stock_id]

        while curr_order_position[stock_id] != -1 and last_order_position+batch_size > curr_order_position[stock_id]:
            order_id = order_list[curr_order_position[stock_id]%order_vol].order_id
            if order_id < hook_current_positon[stock_id]:
                #send_queue.put()
                curr_order_position[stock_id] += 1
            else:
               
                # 判断要不要继续,只管这一个订单
                if hook_current_index[stock_id] >= hook_mtx[stock_id].shape[0]:
                    curr_order_position[stock_id] += 1
                else:
                    hook_order = hook_mtx[stock_id, hook_current_index[stock_id]]
                    target_stk_code = hook_order[1]
                    target_trade_idx = hook_order[2]
                    arg = hook_order[3]
                    if len(trade_lists[target_stk_code - 1]) < target_trade_idx:
                        #不够，要等
                        break
                    else:
                        if trade_lists[target_stk_code - 1][target_trade_idx - 1] > arg:
                            #set order.volume=0
                            pass
                        hook_current_positon[stock_id] = hook_mtx[stock_id, hook_current_index[stock_id], 0]
                        hook_current_index[stock_id] += 1
                        curr_order_position[stock_id] += 1
            if curr_order_position[stock_id] >= stock_size:
                curr_order_position[stock_id] = -1
                break
        stock_id += 1
        if (order_id>5000):
            print(hook_current_positon)

            # 管了就会更新hook_current_positon, hook_current_index




# test_queue = multiprocessing.Queue()
# test_queue.put_nowait()
if __name__ == "__main__":
    #data_file_path = r'D:\HKU\UbiYagami\data_test\100x10x10'
    #with record_time():
    # first 5000 result has generated
    file_path = '100x10x10'
    trade_lists = []
    client_id = 0

    for i in range(10):
        temp_file_path = file_path + '/trade' + str(i + 1)
        trade_lists.append(read_answer_from_file(temp_file_path))
    hook_mtx = h5py.File('100x10x10\hook.h5', 'r')['hook']
    put_data_in_queue(hook_mtx, client_id, trade_lists)