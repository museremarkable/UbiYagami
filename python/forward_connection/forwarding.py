#!/usr/bin/python3
# -*- coding: utf-8 -*-

import asyncio
import json
from argparse import ArgumentParser
# import hexdump
# import aiohttp_socks

class tcpproxy:
    def __init__(self, remote_ip, remote_port, socks5_url=None):
        self.__remote_ip = remote_ip
        self.__remote_port = remote_port

        self.__socks5_url = socks5_url

    async def __copy_data_thread(self, info, reader, writer):
        addr = writer.get_extra_info('peername')
        while True:
            chunk = await reader.readline()
            if not chunk:
                break
            print("{0}:{1}".format(info, addr))
            # hexdump.hexdump(chunk)
            writer.write(chunk)
            await writer.drain()

        print("close sock[{0}]:{1}".format(info, addr))
        writer.close()

    async def accept_handle(self, a_reader, a_writer):
        c_reader, c_writer = await asyncio.open_connection(
            host=self.__remote_ip,
            port=self.__remote_port
        )
        #         else:
        #             c_reader, c_writer = await aiohttp_socks.open_connection(
        #                 proxy_url = socks5_url,
        #                 host = self.__remote_ip,
        #                 port = self.__remote_port
        #                 )

        dltasks = set()
        dltasks.add(asyncio.ensure_future(self.__copy_data_thread('c->a', c_reader, a_writer)))
        dltasks.add(asyncio.ensure_future(self.__copy_data_thread('a->c', a_reader, c_writer)))
        dones, dltasks = await asyncio.wait(dltasks, return_when=asyncio.FIRST_COMPLETED)


def main(local_ip, local_port, remote_ip, remote_port, socks5_url=None):
    tp = tcpproxy(remote_ip, remote_port, socks5_url)

    loop = asyncio.get_event_loop()
    coro = asyncio.start_server(tp.accept_handle, local_ip, local_port, loop=loop)
    server = loop.run_until_complete(coro)

    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()


if __name__ == "__main__":
    # socks5_url = 'socks5://127.0.0.1:7000'
    with open('forward_config.txt', 'r') as f:
        config = eval(f.read())
    config['local_ip'] = '0.0.0.0'
    # parser = ArgumentParser()
    # parser.add_argument("-li", "--local_ip", help="local_ip")
    # parser.add_argument("-lp", "--respath", help="result folder path")
    # parser.add_argument("-ri", "--client_id", help="client_id, which is 1 or 2")
    # args = parser.parse_args()
    main(
        **config
        # socks5_url = 10049
    )
