
from data_type import Order, MinOrder, Trade, OrderType, DirectionType, Quote
from data_type import OperationType, SubOrder
from typing import List, Dict, Tuple, Sequence
from multiprocessing import Queue, Process
from multiprocessing.managers import BaseManager 
import logging
from time import sleep
import h5py

logging.basicConfig(level=logging.DEBUG #设置日志输出格式
                    ,filename="exchange_runtime.log" #log日志输出的文件位置和文件名
                    ,filemode="w" #文件的写入格式，w为重新写入文件，默认是追加
                    ,format="%(asctime)s - %(name)s - %(levelname)-9s - %(filename)-8s : %(lineno)s line - %(message)s" #日志输出的格式
                    # -8表示占位符，让输出左对齐，输出长度都为8位
                    ,datefmt="%Y-%m-%d %H:%M:%S" #时间输出的格式
                    )


class BookBase:
    """
    For database based book caching
    """
    def __init__(self):
        pass

    def push_back():
        pass

    def pop_in():
        pass

    def storage_match():
        pass


class OrderLink:
    """
    A list of orders under each price level
    """
    def __init__(self, price, side, stock):
        self.stock = stock
        self.price = price  # price level this link is at
        self.side = side    # int, 0: ask, 1: bid
        self.op_new = OperationType.NEW_BID if self.side else OperationType.NEW_ASK
        self.op_amend = OperationType.AMEND_BID if self.side else OperationType.AMEND_ASK
        self.op_remove = OperationType.REMOVE_BID if self.side else OperationType.REMOVE_ASK

        self.link = []  # orders are stored here
        self.cum = 0        # cumulated volume


    def _search_order_loc(self, order_id: int) -> int:
        """
        Search the location of an order having the same order id, 
        or return the insert location if nothing found
        """
        length = len(self.link)
        for i in range(length):
            the_miniorder = self.link[length-1-i]
            if the_miniorder.order_id == order_id:
                return length-1-i
            elif the_miniorder.order_id < order_id:
                return length-i
        return 0


    def match_order(self, miniorder: MinOrder) -> Tuple[MinOrder, Trade, Quote, List[Order]]:
        """
        Match order from lower order_id to higher until the size is all filled. 
        Otherwise, return the size remains to fill after consuming all the available orders on the link
        Only when there are remaining orders after matching, will the link be updated,
        Orderwise, nothing will be changed in the link
        This enable the full deal order type, the order book can decide whether to remove the price level according to the final result;
        Worth notice that when there are remaining orders after matching, it means the full deal should be deal, so update the link inside will do no harms. 
        : param         miniorder       the mini order to fill in this orderlink
        : return        volume_remain   the remained miniorder after deduced volume from the matching in this order link
        : return        trades          list of transaction detail in Trade type
        : return        quotes          list of book update details in Quote type
        """
        link = self.link
        cum = self.cum
        trades = []
        quotes = []

        volume_remain = miniorder.volume
        for i, link_order in enumerate(link):
            volume_remain -= link_order.volume
            if volume_remain <= 0:
                # Only when the link has rest orders, will it be update; 
                # Otherwise, nothing will change, it will be remove from the orderbook from outside
                volume_diff = link_order.volume+volume_remain
                if volume_remain == 0:
                    self.link = link[i+1:]        
                else:
                    link[i].volume = -volume_remain
                    self.link = link[i:]        

                cum -= volume_diff
                self.cum = cum
                if volume_remain == 0:
                    quote = Quote(self.stock, link_order.order_id, self.price, volume_diff, self.op_remove)
                else:
                    quote = Quote(self.stock, link_order.order_id, self.price, -volume_diff, self.op_amend)
                if self.side: # is bid side
                    trade = Trade(self.stock, link_order.order_id, miniorder.order_id, self.price, volume_diff)
                else:
                    trade = Trade(self.stock, miniorder.order_id, link_order.order_id, self.price, volume_diff)
                quotes.append(quote)
                trades.append(trade)

                volume_remain = 0
                break
            
            cum -= link_order.volume
            # TODO can cancel this branch for better performance?
            quote = Quote(self.stock, link_order.order_id, self.price, link_order.volume, self.op_remove)
            if self.side: # is bid side
                trade = Trade(self.stock, link_order.order_id, miniorder.order_id, self.price, link_order.volume)
            else:
                trade = Trade(self.stock, miniorder.order_id, link_order.order_id, self.price, link_order.volume)
            quotes.append(quote)
            trades.append(trade)

        order_remain = MinOrder(miniorder.order_id, volume_remain)
        return order_remain, trades, quotes


    def insert_order(self, miniorder: MinOrder) -> List[Quote]:
        """
        insert an order to the link at the right place in order_id ascending order
        """
        self.cum += miniorder.volume
        if len(self.link) == 0:
            self.link.append(miniorder)
        else:
            loc = self._search_order_loc(miniorder.order_id)
            self.link.insert(loc, miniorder)

        quotes = Quote(self.stock, miniorder.order_id, self.price, miniorder.volume, self.op_new)
        return [quotes]


    def amend_order(self, miniorder: MinOrder) -> List[Quote]:
        self.cum += miniorder.volume
        loc = self._search_order_loc(miniorder.order_id)
        assert self.link[loc].order_id == miniorder.order_id, f"order id {miniorder.order_id} not found"
        self.link[loc].volume += miniorder.volume

        quotes = Quote(self.stock, miniorder.order_id, self.price, miniorder.volume, self.op_amend)
        return [quotes]


    def cancel_order(self, miniorder: MinOrder) -> List[Quote]:
        loc = self._search_order_loc(miniorder.order_id)
        assert self.link[loc].order_id == miniorder.order_id, f"order id {miniorder.order_id} not found"
        order_removed = self.link.pop(loc)
        self.cum -= order_removed.volume

        quotes = Quote(self.stock, order_removed.order_id, self.price, order_removed.volume, self.op_remove)
        return [quotes]

