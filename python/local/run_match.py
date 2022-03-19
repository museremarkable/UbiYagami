import sys
sys.path.append("..")
sys.path.append("../utils")
sys.path.append("python")
from server.server import MatchingEngine
from multiprocessing import Queue, Process
from connection.connect_wrapper import connect
from client_local import trader
import logging 

logging.basicConfig(level=logging.DEBUG #设置日志输出格式
                    ,filename="local_match_runtime.log" #log日志输出的文件位置和文件名
                    ,filemode="w" #文件的写入格式，w为重新写入文件，默认是追加
                    ,format="%(asctime)s - %(name)s - %(levelname)-9s - %(filename)-8s : %(lineno)s line - %(message)s" #日志输出的格式
                    # -8表示占位符，让输出左对齐，输出长度都为8位
                    ,datefmt="%Y-%m-%d %H:%M:%S" #时间输出的格式                
                    )

def exchange(recv_queue, send_queue, close_file):
	connect_kernel = connect(recv_queue=recv_queue, send_queue=send_queue)
	engine = MatchingEngine(connect=connect_kernel, path_close=close_file)
	engine.engine_main_thread(matching_threads=2)

def distribute_queue(q: Queue, qs: Queue):
	while True:
		obj = q.get()
		for qn in qs:
			qn.put(obj)


if __name__ == "__main__":
	close_file = "data_test/100x10x10/price1.h5"
	# close_file = "data_test/100x1000x1000/price1.h5"

	filepath = r"C:\Users\Leons\git\UbiYagami\data_test\100x10x10"
	# filepath = r"C:\Users\Leons\git\UbiYagami\data_test\100x1000x1000"
	respath = r"C:\Users\Leons\git\UbiYagami\results\trader"

	order_queue, main_feed_queue  = Queue(), Queue()
	feed_queues = []
	for i in range(2):
		feed_queue = Queue()
		feed_queues.append(feed_queue)
		
	process_list = []
	p = Process(target=exchange, args=(order_queue, main_feed_queue, close_file))
	process_list.append(p)
	p.start()

	client_id = 1
	p = Process(target=trader, args=(client_id, order_queue, feed_queues[client_id-1], filepath, respath+str(client_id)))
	process_list.append(p)
	p.start()

	client_id = 2
	p = Process(target=trader, args=(client_id, order_queue, feed_queues[client_id-1], filepath, respath+str(client_id)))
	process_list.append(p)
	p.start()

	
	p = Process(target=distribute_queue, args=(main_feed_queue, feed_queues))
	process_list.append(p)
	p.start()

	for p in process_list:
		p.join()
