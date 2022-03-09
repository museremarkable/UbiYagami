'''heartbeat mechanism'''
KEEPALIVE_COUNTER = 200  # counter加到多少，就发一次keepalive
KEEPALIVE_THRESHOLD = 600  # 多少秒没收到keepalive，就说明这个exchagne下线了