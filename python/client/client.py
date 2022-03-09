import imp
from python.connection.connection import ClientTCP
import h5py
from python.server.server import BuySide, OrderType
from python.server.server import Order
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