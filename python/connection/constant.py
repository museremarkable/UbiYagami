'''heartbeat mechanism'''
KEEPALIVE_COUNTER = 200  # counter加到多少，就发一次keepalive
KEEPALIVE_THRESHOLD = 600  # 多少秒没收到keepalive，就说明这个exchagne下线了

EXCHANGE_IP = ['127.0.0.1']
TRADE_IP = ['127.0.0.1']
TCP_MAX_CONNECTION = 3
PORTS = [12341, 12342, 12343]
