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

def recv_all(conn):
    data = b""
    while not data.endswith(b"\n"):  # Wait for complete message ending in newline
        try:
            part = conn.recv(2048)
            if not part:
                break
            data += part
        except:
            break
    return data


def threaded_client(conn):
    global currentId, pos
    try:

        conn.send(str.encode(currentId))
        player_id = int(currentId)
        print(f"[INFO] Assigned player ID: {player_id}")
        currentId = "1" if currentId == "0" else "0"

        while True:
            try:
                data = recv_all(conn)
                if not data:
                    print("[INFO] Client disconnected gracefully")
                    break

                reply = data.decode('utf-8').strip()
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
                    try:
                        # Validate the peer's stored data
                        parsed = json.loads(pos[nid])
                        if "balls" not in parsed or "new" not in parsed:
                            raise ValueError("Missing keys")
                        reply = pos[nid]
                    except Exception as e:
                        print("[SERVER ERROR] Corrupt data for player", nid, ":", pos[nid])
                        print("[SERVER ERROR] Exception:", e)
                        reply = json.dumps({"id": nid, "balls": [], "new": []})


                conn.sendall((reply + "\n").encode())

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

