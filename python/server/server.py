from data_type import Order, MinOrder, Trade, OrderType, DirectionType, Quote
from python.server.data_type import SubOrder
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
    The link list of orders under each price level
    """
    def __init__(self, orders: List[Order]):
        self.link = orders

    def match_order(self, miniorder: MinOrder) -> Tuple[MinOrder, Trade, Quote]:
        """
        Match order from lower order_id to higher until the size is all filled. 
        Otherwise, return the size remain to fill after consuming all the available orders on the link
        : param         miniorder       the mini order to fill in this orderlink
        : return1                       the remained miniorder after matching in this order link
        : return2                       list of transaction detail in Trade type
        : return3
        """
        pass
        remain = 0
        ls_trade = []
        ls_quote = []
        return remain, ls_trade, ls_quote

    def pre_match_order(self, miniorder: MinOrder) -> Tuple[MinOrder, Trade, Quote, List[Order]]:
        """
        Used for full deal, create a list of order after matching, 
        If all deal, this orderlink would be replaced outside with the one initiated by the list of orders created from here 
        : param         miniorder       the mini order to fill in this orderlink
        : return                        a list of orders used to initiate a new orderlink
        """
        pass


    def insert_order(self, minorder: MinOrder) -> List[Quote]:
        """
        for order type 
        LIMIT_ORDER, 
        OUR_BEST_PRICE_ORDER
        """
        pass

    def amend_order(self, miniorder: MinOrder, order_id, diff) -> List[Quote]:
        pass

    def cancel_order(self, miniorder: MinOrder, order_id) -> List[Quote]:
        pass

class OrderBook:
    """
    data structure to store record
    to be defined, just for demo , will write in altree ?
    """
    def __init__(self):
        self.levels = [{}, {}]
        self.sorted_prices = [[], []]
        self.best_prices = [10000000, 0]
        self.levels_locks = []

    def _opposite_side(self, direction: DirectionType) -> int:
        return 1 if direction == DirectionType.SELL else 0

    def _to_bid_ask_book(self, direction: DirectionType) -> int:
        """
        Interpret the bid/ask side from the order direction
        : param     direction   DirectionType, order direction
        : return    int, 0: ask, 1: bid
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

    def _create_price_level(self, order, bid_ask) -> List[Quote]:
        """
        Create a new OrderLink at the specified price level of the bid/ask book, and insert the order to the OrderLink;
        Update best price and price list
        : param     order       Order, to insert to the OrderLink in the bid/ask book
        : param     bid_ask     int, 0: ask, 1: bid
        : return                list of quote of ADD order
        """
        pass

    def _remove_price_level(self, price, bid_ask):
        """
        Delete the specified price level from the bid/ask book;
        Update best price and price list
        : param     price       float, specified price to get from the bid/ask book
        : param     bid_ask     int, 0: ask, 1: bid
        """
        pass

    def _change_price_level(self, price, order_list, bid_ask):
        """
        Replace the level with a new one, given a sorted list of orders 
        """
        self.levels[bid_ask][price] = OrderLink(order_list)


    def _get_price_level(self, price, bid_ask) -> OrderLink:
        """
        Get the orderLink of the specified price level
        : param     price       float, specified price to get from the bid/ask book
        : param     bid_ask     int, 0: ask, 1: bid
        : return                OrderLink
        """
        return OrderLink()
        pass
    
    def _get_sorted_prices(self, bid_ask ) -> list:
        """
        Get a list of price of the entire bid/ask book, sorted from best price to worse;
        : param     bid_ask     int, 0: ask, 1: bid
        return                  list of prices(float), sorted from best to worse  
        """
        pass

    def _get_top5_prices(self, bid_ask) -> list:
        """
        Get sorted top 5 optimal prices from self.bid_ask_sort_price
        : param     bid_ask     int, 0: ask, 1: bid
        : return                list of (float), length 5, sorted from best to worse  
        """
        pass

    def _get_best_price(self, bid_ask) -> float:
        """
        Get the best price of the bid/ask book
        : param     bid_ask     int, 0: ask, 1: bid
        : return                price(float)
        """
        pass

    '''
    Handle passive order below (with price), has trade part and book adding part
    '''
    def handle_order_limit(self, order: SubOrder) -> Tuple[Trade, Quote]:
        # copy attribute first in case they changed in other processes
        side = self._to_bid_ask_book(order.direction)
        oppo_side = self._opposite_side(order.direction)
        best_prices = self.best_prices
        sorted_prices = self.sorted_prices
        is_remained = True    
        order_remain = order.to_minorder()
        trades = []
        quotes = []

        if self._is_after(order.price, best_prices[oppo_side], oppo_side):
            # price in opposite side, can match first, then store the remainder if any 
            for book_price in sorted_prices[oppo_side]:     # match in available prices in the opposite book
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
        best_prices = self.best_prices
        order_remain = order.to_minorder()
        trades = []
        quotes = []  
        price = best_prices[oppo_side]

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
        best_prices = self.best_prices
        orderlink = self._get_price_level(best_prices[side], side)
        this_quotes = orderlink.insert_order(order.to_minorder())
        quotes += this_quotes

        return trades, quotes


    '''
    Handle active order below (without price), only has trade part
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
        prices = self.sorted_prices

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
        prices = self.sorted_prices
        changed_levels = {}

        # matching stage 
        for price in prices:     # match in top 5 prices in the opposite book
            orderlink = self._get_price_level(price, oppo_side)
            order_remain, this_trades, this_quotes, finallink = orderlink.pre_match_order(order_remain)
            trades += this_trades
            quotes += this_quotes
            changed_levels[price] = finallink
            if order_remain.volume == 0:  
                # the order is all filled
                for p, l in changed_levels:
                    if len(l) == 0:
                        self._remove_price_level(p, oppo_side)
                    else: 
                        self._change_price_level(p, l, oppo_side)
                is_remained = False
                break

        if is_remained:     
            # if still volume remained after matching
            pass # TODO can do remaining order cancel feedback?

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

    