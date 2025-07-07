import gi
import subprocess
import signal
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
from config import MAX_HISTORY
import socket
import json

HOST = 'localhost'
PORT = 12345
MESSAGE = "Hello World!"

def get_clipboard():
    """
    Retrieve clipboard text synchronously using xclip.
    """
    try:
        result = subprocess.run(
            ['xclip', '-selection', 'clipboard', '-o'],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return None

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
        text = get_clipboard()
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

def print_history():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()
        print(f"Server listening on {HOST}:{PORT}")
        conn, addr = server.accept()

        with conn:
            print(f"Connected by {addr}")

            request = conn.recv(1024).decode()
            if request == "send array":
                json_data = json.dumps(tracker.history)  # convert list to JSON string
                conn.sendall(json_data.encode())
    
    return True  # keep this callback running repeatedly

GLib.timeout_add(500, print_history)  # print every 1 second
Gtk.main()







