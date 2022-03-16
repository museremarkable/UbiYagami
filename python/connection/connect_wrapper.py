from python.server.data_type import OperationType, Order, Trade, Quote, DirectionType, OrderType
import json
from multiprocessing import Queue
from time import sleep

def json_to_order(js: json):
	dic = json.loads(js)
	stk = dic['s']
	orderId = dic['o']
	direction = dic['d']
	price = dic['p']
	volume = dic['v']
	ordertype = dic['t']
	order = Order(
		stk_code=int(stk),
		order_id=int(orderId),
		direction=DirectionType(direction),
		price=price,
		volume=int(volume),
		type=OrderType(ordertype)
	)
	return order
     
def dict_to_quote(dic: dict):
	return Quote(
				stk_code=int(dic['s']), 
				order_id=int(dic['o']), 
				price=dic['p'], 
				volume=int(dic['v']), 
				operation=OperationType(dic['O'])
			)

def dict_to_trade(dic: dict):
	return Trade(
				stk_code=int(dic['s']), 
				bid_id=int(dic['b']), 
				ask_id=int(dic['a']), 
				price=dic['p'], 
				volume=int(dic['v'])
				)
	

"""
Message headers:
	A: Acknowledge, return the message to acknowledge receiving the previous one, 
					for order ack (client side) {'A':{'s': xxx, 'o': xxx}}, 
					for trade and quote (server side) {'A':{'c': xxx}}
	O: Order
	F: Feeds, including: {'F':{'T':{}, 'Q':{}}}
		T: Trade
		Q: Quote
"""


class connect:
	def __init__(self, recv_queue, send_queue):
		self.read_queue = recv_queue
		self.send_queue = send_queue
		# self.send_q_queue = qq

	def recv_order(self):
		return self.read_queue.get()

	def send_feed(self, message: dict):
		self.send_queue.put(message)


class ConnectServer():
	def __init__(self):
		self.feed_waiting_list = {}

	def _recv_message(self) -> json:
		pass

	def _send_message(self):
		pass


	def send_feed(self, trades, quotes):
		pass

	def recv_order(self, ) -> Order:
		message = json.loads(self._recv_message())
		order = message.get('O')
		if order is not None:

			pass


class ConnectClient():
	def __init__(self, n_stock):
		self.order_waiting_list = [{}] * n_stock
		self.feed_recv_queue = Queue()
		self.ack_queue= Queue()

	def _recv_message(self) -> json:
		pass

	def _send_message(self, js: json):
		pass

	def _resend_waiting(self):
		if sum(list(map(len, self.order_waiting_list))) != 0:
			for stk in self.order_waiting_list:
				for k, v in stk.items():
					self._send_message(v)


	def send_order(self, order: Order):
		while not self.ack_queue.empty():
			ack = self.ack_queue.get()
			self.order_waiting_list[ack['s']-1].pop(ack['o'])

		message = self._recv_message()
		if message is not None:
			message = json.loads(message)
			ack = message.get['A']
			feed = message.get('F')

			if ack is not None:
				self.order_waiting_list[ack['s']-1].pop(ack['o'])
			if feed is not None:
				self.feed_recv_queue.put(feed)

		self._resend_waiting()
		js = json.dumps({'O': order.to_dict()})
		self.order_waiting_list[order.stk_code-1][order.order_id] = js
		self._send_message(js)

	def _dict_to_feedout(self, dic: dict):
		trade = dic.get('T')
		quote = dic.get('Q')
		feed_out = {}
		if trade is not None:
			feed_out['trade'] = dict_to_trade(dic['T'])
		if quote is not None:
			feed_out['quote'] = dict_to_quote(dic['Q'])
		return feed_out


	def recv_feed(self):
		if not self.feed_recv_queue.empty():
			feed = self.feed_recv_queue.get()
			return self._dict_to_feedout(feed)
		else:
			while True: 
				message = self._recv_message()
				if message is not None:
					message = json.loads(message)
					ack = message.get('A')
					feed = message.get('F')
					if ack is not None:
						self.ack_queue.put(ack)
					if feed is not None:
						return self._dict_to_feedout(feed)
				else: sleep(0.1)