class OrderBook:
    """
    data structure to store record
    to be defined, just for demo , will write in altree ?
    """
    def __init__(self, stock):
        self.stock = stock
        self.levels = [{}, {}]
        self.sorted_prices = [[], []]
        self.best_prices = [10000000, 0]
        self.levels_locks = []      # TODO for multiprocess

    def _opposite_side(self, direction: DirectionType) -> int:
        """
        Return a side of a book opposite to the order direction
        : param     direction   DirectionType, order direction
        : return                int, 0: ask, 1: bid
        """
        return 0 if direction == DirectionType.BUY else 1


    def _to_bid_ask_book(self, direction: DirectionType) -> int:
        """
        Interpret the bid/ask side from the order direction
        : param     direction   DirectionType, order direction
        : return                int, 0: ask, 1: bid
        """
        return 1 if direction == DirectionType.BUY else 0


    def _is_after(self, price1, price2, bid_ask) -> bool:
        """
        See if price1 should be place after price2 in the order book, meaning price1 is worse than price2
        : param     price1      comparator parameter1
        : param     price2      comparator parameter2
        : param     bid_ask     int, 0: ask, 1: bid
        : return                boolean, True for price1 is after price2, vice versa;
        """
        return price1 < price2 if bid_ask else price1 > price2


    def _create_price_level(self, order: SubOrder, bid_ask) -> List[Quote]:
        """
        Create a new OrderLink at the specified price level of the bid/ask book, and insert the order to the OrderLink;
        Update best price and price list
        : param     order       Order, to insert to the OrderLink in the bid/ask book
        : param     bid_ask     int, 0: ask, 1: bid
        : return                list of quote of ADD order
        """
        self.levels[bid_ask][order.price] = OrderLink(order.price, bid_ask, self.stock)
        quotes = self.levels[bid_ask][order.price].insert_order(order.to_minorder())
        is_new_best = self._is_after(self._get_best_price(bid_ask), order.price, bid_ask)
        if is_new_best:
            self.best_prices[bid_ask] = order.price

        if len(self.sorted_prices[bid_ask]) == 0:
            self.sorted_prices[bid_ask].append(order.price)
        else:
            IS_ASSIGNED = False
            for i, p in enumerate(self.sorted_prices[bid_ask]):
                if self._is_after(p, order.price, bid_ask):
                    self.sorted_prices[bid_ask].insert(i, order.price)
                    IS_ASSIGNED = True
                    break
            if not IS_ASSIGNED:
                self.sorted_prices[bid_ask].append(order.price)
        return quotes

    def _remove_price_level(self, price, bid_ask):
        """
        Delete the specified price level from the bid/ask book;
        Update best price and price list
        : param     price       float, specified price to get from the bid/ask book
        : param     bid_ask     int, 0: ask, 1: bid
        """
        self.levels[bid_ask].pop(price, None)
        loc = self.sorted_prices[bid_ask].index(price)
        self.sorted_prices[bid_ask].pop(loc)
        if loc == 0:
            # if the best price is removed
            if len(self.sorted_prices[bid_ask]) == 0: # it is the last price level 
                self.best_prices[bid_ask] = 0 if bid_ask else 10000000
            else:
                self.best_prices[bid_ask] = self.sorted_prices[bid_ask][0]


    # def _change_price_level(self, price, order_list, bid_ask):
    #     """
    #     Replace the level with a new one, given a sorted list of orders 
    #     """
    #     self.levels[bid_ask][price] = OrderLink(order_list, price, bid_ask, self.stock)


    def _get_price_level(self, price, bid_ask) -> OrderLink:
        """
        Get the orderLink of the specified price level
        : param     price       float, specified price to get from the bid/ask book
        : param     bid_ask     int, 0: ask, 1: bid
        : return                OrderLink
        """
        return self.levels[bid_ask].get(price)
        
    
    def _get_sorted_prices(self, bid_ask ) -> list:
        """
        Get a list of price of the entire bid/ask book, sorted from best price to worse;
        : param     bid_ask     int, 0: ask, 1: bid
        return                  list of prices(float), sorted from best to worse  
        """
        return self.sorted_prices[bid_ask]


    def _get_top5_prices(self, bid_ask) -> list:
        """
        Get sorted top 5 optimal prices from self.bid_ask_sort_price
        : param     bid_ask     int, 0: ask, 1: bid
        : return                list of (float), length 5, sorted from best to worse  
        """
        return self.sorted_prices[bid_ask][:5]


    def _get_best_price(self, bid_ask) -> float:
        """
        Get the best price of the bid/ask book
        : param     bid_ask     int, 0: ask, 1: bid
        : return                price(float)
        """
        return self.best_prices[bid_ask]

    def get_price_depth(self):
        price_depth = {'bid':{}, 'ask':{}}
        
        book_side = self.levels[0]
        print_book = {}
        for pr, ol in book_side.items():
            print_book[pr] = ol.cum
        price_depth['ask'] = print_book
        
        book_side = self.levels[1]
        print_book = {}
        for pr, ol in book_side.items():
            print_book[pr] = ol.cum
        price_depth['bid'] = print_book

        return price_depth

    '''
    Handle passive order below (with price), has trade part and book adding part
    '''
    def handle_order_limit(self, order: SubOrder) -> Tuple[Trade, Quote]:
        # copy attribute first in case they changed in other processes
        side = self._to_bid_ask_book(order.direction)
        oppo_side = self._opposite_side(order.direction)
        oppo_best_price = self._get_best_price(oppo_side)
        sorted_prices = list(self._get_sorted_prices(oppo_side))
        is_remained = True    
        order_remain = order.to_minorder()
        trades = []
        quotes = []

        if not self._is_after(oppo_best_price, order.price, oppo_side):
            # price in opposite side, can match first, then store the remainder if any 
            for book_price in sorted_prices:     # match in available prices in the opposite book
                if self._is_after(book_price, order.price, oppo_side):   
                    # the order is filled till taking worse price
                    break
                orderlink = self._get_price_level(book_price, oppo_side)
                order_remain, this_trades, this_quotes = orderlink.match_order(order_remain)
                trades += this_trades
                quotes += this_quotes
                if order_remain.volume == 0:  
                    # the order is all filled
                    if orderlink.cum == 0:
                        self._remove_price_level(book_price, oppo_side)
                    is_remained = False
                    break
                else:
                    self._remove_price_level(book_price, oppo_side)


            if is_remained:     
                # if still volume remained after matching, create level at this side at the order price
                order.volume = order_remain.volume
                # self._remove_price_level(order.price, oppo_side)
                this_quotes = self._create_price_level(order, side)
                quotes += this_quotes

        else:
            # if price in the order side
            # put them into the book as a passive order
            orderlink = self._get_price_level(order.price, side)
            if orderlink is None:
                this_quotes = self._create_price_level(order, side)
            else:
                this_quotes = orderlink.insert_order(order.to_minorder())
            quotes += this_quotes
        
        return trades, quotes


    def handle_order_counter_side_optimal(self, order: SubOrder) -> Tuple[Trade, Quote]:
        # copy attribute first in case they changed in other processes
        side = self._to_bid_ask_book(order.direction)
        oppo_side = self._opposite_side(order.direction)
        order_remain = order.to_minorder()
        trades = []
        quotes = []  
        price = self._get_best_price(oppo_side)

        # match first, then store the remainder if any 
        orderlink = self._get_price_level(price, oppo_side)
        if orderlink is not None:
            order_remain, this_trades, this_quotes = orderlink.match_order(order_remain)
            trades += this_trades
            quotes += this_quotes
            if order_remain.volume != 0:  
                # still volume remained after matching, meaning the price level is consumed out.
                # create level at this side at the order price
                order.volume = order_remain.volume
                self._remove_price_level(price, oppo_side)
                order.price = price
                this_quotes = self._create_price_level(order, side)
                quotes += this_quotes
            else:
                if orderlink.cum == 0:
                    self._remove_price_level(price, oppo_side)

        else:
            logging.info(f"Order ID: {order.order_id} - opposite side optimal order discarded, order book empty. ")

        return trades, quotes


    def handle_order_own_side_optimal(self, order: SubOrder) -> Tuple[Trade, Quote]:
        side = self._to_bid_ask_book(order.direction)
        trades = []
        quotes = []  
        price = self._get_best_price(side)
        orderlink = self._get_price_level(price, side)
        if orderlink is not None:
            this_quotes = orderlink.insert_order(order.to_minorder())
            quotes += this_quotes
        else:
            logging.info(f"Order ID: {order.order_id} - own side optimal order discarded, order book empty. ")

        return trades, quotes


    '''
    Handle active order below (without price), only has trade part, no order adding
    '''
    def handle_order_best_five(self, order: SubOrder) -> Tuple[Trade, Quote]:
        # copy attribute first in case they changed in other processes
        oppo_side = self._opposite_side(order.direction)
        trades = []
        quotes = []
        is_remained = True    
        
        order_remain = order.to_minorder()
        prices = list(self._get_top5_prices(oppo_side))

        # matching stage 
        for book_price in prices:     # match in top 5 prices in the opposite book
            orderlink = self._get_price_level(book_price, oppo_side)
            order_remain, this_trades, this_quotes = orderlink.match_order(order_remain)
            trades += this_trades
            quotes += this_quotes
            if order_remain.volume == 0:  
                # the order is all filled
                if orderlink.cum == 0:
                    self._remove_price_level(book_price, oppo_side)
                is_remained = False
                break
            else:
                # still volume remained, meaning the price level is empty now, remove it 
                self._remove_price_level(book_price, oppo_side)

        if is_remained:     
            # if still volume remained after matching
            pass # TODO can do remaining order cancel feedback?
            logging.info(f"Order ID: {order.order_id} - {OrderType.TOP_FIVE_INS_TRANS_REMAIN_CANCEL_ORDER} Not fully filled, withdraw the rest. ")

        return trades, quotes

    def handle_order_immediate_transact(self, order: SubOrder) -> Tuple[Trade, Quote]:
        # copy attribute first in case they changed in other processes
        oppo_side = self._opposite_side(order.direction)
        trades = []
        quotes = []
        is_remained = True    
        
        order_remain = order.to_minorder()
        prices = list(self._get_sorted_prices(oppo_side))

        # matching stage 
        for book_price in prices:     # match in top 5 prices in the opposite book
            orderlink = self._get_price_level(book_price, oppo_side)
            order_remain, this_trades, this_quotes = orderlink.match_order(order_remain)
            trades += this_trades
            quotes += this_quotes
            if order_remain.volume == 0:  
                # the order is all filled
                if orderlink.cum == 0:
                    self._remove_price_level(book_price, oppo_side)
                is_remained = False
                break
            else:
                # still volume remained, meaning the price level is empty now, remove it 
                self._remove_price_level(book_price, oppo_side)

        if is_remained:     
            # if still volume remained after matching
            logging.info(f"Order ID: {order.order_id} - {OrderType.IMMEDIATE_TRANS_REMAIN_CANCEL_ORDER} Not fully filled, withdraw the rest")
            pass # TODO can do remaining order cancel feedback?

        return trades, quotes

    def handle_order_full_deal(self, order: SubOrder) -> Tuple[Trade, Quote]:
        # copy attribute first in case they changed in other processes
        oppo_side = self._opposite_side(order.direction)
        trades = []
        quotes = []
        is_remained = True    
        
        order_remain = order.to_minorder()
        prices = list(self._get_sorted_prices(oppo_side))
        levels_to_remove = []

        # matching stage 
        for price in prices:     # match in top 5 prices in the opposite book
            orderlink = self._get_price_level(price, oppo_side)
            order_remain, this_trades, this_quotes = orderlink.match_order(order_remain)
            trades += this_trades
            quotes += this_quotes
            if order_remain.volume == 0:  
                # the order is all filled
                if orderlink.cum == 0:
                    levels_to_remove.append(price)
                is_remained = False
                break
            levels_to_remove.append(price)

        if is_remained:     
            # if still volume remained after matching
            trades = []
            quotes = []
            logging.info(f"Order ID: {order.order_id} - {OrderType.FULL_DEAL_OR_CANCEL_ORDER} Not fully filled, cancel the order")
        else:
            for p in levels_to_remove:         # update levels
                self._remove_price_level(p, oppo_side)

        return trades, quotes


    """
    TODO this part can rewrite in cython for further performance improment ?
    """
