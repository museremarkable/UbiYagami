import logging
from math import log
from random import uniform, seed
from time import sleep, time
import numpy as np
import pandas as pd

"""
performance test

"""
class Timer:
    def __enter__(self):
        self.start = time()
        return self

    def __exit__(self, *args):
        self.end = time()
        self.interval = self.end - self.start