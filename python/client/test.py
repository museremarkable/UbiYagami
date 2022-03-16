import h5py
import multiprocessing
import os
import logging

logger = logging.getLogger()
handler = logging.FileHandler('./TestLogFile.log')
logging.basicConfig(level=logging.DEBUG)
formatter = logging.Formatter('%(asctime)s  %(name)s  %(levelname)s: %(message)s')
logger.addHandler(handler)
handler.setFormatter(formatter)


def put_data_in_queue(order_id, trade_lists):
    
    while True:
        for i in range(10):
            trade_lists[i].append(123)
        
def communicate_with_server(order_id, trade_lists):
    
    while True:
        logger.info(trade_lists[0])

def write_results_to_file(order_id, trade_lists):

    while True:
        for i in range(10):
            trade_lists[i].append(321)
if __name__ == '__main__':
    manager = multiprocessing.Manager()
        # a simple implemment to achieve result
    #trade_lists = manager.list()\
    trade_lists = []
    for i in range(10):
        trade_lists.append(manager.list())

    process_put_data_in_queue = multiprocessing.Process(target=put_data_in_queue, args=(1, trade_lists),)
    process_communicate_with_server = multiprocessing.Process(target=communicate_with_server, args=(1, trade_lists),)
    process_write_result_to_file = multiprocessing.Process(target=write_results_to_file, args=(1, trade_lists),)

    process_put_data_in_queue.start()
    #process_put_data_in_queue.join()
    process_communicate_with_server.start()
    #process_communicate_with_server.join()
    process_write_result_to_file.start()
    #process_write_result_to_file.join()
    process_list = []
    process_list.append(process_put_data_in_queue)
    process_list.append(process_communicate_with_server)
    process_list.append(process_write_result_to_file)
    for p in process_list:
        p.join()

