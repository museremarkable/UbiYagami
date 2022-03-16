import asyncio
import time
from wirte_logger import get_logger
from data_trans import convert_msg2obj, convert_obj2msg
import socket
from asyncio import StreamWriter, StreamReader
class TCPServer():
    def __init__(self, order_queue, response_queue):
        self.order_queue = order_queue
        self.response_queue = response_queue

    async def handle_echo(self, reader, writer):

        data = await reader.readline()
        message = data.decode()
        addr = writer.get_extra_info('peername')
        print(f"Received {message!r} from {addr!r}")
        # print(f"Send: {message!r}")
        # writer.write(self.count_msg(data))
        # await writer.drain()
        asyncio.create_task(self._listen_for_stream(reader, writer))
        asyncio.create_task(self._write_for_stream(writer))

        #解决了IO多路复用问题
        # while (data := await asyncio.wait_for(reader.readline(), 60) != b''):
        #     print(data)
        #     writer.write(str(data).encode())
        #     await writer.drain()
        # while True:
        #     data = await asyncio.wait_for(reader.readline(), 60)
        #     if data == b'':
        #         break
        #     print(data)
        #     writer.write(str(data).encode())
        #     await writer.drain()
        # print("Close the connection")
        # writer.close()
    def count_msg(self,msg):
        return str(len(msg)).encode()+b'-'+msg

    async def _write_for_stream(self, writer: StreamWriter):
        while True:
            if self.response_queue.empty():
                await asyncio.sleep(0.1)
            else:
                data = self.response_queue.get()
                #msg = convert_obj2msg(data)
                msg = b' test'
                if not msg.endswith(b'\n'):
                    msg = msg + b'\n'
                writer.write(msg)
                await writer.drain()
                await asyncio.sleep(1)
        print("Close the connection")
        writer.close()

    async def _listen_for_stream(self, reader: StreamReader, writer: StreamWriter):
        while True:
            data = await asyncio.wait_for(reader.readline(), 60)
            if data.startswith(b'CONNECT'):
                print(data)
            else:
                print(data)
                data = convert_msg2obj(data)
                self.order_queue.put(data)
        print("Close the connection")
        writer.close()

    async def server_content(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        host = s.getsockname()[0]
        s.close()
        host = host  # '106.15.11.226'
        port = 12345
        server = await asyncio.start_server(
            self.handle_echo, host, port)

        addr = server.sockets[0].getsockname()
        print(f'Serving on {addr}')

        async with server:
            await server.serve_forever()

async def async_get_queue(queue):
    return queue.get()

def server(order_queue, response_queue):
    tcp = TCPServer(order_queue, response_queue)
    asyncio.run(tcp.server_content())
