import socket
import json
from _thread import *
import sys

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server = 'localhost'
port = 5555

server_ip = socket.gethostbyname(server)

try:
    s.bind((server, port))

except socket.error as e:
    print(str(e))

s.listen(2)
print("Waiting for a connection")

currentId = "0"
pos = ["", ""]
def threaded_client(conn):
    global currentId, pos
    conn.send(str.encode(currentId))
    currentId = "1"
    reply = ''
    while True:
        try:
            data = conn.recv(2048)
            reply = data.decode('utf-8')
            if not data:
                conn.send(str.encode("Goodbye"))
                break
            else:
                print("Recieved: " + reply)
                arr = reply.split(":")
                id = int(arr[0]) if reply.startswith("{") is False else int(json.loads(reply)["id"])
                pos[id] = reply  # Store full JSON

                nid = 1 if id == 0 else 0
                if pos[nid] == "":
                    reply = json.dumps({"id": nid, "balls": []})
                else:
                    reply = pos[nid][:]

                print("Sending: " + reply)

            conn.sendall(str.encode(reply))
        except Exception as e:
            print("Fail:", e)
            break

    print("Connection Closed")
    conn.close()

while True:
    conn, addr = s.accept()
    print("Connected to: ", addr)

    start_new_thread(threaded_client, (conn,))
