import queue
import socket
import asyncio

class PollableQueue(queue.Queue):
    def __init__(self, maxsize=0):
        super().__init__(maxsize)
        # don't need to consider sort in single machine.
        # 278 bytes limit on linux
        # self._putsocket, self._getsocket = socket.socketpair()

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('127.0.0.1', 0))
        server.listen(1)
        self._putsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._putsocket.connect(server.getsockname())
        self._getsocket, _ = server.accept()
        server.close()

    def fileno(self):
        return self._getsocket.fileno()

    def put(self, item):
        super().put(item)
        self._putsocket.send(b'x')

    def get(self):
        self._getsocket.recv(1)
        return super().get()