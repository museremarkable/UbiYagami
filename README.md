# UbiYagami
## team-3 八神 使用说明文档

项目追踪文档：https://nbccadminedupl-my.sharepoint.com/:w:/g/personal/zhyile_x2_tn/EV8_97Iz3jFFiTMojmsVI-0BJgONqUFQzKDUzW1Ga0GCAA?e=W4CzkD

This project copnstructed an entire trading closed-loop exchange system, designing from the order placement on the trader side, to the network connecting protocol, then to the exchange matching engine. 

The behaviors of the trader side is contained in the code under the `./python/client` folder. The trader reads and sorts the huge size data, then converts it to a packed struct data stored in the memory. Secondly, to reduce to RAM usage, it uses a rolling window to read the order information from the sorted data so no matter how large the data is, the memory size remains the same. The final version of trader is `./python/client/client_multi_decoupled.py`. 

For the exchange side in `./python/server/server.py`, it contains three architectures which are respectively MatchingEngine, OrderBook, OrderLink in top down order. The OrderLink maintains the minimum size of orders sorted by their order ID, and does the  micro- matching operation. After each matching, it would return both the transaction and the orderbook reconstruction message to the higher level infrastructures. The OrderBook contains many levels of OrderLink each representing one price in either bid or ask side. It also completes the matching process in price level according to 6 different order types. Above that is the MatchingEngine, which receive orders from the connection part, then check and reorder the them before put them into another process doing matching in different OrderBooks of different stocks. 

The connecting protocol contains two parts. The server side for exchanges `./python/connection/connection.py` and the client side for traders `./python/connection/tcp_client,py`. They send orders from trader side and feedback the transaction **Trade** message and the order book reconstruction **Quote** message on top of the TCP protocol. The design makes use of the _asyncio_ method for non-blocking programming. And also take into consideration of switchable port number interface. 
