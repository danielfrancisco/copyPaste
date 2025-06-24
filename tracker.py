import gi
import subprocess
import signal
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
from config import MAX_HISTORY

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
    def __init__(self, max_history, poll_interval_ms=500):
        self.max_history = max_history
        self.poll_interval_ms = poll_interval_ms
        self.history = []
        self.last_clip = None
        self.on_new_clip = None

    def _poll_clipboard(self):
        text = get_clipboard()
        if text and text != self.last_clip:
            self.last_clip = text
            self.history.insert(0, text)
            if len(self.history) > self.max_history:
                self.history.pop()
            if self.on_new_clip:
                # schedule UI update in GTK main thread
                GLib.idle_add(self.on_new_clip, text)
        # return True to keep the timeout active
        return True

    def start(self):
        # schedule the first poll
        GLib.timeout_add(self.poll_interval_ms, self._poll_clipboard)

    def get_history(self):
        return list(self.history)
