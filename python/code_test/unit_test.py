#!/usr/bin/python3
from python.server import MatchingEngine
import unittest
from client.client import Client

"""
unit test
"""
class TestBasicOrders(unittest.TestCase):
    instmt = "TestingInstrument"
    price = 100.0
    lot_size = 1.0

    def check_order(self, order):
        """
        Check the order information
        """
        self.assertTrue(order is not None)


    def check_trade(self, trade):
        """
        Check the trade information
        """
        self.assertTrue(trade is not None)


 


if __name__ == '__main__':
    unittest.main()

