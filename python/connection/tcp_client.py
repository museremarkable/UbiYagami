import sys 
sys.path.append("")
import asyncio
from asyncio import StreamWriter, StreamReader
from utils.wirte_logger import get_logger
from queue import Queue
import json
import socket

class ClientTCP:
    def __init__(self, order_queue, response_queue):
        #todo: queue让外面传进来
        self.ip_address = ["127.0.0.1"]
        self.alive = {}
        self.exchange2writer = {}
        self.binding_port = 8000
        "0 is normal, differnet number corresponding different stastus"
        self.ports_status = [0, 0, 0]
        self.log = get_logger(__name__, filename='streaming_client')
        self.count = 0
        self.order_queue = order_queue
        self.response_queue = response_queue

    async def send_message(self, host, writer: StreamWriter):
        '''send info to server'''
        message = self.response_queue.get()
        print('Send {}'.format(message))
        while message:
            writer.write((str(message).encode()) + b'\n')
            await writer.drain()
            message = self.response_queue.get()
            await asyncio.sleep(2)
        # del self.alive[host]
        # writer.close()

    async def listen_for_messages(self, host, reader: StreamReader):
        while True:
            data = await asyncio.wait_for(reader.readline(), 60)
            if data != b'\n' and data != b'':
                print('Recieved {}'.format(data))
                self.response_queue.put(data+b'res')
                await asyncio.sleep(1)
            else:
                # del self.alive[host]
                #break
                await asyncio.sleep(2)
        print('Server closed connection.')

    async def client_connection(self, host, port):
        print('prepare connection')
        reader, writer = await asyncio.open_connection(host, port)
        self.alive[host] = True
        writer.write(f'CONNECT {port}\n'.encode())
        await writer.drain()
        asyncio.create_task(self.send_message(host, writer))
        asyncio.create_task(self.listen_for_messages(host, reader))

        # return reader, writer

    async def reconnection(self, host, port):
        while True:

            if host not in self.alive.keys():
                self.log.info('Connecting to server {}:{}'.format(host, port))
                try:
                    await self.client_connection(host, port)
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

    async def run_without_retry(self):
        #await self.client_connection('127.0.0.1', 8000)
        reader, writer = await asyncio.open_connection('127.0.0.1', 8000)
        # # self.alive[host] = True
        writer.write(f'CONNECT {8000}\n'.encode())
        await writer.drain()

        asyncio.create_task(self.send_message('127.0.0.1', writer))
        asyncio.create_task(self.listen_for_messages('127.0.0.1', reader))


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