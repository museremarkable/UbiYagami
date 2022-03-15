from data_type import *

def order_comp(o1: Order, o2: Order):
	comp = [o1.stk_code != o2.stk_code,
            o1.order_id != o2.order_id,
			o1.volume != o2.volume,
            o1.direction != o2.direction,
            o1.type != o2.type,
            o1.price != o2.price
            ]
	return sum(comp)

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
     