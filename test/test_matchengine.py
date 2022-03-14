from multiprocessing.managers import BaseManager
import numpy as np
import h5py
import unittest
from unittest import mock

from multiprocessing import Process, Queue
from python.server.data_type import DirectionType, Order, OrderType, Trade, Quote

from python.server.server import MatchingEngine

def order_comp(o1: Order, o2: Order):
	comp = [o1.stk_code != o2.stk_code,
            o1.order_id != o2.order_id,
			o1.volume != o2.volume,
            o1.direction != o2.direction,
            o1.type != o2.type,
            o1.price != o2.price
            ]
	return sum(comp)

def list_to_order(stk, x:list):
    stk = stk
    orderId = x[0]
    direction = x[1]
    price = x[2]
    volume = x[3]
    ordertype = x[4]
    order = Order(
        stk_code=int(stk),
        order_id=int(orderId),
        direction=DirectionType(direction),
        price=price,
        volume=volume,
        type=OrderType(ordertype)
    )
    return order
     

class TestOrderLink(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        print ("this setupclass() method only called once.\n")
        # data_reader = Client(client_id=1, data_file_path="C:/Users/Leons/git/UbiYagami/data_test/100x10x10", res_file_path="")
        # data_reader.data_read()
        # self.order_mtx = data_reader.all_page
        # manager = BaseManager()
        # manager.register("MatchEngine", MatchingEngine)
        # manager.start()
        # self.engine = manager.MatchEngine() 
        self.engine = MatchingEngine()
        

    @classmethod
    def tearDownClass(self):
        print ("this teardownclass() method only called once too.\n")

    def setUp(self):
        print ("do something before test : prepare environment.\n")


    def tearDown(self):
        print ("do something after test : clean up.\n")

    def test_updata_queue_reorder_check(self):
        stk = [3]*16
        orderIds = [1,3,2,4,5,9,10,8,7,6,11,13,12,14,15,16]
        prices = [104.74, 107.3, 93.53, 90.01] * 4
        volumes = [5, 15, 20, 10] * 4
        direction = [-1,1] * 8
        orderType = [0,2,1,5,3,4] * 5 + [0]
        orders = [ 	list_to_order(s[0], s[1:] ) 
                    for s in zip(stk, orderIds, direction, prices, volumes, orderType) ]
        orders[3].volume = 0
        orders[7].volume = 0
        validorder = [0,2,1,4,9,8,5,6,10,12,11,13,14,15]
        
        self.engine._recv_order = mock.Mock(side_effect=orders)

        order_q = Queue()
        feed_q = Queue()
        try:
            self.engine.update_order_queue_thread(order_q, feed_q)
        except StopIteration:
            print('iteration stopped')

        i = 0
        self.assertEqual(False, order_q.empty())
        while not order_q.empty():
            order = order_q.get()
            res = order_comp(order, orders[validorder[i]])
            self.assertEqual(0, res)
            i += 1


