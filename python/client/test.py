import h5py
import sys
sys.path.append('F:/UbiYagami/python')
from enum import IntEnum
from connection.order_type import OrderTick
from connection.pollable_queue import PollableQueue
import logging
logger = logging.getLogger()
handler = logging.FileHandler('./client/ClientLogFile.log')
logging.basicConfig(level=logging.DEBUG)
formatter = logging.Formatter('%(asctime)s  %(name)s  %(levelname)s: %(message)s')
logger.addHandler(handler)
handler.setFormatter(formatter)
logger.debug('This is a sample debug message')
logger.info('This is a sample info messag%d %d'% (1, 2))
logger.warning('This is a sample warning message')
logger.error('This is a sample error message')
logger.critical('This is a sample critical message')

print("begin")
'''
parser = ArgumentParser()
parser.add_argument("-f", "--filepath",  help="data file folder path")
parser.add_argument("-r", "--respath",  help="result folder path")
parser.add_argument("-c", "--client_id",  help="client_id, which is 1 or 2")
args = parser.parse_args()
send_queue = asyncio.Queue()
reveive_queue = asyncio.Queue()
'''
