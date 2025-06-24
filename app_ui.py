import gi
import pyperclip
import subprocess
import signal
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
from config import MAX_HISTORY
from tracker import get_clipboard, ClipboardTracker

class ClipboardHistoryApp(Gtk.Window):
    def __init__(self, tracker: ClipboardTracker):
        super().__init__(title="Quick Paste")
        self.set_default_size(350, 450)
        self.set_border_width(10)
        self.tracker = tracker

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
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.connect("row-activated", self.on_row_activated)
        vbox.pack_start(self.listbox, True, True, 0)
        self.add(vbox)

        # Populate history if any
        for clip in self.tracker.get_history():
            self._add_clip_row(clip)

        # When window is hidden, free widgets (UI)
        self.connect("unmap", self._on_unmap)

    def _add_clip_row(self, text):
        # Display up to first 100 chars
        label = Gtk.Label(label=text[:100], xalign=0)
        row = Gtk.ListBoxRow()
        row.add(label)
        self.listbox.insert(row, 0)
        self.listbox.show_all()
        # Limit UI rows to max_history
        children = self.listbox.get_children()
        if len(children) > self.tracker.max_history:
            self.listbox.remove(self.listbox.get_row_at_index(self.tracker.max_history))

    def on_row_activated(self, listbox, row):
        idx = row.get_index()
        history = self.tracker.get_history()
        if idx < len(history):
            text = history[idx]
            pyperclip.copy(text)
            # hide UI
            self.hide()
            # ensure events processed
            while Gtk.events_pending():
                Gtk.main_iteration_do(False)
            # paste via xdotool
            subprocess.Popen(["xdotool", "type", "--clearmodifiers", "--delay", "0", text])


    def _on_unmap(self, widget):
        # destroy UI widgets only
        self.destroy()
        # tracker continues polling

    def on_new_clip(self, text):
        if self.is_visible():
            self._add_clip_row(text)
        return False  # not a timeout callback






