import gi
import signal
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
from config import MAX_HISTORY
import socket
import json
import threading
from get_clipboard import get_clipboard_function
import sys   

HOST = 'localhost'
PORT = 54321
MESSAGE = "Hello World!"

GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, Gtk.main_quit)

class ClipboardTracker:
    """
    Polls the X clipboard at regular intervals and notifies on changes.
    Keeps a history of clips up to max_history.
    """
    def __init__(self,poll_interval_ms=400):
        self.poll_interval_ms = poll_interval_ms
        self.history = []
        self.last_clip = None
        self.on_new_clip = None

    def _poll_clipboard(self):
        text = get_clipboard_function()
        if text and text != self.last_clip:
            self.last_clip = text
            self.history.insert(0, text)
            if len(self.history) > MAX_HISTORY:
                self.history.pop()
            if self.on_new_clip:
                # schedule UI update in GTK main thread
                GLib.idle_add(self.on_new_clip, text)
        # return True to keep the timeout active
        return True

    def start(self):
        # schedule the first poll
        GLib.timeout_add(self.poll_interval_ms, self._poll_clipboard)

tracker = ClipboardTracker()
tracker.start()

def run_server(server):
    with server:
        server.listen(10)
        print(f"Server listening on {HOST}:{PORT}")

        while True:
            try:
                conn, addr = server.accept()
                with conn:
                    request = conn.recv(1024).decode()
                    if request.strip() == "send array":
                        conn.sendall((json.dumps(tracker.history) + "\n").encode())
            except Exception as e:
                print(f"Server error: {e}")

# Attempt to bind — fail early if already in use
try:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
except OSError as e:
    print(f"Failed to bind to {HOST}:{PORT} — already in use?")
    sys.exit(1)

# Start server in background
threading.Thread(target=run_server, args=(server_socket,), daemon=True).start()

# Optional: print history periodically for debug
def print_history():
    print(tracker.history)
    return True

#GLib.timeout_add(500, print_history)  # every 5s

Gtk.main()
