from multiprocessing import Queue, Process
from server import MatchingEngine
from order_reader import DataReader
from utils import list_to_order
from unittest import mock
from time import sleep
from client_multiprocess_fortest import trader
import sys

class connect:
	def __init__(self, qo, qt, qq):
		self.read_queue = qo
		self.send_t_queue = qt
		self.send_q_queue = qq

	def recv_order(self):
		return self.read_queue.get()

	def send_feed(self, msg):
		trade = msg.get('trade')
		quote = msg.get('quote')
		if trade is not None:
			self.send_t_queue.put(trade)
		self.send_q_queue.put(quote)

if __name__ == "__main__":
	trade_path = "results/trader"
	close_file = "data_test/100x10x10/price1.h5"
	data_path1 = r"data_test_1/100x10x10"
	data_path2 = r"data_test_2/100x10x10"


	qo, qt, qq = Queue(), Queue(), Queue()
	connect_k = connect(qo, qt, qq)
	engine = MatchingEngine(connect_k, path_close=close_file)
	# engine.connect = connect_k

	process_list = []
	p = Process(target=engine.serialize_main_run)
	p.start()
	process_list.append(p)
	process_list += trader(1, data_path1, trade_path+"1", qo, qt)
	process_list += trader(2, data_path2, trade_path+"2", qo, qt)

	# sleep(10)

	# trades = []
	# i = 0
	# try:
	# 	while not qt.empty():
	# 		trade = qt.get()
	# 		print(f"Trade get {i}")
	# 		trades.append(trade)
	# 		i +=1
	# finally:
	# 	f = open(trade_file, 'wb')
	# 	print("write file")
	# 	f.write(b''.join(map(lambda x: x.to_bytes(), trades)))
	# 	f.close()
	for p in process_list:
		p.join(100)

