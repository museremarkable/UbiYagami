import asyncio
import time
async def tcp_echo_client(message):
    reader, writer = await asyncio.open_connection(
        '127.0.0.1', 10048)

    # reader, writer = await asyncio.open_connection(
    #     '10.216.68.189', 8888)
    print(f'Send: {message!r}'+'\n')
    writer.write(message.encode())
    await writer.drain()
    # writer会传回给server
    data = await reader.readline()
    print(f'Received: {data.decode()!r}')
    while True:
        time.sleep(2)
        tem = str(time.time())+'_1\n'
        print(f'Send: {tem!r}')
        writer.write(tem.encode())
        await writer.drain()
        data = await reader.readline()
        print(f'Received: {data.decode()!r}')
        # if int(time.time())%8 == 0:
        #     break
    print('Close the connection')
    writer.close()
    await writer.wait_closed()

asyncio.run(tcp_echo_client('Hello World!\n'))