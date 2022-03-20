import asyncio
import time
from asyncio import StreamWriter, StreamReader
async def handle_echo(reader, writer):
    data = await reader.readline()
    message = data.decode()
    addr = writer.get_extra_info('peername')
    print(f"Received {message!r} from {addr!r}")
    print(f"Send: {message!r}")
    writer.write(count_msg(data))
    await writer.drain()
    asyncio.create_task(_listen_for_stream(reader, writer))
    asyncio.create_task(_write_for_stream(writer))

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
def count_msg(msg):
    return str(len(msg)).encode()+b'-'+msg

async def _write_for_stream(writer: StreamWriter):
    while True:
        writer.write(str('test'+'\n').encode())
        print('send_test')
        await writer.drain()
        await asyncio.sleep(1)
    print("Close the connection")
    writer.close()

async def _listen_for_stream(reader: StreamReader, writer: StreamWriter):
    while True:
        data = await asyncio.wait_for(reader.readline(), 60)
        if data == b'':
            break
        print(data)
        writer.write(str(data).encode())
        await writer.drain()
        await asyncio.sleep(0)
    print("Close the connection")
    writer.close()


async def check_change_port(start, host, port, forever_task):
    while True:
        # 必须的
        if time.time() - start >= 30:
            with open('server_ip_config.txt', 'r') as f:
                new_host, new_port = f.readlines()
            new_port = int(new_port)
            if port != new_port:
                # print('nothing happend')
                forever_task.cancel()
                print('cancel')
                return None
        await asyncio.sleep(1)


async def main():
    print('begin')
    while True:
        with open('server_ip_config.txt', 'r') as f:
            host, port = f.readlines()
        start = time.time()
        port = int(port)
        print(host)
        print(host == '127.0.0.1')
        server = await asyncio.start_server(
            handle_echo, '172.30.240.1', port)
        addr = server.sockets[0].getsockname()
        print(f'Serving on {addr}')
        async with server:
    #     await server.serve_forever()
            forever_task = asyncio.create_task(server.serve_forever())
            asyncio.create_task(check_change_port(start, host, port, forever_task))
            try:
                await forever_task
            except asyncio.CancelledError:
                print("game server exit...")
        await asyncio.sleep(0)

asyncio.run(main())
