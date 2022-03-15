
from python.server.server import MatchingEngine, OrderLink, OrderBook
import unittest
from python.server.data_type import Order, MinOrder, Trade, OrderType, DirectionType, Quote, OperationType, SubOrder

def quote_comp(q1, q2):
	comp = [q1.stk_code != q2.stk_code,
			q1.order_id != q2.order_id,
			q1.price != q2.price,
			q1.volume != q2.volume,
			q1.operation != q2.operation]
	return sum(comp)
	
def trade_comp(t1, t2):
	comp = [t1.stk_code != t2.stk_code,
			t1.bid_id != t2.bid_id,
			t1.ask_id != t2.ask_id,
			t1.price != t2.price,
			t1.volume != t2.volume]
	return sum(comp)

def miniorder_comp(o1, o2):
	comp = [o1.order_id != o2.order_id,
			o1.volume != o2.volume]
	return sum(comp)

class TestOrderLink(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		print ("this setupclass() method only called once.\n")

	@classmethod
	def tearDownClass(cls):
		print ("this teardownclass() method only called once too.\n")

	def setUp(self):
		print ("do something before test : prepare environment.\n")
		stock = 2
		price = 102  # price level this link is at
		side = 0    # int, 0: ask, 1: bid
		orderls = [MinOrder(1, 30), MinOrder(3,5), MinOrder(44,110), MinOrder(50, 2)]
		self.orderlink = OrderLink(price, side, stock)
		for od in orderls:
			self.orderlink.insert_order(od)

	def tearDown(self):
		print ("do something after test : clean up.\n")

	def test_search_loc(self):
		order_id = 44
		loc = self.orderlink._search_order_loc(order_id)
		self.assertEqual(2, loc)
		order_id = 0
		loc = self.orderlink._search_order_loc(order_id)
		self.assertEqual(0, loc)
		order_id = 51
		loc = self.orderlink._search_order_loc(order_id)
		self.assertEqual(4, loc)
		order_id = 3
		loc = self.orderlink._search_order_loc(order_id)
		self.assertEqual(1, loc)


	def test_insert(self):
		orderlink = self.orderlink
		# insert to the end
		order = MinOrder(57, 100)
		quotes = orderlink.insert_order(order)
		true_q = Quote(2, 57, 102, 100, OperationType.NEW_ASK)
		self.assertEqual(0, quote_comp(true_q, quotes[0]))
		self.assertEqual(0, miniorder_comp(orderlink.link[-1], order))
		self.assertEqual(5, len(orderlink.link))
		# insert in between
		order = MinOrder(14, 100)
		quotes = orderlink.insert_order(order)
		true_q = Quote(2, 14, 102, 100, OperationType.NEW_ASK)
		self.assertEqual(0, quote_comp(true_q, quotes[0]))
		self.assertEqual(0, miniorder_comp(orderlink.link[2], order))
		self.assertEqual(6, len(orderlink.link))
		# insert at the head
		order = MinOrder(0, 20)
		quotes = orderlink.insert_order(order)
		true_q = Quote(2, 0, 102, 20, OperationType.NEW_ASK)
		self.assertEqual(0, quote_comp(true_q, quotes[0]))
		self.assertEqual(0, miniorder_comp(orderlink.link[0], order))
		self.assertEqual(7, len(orderlink.link))


	def test_amend(self):
		orderlink = self.orderlink
		order = MinOrder(3, -3)
		quotes = orderlink.amend_order(order)
		true_q = Quote(2, 3, 102, -3, OperationType.AMEND_ASK)
		
		
		self.assertEqual(0, quote_comp(true_q, quotes[0]))
		self.assertEqual(2, orderlink.link[1].volume)
		self.assertEqual(4, len(orderlink.link))


	def test_cancel(self):
		orderlink = self.orderlink
		order = MinOrder(44, 100)
		quotes = orderlink.cancel_order(order)
		true_q = Quote(2, 44, 102, 110, OperationType.REMOVE_ASK)
		self.assertEqual(0, quote_comp(true_q, quotes[0]))
		self.assertEqual(orderlink.link[2].order_id, 50)
		self.assertEqual(3, len(orderlink.link))


	def test_match(self):
		orderlink = self.orderlink
		order = MinOrder(57, 100)
		order_remain, trades, quotes = orderlink.match_order(order)

		true_q = [	Quote(2, 1, 102, 30, OperationType.REMOVE_ASK),
					Quote(2, 3, 102, 5, OperationType.REMOVE_ASK),
					Quote(2, 44, 102, -65, OperationType.AMEND_ASK) ]
		true_t = [	Trade(2, 57, 1, 102, 30),
					Trade(2, 57, 3, 102, 5),
					Trade(2, 57, 44, 102, 65)	]

		self.assertEqual(0, len(true_q)-len(quotes))
		self.assertEqual(0, len(true_t)-len(trades))
		self.assertEqual(0, sum(list(map(quote_comp, true_q, quotes))))
		self.assertEqual(0, sum(list(map(trade_comp, true_t, trades))))

		self.assertEqual(0, order_remain.volume)
		self.assertEqual(57, order_remain.order_id)
		
		self.assertEqual(45, orderlink.link[0].volume)
		self.assertEqual(44, orderlink.link[0].order_id)
		self.assertEqual(2, len(orderlink.link))
		last_link = orderlink.link

		order = MinOrder(60, 50)
		order_remain, trades, quotes = orderlink.match_order(order)
		
		true_q = [	Quote(2, 44, 102, 45, OperationType.REMOVE_ASK),
					Quote(2, 50, 102, 2, OperationType.REMOVE_ASK) ]
		true_t = [	Trade(2, 60, 44, 102, 45),
					Trade(2, 60, 50, 102, 2)	]

		self.assertEqual(0, len(true_q)-len(quotes))
		self.assertEqual(0, len(true_t)-len(trades))
		self.assertEqual(0, sum(list(map(quote_comp, true_q, quotes))))
		self.assertEqual(0, sum(list(map(trade_comp, true_t, trades))))

		self.assertEqual(3, order_remain.volume)
		self.assertEqual(60, order_remain.order_id)
		
		self.assertEqual(45, orderlink.link[0].volume)
		self.assertEqual(44, orderlink.link[0].order_id)
		self.assertEqual(2, len(orderlink.link))
		self.assertEqual(0, len(last_link)-len(orderlink.link))
		self.assertEqual(0, sum(list(map(miniorder_comp, last_link, orderlink.link))))


Oorderbook = OrderBook(2)

class TestOrderBook(unittest.TestCase):
	@classmethod
	def setUpClass(self):
		print ("this setupclass() method only called once.\n")
		# globals()['orderbook'] = OrderBook(2)
		self.orderbook = OrderBook(2)

	@classmethod
	def tearDownClass(cls):
		print ("this teardownclass() method only called once too.\n")

	def setUp(self):
		print ("do something before test : prepare environment.\n")

	def tearDown(self):
		print ("do something after test : clean up.\n")

	def init_book(self):
		# orderbook = globals()['orderbook']
		orderbook = OrderBook(2)

		# test bid side
		bid = 1
		orderIds = [1,2,4,6]
		prices = [118, 120, 117, 119]
		volumes = [30, 20, 5, 10]
		orders = [ 	SubOrder(Id, DirectionType.BUY, pr, vl) 
					for Id, pr, vl in zip(orderIds, prices, volumes) ]
		for order in orders:
			orderbook._create_price_level(order, bid)

		# test ask side
		bid = 0
		orderIds = [3,5,7,8]
		prices = [123, 122, 124, 125]
		volumes = [30, 20, 5, 10]
		orders = [ 	SubOrder(Id, DirectionType.SELL, pr, vl) 
					for Id, pr, vl in zip(orderIds, prices, volumes) ]
		for order in orders:
			orderbook._create_price_level(order, bid)

		return orderbook

		'''
		bid 	price	ask
				125		10
				124		5
				123		30
				122		20
		20		120
		10		119
		30		118
		5		117
		'''

	def init_book_deep(self):
		# orderbook = globals()['orderbook']
		orderbook = OrderBook(2)

		# test bid side
		bid = 1
		orderIds = [1,2,4,6,9,11,14]
		prices = [118, 120, 117, 119, 115, 114, 111]
		volumes = [30, 20, 5, 10, 20, 5, 10]
		orders = [ 	SubOrder(Id, DirectionType.BUY, pr, vl) 
					for Id, pr, vl in zip(orderIds, prices, volumes) ]
		for order in orders:
			orderbook._create_price_level(order, bid)

		# test ask side
		bid = 0
		orderIds = [3,5,7,8,10,12,13]
		prices = [123, 122, 124, 125, 126, 127, 130]
		volumes = [30, 20, 5, 10, 30, 5, 3]
		orders = [ 	SubOrder(Id, DirectionType.SELL, pr, vl) 
					for Id, pr, vl in zip(orderIds, prices, volumes) ]
		for order in orders:
			orderbook._create_price_level(order, bid)

		return orderbook

		'''
		id	bid 	price	ask	id
					130		3	13
					127		5	12
					126		30	10
					125		10	8
					124		5	7
					123		30	3
					122		20	5
		2	20		120
		6	10		119
		1	30		118
		4	5		117
		9	20		115
		11	5		114
		14	10		111
		'''

	def test_create_level(self):
		# orderbook = globals()['orderbook']
		orderbook = self.orderbook

		# test bid side
		bid = 1
		orderIds = [1,2,4,6]
		prices = [118, 120, 117, 119]
		volumes = [30, 20, 5, 10]
		orders = [ 	SubOrder(Id, DirectionType.BUY, pr, vl) 
					for Id, pr, vl in zip(orderIds, prices, volumes) ]
		for order in orders:
			orderbook._create_price_level(order, bid)
		
		self.assertEqual(sorted(prices, reverse=True), orderbook._get_sorted_prices(bid))
		self.assertEqual(sorted(prices, reverse=True)[0], orderbook._get_best_price(bid))
		self.assertEqual(sorted(prices, reverse=True)[:5], orderbook._get_top5_prices(bid))

		for i, pr in enumerate(prices):
			orderlink = orderbook._get_price_level(pr, bid)
			self.assertEqual(volumes[i], orderlink.cum)
		orderlink = orderbook._get_price_level(121, bid)
		self.assertEqual(None, orderlink)

		# test ask side
		bid = 0
		orderIds = [3,5,7,8]
		prices = [123, 122, 124, 125]
		volumes = [30, 20, 5, 10]
		orders = [ 	SubOrder(Id, DirectionType.SELL, pr, vl) 
					for Id, pr, vl in zip(orderIds, prices, volumes) ]
		for order in orders:
			orderbook._create_price_level(order, bid)

		self.assertEqual(sorted(prices, reverse=False), orderbook._get_sorted_prices(bid))
		self.assertEqual(sorted(prices, reverse=False)[0], orderbook._get_best_price(bid))
		self.assertEqual(sorted(prices, reverse=False)[:5], orderbook._get_top5_prices(bid))
		
		for i, pr in enumerate(prices):
			orderlink = orderbook._get_price_level(pr, bid)
			self.assertEqual(volumes[i], orderlink.cum)
		orderlink = orderbook._get_price_level(121, bid)
		self.assertEqual(None, orderlink)

		self.orderbook = orderbook

		'''
		id	bid 	price	ask	id
					125		10	8
					124		5	7
					123		30	3
					122		20	5
		2	20		120
		6	10		119
		1	30		118
		4	5		117
		'''

	def test_handle_limit(self):
		orderbook = self.init_book()

		# test buy 
		orderIds = [9,10,13,12]
		prices = [118, 122, 125, 121]
		volumes = [10, 25, 20, 10]
		orders = [ 	SubOrder(Id, DirectionType.BUY, pr, vl) 
					for Id, pr, vl in zip(orderIds, prices, volumes) ]

		true_q = [	Quote(2, 9, 118, 10, OperationType.NEW_BID),
					Quote(2, 5, 122, 20, OperationType.REMOVE_ASK),
					Quote(2, 10, 122, 5, OperationType.NEW_BID),
					Quote(2, 3, 123, -20, OperationType.AMEND_ASK),
					Quote(2, 12, 121, 10, OperationType.NEW_BID),	]
		true_t = [	Trade(2, 10, 5, 122, 20),
					Trade(2, 13, 3, 123, 20)	]

		trades = []
		quotes = []
		for order in orders:
			this_trades, this_quotes = orderbook.handle_order_limit(order)
			trades += this_trades
			quotes += this_quotes

		self.assertEqual(0, len(true_q)-len(quotes))
		self.assertEqual(0, len(true_t)-len(trades))
		self.assertEqual(0, sum(list(map(quote_comp, true_q, quotes))))
		self.assertEqual(0, sum(list(map(trade_comp, true_t, trades))))

		book = orderbook.get_price_depth()
		true_book = {
				'bid':{
						122:	5,
						121:	10,
						120: 	20,
						119:	10,
						118:	40,
						117:	5
					},
				'ask':{
						125:	10,
						124:	5,
						123:	10
					}
				}
		self.assertEqual(0, len(set(true_book['bid'].items()) - set(book['bid'].items())))
		self.assertEqual(0, len(set(true_book['ask'].items()) - set(book['ask'].items())))

		'''
		id	bid 	price	ask	id
					125		10	8
					124		5	7
					123		10	3
		10	5		122 	
		12	10		121		
		2	20		120
		6	10		119
		1,9	40		118
		4	5		117
		'''

		# test sell 
		orderIds = [11,14,15,16]
		prices = [124, 119, 120, 119]
		volumes = [10, 25, 20, 10]
		orders = [ 	SubOrder(Id, DirectionType.SELL, pr, vl) 
					for Id, pr, vl in zip(orderIds, prices, volumes) ]

		true_q = [	Quote(2, 11, 124, 10, OperationType.NEW_ASK),
					Quote(2, 10, 122, 5, OperationType.REMOVE_BID),
					Quote(2, 12, 121, 10, OperationType.REMOVE_BID),
					Quote(2, 2, 120, -10, OperationType.AMEND_BID),
					Quote(2, 2, 120, 10, OperationType.REMOVE_BID),	
					Quote(2, 15, 120, 10, OperationType.NEW_ASK),	
					Quote(2, 6, 119, 10, OperationType.REMOVE_BID),	
					]
		true_t = [	Trade(2, 10, 14, 122, 5),
					Trade(2, 12, 14, 121, 10),	
					Trade(2, 2, 14, 120, 10),	
					Trade(2, 2, 15, 120, 10),	
					Trade(2, 6, 16, 119, 10),	
					]

		trades = []
		quotes = []
		for order in orders:
			this_trades, this_quotes = orderbook.handle_order_limit(order)
			trades += this_trades
			quotes += this_quotes
			
		self.assertEqual(0, len(true_q)-len(quotes))
		self.assertEqual(0, len(true_t)-len(trades))
		self.assertEqual(0, sum(list(map(quote_comp, true_q, quotes))))
		self.assertEqual(0, sum(list(map(trade_comp, true_t, trades))))

		book = orderbook.get_price_depth()
		true_book = {
				'bid':{
						118:	40,
						117:	5
					},
				'ask':{
						125:	10,
						124:	15,
						123:	10,
						120:	10
					}
				}
		self.assertEqual(0, len(set(true_book['bid'].items()) - set(book['bid'].items())))
		self.assertEqual(0, len(set(true_book['ask'].items()) - set(book['ask'].items())))
		
		'''
		bid 	price	ask
				125		10
				124		15
				123		10
				120		10
		40		118
		5		117
		'''

	def test_handle_counter(self):
		orderbook = self.init_book()
		'''
		bid 	price	ask
				125		10
				124		5
				123		30
				122		20
		20		120
		10		119
		30		118
		5		117
		'''

		# test buy 
		orderIds = [9,10,13]
		prices = [118, 122, 125]
		volumes = [10, 25, 20]
		orders = [ 	SubOrder(Id, DirectionType.BUY, pr, vl) 
					for Id, pr, vl in zip(orderIds, prices, volumes) ]
		for order in orders:
			orderbook.handle_order_counter_side_optimal(order)

		book = orderbook.get_price_depth()
		true_book = {
				'bid':{
						122:	15,
						120: 	20,
						119:	10,
						118:	30,
						117:	5
					},
				'ask':{
						125:	10,
						124:	5,
						123:	10,
					}
				}
		self.assertEqual(0, len(set(true_book['bid'].items()) - set(book['bid'].items())))
		self.assertEqual(0, len(set(true_book['ask'].items()) - set(book['ask'].items())))
		'''
		bid 	price	ask
				125		10
				124		5
				123		10
		15		122 	
		20		120
		10		119
		30		118
		5		117
		'''
		'''
		bid 	price	ask
				125		10
				124		5
				123		10
				122 	5
		10		119
		30		118
		5		117
		'''

		# test sell 
		orderIds = [11,14,15]
		prices = [124, 119, 120]
		volumes = [5, 15, 20]
		orders = [ 	SubOrder(Id, DirectionType.SELL, pr, vl) 
					for Id, pr, vl in zip(orderIds, prices, volumes) ]
		for order in orders:
			orderbook.handle_order_counter_side_optimal(order)

		book = orderbook.get_price_depth()
		true_book = {
				'bid':{
						119:	10,
						118:	30,
						117:	5
					},
				'ask':{
						125:	10,
						124:	5,
						123:	10,
						122:	5
					}
				}
		self.assertEqual(0, len(set(true_book['bid'].items()) - set(book['bid'].items())))
		self.assertEqual(0, len(set(true_book['ask'].items()) - set(book['ask'].items())))
		'''
		bid 	price	ask
				125		10
				124		5
				123		10
				122 	15
		20		120
		10		119
		30		118
		5		117
		'''

	def test_handle_own(self):
		orderbook = self.init_book()
		'''
		bid 	price	ask
				125		10
				124		5
				123		30
				122		20
		20		120
		10		119
		30		118
		5		117
		'''

		# test buy 
		orderIds = [9,10,13]
		prices = [118, 122, 125]
		volumes = [10, 25, 20]
		orders = [ 	SubOrder(Id, DirectionType.BUY, pr, vl) 
					for Id, pr, vl in zip(orderIds, prices, volumes) ]
		for order in orders:
			orderbook.handle_order_own_side_optimal(order)

		book = orderbook.get_price_depth()
		true_book = {
				'bid':{
						120: 	75,
						119:	10,
						118:	30,
						117:	5
					},
				'ask':{
						122:	20,
						123:	30,
						124:	5,
						125:	10,
					}
				}
		self.assertEqual(0, len(set(true_book['bid'].items()) - set(book['bid'].items())))
		self.assertEqual(0, len(set(true_book['ask'].items()) - set(book['ask'].items())))
		'''
		bid 	price	ask
				125		10
				124		5
				123		30
				122		20
		75		120
		10		119
		30		118
		5		117
		'''

		# test sell 
		orderIds = [11,14,15]
		prices = [124, 119, 120]
		volumes = [5, 15, 20]
		orders = [ 	SubOrder(Id, DirectionType.SELL, pr, vl) 
					for Id, pr, vl in zip(orderIds, prices, volumes) ]
		for order in orders:
			orderbook.handle_order_own_side_optimal(order)

		book = orderbook.get_price_depth()
		true_book = {
				'bid':{
						120: 	75,
						119:	10,
						118:	30,
						117:	5
					},
				'ask':{
						122:	60,
						123:	30,
						124:	5,
						125:	10,
					}
				}
		self.assertEqual(0, len(set(true_book['bid'].items()) - set(book['bid'].items())))
		self.assertEqual(0, len(set(true_book['ask'].items()) - set(book['ask'].items())))
		'''
		bid 	price	ask
				125		10
				124		5
				123		30
				122		60
		75		120
		10		119
		30		118
		5		117
		'''

	def test_handle_top5(self):
		orderbook = self.init_book_deep()
		'''
		bid 	price	ask
				130		3
				127		5
				126		30
				125		10
				124		5
				123		30
				122		20
		20		120
		10		119
		30		118
		5		117
		20		115
		5		114
		10		111
		'''

		# test buy 
		orderIds = [9,10]
		prices = [118, 122]
		volumes = [30, 80]
		orders = [ 	SubOrder(Id, DirectionType.BUY, pr, vl) 
					for Id, pr, vl in zip(orderIds, prices, volumes) ]
		for order in orders:
			trades, quotes = orderbook.handle_order_best_five(order)

		book = orderbook.get_price_depth()
		true_book = {
				'bid':{
						120: 20, 119: 10, 118: 30, 117: 5, 115: 20, 114: 5, 111: 10
					},
				'ask':{
						130: 3,
					}
				}
		self.assertEqual(0, len(set(true_book['bid'].items()) - set(book['bid'].items())))
		self.assertEqual(0, len(set(true_book['ask'].items()) - set(book['ask'].items())))

		# test sell 
		orderIds = [11,]
		prices = [124, ]
		volumes = [70, ]
		orders = [ 	SubOrder(Id, DirectionType.SELL, pr, vl) 
					for Id, pr, vl in zip(orderIds, prices, volumes) ]
		for order in orders:
			orderbook.handle_order_best_five(order)

		book = orderbook.get_price_depth()
		true_book = {
				'bid':{
						115: 15, 114: 5, 111: 10
					},
				'ask':{
						130: 3,
					}
				}
		self.assertEqual(0, len(set(true_book['bid'].items()) - set(book['bid'].items())))
		self.assertEqual(0, len(set(true_book['ask'].items()) - set(book['ask'].items())))


	def test_handle_immitdiate(self):
		orderbook = self.init_book_deep()
		'''
		bid 	price	ask
				130		3
				127		5
				126		30
				125		10
				124		5
				123		30
				122		20
		20		120
		10		119
		30		118
		5		117
		20		115
		5		114
		10		111
		'''
		# test buy 
		orderIds = [9,10]
		prices = [118, 122]
		volumes = [30, 80]
		orders = [ 	SubOrder(Id, DirectionType.BUY, pr, vl) 
					for Id, pr, vl in zip(orderIds, prices, volumes) ]
		for order in orders:
			orderbook.handle_order_immediate_transact(order)

		book = orderbook.get_price_depth()
		true_book = {
				'bid':{
						120: 20, 119: 10, 118: 30, 117: 5, 115: 20, 114: 5, 111: 10
					},
				'ask':{
					}
				}
		self.assertEqual(0, len(set(true_book['bid'].items()) - set(book['bid'].items())))
		self.assertEqual(0, len(set(true_book['ask'].items()) - set(book['ask'].items())))

		# test sell 
		orderIds = [11,]
		prices = [124, ]
		volumes = [75, ]
		orders = [ 	SubOrder(Id, DirectionType.SELL, pr, vl) 
					for Id, pr, vl in zip(orderIds, prices, volumes) ]
		for order in orders:
			orderbook.handle_order_immediate_transact(order)

		book = orderbook.get_price_depth()
		true_book = {
				'bid':{
						115: 10, 114: 5, 111: 10
					},
				'ask':{
					}
				}
		self.assertEqual(0, len(set(true_book['bid'].items()) - set(book['bid'].items())))
		self.assertEqual(0, len(set(true_book['ask'].items()) - set(book['ask'].items())))


	def test_handle_fulldeal(self):
		orderbook = self.init_book_deep()
		'''
		id	bid 	price	ask	id
					130		3	13
					127		5	12
					126		30	10
					125		10	8
					124		5	7
					123		30	3
					122		20	5
		2	20		120
		6	10		119
		1	30		118
		4	5		117
		9	20		115
		11	5		114
		14	10		111
		'''
		# test buy 
		orderIds = [9,10]
		prices = [118, 122]
		volumes = [20, 80]
		orders = [ 	SubOrder(Id, DirectionType.BUY, pr, vl) 
					for Id, pr, vl in zip(orderIds, prices, volumes) ]

		true_q = [	Quote(2, 5, 122, 20, OperationType.REMOVE_ASK),
					Quote(2, 3, 123, 30, OperationType.REMOVE_ASK),
					Quote(2, 7, 124, 5, OperationType.REMOVE_ASK),
					Quote(2, 8, 125, 10, OperationType.REMOVE_ASK),
					Quote(2, 10, 126, 30, OperationType.REMOVE_ASK),	
					Quote(2, 12, 127, 5, OperationType.REMOVE_ASK),	
					]
		true_t = [	Trade(2, 9, 5, 122, 20),
					Trade(2, 10, 3, 123, 30),	
					Trade(2, 10, 7, 124, 5),	
					Trade(2, 10, 8, 125, 10),	
					Trade(2, 10, 10, 126, 30),	
					Trade(2, 10, 12, 127, 5),	
					]

		trades = []
		quotes = []
		for order in orders:
			this_trades, this_quotes = orderbook.handle_order_full_deal(order)
			trades += this_trades
			quotes += this_quotes

		self.assertEqual(0, len(true_q)-len(quotes))
		self.assertEqual(0, len(true_t)-len(trades))
		self.assertEqual(0, sum(list(map(quote_comp, true_q, quotes))))
		self.assertEqual(0, sum(list(map(trade_comp, true_t, trades))))

		book = orderbook.get_price_depth()
		true_book = {
				'bid':{
						120: 20, 119: 10, 118: 30, 117: 5, 115: 20, 114: 5, 111: 10
					},
				'ask':{
						130: 3,
					}
				}
		self.assertEqual(0, len(set(true_book['bid'].items()) - set(book['bid'].items())))
		self.assertEqual(0, len(set(true_book['ask'].items()) - set(book['ask'].items())))

		# test sell 
		orderIds = [11,12,13]
		prices = [124, 124, 125]
		volumes = [70, 5, 30]
		orders = [ 	SubOrder(Id, DirectionType.SELL, pr, vl) 
					for Id, pr, vl in zip(orderIds, prices, volumes) ]
					
		true_q = [	Quote(2, 2, 120, 20, OperationType.REMOVE_BID),
					Quote(2, 6, 119, 10, OperationType.REMOVE_BID),
					Quote(2, 1, 118, 30, OperationType.REMOVE_BID),
					Quote(2, 4, 117, 5, OperationType.REMOVE_BID),
					Quote(2, 9, 115, -5, OperationType.AMEND_BID),	
					Quote(2, 9, 115, -5, OperationType.AMEND_BID),	
					]
		true_t = [	Trade(2, 2, 11, 120, 20),
					Trade(2, 6, 11, 119, 10),	
					Trade(2, 1, 11, 118, 30),	
					Trade(2, 4, 11, 117, 5),	
					Trade(2, 9, 11, 115, 5),	
					Trade(2, 9, 12, 115, 5),	
					]

		trades = []
		quotes = []
		for order in orders:
			this_trades, this_quotes = orderbook.handle_order_full_deal(order)
			trades += this_trades
			quotes += this_quotes

		self.assertEqual(0, len(true_q)-len(quotes))
		self.assertEqual(0, len(true_t)-len(trades))
		self.assertEqual(0, sum(list(map(quote_comp, true_q, quotes))))
		self.assertEqual(0, sum(list(map(trade_comp, true_t, trades))))

		book = orderbook.get_price_depth()
		true_book = {
				'bid':{
						115: 10, 114: 5, 111: 10
					},
				'ask':{
						130: 3, 
					}
				}
		self.assertEqual(0, len(set(true_book['bid'].items()) - set(book['bid'].items())))
		self.assertEqual(0, len(set(true_book['ask'].items()) - set(book['ask'].items())))


