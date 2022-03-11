from python.server.data_type import Order, MinOrder, Trade, OrderType, DirectionType, Quote
from python.server.data_type import OperationType, SubOrder
from typing import List, Dict, Tuple, Sequence

class BookBase:
    """
    For database based book caching
    """
    def __init__(self):
        pass

    def push_back():
        pass

    def pull_in():
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
            if volume_remain < 0:
                # Only when the link has rest orders, will it be update; 
                # Otherwise, nothing will change, it will be remove from the orderbook from outside
                volume_diff = link_order.volume+volume_remain
                link[i].volume = -volume_remain
                self.link = link[i:]        
                volume_remain = 0

                cum -= volume_diff
                self.cum = cum
                quote = Quote(self.stock, link_order.order_id, self.price, volume_diff, self.op_amend)
                if self.side: # is bid side
                    trade = Trade(self.stock, link_order.order_id, miniorder.order_id, self.price, volume_diff)
                else:
                    trade = Trade(self.stock, miniorder.order_id, link_order.order_id, self.price, volume_diff)
                quotes.append(quote)
                trades.append(trade)
            
            cum -= link_order.volume
            # TODO can cancel this branch for better performance?
            quote = Quote(self.stock, link_order.order_id, self.price, link_order.volume, self.op_remove)
            if self.side: # is bid side
                trade = Trade(self.stock, link_order.order_id, miniorder.order_id, self.price, link_order.volume)
            else:
                trade = Trade(self.stock, miniorder.order_id, link_order.order_id, self.price, link_order.volume)
            quotes.append(quote)
            trades.append(trade)

            if volume_remain == 0:
                break

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

        return trades, quotes


    def handle_order_own_side_optimal(self, order: SubOrder) -> Tuple[Trade, Quote]:
        side = self._to_bid_ask_book(order.direction)
        trades = []
        quotes = []  
        price = self._get_best_price(side)
        orderlink = self._get_price_level(price, side)
        this_quotes = orderlink.insert_order(order.to_minorder())
        quotes += this_quotes

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
                is_remained = False
                break
            else:
                # still volume remained, meaning the price level is empty now, remove it 
                self._remove_price_level(book_price, oppo_side)

        if is_remained:     
            # if still volume remained after matching
            pass # TODO can do remaining order cancel feedback?

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
                is_remained = False
                break
            else:
                # still volume remained, meaning the price level is empty now, remove it 
                self._remove_price_level(book_price, oppo_side)

        if is_remained:     
            # if still volume remained after matching
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
                is_remained = False
                break
            levels_to_remove.append(price)

        if is_remained:     
            # if still volume remained after matching
            trades = []
            quotes = []
            pass # TODO can do remaining order cancel feedback?
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
    """
    def __init__(self):
        self.order_books = {}       # order book of different stocks
        self.curr_order_id = 0
        self.curr_trade_id = 0
        print("test")

    "fun parameter is not determined, just for temporary"
    def handle_order(self, str_code, order_id, price, volume, direction):
        """
        Add an order
        :param str_code     股票的代码
        :order_id           order ID
        :param price        当前order的bid/ask的价格
        :param volume       当前order的bid/ask的数量
        :param direction    order是买入还是卖出        
        :return The order and the list of trades.
                Empty list if there is no matching.
        """
        pass
    def change_order(self, order_id, str_code):
        """
        Cancel order
        :param order_id     order ID
        :param str_code     股票代码
        :return The order if the cancellation is successful
        """
        pass

    