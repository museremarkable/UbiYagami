import asyncio
import multiprocessing
import time


import multiprocessing

def read_data_from_file(send_queue):
    print("read data then put it in send_queue")
  
def send_data_to_server(send_queue):
    """
    function to square a given list
    """
    print("fetch data from send queue, send to server")
    # append squares of mylist to queue

def receive_data_from_server(receive_queue):
    print("receive data")
  
def write_result_to_file(receive_queue):
    """
    function to print queue elements
    """
    print("write file!")
  
if __name__ == "__main__":
    # input list
    mylist = [1,2,3,4]
  
    # creating multiprocessing Queue
    send_queue = multiprocessing.Queue()
    receive_queue = multiprocessing.Queue()
    # creating new processes
    process_read_data_from_file = multiprocessing.Process(target=read_data_from_file, args=(send_queue,))
    process_send_data_to_server = multiprocessing.Process(target=send_data_to_server, args=(send_queue,))
    process_receive_data_from_server = multiprocessing.Process(target=receive_data_from_server, args=(receive_queue,))
    process_write_result_to_file = multiprocessing.Process(target=write_result_to_file, args=(receive_queue,))
    # running process p1 to square list
    p1.start()
    p1.join()
  
    # running process p2 to get queue elements
    p2.start()
    p2.join()