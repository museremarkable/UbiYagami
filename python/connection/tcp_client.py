import sys 
sys.path.append("")
import asyncio
from asyncio import StreamWriter, StreamReader
from utils.wirte_logger import get_logger
from utils.data_trans import convert_msg2obj, convert_obj2msg
from queue import Queue
import json
import socket

class ClientTCP:
    def __init__(self, order_queue, response_queue):
        #todo: queue让外面传进来
        self.ip_address = ["10.216.68.191", '10.216.68.192']
        self.alive = {}
        self.exchange2writer = {}
        self.binding_port = 62345
        "0 is normal, differnet number corresponding different stastus"
        self.ports_status = [0, 0, 0]
        self.log = get_logger(__name__, filename='streaming_client')
        self.count = 0
        self.order_queue = order_queue
        self.response_queue = response_queue

    async def send_message(self, host, writer: StreamWriter):
        '''send info to server'''
        message = self.response_queue.get()
        if type(message)!=bytes and type(message)!=str:
            message = convert_obj2msg(message)
            #json.dumps(message.__dict__).encode()
        while message!=b'' and message!='':
            if type(message) != bytes:
                message = message.encode()
            if not message.endswith(b'\n'):
                message = message + b'\n'
            await self._notify_all(message)
            # writer.write(message)
            # await writer.drain()

            message = self.response_queue.get()
            if type(message) != bytes and type(message)!=str:
                message = convert_obj2msg(message)
            await asyncio.sleep(0.015)
        self.log.info('While statement is skipped')
        # del self.alive[host]
        # writer.close()

    async def listen_for_messages(self, host, reader: StreamReader):
        self.log.info('listern stream begin')
        while True:
            data = await asyncio.wait_for(reader.readline(), 60)
            if data != b'\n' and data != b'':
                self.log.info('Recieved {}'.format(data))
                data = convert_msg2obj(data)
                self.order_queue.put(data)
                await asyncio.sleep(0.01)
            else:
                # del self.alive[host]
                #break
                await asyncio.sleep(0.05)
        print('Server closed connection.')

    async def client_connection(self, host, port):
        self.log.info('Connection begin')
        reader, writer = await asyncio.open_connection(host, port)
        self.exchange2writer[host] = writer
        writer.write(f'CONNECT-{port}\n'.encode())
        await writer.drain()
        asyncio.create_task(self.send_message(host, writer))
        asyncio.create_task(self.listen_for_messages(host, reader))

        # return reader, writer

    async def _notify_all(self, msg):
        # todo: response queue
        # 广播
        inactive_trade = []
        for addr, writer in self.exchange2writer.items():
            try:
                if type(msg) == bytes:
                    writer.write(msg)
                else:
                    writer.write(msg.encode())
                await writer.drain()
            except ConnectionError as e:
                self.log.exception('Could not write to client.', exc_info=e)
                inactive_trade.append(addr)
                [await self._del_exchange(username) for username in inactive_trade]
        self.log.info('Send message {}'.format(msg))
        await asyncio.sleep(0.05)

    async def _del_exchange(self, trad_add):
        try:
            writer = self.exchange2writer[trad_add]
            del self.exchange2writer[trad_add]
            writer.close()
            await writer.wait_closed()
            self.log.info(f'Delete trade{trad_add}')
        except Exception as e:
            self.log.error('Error closing client writer, ignoring.')

    async def reconnection(self, host, port):
        while True:
            if host not in self.exchange2writer.keys():
                try:
                    await self.client_connection(host, port)
                    self.log.info('Connecting to server {}:{}'.format(host, port))
                except ConnectionRefusedError:
                    self.log.error('Connection to server {}:{} failed!'.format(host, port))
                except asyncio.TimeoutError:
                    self.log.error('Connection to server {}:{} timed out!'.format(host, port))
                else:
                    self.log.error('Connection to server {}:{} is closed.'.format(host, port))
            await asyncio.sleep(2)

    async def run_main(self):
        #for ip in self.ip_address:
        #await self.client_connection('127.0.0.1', 8888)
        coros = [self.reconnection(host, self.binding_port) for host in self.ip_address]
        await asyncio.gather(*coros)

    # async def run_without_retry(self):
    #     #await self.client_connection('127.0.0.1', 8000)
    #     reader, writer = await asyncio.open_connection('127.0.0.1', 8000)
    #     # # self.alive[host] = True
    #     writer.write(f'CONNECT {8000}\n'.encode())
    #     await writer.drain()

    #     asyncio.create_task(self.send_message('127.0.0.1', writer))
    #     asyncio.create_task(self.listen_for_messages('127.0.0.1', reader))


def run_client(order_queue, response_queue):
    # order_queue = Queue()
    # response_queue = Queue()
    # count = 100
    # while count <= 120:
    #     count += 1
    #     order_queue.put(str(count)+'\n')
    #     response_queue.put(str(count)+'\n')
    # Client_run = ClientTCP(order_queue, response_queue)
    # asyncio.get_event_loop().run_until_complete(Client_run.run_without_retry())
    loop = asyncio.get_event_loop()
    Client_run = ClientTCP(order_queue, response_queue)
    loop.run_until_complete(Client_run.run_main())
    loop.close()