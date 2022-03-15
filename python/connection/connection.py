import asyncio
from asyncio import StreamWriter, StreamReader
from python.utils.wirte_logger import get_logger
from python.connection.pollable_queue import PollableQueue
from queue import Queue
from enum import IntEnum
import json
import socket


class Operation(IntEnum):
    HEARTBEAT = 0
    RAW_ORDER = 1
    RAW_ORDER_RESPONSE = 2
    TRADE_ORDER = 3
    TRADE_ORDER_RESPONSE = 4


class ServerTCP:
    def __init__(self,order_queue, response_queue):
        self.trader2writer = {}
        self.binding_ports = [100, 101, 102]
        self.ports_status = [0, 0, 0]
        self.order_queue = order_queue
        self.response_queue = response_queue
        self.log = get_logger(__name__, filename='streaming_server')

    async def server_connection(self, host: str, port: int):
        "receive order from client , send result to two client"
        server = await asyncio.start_server(self.client_connected, host, port)
        async with server:
            await server.serve_forever()

    async def client_connected(self, reader: StreamReader, writer: StreamWriter):
        '''
        wait client to give valid info, otherwise, disconnect them.
        :param reader:
        :param writer:
        :return:
        '''
        msg = await reader.readline()
        # todo: read n bytes
        operation, args = msg.split(b'-')
        operation = int(operation.decode())
        addr = writer.get_extra_info('peername')
        self._add_trade(addr, reader, writer)
        # if operation == Operation.HEARTBEAT:
        #     if addr not in self.trader2writer.keys():
        #         self._add_trade(addr, reader, writer)
        #     # todo:mark一下自己的名字
        #     # todo: 这里只建立连接，别的都留给exchange做
        #     writer.write(str(Operation.HEARTBEAT).encode())
        #     await writer.drain()
        # elif operation == Operation.RAW_ORDER:
        #     order = json.loads(args)
        #     self.order_queue.put(order)
        #
        #     writer.write(order['count'])
        #     await writer.drain()
        #     self.log.warn(f"Received msg from {addr!r}")
        #     # todo: wait_response
        # elif operation == Operation.TRADE_ORDER_RESPONSE:
        #     pass
        # #     # todo: 返回对应的序号
        # # todo: 如果考虑断连，后面可以通过加response的方式进行测试
        # #     pass
        # #     self.response_queue.put(b'SUCC'+'-')
        # else:
        #     self.log.error('Got invalid command from client, disconnecting.')
        #     writer.close()
        #     await writer.wait_closed()

    def _add_trade(self, trad_add, reader: StreamReader, writer: StreamWriter):
        self.trader2writer[trad_add] = writer
        asyncio.create_task(self._listen_for_stream(trad_add, reader, writer))

    async def _del_trade(self, trad_add):
        writer = self.trader2writer[trad_add]
        del self.trader2writer[trad_add]
        try:
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            self.log.error('Error closing client writer, ignoring.')

    async def _listen_for_stream(self, trad_add, reader: StreamReader, writer: StreamWriter):
        try:
            while True:
                data = await asyncio.wait_for(reader.readline(), 60)
                if data == b'':
                    break
                self.trans_stream2exchange(trad_add, data)
                writer.write(str(data).encode())
                await writer.drain()
            # while(data := await asyncio.wait_for(reader.readline(),60)!=b''):
            #     self.trans_stream2exchange(data)
        except Exception as e:
            self.log.error('Error reading from client.')


    def trans_stream2exchange(self,trad_add, msg):
        '''
        give stream to exchange.
        :return:
        # todo: 写到queue里， put之后就返给feedback
        '''
        operation, args = msg.split(b'-')
        operation = int(operation.decode())
        if operation == Operation.HEARTBEAT:
            pass
        elif operation == Operation.RAW_ORDER:
            order = json.loads(args)
            self.order_queue.put(order)
            self._notify_all(str(Operation.RAW_ORDER_RESPONSE)+'-'+order['count'])
            # todo: wait_response
        elif operation == Operation.TRADE_ORDER_RESPONSE:
            # todo: 返回对应的序号
            pass
        # todo: 如果考虑断连，后面可以通过加response的方式进行测试
        #     pass
        #     self.response_queue.put(b'SUCC'+'-')
        else:
            self.log.error('Got invalid command from client, disconnecting.')
            self._del_trade(trad_add)
        # self.order_queue.put(json.loads(msg))
        # self._send_response(b'RESPONSE'+msg)
        #收到信息

    def send_trade(self):
        while True:
            data = self.response_queue.get()
            if data:
                msg = str(Operation.TRADE_ORDER).encode()+data.encode()
                self._notify_all(msg)
            else:
                break

    async def _notify_all(self, msg):
        # todo: response queue
        # 广播
        inactive_trade = []
        for addr, writer in self.trader2writer.items():
            try:
                writer.write(msg.decode())
                await writer.drain()
            except ConnectionError as e:
                self.log.exception('Could not write to client.', exc_info=e)
                inactive_trade.append(addr)
                [await self._del_trade(username) for username in inactive_trade]


async def main():
    order_queue = PollableQueue()
    response_queue = PollableQueue()
    ServerTCP(order_queue, response_queue)


asyncio.run(main())




