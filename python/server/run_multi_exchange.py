
import sys

from numpy import mat
sys.path.append("..")
sys.path.append("../utils")
from connection.connection import server
# from simple_server_test import server
from server import MatchingEngine
from multiprocessing import Queue, Process
from connection.connect_wrapper import connect


def exchange(recv_queue, send_queue):
       connect_kernel = connect(recv_queue=recv_queue, send_queue=send_queue)
       engine = MatchingEngine(connect=connect_kernel, path_close=close_file)
       engine.engine_main_thread(matching_threads=2)


if __name__ == "__main__":

	close_file = "../../data/100x10x10/price1.h5"
	data_path = "../../data/100x10x10"

	recv_queue, send_queue = Queue(), Queue()
	# server = ServerTCP(recv_queue, send_queue, host, port)
	# connect_kernel = connect(recv_queue=recv_queue, send_queue=send_queue)
	# engine = MatchingEngine(connect=connect_kernel, path_close=close_file)

	process_list = []
	# p = Process(target=engine.serialize_main_run, args=())
	p = Process(target=exchange, args=(recv_queue, send_queue ))
	process_list.append(p)
	p.start()
	print('Add Process server TCP')
	p = Process(target=server, args=(recv_queue, send_queue, 62345))
	process_list.append(p)
	p.start()

	for p in process_list:
		p.join()
