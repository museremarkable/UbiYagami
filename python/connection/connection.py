import asyncio
from asyncio import StreamWriter, StreamReader
from wirte_logger import get_logger
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
    def __init__(self, order_queue, response_queue, host: str, port: int):
        self.trader2writer = {}
        self.host = host
        self.port = port
        # self.binding_ports = [100, 101, 102]
        # self.ports_status = [0, 0, 0]
        self.order_queue = order_queue
        self.response_queue = response_queue
        self.log = get_logger(__name__, filename='streaming_server')
        self.server_connection(self.host, self.port)

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
        # operation, args = msg.split(b'-')
        # operation = int(operation.decode())
        addr = writer.get_extra_info('peername')
        self._add_trade(addr, reader, writer)
        # if operation == Operation.HEARTBEAT:
        #     if addr not in self.trader2writer.keys():R
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
        asyncio.create_task(self._listen_for_stream(trad_add, reader))
        asyncio.create_task(self._write_for_stream(trad_add, writer))

    async def _del_trade(self, trad_add):
        # print('_del_trade is called')
        try:
            writer = self.trader2writer[trad_add]
            del self.trader2writer[trad_add]
            writer.close()
            await writer.wait_closed()
            self.log.info(f'Delete trade{trad_add}')
        except Exception as e:
            self.log.error('Error closing client writer, ignoring.')

    async def _write_for_stream(self, trad_add, writer: StreamWriter):
        while True:
            try:
                data = self.response_queue.get()
                data = data.encode()
                if data != b'\n' and data != b'':
                    await self._notify_all(data)
                #     writer.write(data.encode()+b'\n')
                #     print('Send {}'.format(data))
                # await writer.drain()
            except Exception as e:
                self.log.exception(e)
                # await self._del_trade(trad_add)
                await asyncio.sleep(1)


    async def _listen_for_stream(self, trad_add, reader: StreamReader):#, writer: StreamWriter):
        try:
            while True:
                data = await asyncio.wait_for(reader.readline(), 60)
                print('received {}'.format(data))
                if data == b'\n' or data == b'':
                    #break
                    data = b'test'
                    await asyncio.sleep(1)
                self.trans_stream2exchange(trad_add, data)
                # writer.write(str(data).encode())
                # await writer.drain()
            # while(data := await asyncio.wait_for(reader.readline(),60)!=b''):
            #     self.trans_stream2exchange(data)
        except Exception as e:
            self.log.error('Error reading from client.')
            self.log.exception(e)
            await self._del_trade(trad_add)


    def trans_stream2exchange(self,trad_add, msg):
        '''
        give stream to exchange.
        :return:
        # todo: 写到queue里， put之后就返给feedback
        '''
        #operation, args = msg.split(b'-')
        #operation = int(operation.decode())
        #print('receive{}'.format(msg))
        self.order_queue.put(msg)
        self.response_queue.put(msg)
        # if operation == Operation.HEARTBEAT:
        #     pass
        # elif operation == Operation.RAW_ORDER:
        #     order = json.loads(args)
        #     self.order_queue.put(order)
        #     self._notify_all(str(Operation.RAW_ORDER_RESPONSE)+'-'+order['count'])
        #     # todo: wait_response
        # elif operation == Operation.TRADE_ORDER_RESPONSE:
        #     # todo: 返回对应的序号
        #     pass
        # # todo: 如果考虑断连，后面可以通过加response的方式进行测试
        # #     pass
        # #     self.response_queue.put(b'SUCC'+'-')
        # else:
        #     self.log.error('Got invalid command from client, disconnecting.')
        #     self._del_trade(trad_add)
        # self.order_queue.put(json.loads(msg))
        # self._send_response(b'RESPONSE'+msg)
        #收到信息

    # def send_trade(self):
    #     while True:
    #         data = self.response_queue.get()
    #         if data:
    #             msg = str(Operation.TRADE_ORDER).encode()+data.encode()
    #             self._notify_all(msg)
    #         else:
    #             break

    async def _notify_all(self, msg):
        # todo: response queue
        # 广播
        inactive_trade = []
        for addr, writer in self.trader2writer.items():
            try:
                if type(msg) == bytes:
                    writer.write(msg)
                else:
                    writer.write(msg.encode())
                await writer.drain()
                await asyncio.sleep(1)
            except ConnectionError as e:
                self.log.exception('Could not write to client.', exc_info=e)
                inactive_trade.append(addr)
                [await self._del_trade(username) for username in inactive_trade]


async def run_server(order_queue, response_queue):
    # order_queue = Queue()
    # response_queue = Queue()
    # count = 0
    # while count <= 50:
    #     count += 1
    #     order_queue.put(str(count)+'\n')
    #     response_queue.put(str(count)+'\n')
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    host = s.getsockname()[0]
    s.close()
    host = host  # '106.15.11.226'
    port = 12345
    server = ServerTCP(order_queue, response_queue, host, port)
    await server.server_connection('127.0.0.1', 8000)


def server(order_queue, response_queue):
    asyncio.run(run_server(order_queue, response_queue))




