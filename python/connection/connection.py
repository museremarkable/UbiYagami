class ServerTCP:
    def __init__(self):
        self.binding_ports = [100, 101, 102]
        
    def server_connection(self):
        "receive order from client , send result to two client"
        pass

class ClientTCP:
    def __init__(self):
        self.ip_address = ["",""]
        self.binding_ports = [100, 101, 102]
        "0 is normal, differnet number corresponding different stastus"
        self.ports_status = [0, 0, 0]
    def client_connection(self):
        "send order to two exchanger? "
        pass
