import gi
import signal
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
from config import MAX_HISTORY
from tracker import get_clipboard, ClipboardTracker
from app_ui import ClipboardHistoryApp

def main():
    # Handle Ctrl+C to quit GTK loop
    signal.signal(signal.SIGINT, lambda *args: Gtk.main_quit())

    tracker = ClipboardTracker(MAX_HISTORY)
    tracker.start()

    app = ClipboardHistoryApp(tracker)
    # connect tracker's callback to UI handler
    tracker.on_new_clip = app.on_new_clip
    app.show_all()

    Gtk.main()

if __name__ == "__main__":
    main()



    