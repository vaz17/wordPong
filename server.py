import socket
import json
from _thread import *
import sys
from config import SERVER_IP, PORT

# Server setup
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server = SERVER_IP
port = PORT

try:
    s.bind((server, port))
except socket.error as e:
    print(f"[ERROR] Failed to bind socket: {e}")
    sys.exit(1)

s.listen(2)
print(f"[INFO] Server listening on {server}:{port}")

currentId = "0"
pos = ["", ""]

def threaded_client(conn):
    global currentId, pos
    try:
        conn.send(str.encode(currentId))
        player_id = int(currentId)
        print(f"[INFO] Assigned player ID: {player_id}")
        currentId = "1" if currentId == "0" else "0"

        while True:
            try:
                data = conn.recv(2048)
                if not data:
                    print("[INFO] Client disconnected gracefully")
                    break

                reply = data.decode('utf-8')
                if not reply:
                    continue

                # Determine if message is JSON
                if reply.startswith("{"):
                    obj = json.loads(reply)
                    id = int(obj["id"])
                else:
                    arr = reply.split(":")
                    id = int(arr[0])

                pos[id] = reply
                nid = 1 if id == 0 else 0

                if pos[nid] == "":
                    reply = json.dumps({"id": nid, "balls": [], "new": []})
                else:
                    reply = pos[nid]

                conn.sendall(str.encode(reply))

            except Exception as e:
                print(f"[ERROR] Inner loop exception: {e}")
                break

    except Exception as e:
        print(f"[ERROR] Connection setup failed: {e}")

    print("[INFO] Closing connection")
    conn.close()

# Main loop
while True:
    try:
        conn, addr = s.accept()
        print(f"[INFO] Connected to: {addr}")
        start_new_thread(threaded_client, (conn,))
    except KeyboardInterrupt:
        print("\n[INFO] Server shutting down.")
        s.close()
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Accept failed: {e}")

