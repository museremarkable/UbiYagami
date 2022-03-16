from multiprocessing import Queue, Process
from server import MatchingEngine
from order_reader import DataReader
from utils import list_to_order
from unittest import mock
from time import sleep

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
	trade_file = "python/server/trade2"
	close_file = "data_test/100x10x10/price1.h5"
	data_path = r"C:\Users\Leons\git\UbiYagami\data_test\100x10x10"


	trader1 = DataReader(1, data_file_path=data_path, res_file_path="")
	trader2 = DataReader(2, data_file_path=data_path, res_file_path="")
	trader1.data_read()
	trader2.data_read()

	stk1_1 = trader1.all_page[1]
	stk1_2 = trader2.all_page[1]

	orders = []
	for x,y in zip(stk1_1, stk1_2):
		orders += [list_to_order(2,x), list_to_order(2,y)]

	qo, qt, qq = Queue(), Queue(), Queue()
	connect_k = connect(qo, qt, qq)
	engine = MatchingEngine(connect_k, path_close=close_file)
	# engine.connect = connect_k


	p = Process(target=engine.serialize_main_run)
	p.start()

	for o in orders:
		qo.put(o)

	sleep(10)

	trades = []
	i = 0
	try:
		while not qt.empty():
			trade = qt.get()
			print(f"Trade get {i}")
			trades.append(trade)
			i +=1
	finally:
		f = open(trade_file, 'wb')
		print("write file")
		f.write(b''.join(map(lambda x: x.to_bytes(), trades)))
		f.close()

	p.join(100)


