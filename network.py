import socket
import json
from config import SERVER_IP, PORT


class Network:

    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = SERVER_IP # For this to work on your machine this must be equal to the ipv4 address of the machine running the server
                                    # You can find this address by typing ipconfig in CMD and copying the ipv4 address. Again this must be the servers
                                    # ipv4 address. This feild will be the same for all your clients.
        self.port = PORT
        self.addr = (self.host, self.port)
        self.id = self.connect()

    def connect(self):
        self.client.connect(self.addr)
        return self.client.recv(2048).decode()

    def send(self, data):
        try:
            self.client.sendall((data + "\n").encode())  # Send with newline delimiter

            # Wait until full message is received
            received = b""
            while not received.endswith(b"\n"):
                part = self.client.recv(2048)
                if not part:
                    break
                received += part

            return received.decode().strip()
        except Exception as e:
            print(f"[ERROR] Network send failed: {e}")
            return json.dumps({"balls": [], "new": []})
