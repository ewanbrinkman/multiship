import socket
from pickle import dumps, loads
from settings import *


class Network:
    def __init__(self, server_ip, port):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.settimeout(CONN_TIMEOUT)
        self.server_ip = server_ip
        self.server_port = port
        self.address = (self.server_ip, self.server_port)
        self.player = self.connect()

    def get_player(self):
        return self.player

    def connect(self):
        try:
            self.client.connect(self.address)
            return loads(self.client.recv(RECEIVE_LIMIT))
        except socket.error:
            print(f"Error Connecting To {self.server_ip}:{self.server_port}")

    def send(self, data):
        try:
            self.client.send(dumps(data))
            return loads(self.client.recv(RECEIVE_LIMIT))
        except EOFError:
            print("\nConnection Closed: Error Sending Data To The Server")
            return "Error: Error Sending Data To The Server"
        except ConnectionResetError:
            print("\nConnection Closed: Connection Was Reset")
            return "Error: Connection Was Reset"
        except socket.timeout:
            print("\nConnection Timed Out")
            return "Error: Connection Timed Out"
