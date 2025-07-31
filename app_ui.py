
import gi
import pyperclip
import subprocess
import signal
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
from config import MAX_HISTORY
import pyperclip
import json
import time
import os
import threading
from history_list import get_history_list, run_event

HOST = 'localhost'
PORT = 54321

prev_history = {'items':None}

history_list = {'items':[]}

history_rows = []

class ClipboardHistoryApp(Gtk.Window):
    def __init__(self,):
        super().__init__(title="copyPaste")
        self.set_default_size(300, 450)
        
        # Load CSS styling
        css = Gtk.CssProvider()

        # Get absolute path to main.css, regardless of working directory
        css_file = os.path.join(os.path.dirname(__file__), "main.css")

        try:
            with open(css_file, "rb") as f:
                css.load_from_data(f.read())
                Gtk.StyleContext.add_provider_for_screen(
                    Gdk.Screen.get_default(),
                    css,
                    Gtk.STYLE_PROVIDER_PRIORITY_USER
                )
        except Exception as e:
         print(f"Failed to load CSS: {e}")

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
            self.listbox.remove(self.listbox.get_row_at_index(MAX_HISTORY))
    
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
        run_event.clear()  # Signal thread to stop
        Gtk.main_quit()  # Stop GTK main loop
        print("Application exited cleanly.")
    
    def on_new_clip(self, text):
        if self.is_visible():
            self._add_clip_row(text)
        return False  # not a timeout callback

app = ClipboardHistoryApp()

history_list_thread = threading.Thread(target = get_history_list,args=(prev_history, history_list, HOST, PORT,app))

history_list_thread.start()

app.show_all()

Gtk.main()