class MatchingEngine:
    """
    all matching operation is accomplished in this class
    multiplex by stock code in this level 
    * order id sorting
    * order checking (out of price range limit, volume>0, price>0, id>0)
    """
    def __init__(self, connect, path_close="data_test/100x10x10/price1.h5"):
        self.order_books = {}       # order book of different stocks
        self.next_order_id = {}
        self.order_queue = Queue()
        self.feed_queue = Queue()
        self.order_cache = {}   # list of dicts
        # data_file_path = 'data_test/100x10x10'
        # prev_price_path = data_file_path + '/'+ "price1.h5"
        price_mtx = h5py.File(path_close, 'r')['prev_close']
        self.flip_unit = 0.01
        self.limit = list(map(self._limit_calculate, price_mtx))

        self.connect = connect     # TODO TBA


    def _limit_calculate(self, close):
        upper = round(close*1.1, 2)
        lower = round(close*0.9, 2)
        upper = upper if upper > close+self.flip_unit else close+self.flip_unit 
        lower = lower if lower < close-self.flip_unit else close-self.flip_unit
        return upper, lower

    def _recv_order(self) -> Order:
        return self.connect.recv_order()

    def _send_feed(self, message: dict):
        self.connect.send_feed(message)

    def _check_order(self, order: Order):
        valid = True
        if order.order_id < 0: 
            logging.error(f"Order ID: {order.order_id} < 0")
            valid = False
        if order.volume < 0: 
            logging.error(f"Order ID: {order.order_id} - volume {order.volume} < 0")  # volume == 0 for void order indicating that the hook is not triggered
            valid = False
        if order.volume == 0: 
            logging.info(f"Order ID: {order.order_id} - volume == 0, is empty order")  # volume == 0 for void order indicating that the hook is not triggered
            valid = False
        if order.price <= 0: 
            logging.error(f"Order ID: {order.order_id} - price {order.price} <= 0")
            valid = False
        if order.type > 5: 
            logging.error(f"Order ID: {order.order_id} - invalid order type {order.type}")
            valid = False
        if order.type == OrderType.LIMIT_ORDER:
            if order.price > self.limit[order.stk_code-1][0] or order.price < self.limit[order.stk_code-1][1]:  # price range limit
                logging.warning(f"Order ID: {order.order_id} - price {order.price} exceeds limit {self.limit[order.stk_code-1]}")
                valid = False

        return valid 


    def _new_stock_symbol(self, stock):
        self.order_books[stock] = OrderBook(stock)
        self.next_order_id[stock] = 1
        self.order_cache[stock] = {}        # price -> Order

    def _store_trades(self, trades: List[Trade]):
        for t in trades:
            t.to_bytes()  #TODO

    def _put_queue_feeds(self, trades, quotes):
        self.feed_queue.put((trades, quotes))

    def _get_queue_feeds(self) -> Tuple[List[Trade], List[Quote]]:
        if not self.feed_queue.empty():
            return self.feed_queue.get()
        else: 
            return None, None

    def _put_queue_valid_order(self, order: Order):
        self.next_order_id[order.stk_code] += 1
        if self._check_order(order):               # if is valid order
            self.order_queue.put(order)
        else:
            logging.info(f"Order ID: {order.order_id} - order discarded")


    def _get_queue_valid_order(self):
        return self.order_queue.get(block=True)

    def _handle_order_all_stock_single_loop(self):
        while not self.order_queue.empty():
            order = self.order_queue.get()
            order_type = order.type 
            stock = order.stk_code
            logging.info(f"Order ID: {order.order_id} - {order_type} order executing")
            if order_type == OrderType.LIMIT_ORDER:
                trades, quotes = self.order_books[stock].handle_order_limit(order.to_suborder())
            elif order_type == OrderType.COUNTER_PARTY_BEST_PRICE_ORDER: 
                trades, quotes = self.order_books[stock].handle_order_counter_side_optimal(order.to_suborder())
            elif order_type == OrderType.OUR_BEST_PRICE_ORDER:
                trades, quotes = self.order_books[stock].handle_order_own_side_optimal(order.to_suborder())
            elif order_type == OrderType.TOP_FIVE_INS_TRANS_REMAIN_CANCEL_ORDER:
                trades, quotes = self.order_books[stock].handle_order_best_five(order.to_suborder())
            elif order_type == OrderType.IMMEDIATE_TRANS_REMAIN_CANCEL_ORDER:
                trades, quotes = self.order_books[stock].handle_order_immediate_transact(order.to_suborder())
            elif order_type == OrderType.FULL_DEAL_OR_CANCEL_ORDER:
                trades, quotes = self.order_books[stock].handle_order_full_deal(order.to_suborder())
            
            self._put_queue_feeds(trades, quotes)

    def serialize_main_run(self):
        """
        Without multiprocessing
        """
        while True:
            order = self._recv_order()
            if self.order_books.get(order.stk_code) is None:
                self._new_stock_symbol(order.stk_code)
            
            if order.order_id == self.next_order_id[order.stk_code]:        # if hit next order_id
                self._put_queue_valid_order(order)
                # if the next id has already been waiting in cache
                while self.order_cache[order.stk_code].get(self.next_order_id[order.stk_code]) is not None:
                    order = self.order_cache[order.stk_code].pop(self.next_order_id[order.stk_code]) 
                    self._put_queue_valid_order(order)
            elif order.order_id > self.next_order_id[order.stk_code]: 
                self.order_cache[order.stk_code][order.order_id] = order

            self._handle_order_all_stock_single_loop()

            while not self.feed_queue.empty():
                trades, quotes = self.feed_queue.get()
                if len(trades) !=0:
                    minlen = len(trades)
                    for i in range(minlen):
                        self._send_feed({'trade':trades[i], 'quote':quotes[i]})
                    for q in quotes[minlen:]:
                        self._send_feed({'quote':q})


    def update_order_queue_thread(self): #, order_queue: Queue, feed_queue: Queue):
        """
        Feed queue
        When a new order arrived, update the current order_id and put it into the queue if valid
        """
        # self.feed_queue = feed_queue
        # self.order_queue = order_queue

        while True:
            order = self._recv_order()
            if self.order_books.get(order.stk_code) is None:
                self._new_stock_symbol(order.stk_code)
            
            if order.order_id == self.next_order_id[order.stk_code]:        # if hit next order_id
                self._put_queue_valid_order(order)
                # if the next id has already been waiting in cache
                while self.order_cache[order.stk_code].get(self.next_order_id[order.stk_code]) is not None:
                    order = self.order_cache[order.stk_code].pop(self.next_order_id[order.stk_code]) 
                    self._put_queue_valid_order(order)
            else: 
                self.order_cache[order.stk_code][order.order_id] = order

            trades, quotes = self._get_queue_feeds()  # TODO improve message congestion blocking
            if len(trades) !=0:
                minlen = len(trades)
                for i in range(minlen):
                    self._send_feed({'trade':trades[i], 'quote':quotes[i]})
                for q in quotes[minlen:]:
                    self._send_feed({'quote':q})


    def handle_order_all_stocks_thread(self):
        """
        Consume queue
        Read reordered orders from the queue, and handle them according to order types
        """
        # self.feed_queue = feed_queue
        # self.order_queue = order_queue
        
        while True:
            order = self._get_queue_valid_order()
            order_type = order.type 
            stock = order.stk_code
            logging.info(f"Order ID: {order.order_id} - {order_type} order executing")
            if order_type == OrderType.LIMIT_ORDER:
                trades, quotes = self.order_books[stock].handle_order_limit(order.to_suborder())
            elif order_type == OrderType.COUNTER_PARTY_BEST_PRICE_ORDER: 
                trades, quotes = self.order_books[stock].handle_order_counter_side_optimal(order.to_suborder())
            elif order_type == OrderType.OUR_BEST_PRICE_ORDER:
                trades, quotes = self.order_books[stock].handle_order_own_side_optimal(order.to_suborder())
            elif order_type == OrderType.TOP_FIVE_INS_TRANS_REMAIN_CANCEL_ORDER:
                trades, quotes = self.order_books[stock].handle_order_best_five(order.to_suborder())
            elif order_type == OrderType.IMMEDIATE_TRANS_REMAIN_CANCEL_ORDER:
                trades, quotes = self.order_books[stock].handle_order_immediate_transact(order.to_suborder())
            elif order_type == OrderType.FULL_DEAL_OR_CANCEL_ORDER:
                trades, quotes = self.order_books[stock].handle_order_full_deal(order.to_suborder())
            
            self._put_queue_feeds(trades, quotes)


    def engine_main_thread(self):
        """
        start up threads here
        """
        process_list = []
        for i in range(1):
            p = Process(target=self.handle_order_all_stocks_thread, args=())
            process_list.append(p)

        p = Process(target=self.update_order_queue_thread, args=())
        process_list.append(p)

        for p in process_list:
            p.start()

        for p in process_list:
            p.join()




        

    