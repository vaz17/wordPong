import socket
import json
from _thread import start_new_thread
from config import SERVER_IP, PORT

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server = SERVER_IP
port = PORT

server_ip = socket.gethostbyname(server)

try:
    s.bind((server, port))
except socket.error as e:
    print("[BIND ERROR]", str(e))
    exit()

s.listen(2)
print("[SERVER STARTED] Waiting for connections on", server_ip, port)

positions = ["", ""]

def threaded_client(conn, player_id):
    print(f"[NEW CONNECTION] Player {player_id} connected.")
    conn.sendall(str(player_id).encode("utf-8"))

    while True:
        try:
            data = conn.recv(4096)
            if not data:
                print(f"[DISCONNECT] Player {player_id} disconnected.")
                break

            decoded = data.decode("utf-8")
            msg = json.loads(decoded)
            positions[player_id] = decoded

            other_id = 1 - player_id
            if positions[other_id] == "":
                reply = json.dumps({"id": other_id, "balls": [], "new": []})
            else:
                reply = positions[other_id]

            conn.sendall(reply.encode("utf-8"))

        except Exception as e:
            print(f"[ERROR] Player {player_id}: {e}")
            break

    positions[player_id] = ""  # Clear stored state
    conn.close()
    print(f"[CONNECTION CLOSED] Player {player_id}")

player_count = 0
while True:
    conn, addr = s.accept()
    if player_count >= 2:
        print(f"[REJECTED] Too many players: {addr}")
        conn.sendall(b"Server full")
        conn.close()
        continue

    print("[CONNECTED]", addr)
    start_new_thread(threaded_client, (conn, player_count))
    player_count += 1

