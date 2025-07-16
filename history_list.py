import json
import time
import socket

def get_history_list(prev_history, history_list, run_history_thread, HOST, PORT):
  
  while run_history_thread:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect((HOST, PORT))
            client.sendall(b"send array")
            buffer = b""
            while True:
                chunk = client.recv(1024)
                if not chunk:
                    break
                buffer += chunk
                if b"\n" in chunk:
                    break
            data = buffer.strip()

        history_list['items'] = json.loads(data.decode())

        if history_list['items'] != prev_history['items']:
            prev_history['items'] = history_list['items']
            GLib.idle_add(app.update_history_gui, history_list)

        time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nStopped by user.")
        break
    except Exception as e:
        print("Client error:", e)
        time.sleep(2)