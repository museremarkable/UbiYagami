import asyncio
from asyncio import StreamWriter, StreamReader
from python.utils.wirte_logger import get_logger
from queue import Queue


class ServerTCP:
    def __init__(self):
        self.binding_ports = [100, 101, 102]
        self.order_queue = Queue()
        self.response_queue = Queue()
        self.log = get_logger(__name__, filename='streaming_server')

    async def server_connection(self, host:str, port:int):
        "receive order from client , send result to two client"
        server = await asyncio.start_server(self.client_connected, host, port)
        async with server:
            await server.serve_forever()

    async def client_connected(self, reader: StreamReader, writer:StreamWriter):
        '''
        todo: 传一堆还是传一个。
        wait client to give valid info, otherwise, disconnect them.
        :param reader:
        :param writer:
        :return:
        '''
        msg = await reader.read(2 << 1024)
        # todo: read n bytes
        operation, args = msg.split(b' ')
        # todo: delimeter
        if operation == b'HEARTBEAT':
            pass
        elif operation == b'INFO':
            # todo: unpack msg 2 order struct
            #
            pass
        else:
            self.log.error('Got invalid command from client, disconnecting.')
            writer.close()
            await writer.wait_closed()

    def trans_stream2exchange(self, reader: StreamReader, writer:StreamWriter):
        '''
        give stream to exchange.
        :param reader:
        :param writer:
        :return:
        # todo: 写到queue里， put之后就返给feedback
        '''
        asyncio.create_task()

    async  def _send_response(self):
        # todo: response queue
        # 广播
        pass

    async def _notify_all(self, msg: str):




class ClientTCP:
    def __init__(self):
        self.ip_address = ["",""]
        self.binding_ports = [100, 101, 102]
        "0 is normal, differnet number corresponding different stastus"
        self.ports_status = [0, 0, 0]
    def client_connection(self):
        "send order to two exchanger? "
        pass
