import sys
sys.path.append("..")
sys.path.append("../utils")
# from connection.connection import server
from simple_server_test import server
from server import MatchingEngine
from multiprocessing import Queue, Process
from connection.connect_wrapper import connect
# from connection.connection import ServerTCP
from connection.connect_wrapper import connect

# path = os.path.join(os.path.dirname(__file__), os.pardir)
# sys.path.append(path)

if __name__ == "__main__":

	trade_file = "trade_result"
	close_file = "../../data/100x10x10/price1.h5"
	data_path = "../../data/100x10x10"
	host = '106.15.11.226'
	port = 12345

	recv_queue, send_queue = Queue(), Queue()
	# server = ServerTCP(recv_queue, send_queue, host, port)
	connect_kernel = connect(recv_queue=recv_queue, send_queue=send_queue)
	engine = MatchingEngine(connect=connect_kernel, path_close=close_file)

	process_list = []
	p = Process(target=engine.serialize_main_run, args=())
	process_list.append(p)
	p.start()
	print('Add Process server TCP')
	p = Process(target=server, args=(recv_queue, send_queue, ))#host, port
	process_list.append(p)
	p.start()

	for p in process_list:
		p.join()
