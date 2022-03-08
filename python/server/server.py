from data_type import Order, MinOrder, Trade, OrderType, DirectionType, Quote
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
    def __init__(self, orders: List[MinOrder], price, side, stock):
        self.stock = stock
        self.price = price  # price level this link is at
        self.side = side    # int, 0: ask, 1: bid

        self.link = orders  # orders are stored here
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



    def match_order(self, miniorder: MinOrder) -> Tuple[MinOrder, Trade, Quote, List[Order]]:
        """
        Match order from lower order_id to higher until the size is all filled. 
        Otherwise, return the size remains to fill after consuming all the available orders on the link
        : param         miniorder       the mini order to fill in this orderlink
        : return1                       the remained miniorder after matching in this order link
        : return2                       list of transaction detail in Trade type
        : return3
        : return        ls_order        list of Order, rest orders after matching
        """
        pass
        remain = 0
        ls_trade = []
        ls_quote = []
        return remain, ls_trade, ls_quote, ls_order
        

    def pre_match_order(self, miniorder: MinOrder) -> Tuple[MinOrder, Trade, Quote, List[Order]]:
        """
        Used for full deal, it doesn't create its link but create a list of order after matching, 
        If all deal, this orderlink would be replaced outside with the one initiated by the list of orders created from here 
        : param         miniorder       the mini order to fill in this orderlink
        : return                        a list of orders used to initiate a new orderlink
        """
        pass


    def insert_order(self, miniorder: MinOrder) -> List[Quote]:
        """
        insert an order to the link at the right place in order_id ascending order
        """
        self.cum += miniorder.volume
        loc = self._search_order_loc(miniorder.order_id)
        self.link.insert(loc, miniorder)

        operation = OperationType.NEW_BID if self.side else OperationType.NEW_ASK
        quotes = Quote(self.stock, miniorder.order_id, self.price, miniorder.volume, operation)
        return [quotes]


    def amend_order(self, miniorder: MinOrder, order_id, diff) -> List[Quote]:
        self.cum += miniorder.volume
        loc = self._search_order_loc(miniorder.order_id)
        self.link[loc].volume += miniorder.volume

        operation = OperationType.AMEND_BID if self.side else OperationType.AMEND_ASK
        quotes = Quote(self.stock, miniorder.order_id, self.price, miniorder.volume, operation)
        return [quotes]


    def cancel_order(self, miniorder: MinOrder, order_id) -> List[Quote]:
        self.cum += miniorder.volume
        loc = self._search_order_loc(miniorder.order_id)
        order_removed = self.link.pop(loc)
        
        operation = OperationType.REMOVE_BID if self.side else OperationType.REMOVE_ASK
        quotes = Quote(self.stock, order_removed.order_id, self.price, -order_removed.volume, operation)
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
        self.levels[order.price] = OrderLink([order.to_minorder()], order.price, bid_ask, self.stock)
        is_new_best = self._is_after(self._get_best_price(), order.price, bid_ask)
        if is_new_best:
            self.best_prices[bid_ask] = order.price

        if len(self.sorted_prices[bid_ask]) == 0:
            self.sorted_prices[bid_ask].append(order.price)
        else:
            for i, p in enumerate(self.sorted_prices[bid_ask]):
                if self._is_after(p, order.price, bid_ask):
                    break
            self.sorted_prices[bid_ask].insert(i, order.price)


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


    def _change_price_level(self, price, order_list, bid_ask):
        """
        Replace the level with a new one, given a sorted list of orders 
        """
        self.levels[bid_ask][price] = OrderLink(order_list, price, bid_ask, self.stock)


    def _get_price_level(self, price, bid_ask) -> OrderLink:
        """
        Get the orderLink of the specified price level
        : param     price       float, specified price to get from the bid/ask book
        : param     bid_ask     int, 0: ask, 1: bid
        : return                OrderLink
        """
        return self.levels[bid_ask][price]
        
    
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


    '''
    Handle passive order below (with price), has trade part and book adding part
    '''
    def handle_order_limit(self, order: SubOrder) -> Tuple[Trade, Quote]:
        # copy attribute first in case they changed in other processes
        side = self._to_bid_ask_book(order.direction)
        oppo_side = self._opposite_side(order.direction)
        oppo_best_price = self._get_best_price(oppo_side)
        sorted_prices = self._get_sorted_prices(oppo_side)
        is_remained = True    
        order_remain = order.to_minorder()
        trades = []
        quotes = []

        if self._is_after(order.price, oppo_best_price, oppo_side):
            # price in opposite side, can match first, then store the remainder if any 
            for book_price in sorted_prices:     # match in available prices in the opposite book
                orderlink = self._get_price_level(book_price, oppo_side)
                order_remain, this_trades, this_quotes = orderlink.match_order(order_remain)
                trades += this_trades
                quotes += this_quotes
                if order_remain.volume == 0:  
                    # the order is all filled
                    is_remained = False
                    break

                if self._is_after(book_price, order.price, side):   
                    # the order is filled till taking worse price
                    break

            if is_remained:     
                # if still volume remained after matching, create level at this side at the order price
                order.volume = order_remain.volume
                self._remove_price_level(order.price, oppo_side)
                self._create_price_level(order, side)

        else:
            # if price in the order side
            # put them into the book as a passive order
            orderlink = self._get_price_level(order.price, side)
            if orderlink is None:
                this_quotes = self._create_price_level(order, side)
            else:
                this_quotes = orderlink.add_order(order.to_minorder())
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
        prices = self._get_top5_prices(oppo_side)

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
        prices = self._get_sorted_prices(oppo_side)

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
        prices = self._get_sorted_prices(oppo_side) 
        changed_levels = {}

        # matching stage 
        for price in prices:     # match in top 5 prices in the opposite book
            orderlink = self._get_price_level(price, oppo_side)
            order_remain, this_trades, this_quotes, link_remain = orderlink.pre_match_order(order_remain)
            trades += this_trades
            quotes += this_quotes
            changed_levels[price] = link_remain
            if order_remain.volume == 0:  
                # the order is all filled
                is_remained = False
                break

        if is_remained:     
            # if still volume remained after matching
            trades = []
            quotes = []
            pass # TODO can do remaining order cancel feedback?
        else:
            for p, l in changed_levels:         # update levels
                if len(l) == 0:
                    self._remove_price_level(p, oppo_side)
                else: 
                    self._change_price_level(p, l, oppo_side)

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

    