from multiprocessing import Queue, Process
from client_multiprocess_fortest import trader
from server import MatchingEngine
import sys
sys.path.append("..")

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



def exchange(recv_queue, send_queue):
	connect_kernel = connect(recv_queue=recv_queue, send_queue=send_queue)
	engine = MatchingEngine(connect=connect_kernel, path_close=close_file)
	engine.engine_main_thread(matching_threads=2)


if __name__ == "__main__":
	trade_path = "results/trader"
	close_file = "data_test/100x10x10/price1.h5"
	data_path1 = r"data_test_1/100x10x10"
	data_path2 = r"data_test_2/100x10x10"


	qo, qt, qq = Queue(), Queue(), Queue()

	process_list = []
	p = Process(target=exchange, args=(qo, qt))
	p.start()
	process_list.append(p)
	process_list += trader(1, data_path1, trade_path+"1", qo, qt)
	process_list += trader(2, data_path2, trade_path+"2", qo, qt)

	for p in process_list:
		p.join()
	

