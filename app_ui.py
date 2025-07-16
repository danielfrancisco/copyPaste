import gi
import pyperclip
import subprocess
import signal
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
from config import MAX_HISTORY
import pyperclip
import json
import socket
import json
import time
import threading

HOST = 'localhost'
PORT = 3000

previous_history = None

history_list = []

history_rows = []

run_history_thread = True

def get_history_list():
  global previous_history, history_list, run_history_thread
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

        history_list = json.loads(data.decode())

        if history_list != previous_history:
            previous_history = history_list
            GLib.idle_add(app.update_history_gui, history_list)

        time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nStopped by user.")
        break
    except Exception as e:
        print("Client error:", e)
        time.sleep(2)

history_list_thread = threading.Thread(target = get_history_list)
history_list_thread.start()

class ClipboardHistoryApp(Gtk.Window):
    def __init__(self,):
        super().__init__(title="Quick Paste")
        self.set_default_size(350, 450)
        
        # Load CSS styling
        css = Gtk.CssProvider()
        try:
            with open("main.css", "rb") as f:
                css.load_from_data(f.read())
                Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(),
                css,
                Gtk.STYLE_PROVIDER_PRIORITY_USER
            )
        except FileNotFoundError:
            pass

        # Layout
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        self.listbox = Gtk.ListBox()
        self.listbox.get_style_context().add_class("history_list")
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.connect("row-activated", self.on_row_activated)

        # Make sure the listbox can receive focus
        self.listbox.set_can_focus(True)
       
       # Create a ScrolledWindow
        scrolled_window = Gtk.ScrolledWindow()
        
        # No horizontal, vertical as needed
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)  

        # Make sure the scrolled window doesn't block focus
        scrolled_window.set_can_focus(False)

        # Add the listbox inside the scroll container
        scrolled_window.add(self.listbox)  
        
        vbox.pack_start(scrolled_window, True, True, 0)

        self.add(vbox)

        # Populate history if any
        for clip in history_list:
            self._add_clip_row(clip)

        # When window is hidden, free widgets (UI)
        self.connect("unmap", self._on_unmap)

    def _add_clip_row(self, text):
        # Display up to first 100 chars
        
        label = Gtk.Label(label=text[:100], xalign=0)
        history_rows.insert(0,text)
        row = Gtk.ListBoxRow()
        row.set_can_focus(True)  
        row.add(label)
        self.listbox.insert(row, 0)
        self.listbox.show_all()
        # Limit UI rows to max_history
        children = self.listbox.get_children()
        if len(children) > MAX_HISTORY :
            self.listbox.remove(self.listbox.get_row_at_index(MAX_HISTORY ))

    # Called from background thread via GLib.idle_add
    def update_history_gui(self, new_history):
        # Clear the old UI list
        self.listbox.foreach(lambda widget: self.listbox.remove(widget))
        for clip in reversed(new_history[-MAX_HISTORY:]):
            self._add_clip_row(str(clip))
        return False  # Return False to indicate one-time callback
    
    def on_row_activated(self, listbox, row):
        idx = row.get_index()
        history = history_rows
        
        if idx < len(history):
            text = history[idx]
            p = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
            p.communicate(input=text.encode('utf-8')) # Copy the text to clipboard

            self.hide() # hide UI
            # ensure events processed
            while Gtk.events_pending():
                Gtk.main_iteration_do(False)
            # paste via xdotool
            time.sleep(0.05)  # 50 ms pause
            subprocess.Popen(["xdotool", "key", "--clearmodifiers", "ctrl+shift+v"])
    
    def _on_unmap(self, widget):
        global run_history_thread
        run_history_thread = False  # Stop the thread loop

        Gtk.main_quit()  # Stop GTK main loop
        print("Application exited cleanly.")


    def on_new_clip(self, text):
        if self.is_visible():
            self._add_clip_row(text)
        return False  # not a timeout callback

app = ClipboardHistoryApp()

app.show_all()

Gtk.main()

