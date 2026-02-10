# ============================================================
# OBS WINDOW SCREENSHOT TOOL (Windows + Tkinter)
# ------------------------------------------------------------
# - 6 tabs (profiles), each with independent settings + config file
# - Press Start to begin auto-check at configured frequency
# - Press Stop to pause checking
# - If match: increment a number in a selected .txt file
# - Cooldown after a match before checking again
# - Load/save settings from per-profile config files
# - Shows current count and running status in UI
# - No screenshot file is saved (in-memory compare only)
# - Manual +/- buttons to increment/decrement by 1
# - Configurable sliders in a Configure window
# - Editable profile names (tab titles)
# - Test image button with live detection + confidence
# - Barebones RPC broadcast integration per profile
# ============================================================

# =========================
# IMPORTS
# =========================
import os
import sys
import time
import ctypes
import threading
import json
import webbrowser
import tkinter as tk
import tkinter.font as tkfont
from ctypes import wintypes
from tkinter import messagebox, filedialog, ttk, simpledialog
from PIL import Image, ImageTk, ImageSequence, ImageDraw

try:
    from pypresence import Presence
except Exception:
    Presence = None

try:
    import keyboard
except Exception:
    keyboard = None

try:
    import winsound
except Exception:
    winsound = None

import cv2
import numpy as np


# =========================
# THEME
# =========================
# Dark mode colors
DARK_BG = "#1e1e1e"
DARK_FG = "#e6e6e6"
DARK_ACCENT = "#2d2d2d"
DARK_BUTTON = "#3a3a3a"
DARK_BORDER = "#444444"
DARK_HOTKEY_WAIT_BG = "#4a4a4a"
LINK_COLOR = "#4a90e2"  # Blue color for clickable links

HOTKEY_WAIT_BG = DARK_HOTKEY_WAIT_BG

BUTTON_PADX = 12
BUTTON_PADY = 0
BUTTON_HEIGHT = 1
COUNTER_BUTTON_HEIGHT = 1

# Standard button sizing for consistent UI (420px wide buttons)
STANDARD_BUTTON_WIDTH_PX = 420  # Target pixel width for standard buttons
STANDARD_BUTTON_IPADX = 186     # Internal padding to achieve 420px width
STANDARD_BUTTON_PADY = (2, 2)   # Vertical padding (2px top, 2px bottom)

FONT_NAME = "Pokémon DP Pro Regular"
FONT_FILENAME = "pokemon-dp-pro.ttf"
FR_PRIVATE = 0x10
BASE_FONT_SIZE = 18
LARGE_FONT_SIZE = 24
SMALL_BUTTON_FONT_SIZE = 16
TAB_FONT_SIZE = BASE_FONT_SIZE + 2
RPC_ICON_SIZE = 24
PROFILE_NAME_MAX_LENGTH = 12
MIN_INCREMENT = 1
MAX_INCREMENT = 99
GIF_SPEED_FACTOR = 0.5  # play at ~50% of original GIF speed
START_ACTIVE_COLOR = "#f49269"
ALERT_COOLDOWN_SECONDS = 0.2


def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def register_font(font_path):
    if not os.path.isfile(font_path):
        return False
    return ctypes.windll.gdi32.AddFontResourceExW(font_path, FR_PRIVATE, 0) > 0


def apply_dark_theme(root):
    """Apply dark theme to root window"""
    root.configure(bg=DARK_BG)
    root.option_add("*Background", DARK_BG)
    root.option_add("*Foreground", DARK_FG)
    root.option_add("*Button.Background", DARK_BUTTON)
    root.option_add("*Button.Foreground", DARK_FG)
    root.option_add("*Entry.Background", DARK_ACCENT)
    root.option_add("*Entry.Foreground", DARK_FG)
    root.option_add("*Entry.InsertBackground", DARK_FG)
    root.option_add("*Entry.Justify", "left")
    root.option_add("*Checkbutton.Background", DARK_BG)
    root.option_add("*Checkbutton.Foreground", DARK_FG)
    root.option_add("*Checkbutton.ActiveBackground", DARK_BG)
    root.option_add("*Checkbutton.ActiveForeground", DARK_FG)
    root.option_add("*Checkbutton.SelectColor", DARK_ACCENT)
    root.option_add("*Checkbutton.HighlightThickness", 0)
    root.option_add("*Checkbutton.BorderWidth", 0)
    root.option_add("*Checkbutton.Relief", "flat")
    root.option_add("*Checkbutton.HighlightBackground", DARK_BG)
    root.option_add("*Checkbutton.HighlightColor", DARK_BG)
    root.option_add("*Label.Background", DARK_BG)
    root.option_add("*Label.Foreground", DARK_FG)
    root.option_add("*Scale.Background", DARK_BG)
    root.option_add("*Scale.Foreground", DARK_FG)
    root.option_add("*Listbox.Background", DARK_ACCENT)
    root.option_add("*Listbox.Foreground", DARK_FG)
    root.option_add("*Font", (FONT_NAME, BASE_FONT_SIZE))
    # Make all button text bold globally
    root.option_add("*Button.font", (FONT_NAME, BASE_FONT_SIZE, "bold"))

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TFrame", background=DARK_BG)
    style.configure("TLabel", background=DARK_BG, foreground=DARK_FG)
    style.configure(
        "TNotebook",
        background=DARK_BG,
        bordercolor=DARK_BUTTON,
        lightcolor=DARK_BUTTON,
        darkcolor=DARK_BUTTON,
        borderwidth=1,
        padding=0,
        tabmargins=(0, 0, 0, 0)
    )
    style.layout("TNotebook", [("Notebook.client", {"sticky": "nswe"})])
    style.configure(
        "TNotebook.Tab",
        background="#0f0f0f",
        foreground="#9a9a9a",
        font=(FONT_NAME, TAB_FONT_SIZE),
        borderwidth=1,
        bordercolor=DARK_BUTTON,
        lightcolor=DARK_BUTTON,
        darkcolor=DARK_BUTTON,
        focuscolor=DARK_BUTTON,
        padding=[10, 4, 15, 4]
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", DARK_BG)],
        foreground=[("selected", DARK_FG)],
        bordercolor=[("selected", DARK_BUTTON)],
        lightcolor=[("selected", DARK_BUTTON)],
        darkcolor=[("selected", DARK_BUTTON)],
        focuscolor=[("selected", DARK_BUTTON)],
        padding=[("selected", [10, 4, 15, 4])]
    )
    style.configure("TButton", background=DARK_BUTTON, foreground=DARK_FG)
    style.map("TButton", background=[("active", "#606060")])
    style.configure(
        "Treeview",
        background=DARK_ACCENT,
        fieldbackground=DARK_ACCENT,
        foreground=DARK_FG
    )
    style.configure("Treeview.Heading", background=DARK_BUTTON, foreground=DARK_FG)
    style.configure(
        "AlertSound.Treeview",
        rowheight=36,
        background=DARK_ACCENT,
        fieldbackground=DARK_ACCENT,
        foreground=DARK_FG,
        font=(FONT_NAME, BASE_FONT_SIZE + 1),
        selectbackground=START_ACTIVE_COLOR,
        selectforeground=DARK_FG
    )
    style.map(
        "AlertSound.Treeview",
        background=[("selected", START_ACTIVE_COLOR)],
        foreground=[("selected", DARK_FG)],
        fieldbackground=[("selected", START_ACTIVE_COLOR)]
    )
    style.configure(
        "TScrollbar",
        background=DARK_BUTTON,
        troughcolor=DARK_BG,
        arrowcolor=DARK_FG
    )


# --- Drag guard helpers (prevent dragging when interacting with inputs) ---
INTERACTIVE_DRAG_WIDGETS = (
    tk.Entry, ttk.Entry,
    tk.Text,
    tk.Listbox,
    tk.Canvas,  # Added to prevent drag interference with Pokemon selection
    tk.Scale,
    ttk.Combobox,
    ttk.Treeview,
    ttk.Scrollbar,
    tk.Checkbutton, ttk.Checkbutton,
    tk.Button, ttk.Button,
    tk.Spinbox,
)

def is_interactive_widget(widget):
    return isinstance(widget, INTERACTIVE_DRAG_WIDGETS)

def get_widget_under_cursor(event):
    # First check if event.widget itself is interactive - most reliable
    if hasattr(event.widget, 'winfo_class') and is_interactive_widget(event.widget):
        return event.widget
    
    # Handle case where event.widget might be a string (e.g., from Combobox)
    if not hasattr(event.widget, 'winfo_containing'):
        return event.widget
    
    # Fallback to winfo_containing for other cases
    widget = event.widget.winfo_containing(event.x_root, event.y_root)
    return widget or event.widget

def is_interactive_click(event):
    """Check if click event is on an interactive widget."""
    widget = get_widget_under_cursor(event)
    return is_interactive_widget(widget)


def install_unfocus_on_click(root_window):
    def on_click(event):
        target = get_widget_under_cursor(event)
        if not is_interactive_widget(target):
            # Only call widget methods if target is actually a widget
            if hasattr(target, 'winfo_toplevel'):
                target.winfo_toplevel().focus_set()
    root_window.bind_all("<Button-1>", on_click, add="+")


def set_window_disabled(window, disabled):
    if not window or not window.winfo_exists():
        return
    try:
        window.attributes("-disabled", disabled)
    except Exception:
        pass
    state = "disabled" if disabled else "normal"

    def apply_state(widget):
        try:
            widget.configure(state=state)
        except Exception:
            pass
        for child in widget.winfo_children():
            apply_state(child)

    apply_state(window)


# =========================
# PATHS
# =========================
SCRIPT_FOLDER = os.path.dirname(os.path.abspath(__file__))
RPC_CONFIG_FOLDER = os.path.join(SCRIPT_FOLDER, "rpc_config")
REFERENCES_FOLDER = os.path.join(SCRIPT_FOLDER, "references")
HOTKEYS_CONFIG_PATH = os.path.join(SCRIPT_FOLDER, "hotkeys_config.txt")
UI_CONFIG_PATH = os.path.join(SCRIPT_FOLDER, "ui_config.txt")
ALERTS_AUDIO_FOLDER = os.path.join(SCRIPT_FOLDER, "assets", "audio")
ICON_PATH = os.path.join(SCRIPT_FOLDER, "assets", "rotom", "main", "main_icon.ico")
FONT_PATH = resource_path(os.path.join("fonts", FONT_FILENAME))
ICON_RPC_INACTIVE_PATH = resource_path(os.path.join("assets", "rotom", "rpc", "icon_rpc_inactive.png"))
ICON_RPC_ENABLED_PATH = resource_path(os.path.join("assets", "rotom", "rpc", "icon_rpc_enabled.png"))
ICON_RPC_ACTIVE_PATH = resource_path(os.path.join("assets", "rotom", "rpc", "icon_rpc_active.gif"))
ICON_COUNT_INACTIVE_PATH = resource_path(os.path.join("assets", "rotom", "count", "icon_count_inactive.png"))
ICON_COUNT_ENABLED_PATH = resource_path(os.path.join("assets", "rotom", "count", "icon_count_enabled.png"))
ICON_COUNT_ACTIVE_PATH = resource_path(os.path.join("assets", "rotom", "count", "icon_count_active.gif"))
ICON_AUDIO_INACTIVE_PATH = resource_path(os.path.join("assets", "rotom", "audio", "icon_audio_inactive.png"))
ICON_AUDIO_ENABLED_PATH = resource_path(os.path.join("assets", "rotom", "audio", "icon_audio_active.png"))
ICON_AUDIO_ACTIVE_PATH = resource_path(os.path.join("assets", "rotom", "audio", "icon_audio_active.gif"))
ICON_COUNT_ERROR_PATH = resource_path(os.path.join("assets", "rotom", "count", "icon_count_error.png"))
ICON_RPC_ERROR_PATH = resource_path(os.path.join("assets", "rotom", "count", "icon_rpc_error.png"))
ICON_RESET_PATH = resource_path(os.path.join("assets", "ui", "reset.png"))

# UI Audio Paths
UI_SOUND_START_PATH = resource_path(os.path.join("assets", "ui_audio", "start.wav"))
UI_SOUND_STOP_PATH = resource_path(os.path.join("assets", "ui_audio", "stop.wav"))
UI_SOUND_ERROR_PATH = resource_path(os.path.join("assets", "ui_audio", "error.wav"))

os.makedirs(RPC_CONFIG_FOLDER, exist_ok=True)
os.makedirs(REFERENCES_FOLDER, exist_ok=True)
os.makedirs(ALERTS_AUDIO_FOLDER, exist_ok=True)


# =========================
# HOTKEY DEFAULTS
# =========================
DEFAULT_HOTKEYS = {
    "start_stop": "F1",
    "capture": "F2",
}


# =========================
# GLOBALS
# =========================
ACTIVE_BROADCAST_PROFILE = None
hotkey_manager = None
RUN_BADGE_IMG = None
TOOLTIP_ENABLED = True
TOOLTIP_ENABLED_KEY = "tooltips_enabled:"


# =========================
# RPC COUNTER OPTIONS
# =========================
CONFIG_KEY_RPC_SUFFIX = "rpc_counter_suffix:"
RPC_COUNTER_OPTIONS = [
    ("Soft Reset", "SRs"),
    ("Random Encounter", "REs"),
    ("Run Away", "RAs"),
    ("Breeding", "Hatched"),
    ("Default / Other", "Encounters"),
]


# =========================
# WINDOW ICON + TITLE
# =========================

def build_run_badge(size=10, color=START_ACTIVE_COLOR):
    img = tk.PhotoImage(width=size, height=size)
    img.put(color, to=(0, 0, size-1, size-1))
    return img

# New helper: build circular tab badges (filled or hollow)
def build_tab_badge(size=12, color=START_ACTIVE_COLOR, filled=True, outline_width=None):
    """
    Build a circular badge as a Tk PhotoImage using PIL.
    - size: diameter in pixels
    - color: fill or outline color
    - filled: True => filled circle; False => hollow circle (transparent inside)
    - outline_width: thickness for hollow circle outline; defaults to size//6
    """
    if outline_width is None:
        outline_width = max(1, size // 6)

    # Create transparent image
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    padding = outline_width // 2 + 1
    bbox = (padding, padding, size - padding - 1, size - padding - 1)

    if filled:
        draw.ellipse(bbox, fill=color)
    else:
        # Hollow: draw an outer ellipse with transparent fill and colored outline
        draw.ellipse(bbox, outline=color, width=outline_width)

    return ImageTk.PhotoImage(img)


def apply_window_style(window, title="RotomCamRPC"):
    window.title(title)
    try:
        if os.path.isfile(ICON_PATH):
            window.iconbitmap(ICON_PATH)
    except Exception:
        pass


def open_hotkeys_window(parent_grab=None, profile=None):
    if hotkey_manager is None:
        return

    win = tk.Toplevel(root)
    apply_window_style(win)
    win.resizable(False, False)
    win.transient(root)
    win.grab_set()

    hotkey_manager.suspend()

    if parent_grab and parent_grab.winfo_exists():
        set_window_disabled(parent_grab, True)

    if profile:
        profile._enter_modal(win)

    container = tk.Frame(win, bg=DARK_BG)
    container.pack(padx=12, pady=12)

    entries = {}

    def build_event_hotkey(event):
        modifiers = []
        if event.state & 0x0004:
            modifiers.append("Ctrl")
        if event.state & 0x0001:
            modifiers.append("Shift")
        if event.state & 0x0008:
            modifiers.append("Alt")

        key = event.keysym
        if len(key) == 1:
            key = key.upper()
        else:
            key = key.upper() if key.lower().startswith("f") and key[1:].isdigit() else key.title()

        return "+".join(modifiers + [key]) if modifiers or key else ""

    def set_readonly_text(entry, value):
        entry.config(state="normal")
        entry.delete(0, tk.END)
        entry.insert(0, value)
        entry.config(state="readonly")

    def set_waiting_state(entry, waiting):
        entry.configure(readonlybackground=HOTKEY_WAIT_BG if waiting else DARK_ACCENT)

    def add_row(row, label_text, key):
        tk.Label(container, text=label_text).grid(row=row, column=0, sticky="w", pady=4)
        entry = tk.Entry(container, width=20, state="readonly")
        entry.grid(row=row, column=1, padx=8, pady=4, sticky="w")
        entry.configure(readonlybackground=DARK_ACCENT)
        set_readonly_text(entry, hotkey_manager.hotkeys.get(key, ""))
        entries[key] = entry

        def capture_hotkey(event):
            new_hotkey = normalize_hotkey_display(build_event_hotkey(event))
            set_readonly_text(entry, new_hotkey)
            set_waiting_state(entry, False)
            return "break"

        def clear_hotkey(_event):
            set_readonly_text(entry, "")
            set_waiting_state(entry, False)

        def on_focus_in(_event):
            set_waiting_state(entry, True)

        def on_focus_out(_event):
            set_waiting_state(entry, False)

        def on_click(_event):
            entry.focus_set()
            set_waiting_state(entry, True)

        entry.bind("<KeyPress>", capture_hotkey)
        entry.bind("<Escape>", clear_hotkey)
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        entry.bind("<Button-1>", on_click)

    profile_name = profile.profile_name_var.get().strip() if profile else ""
    profile_label = profile_name or (profile.default_tab_name if profile else "Profile")

    tk.Label(container, text="Global:", font=(FONT_NAME, BASE_FONT_SIZE, "bold")).grid(
        row=0, column=0, columnspan=2, sticky="w", pady=(0, 4)
    )
    tk.Label(
        container,
        text="(Press escape to unbind hotkeys)",
        fg=DARK_FG,
        bg=DARK_BG,
        font=(FONT_NAME, BASE_FONT_SIZE - 2)
    ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 6))

    add_row(2, "Start / Stop:", "start_stop")
    add_row(3, "Capture:", "capture")

    global_var = tk.BooleanVar(value=hotkey_manager.global_enabled)
    global_check = tk.Checkbutton(
        container,
        text="Enable hotkeys while minimized",
        variable=global_var,
        takefocus=0
    )
    global_check.grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 4))

    if keyboard is None:
        global_check.config(state="disabled")
        tk.Label(
            container,
            text="Install the 'keyboard' package to enable global hotkeys.",
            fg="#d46a6a"
        ).grid(row=5, column=0, columnspan=2, sticky="w")

    tk.Label(container, text=f"{profile_label}:", font=(FONT_NAME, BASE_FONT_SIZE, "bold")).grid(
        row=6, column=0, columnspan=2, sticky="w", pady=(8, 4)
    )

    profile_count_plus = profile.count_plus_hotkey if profile else ""
    profile_count_minus = profile.count_minus_hotkey if profile else ""

    tk.Label(container, text="+ Count:").grid(row=7, column=0, sticky="w", pady=4)
    count_plus_entry = tk.Entry(container, width=20, state="readonly")
    count_plus_entry.grid(row=7, column=1, padx=8, pady=4, sticky="w")
    count_plus_entry.configure(readonlybackground=DARK_ACCENT)
    set_readonly_text(count_plus_entry, profile_count_plus)

    tk.Label(container, text="- Count:").grid(row=8, column=0, sticky="w", pady=4)
    count_minus_entry = tk.Entry(container, width=20, state="readonly")
    count_minus_entry.grid(row=8, column=1, padx=8, pady=4, sticky="w")
    count_minus_entry.configure(readonlybackground=DARK_ACCENT)
    set_readonly_text(count_minus_entry, profile_count_minus)

    def bind_profile_hotkey(entry):
        def capture_hotkey(event):
            new_hotkey = normalize_hotkey_display(build_event_hotkey(event))
            set_readonly_text(entry, new_hotkey)
            set_waiting_state(entry, False)
            return "break"

        def clear_hotkey(_event):
            set_readonly_text(entry, "")
            set_waiting_state(entry, False)

        def on_focus_in(_event):
            set_waiting_state(entry, True)

        def on_focus_out(_event):
            set_waiting_state(entry, False)

        def on_click(_event):
            entry.focus_set()
            set_waiting_state(entry, True)

        entry.bind("<KeyPress>", capture_hotkey)
        entry.bind("<Escape>", clear_hotkey)
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        entry.bind("<Button-1>", on_click)

    bind_profile_hotkey(count_plus_entry)
    bind_profile_hotkey(count_minus_entry)

    # Track initial state for change detection
    initial_hotkeys = {key: entry.get() for key, entry in entries.items()}
    initial_global_enabled = global_var.get()
    initial_count_plus = count_plus_entry.get()
    initial_count_minus = count_minus_entry.get()

    def check_for_changes():
        """Check if any hotkey settings have changed"""
        # Check global hotkeys
        for key, entry in entries.items():
            if entry.get() != initial_hotkeys[key]:
                return True
        # Check global enabled checkbox
        if global_var.get() != initial_global_enabled:
            return True
        # Check profile hotkeys
        if profile:
            if count_plus_entry.get() != initial_count_plus:
                return True
            if count_minus_entry.get() != initial_count_minus:
                return True
        return False

    def update_apply_button_color():
        """Update Apply button color based on whether changes exist"""
        if check_for_changes():
            apply_button.config(bg=START_ACTIVE_COLOR, activebackground=START_ACTIVE_COLOR)
        else:
            apply_button.config(bg=DARK_BUTTON, activebackground=DARK_BUTTON)

    def apply_changes():
        new_hotkeys = {}
        for key, entry in entries.items():
            new_hotkeys[key] = normalize_hotkey_display(entry.get().strip())

        hotkey_manager.set_global_enabled(global_var.get())
        hotkey_manager.set_hotkeys(new_hotkeys)
        save_hotkeys_config(hotkey_manager.hotkeys, hotkey_manager.global_enabled)

        if profile:
            profile.set_count_hotkeys(
                normalize_hotkey_display(count_plus_entry.get().strip()),
                normalize_hotkey_display(count_minus_entry.get().strip())
            )

        hotkey_manager.resume()
        hotkey_manager.register_local_hotkeys()
        hotkey_manager.refresh_profile_hotkeys()
        if parent_grab and parent_grab.winfo_exists():
            set_window_disabled(parent_grab, False)
            parent_grab.grab_set()
            parent_grab.focus_force()
        if profile:
            profile._exit_modal()
        win.destroy()

    def on_close():
        hotkey_manager.resume()
        hotkey_manager.register_local_hotkeys()
        hotkey_manager.refresh_profile_hotkeys()
        if parent_grab and parent_grab.winfo_exists():
            set_window_disabled(parent_grab, False)
            parent_grab.grab_set()
            parent_grab.focus_force()
        if profile:
            profile._exit_modal()
        win.destroy()

    button_row = tk.Frame(win, bg=DARK_BG)
    button_row.pack(padx=12, pady=(0, 12), fill="x")

    button_row.grid_columnconfigure(0, weight=1)
    button_row.grid_columnconfigure(1, weight=1)

    apply_button = tk.Button(
        button_row,
        text="Apply",
        command=apply_changes,
        padx=BUTTON_PADX,
        pady=BUTTON_PADY,
        height=BUTTON_HEIGHT
    )
    apply_button.grid(row=0, column=0, padx=(0, 8), sticky="e")
    
    tk.Button(
        button_row,
        text="Close",
        command=on_close,
        padx=BUTTON_PADX,
        pady=BUTTON_PADY,
        height=BUTTON_HEIGHT
    ).grid(row=0, column=1, padx=(8, 0), sticky="w")

    # Bind change detection to all entries
    for entry in entries.values():
        entry.bind("<KeyRelease>", lambda e: update_apply_button_color())
    count_plus_entry.bind("<KeyRelease>", lambda e: update_apply_button_color())
    count_minus_entry.bind("<KeyRelease>", lambda e: update_apply_button_color())
    global_var.trace_add("write", lambda *args: update_apply_button_color())

    # Initial button color
    update_apply_button_color()

    win.protocol("WM_DELETE_WINDOW", on_close)

    center_window(win, root)


def open_hotkeys_inline(profile):
    """Open hotkeys configuration as an inline view (not popup)."""
    ProfileTab._global_sub_setting_active = "hotkeys"  # Set global flag
    if hotkey_manager is None:
        return
    
    container = profile._show_sub_setting("Hotkeys")
    profile._current_sub_setting = "hotkeys"  # Track current sub-setting
    
    hotkey_manager.suspend()
    
    # Content frame
    content_frame = tk.Frame(container, bg=DARK_BG)
    content_frame.pack(fill="both", expand=True, padx=12, pady=6)
    
    entries = {}
    
    def build_event_hotkey(event):
        modifiers = []
        if event.state & 0x0004:
            modifiers.append("Ctrl")
        if event.state & 0x0001:
            modifiers.append("Shift")
        if event.state & 0x0008:
            modifiers.append("Alt")
        
        key = event.keysym
        if len(key) == 1:
            key = key.upper()
        else:
            key = key.upper() if key.lower().startswith("f") and key[1:].isdigit() else key.title()
        
        return "+".join(modifiers + [key]) if modifiers or key else ""
    
    def set_readonly_text(entry, value):
        entry.config(state="normal")
        entry.delete(0, tk.END)
        entry.insert(0, value)
        entry.config(state="readonly")
    
    def set_waiting_state(entry, waiting):
        entry.configure(readonlybackground=HOTKEY_WAIT_BG if waiting else DARK_ACCENT)
    
    def add_row(row, label_text, key):
        tk.Label(content_frame, text=label_text).grid(row=row, column=0, sticky="w", pady=4)
        entry = tk.Entry(content_frame, width=12, state="readonly")
        entry.grid(row=row, column=1, padx=8, pady=4, sticky="w")
        entry.configure(readonlybackground=DARK_ACCENT)
        set_readonly_text(entry, hotkey_manager.hotkeys.get(key, ""))
        entries[key] = entry
        
        def capture_hotkey(event):
            new_hotkey = normalize_hotkey_display(build_event_hotkey(event))
            set_readonly_text(entry, new_hotkey)
            set_waiting_state(entry, False)
            return "break"
        
        def clear_hotkey(_event):
            set_readonly_text(entry, "")
            set_waiting_state(entry, False)
        
        def on_focus_in(_event):
            set_waiting_state(entry, True)
        
        def on_focus_out(_event):
            set_waiting_state(entry, False)
        
        def on_click(_event):
            entry.focus_set()
            set_waiting_state(entry, True)
        
        entry.bind("<KeyPress>", capture_hotkey)
        entry.bind("<Escape>", clear_hotkey)
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        entry.bind("<Button-1>", on_click)
    
    profile_name = profile.profile_name_var.get().strip() if profile else ""
    profile_label = profile_name or (profile.default_tab_name if profile else "Profile")
    
    tk.Label(content_frame, text="Global:", font=(FONT_NAME, BASE_FONT_SIZE, "bold")).grid(
        row=0, column=0, columnspan=2, sticky="w", pady=(0, 4)
    )
    tk.Label(
        content_frame,
        text="(Press escape to unbind hotkeys)",
        fg=DARK_FG,
        bg=DARK_BG,
        font=(FONT_NAME, BASE_FONT_SIZE - 2)
    ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 6))
    
    add_row(2, "Start / Stop:", "start_stop")
    add_row(3, "Capture:", "capture")
    
    global_var = tk.BooleanVar(value=hotkey_manager.global_enabled)
    global_check = tk.Checkbutton(
        content_frame,
        text="Enable hotkeys while minimized",
        variable=global_var,
        takefocus=0
    )
    global_check.grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 4))
    
    if keyboard is None:
        global_check.config(state="disabled")
        tk.Label(
            content_frame,
            text="Install the 'keyboard' package to enable global hotkeys.",
            fg="#d46a6a"
        ).grid(row=5, column=0, columnspan=2, sticky="w")
    
    # Spacer between global and profile hotkeys
    tk.Label(content_frame, text="", bg=DARK_BG).grid(row=6, column=0, columnspan=2, pady=(0, 2))
    
    tk.Label(content_frame, text=f"{profile_label}:", font=(FONT_NAME, BASE_FONT_SIZE, "bold")).grid(
        row=7, column=0, columnspan=2, sticky="w", pady=(8, 4)
    )
    
    profile_count_plus = profile.count_plus_hotkey if profile else ""
    profile_count_minus = profile.count_minus_hotkey if profile else ""
    
    tk.Label(content_frame, text="+ Count:").grid(row=8, column=0, sticky="w", pady=4)
    count_plus_entry = tk.Entry(content_frame, width=12, state="readonly")
    count_plus_entry.grid(row=8, column=1, padx=8, pady=4, sticky="w")
    count_plus_entry.configure(readonlybackground=DARK_ACCENT)
    set_readonly_text(count_plus_entry, profile_count_plus)
    
    tk.Label(content_frame, text="- Count:").grid(row=9, column=0, sticky="w", pady=4)
    count_minus_entry = tk.Entry(content_frame, width=12, state="readonly")
    count_minus_entry.grid(row=9, column=1, padx=8, pady=4, sticky="w")
    count_minus_entry.configure(readonlybackground=DARK_ACCENT)
    set_readonly_text(count_minus_entry, profile_count_minus)
    
    def bind_profile_hotkey(entry):
        def capture_hotkey(event):
            new_hotkey = normalize_hotkey_display(build_event_hotkey(event))
            set_readonly_text(entry, new_hotkey)
            set_waiting_state(entry, False)
            return "break"
        
        def clear_hotkey(_event):
            set_readonly_text(entry, "")
            set_waiting_state(entry, False)
        
        def on_focus_in(_event):
            set_waiting_state(entry, True)
        
        def on_focus_out(_event):
            set_waiting_state(entry, False)
        
        def on_click(_event):
            entry.focus_set()
            set_waiting_state(entry, True)
        
        entry.bind("<KeyPress>", capture_hotkey)
        entry.bind("<Escape>", clear_hotkey)
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        entry.bind("<Button-1>", on_click)
    
    bind_profile_hotkey(count_plus_entry)
    bind_profile_hotkey(count_minus_entry)
    
    # Track initial state for change detection
    initial_hotkeys = {key: entry.get() for key, entry in entries.items()}
    initial_global_enabled = global_var.get()
    initial_count_plus = count_plus_entry.get()
    initial_count_minus = count_minus_entry.get()
    
    def check_for_changes():
        for key, entry in entries.items():
            if entry.get() != initial_hotkeys[key]:
                return True
        if global_var.get() != initial_global_enabled:
            return True
        if count_plus_entry.get() != initial_count_plus:
            return True
        if count_minus_entry.get() != initial_count_minus:
            return True
        return False
    
    def update_apply_button_color():
        if check_for_changes():
            apply_button.config(bg=START_ACTIVE_COLOR, activebackground=START_ACTIVE_COLOR)
        else:
            apply_button.config(bg=DARK_BUTTON, activebackground=DARK_BUTTON)
    
    def apply_changes():
        nonlocal initial_hotkeys, initial_global_enabled, initial_count_plus, initial_count_minus
        new_hotkeys = {}
        for key, entry in entries.items():
            new_hotkeys[key] = normalize_hotkey_display(entry.get().strip())
        
        hotkey_manager.set_global_enabled(global_var.get())
        hotkey_manager.set_hotkeys(new_hotkeys)
        save_hotkeys_config(hotkey_manager.hotkeys, hotkey_manager.global_enabled)
        
        profile.set_count_hotkeys(
            normalize_hotkey_display(count_plus_entry.get().strip()),
            normalize_hotkey_display(count_minus_entry.get().strip())
        )
        
        hotkey_manager.resume()
        hotkey_manager.register_local_hotkeys()
        hotkey_manager.refresh_profile_hotkeys()
        initial_hotkeys = {key: entry.get() for key, entry in entries.items()}
        initial_global_enabled = global_var.get()
        initial_count_plus = count_plus_entry.get()
        initial_count_minus = count_minus_entry.get()
        update_apply_button_color()
    
    def on_close():
        hotkey_manager.resume()
        hotkey_manager.register_local_hotkeys()
        hotkey_manager.refresh_profile_hotkeys()
        profile._close_sub_setting()
    
    # Bind change detection to all entries
    for entry in entries.values():
        entry.bind("<KeyRelease>", lambda e: update_apply_button_color())
    count_plus_entry.bind("<KeyRelease>", lambda e: update_apply_button_color())
    count_minus_entry.bind("<KeyRelease>", lambda e: update_apply_button_color())
    global_var.trace_add("write", lambda *args: update_apply_button_color())
    
    # Spacer to push buttons to bottom
    spacer = tk.Frame(container, bg=DARK_BG)
    spacer.pack(fill="both", expand=True)
    
    # Back button at bottom - 420px wide standard button
    tk.Button(
        container,
        text="Back",
        command=on_close,
        padx=BUTTON_PADX,
        pady=BUTTON_PADY,
        height=2
    ).pack(pady=STANDARD_BUTTON_PADY, side="bottom", ipadx=STANDARD_BUTTON_IPADX)
    
    # Apply button above Back - 420px wide standard button
    apply_button = tk.Button(
        container,
        text="Apply",
        command=apply_changes,
        padx=BUTTON_PADX,
        pady=BUTTON_PADY,
        height=BUTTON_HEIGHT
    )
    apply_button.pack(pady=STANDARD_BUTTON_PADY, side="bottom", ipadx=STANDARD_BUTTON_IPADX)
    
    # Initial button color
    update_apply_button_color()
    
    # Make sub-setting draggable after all widgets created
    profile._finalize_sub_setting()


# =========================
# WINDOW HELPERS
# =========================
def center_window(child, parent):
    # Withdraw window to prevent flashing during positioning
    child.withdraw()
    
    child.update_idletasks()
    child_w = child.winfo_width()
    child_h = child.winfo_height()

    parent_x = parent.winfo_rootx()
    parent_y = parent.winfo_rooty()
    parent_w = parent.winfo_width()
    parent_h = parent.winfo_height()

    x = parent_x + (parent_w // 2) - (child_w // 2)
    y = parent_y + (parent_h // 2) - (child_h // 2)

    child.geometry(f"+{x}+{y}")
    
    # Show window now that it's properly positioned
    child.deiconify()


def load_error_icon(path, size=(100, 100)):
    if not os.path.isfile(path):
        return None
    return ImageTk.PhotoImage(Image.open(path).resize(size, Image.LANCZOS))


def play_ui_sound(sound_path):
    """Play UI feedback sound (non-blocking, graceful failure)"""
    try:
        if winsound is None:
            return  # winsound not available (non-Windows platform)
        
        if os.path.exists(sound_path):
            # Play sound asynchronously (non-blocking)
            winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception:
        pass  # Silently fail if sound can't play


def load_tooltip_enabled():
    if not os.path.exists(UI_CONFIG_PATH):
        return True
    try:
        with open(UI_CONFIG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.lower().startswith(TOOLTIP_ENABLED_KEY):
                    return line.split(":", 1)[1].strip() == "1"
    except Exception:
        return True
    return True


def save_tooltip_enabled(enabled):
    try:
        lines = []
        if os.path.exists(UI_CONFIG_PATH):
            with open(UI_CONFIG_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()
        wrote = False
        for i, line in enumerate(lines):
            if line.lower().startswith(TOOLTIP_ENABLED_KEY):
                lines[i] = f"{TOOLTIP_ENABLED_KEY} {'1' if enabled else '0'}\n"
                wrote = True
                break
        if not wrote:
            lines.append(f"{TOOLTIP_ENABLED_KEY} {'1' if enabled else '0'}\n")
        with open(UI_CONFIG_PATH, "w", encoding="utf-8") as f:
            f.writelines(lines)
    except Exception:
        pass


def add_tooltip(widget, text):
    if widget is None:
        return
    tip = {"win": None}

    def show(_event=None):
        if not TOOLTIP_ENABLED:
            return
        if tip["win"]:
            return
        try:
            widget.update_idletasks()
            w = widget.winfo_width()
            h = widget.winfo_height()
            # Center tooltip horizontally relative to widget
            x = widget.winfo_rootx() + max(0, (w // 2))
            y = widget.winfo_rooty() + h + 6
        except Exception:
            return
        tw = tk.Toplevel(widget)
        tw.wm_overrideredirect(True)
        tw.attributes("-topmost", True)
        # Adjust x after window width is known to center exactly
        label = tk.Label(
            tw, text=text, bg=DARK_ACCENT, fg=DARK_FG, justify="center",
            relief="solid", bd=1, font=(FONT_NAME, BASE_FONT_SIZE - 1),
            wraplength=300
        )
        label.pack(ipadx=6, ipady=3)
        tw.update_idletasks()
        tooltip_w = tw.winfo_width()
        centered_x = x - (tooltip_w // 2)
        tw.geometry(f"+{centered_x}+{y}")
        tip["win"] = tw

    def hide(_event=None):
        if tip["win"]:
            tip["win"].destroy()
        tip["win"] = None

    widget.bind("<Enter>", show, add="+")
    widget.bind("<Leave>", hide, add="+")
    widget.bind("<FocusOut>", hide, add="+")


def show_custom_error(kind, title, message, parent=None):
    # Play error sound
    play_ui_sound(UI_SOUND_ERROR_PATH)
    
    defaults = {
        "count_error": "default count_error",
        "rpc_error": "default rpc_error",
    }
    root_window = parent or globals().get("root")
    win = tk.Toplevel(root_window)
    apply_window_style(win, title)
    win.configure(bg=DARK_BG)
    win.geometry("400x300")
    win.resizable(False, False)
    win.transient(root_window)
    win.grab_set()

    container = tk.Frame(win, bg=DARK_BG)
    container.pack(expand=True, fill="both")

    icon_path = ICON_RPC_ERROR_PATH if kind == "rpc_error" else ICON_COUNT_ERROR_PATH
    icon = load_error_icon(icon_path)

    icon_label = tk.Label(container, bg=DARK_BG)
    icon_label.pack(pady=(6, 2), anchor="center")
    if icon:
        icon_label.config(image=icon)
        win._error_icon = icon

    header = tk.Label(
        container,
        text="Rotom is trying it's best...",
        font=(FONT_NAME, BASE_FONT_SIZE, "bold"),
        bg=DARK_BG,
        fg=DARK_FG
    )
    header.pack(pady=(2, 4), anchor="center")

    body_text = message if message else defaults.get(kind, "default count_error")
    text_box = tk.Text(
        container,
        width=40,
        height=3,
        wrap="word",
        bg=DARK_ACCENT,
        fg=DARK_FG,
        bd=1,
        relief="solid",
        font=(FONT_NAME, BASE_FONT_SIZE - 1)
    )
    text_box.insert("1.0", body_text)
    text_box.tag_add("center", "1.0", "end")
    text_box.tag_configure("center", justify="center")
    text_box.config(state="disabled")
    text_box.pack(padx=20, pady=(0, 10), anchor="center")

    ok_button = tk.Button(
        container,
        text="OK",
        command=win.destroy,
        padx=BUTTON_PADX + 25,
        pady=BUTTON_PADY,
        height=BUTTON_HEIGHT
    )
    ok_button.pack(pady=(0, 12), anchor="center")

    center_window(win, root_window)
    win.protocol("WM_DELETE_WINDOW", win.destroy)
    win.wait_window()


def show_reset_confirmation(profile_name, parent=None):
    """Show custom reset profile confirmation dialog with text verification.
    User must type the profile name to confirm.
    Returns True if user confirms with correct text, False otherwise.
    """
    root_window = parent or globals().get("root")
    win = tk.Toplevel(root_window)
    apply_window_style(win, f"Reset Profile: {profile_name}?")  # Added ?
    win.configure(bg=DARK_BG)
    win.geometry("450x380")  # Increased height for entry box
    win.resizable(False, False)
    win.transient(root_window)
    win.grab_set()
    
    result = {"confirmed": False}
    
    container = tk.Frame(win, bg=DARK_BG)
    container.pack(expand=True, fill="both")
    
    # Load reset icon
    icon = load_error_icon(ICON_RESET_PATH)
    
    icon_label = tk.Label(container, bg=DARK_BG)
    icon_label.pack(pady=(26, 2), anchor="center")  # Added 20px top padding
    if icon:
        icon_label.config(image=icon)
        win._reset_icon = icon
    
    # Profile name header
    header = tk.Label(
        container,
        text=f"Reset Profile: {profile_name}?",  # Added ?
        font=(FONT_NAME, BASE_FONT_SIZE, "bold"),
        bg=DARK_BG,
        fg=DARK_FG
    )
    header.pack(pady=(2, 4), anchor="center")
    
    # Instruction message in text box with warning
    text_box = tk.Text(
        container,
        width=45,
        height=3,  # Increased height to fit warning and instruction
        wrap="word",
        bg=DARK_ACCENT,
        fg=DARK_FG,
        bd=1,
        relief="solid",
        font=(FONT_NAME, BASE_FONT_SIZE - 1)
    )
    text_box.insert("1.0", "WARNING: This change cannot be undone.\n")
    text_box.insert("end", "Enter profile name in the box below to confirm.")
    text_box.tag_configure("warning", foreground=START_ACTIVE_COLOR)
    text_box.tag_add("warning", "1.0", "1.end")  # Apply orange to warning line
    text_box.tag_add("center", "1.0", "end")
    text_box.tag_configure("center", justify="center")
    text_box.config(state="disabled")
    text_box.pack(padx=20, pady=(0, 10), anchor="center")
    
    # Text entry for profile name verification
    entry_var = tk.StringVar()
    entry = tk.Entry(
        container,
        textvariable=entry_var,
        width=30,
        font=(FONT_NAME, BASE_FONT_SIZE)
    )
    entry.pack(pady=(0, 10), anchor="center")
    
    # Button frame
    btn_frame = tk.Frame(container, bg=DARK_BG)
    btn_frame.pack(pady=(0, 0))  # Removed excess bottom padding
    
    def validate_entry():
        """Validate entry and update confirm button state/color."""
        matches = entry_var.get() == profile_name  # Case-sensitive
        if matches:
            confirm_btn.config(
                bg=START_ACTIVE_COLOR,
                activebackground=START_ACTIVE_COLOR,
                state="normal"
            )
        else:
            confirm_btn.config(
                bg=DARK_BUTTON,
                activebackground=DARK_BUTTON,
                state="disabled"
            )
    
    def on_confirm():
        """Only confirm if text matches profile name."""
        if entry_var.get() == profile_name:  # Double-check
            result["confirmed"] = True
            win.destroy()
    
    def on_close():
        result["confirmed"] = False
        win.destroy()
    
    confirm_btn = tk.Button(
        btn_frame,
        text="Confirm",
        command=on_confirm,
        padx=BUTTON_PADX + 15,
        pady=BUTTON_PADY,
        height=BUTTON_HEIGHT,
        width=8,
        state="disabled",  # Start disabled
        bg=DARK_BUTTON,
        activebackground=DARK_BUTTON
    )
    confirm_btn.pack(side="left", padx=5)
    
    close_btn = tk.Button(
        btn_frame,
        text="Close",
        command=on_close,
        padx=BUTTON_PADX + 15,
        pady=BUTTON_PADY,
        height=BUTTON_HEIGHT,
        width=8
    )
    close_btn.pack(side="left", padx=5)
    
    # Bind validation to entry changes
    entry_var.trace_add("write", lambda *args: validate_entry())
    
    # Initialize validation state
    validate_entry()
    
    # Focus on entry for immediate typing
    entry.focus_set()
    
    center_window(win, root_window)
    win.protocol("WM_DELETE_WINDOW", on_close)
    win.wait_window()
    
    return result["confirmed"]


# =========================
# WINDOWS API HELPERS
# =========================
user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)

EnumWindows = user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
GetWindowText = user32.GetWindowTextW
GetWindowTextLength = user32.GetWindowTextLengthW
IsWindowVisible = user32.IsWindowVisible
IsIconic = user32.IsIconic
GetClientRect = user32.GetClientRect
ClientToScreen = user32.ClientToScreen
GetWindowRect = user32.GetWindowRect
GetWindowDC = user32.GetWindowDC
ReleaseDC = user32.ReleaseDC
PrintWindow = user32.PrintWindow

CreateCompatibleDC = gdi32.CreateCompatibleDC
CreateCompatibleBitmap = gdi32.CreateCompatibleBitmap
SelectObject = gdi32.SelectObject
DeleteObject = gdi32.DeleteObject
DeleteDC = gdi32.DeleteDC
GetDIBits = gdi32.GetDIBits
BitBlt = gdi32.BitBlt

BI_RGB = 0
DIB_RGB_COLORS = 0
SRCCOPY = 0x00CC0020


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", ctypes.c_ulong),
        ("biWidth", ctypes.c_long),
        ("biHeight", ctypes.c_long),
        ("biPlanes", ctypes.c_ushort),
        ("biBitCount", ctypes.c_ushort),
        ("biCompression", ctypes.c_ulong),
        ("biSizeImage", ctypes.c_ulong),
        ("biXPelsPerMeter", ctypes.c_long),
        ("biYPelsPerMeter", ctypes.c_long),
        ("biClrUsed", ctypes.c_ulong),
        ("biClrImportant", ctypes.c_ulong),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", ctypes.c_ulong * 3)]


# =========================
# CONFIG KEYS
# =========================
CONFIG_KEY_PROFILE_NAME = "profile_name:"
CONFIG_KEY_TITLE = "title_window:"
CONFIG_KEY_COOLDOWN = "cooldown_seconds:"
CONFIG_KEY_FREQUENCY = "frequency_seconds:"
CONFIG_KEY_THRESHOLD = "match_threshold:"
CONFIG_KEY_IMAGE = "image_path:"
CONFIG_KEY_TEXT = "text_path:"
CONFIG_KEY_INCREMENT = "increment_amount:"
CONFIG_KEY_RPC_GAME = "rpc_game:"
CONFIG_KEY_RPC_TARGET = "rpc_target:"
CONFIG_KEY_RPC_ODDS = "rpc_odds:"
CONFIG_KEY_RPC_ENABLED = "rpc_enabled:"
CONFIG_KEY_COUNT_PLUS = "count_plus_hotkey:"
CONFIG_KEY_COUNT_MINUS = "count_minus_hotkey:"
CONFIG_KEY_ALERT_SOUND = "alert_sound:"
CONFIG_KEY_ALERT_ENABLED = "alert_enabled:"
CONFIG_KEY_ALERT_PLAY_MANUAL = "alert_play_manual:"
CONFIG_KEY_ALERT_PLAY_HOTKEY = "alert_play_hotkey:"
CONFIG_KEY_ALERT_PLAY_AUTO = "alert_play_auto:"


# =========================
# IMAGE / WINDOW HELPERS
# =========================
def find_window_by_title_exact(target_title):
    found_hwnd = None

    def enum_proc(hwnd, _lparam):
        nonlocal found_hwnd
        if not IsWindowVisible(hwnd):
            return True

        length = GetWindowTextLength(hwnd)
        if length == 0:
            return True

        buffer = ctypes.create_unicode_buffer(length + 1)
        GetWindowText(hwnd, buffer, length + 1)
        title = buffer.value

        if title == target_title:
            found_hwnd = hwnd
            return False
        return True

    EnumWindows(EnumWindowsProc(enum_proc), 0)
    return found_hwnd


def list_window_titles():
    titles = []

    def enum_proc(hwnd, _lparam):
        if not IsWindowVisible(hwnd):
            return True

        length = GetWindowTextLength(hwnd)
        if length == 0:
            return True

        buffer = ctypes.create_unicode_buffer(length + 1)
        GetWindowText(hwnd, buffer, length + 1)
        title = buffer.value.strip()

        if title:
            titles.append(title)

        return True

    EnumWindows(EnumWindowsProc(enum_proc), 0)
    titles.sort(key=str.lower)
    return titles

def is_window_minimized(hwnd):
    return bool(IsIconic(hwnd))


def grab_window_image(hwnd):
    window_rect = wintypes.RECT()
    if not GetWindowRect(hwnd, ctypes.byref(window_rect)):
        raise RuntimeError("Failed to get window rect.")

    window_width = window_rect.right - window_rect.left
    window_height = window_rect.bottom - window_rect.top

    if window_width <= 0 or window_height <= 0:
        raise RuntimeError("Invalid window size.")

    hwnd_dc = GetWindowDC(hwnd)
    mem_dc = CreateCompatibleDC(hwnd_dc)
    bitmap = CreateCompatibleBitmap(hwnd_dc, window_width, window_height)
    SelectObject(mem_dc, bitmap)

    result = PrintWindow(hwnd, mem_dc, 0x00000002)
    if not result:
        result = PrintWindow(hwnd, mem_dc, 0x00000000)

    if not result:
        if not BitBlt(mem_dc, 0, 0, window_width, window_height, hwnd_dc, 0, 0, SRCCOPY):
            raise RuntimeError("Failed to capture the window.")

    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = window_width
    bmi.bmiHeader.biHeight = -window_height
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = BI_RGB

    buffer = ctypes.create_string_buffer(window_width * window_height * 4)
    bits = GetDIBits(mem_dc, bitmap, 0, window_height, buffer, ctypes.byref(bmi), DIB_RGB_COLORS)
    if bits == 0:
        raise RuntimeError("GetDIBits failed.")

    img = Image.frombuffer("RGBA", (window_width, window_height), buffer, "raw", "BGRA", 0, 1)

    DeleteObject(bitmap)
    DeleteDC(mem_dc)
    ReleaseDC(hwnd, hwnd_dc)

    return img


def compare_images(screenshot_image, template_path, threshold=0.90):
    screenshot_gray = cv2.cvtColor(np.array(screenshot_image), cv2.COLOR_RGBA2GRAY)
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)

    if template is None:
        raise RuntimeError("Failed to load template image for comparison.")

    sh, sw = screenshot_gray.shape[:2]
    th, tw = template.shape[:2]

    if th > sh or tw > sw:
        return False, 0.0

    result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)
    return max_val >= threshold, max_val


def increment_number_in_file(file_path, increment_amount):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        number = 0
    else:
        number = int(content)

    number = max(0, number + increment_amount)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(str(number))

    return number


def read_number_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        return 0

    return int(content)


def is_counter_file_numeric(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            return True
        int(content)
        return True
    except Exception:
        return False


# =========================
# HOTKEY HELPERS
# =========================
def normalize_hotkey_display(hotkey):
    if not hotkey:
        return ""
    parts = [part.strip() for part in hotkey.replace("-", "+").split("+") if part.strip()]
    if not parts:
        return ""
    normalized = []
    modifier_map = {
        "ctrl": "Ctrl",
        "control": "Ctrl",
        "alt": "Alt",
        "shift": "Shift",
        "cmd": "Cmd",
        "command": "Cmd",
        "win": "Win",
        "windows": "Win",
    }
    for part in parts:
        key_lower = part.lower()
        if key_lower in modifier_map:
            normalized.append(modifier_map[key_lower])
        else:
            if len(part) == 1:
                normalized.append(part.upper())
            else:
                normalized.append(part.upper() if key_lower.startswith("f") and part[1:].isdigit() else part.title())
    return "+".join(normalized)


def hotkey_display_to_keyboard(hotkey):
    if not hotkey:
        return ""
    parts = [part.strip() for part in hotkey.replace("-", "+").split("+") if part.strip()]
    if not parts:
        return ""
    normalized = []
    modifier_map = {
        "ctrl": "ctrl",
        "control": "ctrl",
        "alt": "alt",
        "shift": "shift",
        "cmd": "command",
        "command": "command",
        "win": "windows",
        "windows": "windows",
    }
    for part in parts:
        key_lower = part.lower()
        if key_lower in modifier_map:
            normalized.append(modifier_map[key_lower])
        else:
            normalized.append(key_lower)
    return "+".join(normalized)


def load_hotkeys_config():
    hotkeys = DEFAULT_HOTKEYS.copy()
    global_enabled = False

    if not os.path.exists(HOTKEYS_CONFIG_PATH):
        return hotkeys, global_enabled

    with open(HOTKEYS_CONFIG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            if key == "global_enabled":
                global_enabled = (value == "1")
            elif key in hotkeys:
                if value:
                    hotkeys[key] = normalize_hotkey_display(value)

    return hotkeys, global_enabled


def save_hotkeys_config(hotkeys, global_enabled):
    lines = [
        f"global_enabled: {'1' if global_enabled else '0'}\n",
    ]
    for key in ("start_stop", "capture"):
        lines.append(f"{key}: {hotkeys.get(key, '')}\n")

    with open(HOTKEYS_CONFIG_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)


# =========================
# RPC HELPERS
# =========================
def rpc_read_config(path):
    cfg = {
        "target": "",
        "game": "",
        "icon": "",
        "odds": 8192,
        "application_id": None,
        "counter_suffix": "Encounters",
        "generation": 9  # Default to generation 9 (all Pokemon)
    }

    with open(path, "r", encoding="cp1252") as f:
        for line in f:
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.lower().strip()
                v = v.strip()
                if k == "odds" or k == "generation":
                    try:
                        cfg[k] = int(v)
                    except ValueError:
                        # If generation is invalid, keep default
                        if k == "generation":
                            cfg[k] = 9
                        else:
                            cfg[k] = 8192
                else:
                    cfg[k] = v

    return cfg


def rpc_write_config(path, cfg):
    """
    Write RPC configuration to a game config file.
    
    Args:
        path: Path to the config file
        cfg: Dictionary with config values
    """
    lines = []
    
    # Write fields in a consistent order
    if cfg.get("game"):
        lines.append(f"game: {cfg['game']}\n")
    
    if cfg.get("icon"):
        lines.append(f"icon: {cfg['icon']}\n")
    
    if cfg.get("application_id"):
        lines.append(f"application_id: {cfg['application_id']}\n")
    
    # Always preserve generation field if it exists
    if cfg.get("generation") is not None:
        lines.append(f"generation: {cfg['generation']}\n")
    
    if cfg.get("target"):
        lines.append(f"target: {cfg['target']}\n")
    
    if cfg.get("odds") is not None:
        lines.append(f"odds: {cfg['odds']}\n")
    
    if cfg.get("counter_suffix"):
        lines.append(f"counter_suffix: {cfg['counter_suffix']}\n")
    
    with open(path, "w", encoding="cp1252") as f:
        f.writelines(lines)


def rpc_find_game_configs():
    games = []
    if not os.path.isdir(RPC_CONFIG_FOLDER):
        return games

    for fname in os.listdir(RPC_CONFIG_FOLDER):
        if not fname.endswith(".txt"):
            continue
        path = os.path.join(RPC_CONFIG_FOLDER, fname)
        try:
            with open(path, "r", encoding="cp1252") as f:
                contents = f.read().lower()
                if "application_id:" in contents:
                    games.append(fname[:-4])
        except Exception:
            continue
    return games


def rpc_load_pokemon_list():
    """Load Pokemon names, IDs, and icons from JSON files, sorted by id.
    
    Returns:
        list: List of tuples (pokemon_name, pokemon_id, icon_data) or (pokemon_name, pokemon_id) if no icons
    """
    try:
        # Load Pokemon names from pokemon_gen1_9.json
        json_path = resource_path(os.path.join("json", "pokemon_gen1_9.json"))
        print(f"DEBUG: Looking for Pokemon JSON at: {json_path}")
        print(f"DEBUG: File exists: {os.path.exists(json_path)}")
        
        pokemon_names = []
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                pokemon_data = json.load(f)
                print(f"DEBUG: Loaded JSON, type: {type(pokemon_data).__name__}")
                
                # Handle different JSON structures
                all_pokemon = []
                if isinstance(pokemon_data, dict):
                    # JSON is organized by generation: {"generation_1": [...], "generation_2": [...]}
                    print(f"DEBUG: JSON is a dict with {len(pokemon_data)} keys: {list(pokemon_data.keys())}")
                    for gen_key, gen_pokemon in pokemon_data.items():
                        if isinstance(gen_pokemon, list):
                            print(f"DEBUG: Generation '{gen_key}' has {len(gen_pokemon)} Pokemon")
                            all_pokemon.extend(gen_pokemon)
                        else:
                            print(f"DEBUG: Skipping '{gen_key}', not a list")
                elif isinstance(pokemon_data, list):
                    # JSON is a flat list: [{...}, {...}]
                    print(f"DEBUG: JSON is a list with {len(pokemon_data)} items")
                    all_pokemon = pokemon_data
                else:
                    print(f"DEBUG: Unexpected JSON type: {type(pokemon_data)}")
                    return []
                
                print(f"DEBUG: Total Pokemon collected: {len(all_pokemon)}")
                
                # Filter out non-dictionary items (strings, nulls, etc.)
                valid_pokemon = [p for p in all_pokemon if isinstance(p, dict) and p.get('name')]
                print(f"DEBUG: Found {len(valid_pokemon)} valid Pokemon objects (filtered out {len(all_pokemon) - len(valid_pokemon)} invalid entries)")
                
                # Sort by id and extract names only
                sorted_pokemon = sorted(valid_pokemon, key=lambda x: x.get('id', 0))
                pokemon_names = [p.get('name', '') for p in sorted_pokemon]
                print(f"DEBUG: Extracted {len(pokemon_names)} Pokemon names")
                if pokemon_names:
                    print(f"DEBUG: First few Pokemon: {pokemon_names[:5]}")
        else:
            print(f"DEBUG: Pokemon JSON file not found at {json_path}")
        
        # Load icons directly from assets/pokemon_icons/ directory
        icons_dir = resource_path(os.path.join("assets", "pokemon_icons"))
        print(f"DEBUG: Looking for Pokemon icons in: {icons_dir}")
        icon_map = {}
        
        if os.path.exists(icons_dir) and os.path.isdir(icons_dir):
            # Build icon paths from sorted_pokemon (has both id and name)
            for pokemon in sorted_pokemon:
                pokemon_id = pokemon.get('id', 0)
                pokemon_name = pokemon.get('name', '')
                if pokemon_id and pokemon_name:
                    # Icons are named: {id}_{name}.png
                    icon_filename = f"{pokemon_id}_{pokemon_name}.png"
                    icon_path = os.path.join(icons_dir, icon_filename)
                    
                    # Check if icon file exists
                    if os.path.exists(icon_path):
                        # Store relative path from root for load_pokemon_icon()
                        icon_map[pokemon_name.lower()] = os.path.join("assets", "pokemon_icons", icon_filename)
            
            print(f"DEBUG: Found {len(icon_map)} Pokemon icon files")
        else:
            print(f"DEBUG: Pokemon icons directory not found (icons won't display)")
        
        # Return list of tuples (name, id, icon_path) if icons available, else (name, id)
        if icon_map:
            result = []
            for pokemon in sorted_pokemon:
                pokemon_id = pokemon.get('id', 0)
                pokemon_name = pokemon.get('name', '')
                icon_path = icon_map.get(pokemon_name.lower(), '')
                result.append((pokemon_name, pokemon_id, icon_path))
            print(f"DEBUG: Returning {len(result)} Pokemon with IDs and icon paths")
            return result
        else:
            print(f"DEBUG: No icons found, returning names and IDs only")
            return [(p.get('name', ''), p.get('id', 0)) for p in sorted_pokemon]
            
    except Exception as e:
        print(f"WARNING: Could not load Pokemon list: {e}")
        import traceback
        traceback.print_exc()
    
    print("DEBUG: Returning empty Pokemon list")
    return []  # Return empty list if file not found or error occurred


def rpc_open_options(profile, parent_grab=None):
    if profile.rpc_window and profile.rpc_window.winfo_exists():
        profile.rpc_window.lift()
        return

    win = tk.Toplevel(profile.frame)
    apply_window_style(win)
    win.resizable(False, False)
    win.configure(bg=DARK_BG)

    profile._enter_modal(win)
    if parent_grab and parent_grab.winfo_exists():
        set_window_disabled(parent_grab, True)

    # Add Game section with label
    tk.Label(win, text="Game:").grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
    
    # Game tree frame (match Pokemon grid width of 420px)
    tree_frame = tk.Frame(win, width=420)
    tree_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 6), sticky="nsew")
    
    # Filter below game tree
    tk.Label(win, text="Filter:").grid(row=2, column=0, padx=10, pady=(0, 6), sticky="w")
    filter_entry = tk.Entry(win, width=30)
    filter_entry.grid(row=2, column=1, padx=10, pady=(0, 6), sticky="ew")
    
    # Empty row for spacing after game filter (row 3)
    tk.Label(win, text="").grid(row=3, column=0)

    style = ttk.Style(win)
    # Dark mode scrollbar styling
    style.configure(
        "Rpc.Vertical.TScrollbar",
        background=DARK_ACCENT,
        troughcolor=DARK_BG,
        bordercolor=DARK_BG,
        arrowcolor=DARK_FG
    )
    style.map(
        "Rpc.Vertical.TScrollbar",
        background=[("active", DARK_FG), ("!active", DARK_ACCENT)]
    )
    
    style.configure(
        "Rpc.Treeview",
        font=(FONT_NAME, BASE_FONT_SIZE),
        rowheight=42  # Reduced padding - fits 40x30 icons with minimal padding
    )
    style.configure(
        "Rpc.TCombobox",
        font=(FONT_NAME, BASE_FONT_SIZE),
        fieldbackground=DARK_ACCENT,
        background=DARK_ACCENT,
        foreground=DARK_FG,
        arrowcolor=DARK_FG
    )
    style.map(
        "Rpc.TCombobox",
        fieldbackground=[("readonly", DARK_ACCENT)],
        background=[("readonly", DARK_ACCENT)],
        foreground=[("readonly", DARK_FG)]
    )
    win.option_add("*TCombobox*Listbox.font", (FONT_NAME, BASE_FONT_SIZE))
    win.option_add("*TCombobox*Listbox.background", DARK_ACCENT)
    win.option_add("*TCombobox*Listbox.foreground", DARK_FG)

    # Create scrollbar for game tree
    game_scrollbar = ttk.Scrollbar(
        tree_frame,
        orient="vertical",
        style="Rpc.Vertical.TScrollbar"
    )
    game_scrollbar.pack(side="right", fill="y")

    tree = ttk.Treeview(
        tree_frame,
        show="tree",
        selectmode="browse",
        yscrollcommand=game_scrollbar.set,
        height=4,  # Changed from 6 to 4 - show only 4 games at a time
        style="Rpc.Treeview"
    )
    tree.pack(side="left", fill="both", expand=True)
    game_scrollbar.config(command=tree.yview)
    
    # Configure selection colors to match START_ACTIVE_COLOR (orange)
    style.map(
        "Rpc.Treeview",
        background=[("selected", START_ACTIVE_COLOR)],
        foreground=[("selected", "white")]  # White text on orange background
    )

    win.rpc_icons = []
    win.game_data = []  # Store all game data for filtering

    # Load all game data
    for game_id in rpc_find_game_configs():
        display_name = game_id
        icon_image = None
        config_path = os.path.join(RPC_CONFIG_FOLDER, f"{game_id}.txt")

        try:
            cfg = rpc_read_config(config_path)
            if cfg.get("game"):
                display_name = cfg["game"]

            icon_name = cfg.get("icon", "")
            if icon_name:
                icon_path = os.path.join(SCRIPT_FOLDER, "assets", "game_icon", f"{icon_name}.png")
                if os.path.isfile(icon_path):
                    image = Image.open(icon_path).resize((RPC_ICON_SIZE, RPC_ICON_SIZE), Image.LANCZOS)
                    icon_image = ImageTk.PhotoImage(image)
                    win.rpc_icons.append(icon_image)
        except Exception:
            pass

        win.game_data.append({
            'id': game_id,
            'name': display_name,
            'icon': icon_image
        })

    def populate_tree(filter_text=""):
        """Populate tree with games matching the filter"""
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
        
        # Add matching games
        filter_lower = filter_text.lower()
        for game in win.game_data:
            if not filter_text or filter_lower in game['name'].lower():
                tree.insert("", "end", iid=game['id'], text=f"  {game['name']}", image=game['icon'])
    
    def on_filter_change(*args):
        """Update tree when filter text changes"""
        populate_tree(filter_entry.get())
    
    # Initial population
    populate_tree()
    
    # Bind filter
    filter_entry.bind("<KeyRelease>", on_filter_change)

    if profile.rpc_game_id:
        try:
            tree.selection_set(profile.rpc_game_id)
            tree.see(profile.rpc_game_id)
        except Exception:
            pass  # Item might be filtered out

    # Load Pokemon list for Target selector
    pokemon_list_raw = rpc_load_pokemon_list()
    print(f"DEBUG: Pokemon list for selector contains {len(pokemon_list_raw)} items")
    
    # Format Pokemon names: replace "-" with " " and title case
    def format_pokemon_name(name):
        """Format Pokemon name: replace hyphens with spaces and title case"""
        return name.replace("-", " ").title()
    
    def load_pokemon_icon(icon_data):
        """Load Pokemon icon from URL, base64, or local path"""
        if not icon_data:
            return None
        
        try:
            from io import BytesIO
            import base64
            
            # Check if it's a data URI (base64)
            if icon_data.startswith('data:image'):
                # Extract base64 data
                base64_data = icon_data.split(',', 1)[1] if ',' in icon_data else icon_data
                image_data = base64.b64decode(base64_data)
                image = Image.open(BytesIO(image_data))
            # Check if it's a URL
            elif icon_data.startswith('http://') or icon_data.startswith('https://'):
                import urllib.request
                with urllib.request.urlopen(icon_data, timeout=2) as response:
                    image_data = response.read()
                    image = Image.open(BytesIO(image_data))
            # Assume it's a local file path
            else:
                icon_path = resource_path(icon_data)
                if os.path.exists(icon_path):
                    image = Image.open(icon_path)
                else:
                    return None
            
            # Resize to 32x32 for tree display
            image = image.resize((32, 32), Image.LANCZOS)
            return ImageTk.PhotoImage(image)
        except Exception as e:
            print(f"DEBUG: Failed to load icon: {e}")
            return None
    
    def load_pokemon_sprite(pokemon_name, pokemon_id):
        """Load Pokemon sprite from assets/pokemon_icons/ and scale to 80x80"""
        if not pokemon_name or not pokemon_id:
            return None
        
        try:
            # Sprites are named: {id}_{name}.png in assets/pokemon_icons/
            sprite_filename = f"{pokemon_id}_{pokemon_name}.png"
            sprite_path = resource_path(os.path.join("assets", "pokemon_icons", sprite_filename))
            
            if os.path.exists(sprite_path):
                image = Image.open(sprite_path)
                # Keep original 128x128 size (no scaling)
                return ImageTk.PhotoImage(image)
            else:
                print(f"DEBUG: Sprite not found: {sprite_path}")
                return None
        except Exception as e:
            print(f"DEBUG: Failed to load sprite for {pokemon_name}: {e}")
            return None
    
    # Store both original and formatted names, icons, sprites, and IDs
    win.pokemon_data = []
    win.pokemon_icons = []  # Keep references to prevent garbage collection
    win.pokemon_grid_sprites = []  # Keep sprite references for grid
    
    # Check if pokemon_list_raw contains tuples with icons (3-tuples)
    try:
        has_icons = (pokemon_list_raw and isinstance(pokemon_list_raw[0], tuple) and 
                     len(pokemon_list_raw[0]) == 3)
    except (IndexError, TypeError):
        has_icons = False
    
    # Store current game generation (default to 9 to show all Pokemon)
    win.current_game_generation = 9
    
    if has_icons:
        print(f"DEBUG: Creating Pokemon data with IDs and icons...")
        for pokemon_name, pokemon_id, icon_url in pokemon_list_raw:
            # Load icon (small, for tree view)
            icon_image = load_pokemon_icon(icon_url)
            if icon_image:
                win.pokemon_icons.append(icon_image)
            
            # Store Pokemon data WITHOUT loading sprite yet (lazy load later)
            win.pokemon_data.append({
                'original': pokemon_name,
                'formatted': format_pokemon_name(pokemon_name),
                'icon': icon_image,
                'id': pokemon_id
            })
    else:
        print(f"DEBUG: Creating Pokemon data with IDs only...")
        for pokemon_name, pokemon_id in pokemon_list_raw:
            # Store Pokemon data WITHOUT loading sprite yet (lazy load later)
            win.pokemon_data.append({
                'original': pokemon_name,
                'formatted': format_pokemon_name(pokemon_name),
                'icon': None,
                'id': pokemon_id
            })

    
    # Create Pokemon selector (Canvas grid showing 3×1 = 3 items at once)
    tk.Label(win, text="Target:").grid(row=4, column=0, padx=10, pady=(0, 0), sticky="w")
    
    # Configure column weight to expand
    win.grid_columnconfigure(1, weight=1)
    
    # Frame for pokemon canvas and scrollbar
    pokemon_container = tk.Frame(win, bg=DARK_BG)
    pokemon_container.grid(row=5, column=0, columnspan=2, padx=10, pady=(0, 6), sticky="nsew")
    
    # Filter entry for Pokemon (below canvas)
    tk.Label(win, text="Filter:").grid(row=6, column=0, padx=10, pady=(0, 6), sticky="w")
    pokemon_filter_entry = tk.Entry(win, width=30)
    pokemon_filter_entry.grid(row=6, column=1, padx=10, pady=(0, 6), sticky="ew")
    
    # Empty row for spacing after Pokemon filter (row 7)
    tk.Label(win, text="").grid(row=7, column=0)
    
    # Frame for pokemon canvas and scrollbar
    pokemon_frame = tk.Frame(pokemon_container, bg=DARK_BG)
    pokemon_frame.pack(fill="both", expand=True)
    
    # Create pokemon canvas (3 columns × 1 row, 140×150 cells = 420×150 canvas)
    pokemon_canvas = tk.Canvas(
        pokemon_frame,
        width=420,
        height=150,
        bg=DARK_ACCENT,
        highlightthickness=0
    )
    
    # Configure canvas
    pokemon_canvas.pack(side="left", fill="both", expand=True)
    
    # Store canvas reference on window
    win.pokemon_canvas = pokemon_canvas
    win.filtered_pokemon = []  # Stores currently displayed Pokemon
    win.selected_pokemon_name = ""  # Stores selected Pokemon original name
    win.loaded_sprites = {}  # Cache for loaded sprites {pokemon_original_name: sprite_image}
    
    # Helper function to get game generation
    def get_game_generation(game_name):
        """Get the Pokemon generation for a given game"""
        game_lower = game_name.lower()
        
        # Generation 1
        if any(x in game_lower for x in ["red", "blue", "yellow", "green"]):
            return 1
        # Generation 2
        if any(x in game_lower for x in ["gold", "silver", "crystal"]):
            return 2
        # Generation 3
        if any(x in game_lower for x in ["ruby", "sapphire", "emerald", "firered", "leafgreen"]):
            return 3
        # Generation 4
        if any(x in game_lower for x in ["diamond", "pearl", "platinum", "heartgold", "soulsilver"]):
            return 4
        # Generation 5
        if any(x in game_lower for x in ["black", "white"]):
            return 5
        # Generation 6
        if any(x in game_lower for x in ["x ", "y ", " x", " y", "omega ruby", "alpha sapphire"]):
            return 6
        # Generation 7
        if any(x in game_lower for x in ["sun", "moon", "ultra sun", "ultra moon"]):
            return 7
        # Generation 8
        if any(x in game_lower for x in ["sword", "shield", "brilliant diamond", "shining pearl", "legends arceus", "legends: arceus"]):
            return 8
        # Generation 9
        if any(x in game_lower for x in ["scarlet", "violet"]):
            return 9
        
        # Default to showing all Pokemon (Gen 9)
        return 9
    
    def get_pokemon_generation(pokemon_id):
        """Get generation number from Pokemon ID"""
        if pokemon_id <= 151:
            return 1
        elif pokemon_id <= 251:
            return 2
        elif pokemon_id <= 386:
            return 3
        elif pokemon_id <= 493:
            return 4
        elif pokemon_id <= 649:
            return 5
        elif pokemon_id <= 721:
            return 6
        elif pokemon_id <= 809:
            return 7
        elif pokemon_id <= 905:
            return 8
        else:
            return 9
    
    def draw_grid_cell(canvas, pokemon, x, y, width, height):
        """Draw a single Pokemon grid cell with sprite and name"""
        # Draw cell background
        canvas.create_rectangle(
            x, y, x + width, y + height,
            fill=DARK_ACCENT,
            outline=DARK_BORDER,
            width=1
        )
        
        # Load sprite on-demand if not already loaded
        if 'sprite' not in pokemon or pokemon['sprite'] is None:
            sprite_image = load_pokemon_sprite(pokemon['original'], pokemon['id'])
            if sprite_image:
                pokemon['sprite'] = sprite_image
                win.pokemon_grid_sprites.append(sprite_image)
        
        # Draw sprite (128×128 centered in cell)
        if pokemon.get('sprite'):
            sprite_x = x + width // 2
            sprite_y = y + 70  # Center 128px sprite vertically in 150px cell
            canvas.create_image(sprite_x, sprite_y, image=pokemon['sprite'])
        
        # Draw Pokemon name (bottom of cell)
        name_y = y + height - 10
        canvas.create_text(
            x + width // 2, name_y,
            text=pokemon['formatted'],
            fill=DARK_FG,
            font=(FONT_NAME, 11),  # Increased from 10 to 11pt
            anchor="s"
        )
    
    def highlight_selected_pokemon():
        """Draw orange highlight box around selected Pokemon and redraw sprite/text"""
        canvas = win.pokemon_canvas
        
        # Remove existing highlight
        canvas.delete("highlight")
        
        if not win.selected_pokemon_name:
            return
        
        # Find the selected Pokemon in filtered list
        selected_index = -1
        selected_pokemon = None
        for i, pokemon in enumerate(win.filtered_pokemon):
            if pokemon['original'] == win.selected_pokemon_name:
                selected_index = i
                selected_pokemon = pokemon
                break
        
        if selected_index == -1 or selected_index >= 3 or not selected_pokemon:
            return
        
        # Calculate cell position (3 columns × 1 row for horizontal layout)
        cols = 3
        cell_width = 140
        cell_height = 150
        
        row = selected_index // cols
        col = selected_index % cols
        x = col * cell_width
        y = row * cell_height
        
        # Draw orange filled highlight box
        canvas.create_rectangle(
            x, y, x + cell_width, y + cell_height,
            fill=START_ACTIVE_COLOR,
            outline=START_ACTIVE_COLOR,
            width=0,
            tags="highlight"
        )
        
        # Redraw sprite on top of orange background
        if selected_pokemon.get('sprite'):
            sprite_x = x + cell_width // 2
            sprite_y = y + 70  # Center 128px sprite vertically in 150px cell
            canvas.create_image(sprite_x, sprite_y, image=selected_pokemon['sprite'], tags="highlight")
        
        # Redraw Pokemon name on top of orange background (in white for contrast)
        name_y = y + cell_height - 10
        canvas.create_text(
            x + cell_width // 2, name_y,
            text=selected_pokemon['formatted'],
            fill="white",  # White text on orange background
            font=(FONT_NAME, 11),
            anchor="s",
            tags="highlight"
        )
    
    def on_pokemon_grid_click(event):
        """Handle click on Pokemon grid cell"""
        canvas = win.pokemon_canvas
        
        # Get canvas coordinates (accounting for scroll)
        canvas_x = canvas.canvasx(event.x)
        canvas_y = canvas.canvasy(event.y)
        
        # Calculate which cell was clicked (3 columns × 1 row for horizontal layout)
        cols = 3
        cell_width = 140
        cell_height = 150
        
        col = int(canvas_x // cell_width)
        row = int(canvas_y // cell_height)
        index = row * cols + col
        
        # Check if index is valid
        if 0 <= index < len(win.filtered_pokemon) and index < 3:
            pokemon = win.filtered_pokemon[index]
            win.selected_pokemon_name = pokemon['original']
            highlight_selected_pokemon()
            update_apply_button_color()
    

    def populate_pokemon_grid(filter_text=""):
        """Populate Pokemon grid with first 3 Pokemon matching the filter and generation"""
        canvas = win.pokemon_canvas
        
        # Clear canvas
        canvas.delete("all")
        
        # Get max generation from current game (stored when game is selected)
        max_generation = getattr(win, 'current_game_generation', 9)  # Default to all Pokemon
        print(f"DEBUG: Filtering Pokemon for max generation: {max_generation}")
        
        # Filter Pokemon by generation first
        filtered_by_gen = []
        for pokemon in win.pokemon_data:
            # Get Pokemon generation from its ID
            pokemon_id = pokemon.get('id', 0)
            pokemon_gen = get_pokemon_generation(pokemon_id)
            
            # Only show Pokemon from generations <= max_generation
            if pokemon_gen <= max_generation:
                filtered_by_gen.append(pokemon)
        
        # Apply search filter with prefix prioritization
        if filter_text:
            filter_lower = filter_text.lower()
            
            # Prioritize Pokemon that START with the filter
            starts_with = [p for p in filtered_by_gen 
                          if p['formatted'].lower().startswith(filter_lower)]
            
            # Then Pokemon that CONTAIN the filter
            contains = [p for p in filtered_by_gen 
                       if filter_lower in p['formatted'].lower() 
                       and not p['formatted'].lower().startswith(filter_lower)]
            
            # Combine: prefix matches first, then contains
            win.filtered_pokemon = starts_with + contains
        else:
            win.filtered_pokemon = filtered_by_gen
        
        # Show only the first 3 Pokemon (3x1 grid - horizontal)
        display_pokemon = win.filtered_pokemon[:3]
        
        print(f"DEBUG: Total filtered Pokemon: {len(win.filtered_pokemon)}, Displaying first {len(display_pokemon)} Pokemon")
        
        # Draw the first 3 Pokemon in a 3x1 grid (horizontal)
        cols = 3
        cell_width = 140
        cell_height = 150
        
        current_target = profile.rpc_target if hasattr(profile, 'rpc_target') else ""
        
        for i, pokemon in enumerate(display_pokemon):
            row = i // cols  # 0, 1, 2
            col = i % cols   # Always 0
            x = col * cell_width
            y = row * cell_height
            
            draw_grid_cell(canvas, pokemon, x, y, cell_width, cell_height)
        
        # Select current target if it matches
        if current_target:
            for pokemon in win.filtered_pokemon:
                if pokemon['original'].lower() == current_target.lower():
                    win.selected_pokemon_name = pokemon['original']
                    highlight_selected_pokemon()
                    break
        
        # If no selection, select first Pokemon
        if not win.selected_pokemon_name and win.filtered_pokemon:
            win.selected_pokemon_name = win.filtered_pokemon[0]['original']
            highlight_selected_pokemon()
    
    def on_pokemon_filter_change(*args):
        """Update Pokemon grid when filter text changes"""
        populate_pokemon_grid(pokemon_filter_entry.get())
    
    # Bind filter and click events
    pokemon_filter_entry.bind("<KeyRelease>", on_pokemon_filter_change)
    pokemon_canvas.bind("<Button-1>", on_pokemon_grid_click)
    
    print(f"DEBUG: Grid initialized with {len(win.pokemon_data)} total Pokemon")

    # Helper function to select Pokemon by name
    def select_pokemon_by_name(name):
        """Select a Pokemon in the grid by name (case-insensitive), only if it's in the filtered list"""
        if not name:
            return
        name_lower = name.lower()
        
        # Only search in filtered Pokemon (respects generation filter)
        for pokemon in win.filtered_pokemon:
            if pokemon['original'].lower() == name_lower:
                win.selected_pokemon_name = pokemon['original']
                highlight_selected_pokemon()
                print(f"DEBUG: Selected Pokemon: {pokemon['formatted']} (from {name})")
                return
        print(f"DEBUG: Pokemon '{name}' not found in filtered list (may be wrong generation)")

    suffix_to_label = {suffix: label for label, suffix in RPC_COUNTER_OPTIONS}
    label_to_suffix = {label: suffix for label, suffix in RPC_COUNTER_OPTIONS}
    selected_label = suffix_to_label.get(profile.rpc_counter_suffix, "Default / Other")

    # Empty row for spacing after Pokemon filter (row 7)
    
    tk.Label(win, text="Method:").grid(row=8, column=0, padx=10, pady=(0, 6), sticky="w")
    counter_type_var = tk.StringVar(value=selected_label)
    counter_type_menu = ttk.Combobox(
        win,
        textvariable=counter_type_var,
        values=[label for label, _ in RPC_COUNTER_OPTIONS],
        state="readonly",
        width=18,  # Reduced from 20 to 18 characters
        style="Rpc.TCombobox"
    )
    counter_type_menu.grid(row=8, column=1, padx=10, pady=(0, 6), sticky="w")

    tk.Label(win, text="Odds:").grid(row=9, column=0, padx=10, pady=(0, 6), sticky="w")
    odds_entry = tk.Entry(win, width=5)
    odds_entry.grid(row=9, column=1, padx=10, pady=(0, 6), sticky="w")
    
    # Empty row for spacing after odds (row 10)
    tk.Label(win, text="").grid(row=10, column=0)

    # Function to populate fields from selected game config
    def on_game_selection_change(event=None):
        """
        Populate Target, Method, and Odds fields from the selected game's config file.
        
        This function is called when a game is selected in the tree view.
        It reads the game's config file and updates the UI fields without saving
        changes to the profile. Changes are only saved when Apply is pressed.
        
        Args:
            event: The tree selection event (optional)
        """
        selection = tree.selection()
        if not selection:
            return
        
        game_id = selection[0]
        config_path = os.path.join(RPC_CONFIG_FOLDER, f"{game_id}.txt")
        
        # Clear any previous Pokemon selection when changing games
        win.selected_pokemon_name = ""
        
        try:
            cfg = rpc_read_config(config_path)
            
            # Read generation field from config file
            game_generation = cfg.get("generation", 9)  # Default to 9 (all Pokemon)
            try:
                game_generation = int(game_generation)
                # Clamp to valid range (1-9)
                win.current_game_generation = max(1, min(9, game_generation))
            except (ValueError, TypeError):
                win.current_game_generation = 9  # Default to all if invalid
            
            print(f"DEBUG: Game generation from config: {win.current_game_generation}")
            
            # Repopulate Pokemon grid based on game's generation FIRST
            # This filters Pokemon to only those available in this generation
            populate_pokemon_grid()
            
            # Now select Pokemon from config (only if it's in the filtered list)
            target = cfg.get("target", "")
            select_pokemon_by_name(target)
            
            # Update odds field
            odds = cfg.get("odds", 8192)
            odds_entry.delete(0, tk.END)
            odds_entry.insert(0, str(odds))
            
            # Update counter type/method field
            counter_suffix = cfg.get("counter_suffix", "Encounters")
            counter_label = suffix_to_label.get(counter_suffix, "Default / Other")
            counter_type_var.set(counter_label)
            
        except (FileNotFoundError, KeyError, ValueError):
            # Config file doesn't exist or has invalid data, silently use defaults
            # This is acceptable as the user can manually enter values
            pass
    
    # Bind tree selection event to auto-populate fields
    tree.bind("<<TreeviewSelect>>", on_game_selection_change)
    
    # Populate fields for initially selected game
    if profile.rpc_game_id:
        on_game_selection_change()  # This will populate Pokemon grid with correct generation
    else:
        # No game selected, populate with default (all Pokemon)
        populate_pokemon_grid()
    
    print(f"DEBUG: Pokemon grid populated with {len(win.filtered_pokemon)} items")

    # Helper function to get current pokemon selection from grid
    def get_current_pokemon():
        """Get the currently selected Pokemon from the grid (returns original name)"""
        return win.selected_pokemon_name if win.selected_pokemon_name else ""
    
    # Track initial state for change detection
    initial_game_id = profile.rpc_game_id
    initial_target = get_current_pokemon()
    initial_odds = odds_entry.get()
    initial_counter_type = counter_type_var.get()

    def check_for_changes():
        """Check if any RPC settings have changed"""
        selection = tree.selection()
        current_game_id = selection[0] if selection else ""
        if current_game_id != initial_game_id:
            return True
        if get_current_pokemon() != initial_target:
            return True
        if odds_entry.get() != initial_odds:
            return True
        if counter_type_var.get() != initial_counter_type:
            return True
        return False

    def update_apply_button_color():
        """Update Apply button color based on whether changes exist"""
        if check_for_changes():
            apply_button.config(bg=START_ACTIVE_COLOR, activebackground=START_ACTIVE_COLOR)
        else:
            apply_button.config(bg=DARK_BUTTON, activebackground=DARK_BUTTON)

    def save_fields():
        target = get_current_pokemon()
        odds_text = odds_entry.get().strip()
        try:
            odds = int(odds_text)
        except ValueError:
            show_custom_error(
                "rpc_error",
                "Error ID 60155152: NaN",
                "Rotom can only compute odds that are a whole number.\n(e.g. 1/8192 = \"8192\")",
                parent=win
            )
            return False

        selection = tree.selection()
        if not selection:
            show_custom_error(
                "rpc_error",
                "Error ID 11272852: Invalid Settings",
                "No game has been selected. Please select a game from the menu and try again.",
                parent=win
            )
            return False

        game_id = selection[0]
        profile.rpc_game_id = game_id
        profile.rpc_target = target
        profile.rpc_odds = odds

        selected_suffix = label_to_suffix.get(counter_type_var.get(), "Encounters")
        profile.rpc_counter_suffix = selected_suffix
        profile.update_config_value(CONFIG_KEY_RPC_SUFFIX, selected_suffix)

        profile.update_config_value(CONFIG_KEY_RPC_GAME, game_id)
        profile.update_config_value(CONFIG_KEY_RPC_TARGET, target)
        profile.update_config_value(CONFIG_KEY_RPC_ODDS, odds)
        profile.mark_dirty()
        
        # Save to game config file as well
        config_path = os.path.join(RPC_CONFIG_FOLDER, f"{game_id}.txt")
        try:
            # Read existing config to preserve other fields (or get defaults if file doesn't exist)
            if os.path.exists(config_path):
                game_cfg = rpc_read_config(config_path)
            else:
                # File doesn't exist yet, start with defaults
                game_cfg = {
                    "target": "",
                    "game": "",
                    "icon": "",
                    "odds": 8192,
                    "application_id": None,
                    "counter_suffix": "Encounters",
                    "generation": 9  # Default to generation 9 (all Pokemon)
                }
            
            # Update with new values (preserve generation from existing config)
            game_cfg["target"] = target
            game_cfg["odds"] = odds
            game_cfg["counter_suffix"] = selected_suffix
            # Note: generation is NOT updated here - it's preserved from the file
            # Write back to file
            rpc_write_config(config_path, game_cfg)
        except Exception as e:
            # If we can't write to game config, show error but don't fail the save
            # Profile config is still saved
            print(f"Warning: Could not update game config file: {e}")
        
        return True

    def apply_and_close():
        if save_fields():
            win.destroy()
            profile.rpc_window = None
            profile._exit_modal()
            if parent_grab and parent_grab.winfo_exists():
                set_window_disabled(parent_grab, False)
                parent_grab.grab_set()
                parent_grab.focus_force()

    def close_rpc():
        win.destroy()
        profile.rpc_window = None
        profile._exit_modal()
        if parent_grab and parent_grab.winfo_exists():
            set_window_disabled(parent_grab, False)
            parent_grab.grab_set()
            parent_grab.focus_force()

    button_row = tk.Frame(win, bg=DARK_BG)
    button_row.grid(row=11, column=0, columnspan=2, pady=10)

    apply_button = tk.Button(
        button_row,
        text="Apply",
        command=apply_and_close,
        padx=BUTTON_PADX,
        pady=BUTTON_PADY,
        height=BUTTON_HEIGHT
    )
    apply_button.pack(side="left", padx=6)
    
    tk.Button(
        button_row,
        text="Close",
        command=close_rpc,
        padx=BUTTON_PADX,
        pady=BUTTON_PADY,
        height=BUTTON_HEIGHT
    ).pack(side="left", padx=6)

    # Bind change detection
    tree.bind("<<TreeviewSelect>>", lambda e: (on_game_selection_change(e), update_apply_button_color()))
    odds_entry.bind("<KeyRelease>", lambda e: update_apply_button_color())
    counter_type_var.trace_add("write", lambda *args: update_apply_button_color())

    # Initial button color
    update_apply_button_color()

    win.protocol("WM_DELETE_WINDOW", close_rpc)

    # Calculate and set window size after all widgets are created
    win.update_idletasks()
    natural_width = win.winfo_reqwidth()
    natural_height = win.winfo_reqheight()
    reduced_width = max(440, natural_width - 250)  # Reduce width by 250px, minimum 440px to fit 420px grid + 10px padding each side
    win.geometry(f"{reduced_width}x{natural_height}")

    center_window(win, profile.frame.winfo_toplevel())


def rpc_shiny_confidence(enc, odds):
    p = 1 / odds
    return 1 - (1 - p) ** enc, "▲" if enc >= odds else "▼"


# =========================
# HOTKEY MANAGER
# =========================
class HotkeyManager:
    def __init__(self, root, get_active_profile, get_profiles):
        self.root = root
        self.get_active_profile = get_active_profile
        self.get_profiles = get_profiles
        self.hotkeys = DEFAULT_HOTKEYS.copy()
        self.global_enabled = False
        self._global_handles = []
        self._local_binding = None
        self.suspended = False

    def _clear_global_hotkeys(self):
        if keyboard is None:
            self._global_handles = []
            return
        for handle in self._global_handles:
            try:
                keyboard.remove_hotkey(handle)
            except Exception:
                pass
        self._global_handles = []

    def _register_global_hotkeys(self):
        self._clear_global_hotkeys()
        if self.suspended or not self.global_enabled or keyboard is None:
            return

        def add_hotkey(key, callback):
            if not key:
                return
            key_for_keyboard = hotkey_display_to_keyboard(key)
            if not key_for_keyboard:
                return
            handle = keyboard.add_hotkey(key_for_keyboard, callback)
            self._global_handles.append(handle)

        add_hotkey(self.hotkeys.get("start_stop", ""), self.trigger_start_stop)
        add_hotkey(self.hotkeys.get("capture", ""), self.trigger_capture)

        for profile in self.get_profiles():
            add_hotkey(
                profile.count_plus_hotkey,
                lambda p=profile: p.on_manual_adjust(1, source="hotkey") if p.is_running else None
            )
            add_hotkey(
                profile.count_minus_hotkey,
                lambda p=profile: p.on_manual_adjust(-1, source="hotkey") if p.is_running else None
            )

    def suspend(self):
        self.suspended = True
        self._clear_global_hotkeys()

    def resume(self):
        self.suspended = False
        self._register_global_hotkeys()

    def refresh_profile_hotkeys(self):
        self._register_global_hotkeys()

    def _build_event_hotkey(self, event):
        modifiers = []
        if event.state & 0x0004:
            modifiers.append("Ctrl")
        if event.state & 0x0001:
            modifiers.append("Shift")
        if event.state & 0x0008:
            modifiers.append("Alt")

        key = event.keysym
        if len(key) == 1:
            key = key.upper()
        else:
            key = key.upper() if key.lower().startswith("f") and key[1:].isdigit() else key.title()

        return "+".join(modifiers + [key])

    def _local_keypress(self, event):
        if self.suspended or self.global_enabled:
            return
        pressed = self._build_event_hotkey(event)
        if pressed == self.hotkeys.get("start_stop", ""):
            self.trigger_start_stop()
        elif pressed == self.hotkeys.get("capture", ""):
            self.trigger_capture()

        for profile in self.get_profiles():
            if not profile.is_running:
                continue
            if pressed == profile.count_plus_hotkey:
                profile.on_manual_adjust(1, source="hotkey")
            if pressed == profile.count_minus_hotkey:
                profile.on_manual_adjust(-1, source="hotkey")

    def register_local_hotkeys(self):
        if self._local_binding is None:
            self._local_binding = self.root.bind_all("<KeyPress>", self._local_keypress)

    def set_hotkeys(self, hotkeys):
        self.hotkeys = {
            key: normalize_hotkey_display(value)
            for key, value in hotkeys.items()
        }
        self._register_global_hotkeys()

    def set_global_enabled(self, enabled):
        if enabled and keyboard is None:
            show_custom_error(
                "count_error",
                "Error ID 92057485: Missing Package",
                "Some important files are missing. Please delete the program and download it again from the official GitHub page."
            )
            self.global_enabled = False
            self._register_global_hotkeys()
            return False

        self.global_enabled = enabled
        self._register_global_hotkeys()
        return True

    def trigger_start_stop(self):
        if self.suspended:
            return
        profile = self.get_active_profile()
        if profile:
            profile.on_toggle_start()

    def trigger_capture(self):
        if self.suspended:
            return
        profile = self.get_active_profile()
        if profile:
            profile.on_capture_reference()

    def trigger_count_plus(self):
        if self.suspended:
            return
        profile = self.get_active_profile()
        if profile:
            profile.on_manual_adjust(1, source="hotkey")

    def trigger_count_minus(self):
        if self.suspended:
            return
        profile = self.get_active_profile()
        if profile:
            profile.on_manual_adjust(-1, source="hotkey")


# =========================
# PROFILE TAB CLASS
# =========================
class ProfileTab:
    # Class variable to track if settings menu should be open globally
    _global_settings_open = False
    # Class variable to track which sub-setting is open globally (None, "alerts", "auto", "rpc", "hotkeys", "reset")
    _global_sub_setting_active = None
    
    def __init__(self, parent, profile_index):
        self.notebook = parent
        self.profile_index = profile_index
        self.default_tab_name = f"Profile {profile_index}"
        self.config_path = os.path.join("config", f"config{profile_index}.txt")

        self.selected_image_path = ""
        self.selected_text_path = ""
        self.last_match_time = 0.0
        self.is_running = False
        self.configure_window = None
        self.test_window = None
        self.test_image_button = None
        self.capture_window = None
        self.rpc_window = None
        self.settings_window = None
        self.alert_window = None
        self._drag_offset = (0, 0)
        self._test_drag_offset = (0, 0)
        self._dirty = False
        self._autosave_after_id = None
        self._root_drag_offset = (0, 0)
        self._drag_active = False
        self._modal_depth = 0
        self._locked_tab_index = None
        self._suppress_text_path_change = False
        self._settings_view_active = False
        self._settings_frame = None
        self._current_sub_setting = None  # Track which sub-setting is currently open
        self._alert_icon_selected = None
        self._alert_icon_unselected = None

        self.rpc = None
        self.rpc_thread = None
        self.rpc_stop_event = threading.Event()
        self.rpc_game_id = ""
        self.rpc_target = ""
        self.rpc_odds = 8192
        self.rpc_is_running = False
        self.rpc_enabled = False
        self.rpc_last_stop_time = 0.0
        self.rpc_counter_suffix = "Encounters"

        self.auto_count_var = tk.BooleanVar(value=False)

        self.image_path_var = tk.StringVar()
        self.text_path_var = tk.StringVar()
        self.title_var = tk.StringVar()
        self.profile_name_var = tk.StringVar()
        self.increment_var = tk.StringVar()
        self.count_plus_hotkey = ""
        self.count_minus_hotkey = ""
        self._last_text_path = ""
        self._loading_config = False

        self.audio_enabled = False
        self.audio_enabled_var = tk.BooleanVar(value=False)
        self.alert_sound_file = ""
        self.alert_last_play_time = 0.0
        self.alert_play_manual = True
        self.alert_play_hotkey = True
        self.alert_play_auto = True

        self.rpc_icon_img = None
        self.count_icon_img = None
        self.audio_icon_img = None
        self.rpc_gif_frames = []
        self.count_gif_frames = []
        self.audio_gif_frames = []
        self.rpc_gif_delays = []
        self.count_gif_delays = []
        self.audio_gif_delays = []
        self.rpc_gif_index = 0
        self.count_gif_index = 0
        self.audio_gif_index = 0
        self.rpc_gif_after_id = None
        self.count_gif_after_id = None
        self.audio_gif_after_id = None

        self.image_path_var.trace_add("write", self._on_image_path_change)
        self.text_path_var.trace_add("write", self._on_text_path_change)
        self.title_var.trace_add("write", self._on_title_change)
        self.profile_name_var.trace_add("write", self._on_profile_name_change)
        self.auto_count_var.trace_add("write", self._on_auto_count_toggle)
        self.increment_var.trace_add("write", self._on_increment_change)

        self.frame = tk.Frame(parent, bg=DARK_BG, highlightthickness=0, bd=0)

        self.build_ui()
        self.schedule_autosave()
        self._update_manual_buttons()
        self.set_settings_state(True)
        self._set_inactive_icons()

    def _set_counter_button_colors(self, active):
        if active:
            self.btn_decrement.configure(bg=START_ACTIVE_COLOR, activebackground=START_ACTIVE_COLOR)
            self.btn_increment.configure(bg=START_ACTIVE_COLOR, activebackground=START_ACTIVE_COLOR)
        else:
            self.btn_decrement.configure(bg=DARK_BUTTON, activebackground=DARK_BUTTON)
            self.btn_increment.configure(bg=DARK_BUTTON, activebackground=DARK_BUTTON)
    
    def _update_test_image_button_color(self, color):
        btn = getattr(self, "test_image_button", None)
        if not btn:
            return
        try:
            if btn.winfo_exists():
                btn.config(bg=color, activebackground=color)
            else:
                self.test_image_button = None
        except tk.TclError:
            self.test_image_button = None

    # ---------- Modal helpers ----------
    def _set_tabs_enabled(self, enabled: bool):
        tab_count = self.notebook.index("end")
        if enabled:
            for i in range(tab_count):
                self.notebook.tab(i, state="normal")
            self._locked_tab_index = None
            return

        try:
            current_index = self.notebook.index(self.notebook.select())
        except Exception:
            current_index = 0

        self._locked_tab_index = current_index
        for i in range(tab_count):
            state = "normal" if i == current_index else "disabled"
            self.notebook.tab(i, state=state)

    def _enter_modal(self, window):
        window.transient(self.frame.winfo_toplevel())
        if self._modal_depth == 0:
            self._set_tabs_enabled(False)
        self._modal_depth += 1

    def _exit_modal(self):
        self._modal_depth = max(0, self._modal_depth - 1)
        if self._modal_depth == 0:
            # Only re-enable tabs if settings view is not active
            if not self._settings_view_active:
                self._set_tabs_enabled(True)

    # ---------- Icon helpers ----------
    def _load_icon_image(self, path, size=(100, 128)):
        if not os.path.isfile(path):
            return None
        return ImageTk.PhotoImage(Image.open(path).resize(size, Image.LANCZOS))

    def _load_gif_frames(self, path, size=(100, 128)):
        if not os.path.isfile(path):
            return [], []
        frames = []
        delays = []
        gif = Image.open(path)
        for frame in ImageSequence.Iterator(gif):
            frames.append(ImageTk.PhotoImage(frame.resize(size, Image.LANCZOS)))
            delay = frame.info.get("duration", 100)
            delays.append(max(1, int(delay / max(GIF_SPEED_FACTOR, 0.01))))
        return frames, delays

    def _animate_rpc_gif(self):
        if not self.rpc_gif_frames:
            return
        self.rpc_gif_index = (self.rpc_gif_index + 1) % len(self.rpc_gif_frames)
        self.lbl_rpc_icon.config(image=self.rpc_gif_frames[self.rpc_gif_index])
        delay = self.rpc_gif_delays[self.rpc_gif_index] if self.rpc_gif_delays else 100
        self.rpc_gif_after_id = self.frame.after(delay, self._animate_rpc_gif)

    def _animate_count_gif(self):
        if not self.count_gif_frames:
            return
        self.count_gif_index = (self.count_gif_index + 1) % len(self.count_gif_frames)
        self.lbl_count_icon.config(image=self.count_gif_frames[self.count_gif_index])
        delay = self.count_gif_delays[self.count_gif_index] if self.count_gif_delays else 100
        self.count_gif_after_id = self.frame.after(delay, self._animate_count_gif)
    
    def _animate_audio_gif(self):
        if not self.audio_gif_frames:
            return
        self.audio_gif_index = (self.audio_gif_index + 1) % len(self.audio_gif_frames)
        self.lbl_audio_icon.config(image=self.audio_gif_frames[self.audio_gif_index])
        delay = self.audio_gif_delays[self.audio_gif_index] if self.audio_gif_delays else 100
        self.audio_gif_after_id = self.frame.after(delay, self._animate_audio_gif)

    def _stop_gif_loops(self):
        if self.rpc_gif_after_id is not None:
            self.frame.after_cancel(self.rpc_gif_after_id)
            self.rpc_gif_after_id = None
        if self.count_gif_after_id is not None:
            self.frame.after_cancel(self.count_gif_after_id)
            self.count_gif_after_id = None
        if self.audio_gif_after_id is not None:
            self.frame.after_cancel(self.audio_gif_after_id)
            self.audio_gif_after_id = None

    def _set_inactive_icons(self):
        self._stop_gif_loops()
        # When stopped, show enabled or inactive based on whether features are enabled
        if self.auto_count_var.get():
            self.count_icon_img = self._load_icon_image(ICON_COUNT_ENABLED_PATH)
        else:
            self.count_icon_img = self._load_icon_image(ICON_COUNT_INACTIVE_PATH)
        
        if self.rpc_enabled_var.get():
            self.rpc_icon_img = self._load_icon_image(ICON_RPC_ENABLED_PATH)
        else:
            self.rpc_icon_img = self._load_icon_image(ICON_RPC_INACTIVE_PATH)
        
        if self.audio_enabled_var.get():
            self.audio_icon_img = self._load_icon_image(ICON_AUDIO_ENABLED_PATH)
        else:
            self.audio_icon_img = self._load_icon_image(ICON_AUDIO_INACTIVE_PATH)
        
        if self.rpc_icon_img:
            self.lbl_rpc_icon.config(image=self.rpc_icon_img)
        if self.count_icon_img:
            self.lbl_count_icon.config(image=self.count_icon_img)
        if self.audio_icon_img:
            self.lbl_audio_icon.config(image=self.audio_icon_img)

    def _set_active_icons(self):
        self._stop_gif_loops()
        if self.auto_count_var.get():
            self.count_gif_frames, self.count_gif_delays = self._load_gif_frames(ICON_COUNT_ACTIVE_PATH)
            if self.count_gif_frames:
                self.lbl_count_icon.config(image=self.count_gif_frames[0])
                self.count_gif_index = 0
                self._animate_count_gif()
        else:
            # When not enabled, show inactive icon
            self.count_icon_img = self._load_icon_image(ICON_COUNT_INACTIVE_PATH)
            if self.count_icon_img:
                self.lbl_count_icon.config(image=self.count_icon_img)

        if self.rpc_enabled_var.get():
            self.rpc_gif_frames, self.rpc_gif_delays = self._load_gif_frames(ICON_RPC_ACTIVE_PATH)
            if self.rpc_gif_frames:
                self.lbl_rpc_icon.config(image=self.rpc_gif_frames[0])
                self.rpc_gif_index = 0
                self._animate_rpc_gif()
        else:
            # When not enabled, show inactive icon
            self.rpc_icon_img = self._load_icon_image(ICON_RPC_INACTIVE_PATH)
            if self.rpc_icon_img:
                self.lbl_rpc_icon.config(image=self.rpc_icon_img)
        
        if self.audio_enabled_var.get():
            self.audio_gif_frames, self.audio_gif_delays = self._load_gif_frames(ICON_AUDIO_ACTIVE_PATH)
            if self.audio_gif_frames:
                self.lbl_audio_icon.config(image=self.audio_gif_frames[0])
                self.audio_gif_index = 0
                self._animate_audio_gif()
        else:
            # When not enabled, show inactive icon
            self.audio_icon_img = self._load_icon_image(ICON_AUDIO_INACTIVE_PATH)
            if self.audio_icon_img:
                self.lbl_audio_icon.config(image=self.audio_icon_img)

    def _should_play_alert_for(self, source):
        if source == "manual":
            return self.alert_play_manual
        if source == "hotkey":
            return self.alert_play_hotkey
        if source == "auto":
            return self.alert_play_auto
        return False

    def _play_alert_sound(self, audio_path, use_cooldown=True):
        if winsound is None:
            show_custom_error(
                "count_error",
                "Error ID 77304512: Missing Package",
                "The alert audio package is missing or failed to initialize."
            )
            return

        if not audio_path or not os.path.isfile(audio_path):
            return

        if use_cooldown:
            now = time.monotonic()
            if now - self.alert_last_play_time < ALERT_COOLDOWN_SECONDS:
                return
            self.alert_last_play_time = now

        def play_audio():
            try:
                winsound.PlaySound(audio_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception:
                pass

        threading.Thread(target=play_audio, daemon=True).start()

    def _maybe_play_alert(self):
        if not self.is_running:
            return
        if not self.audio_enabled_var.get():
            return
        if not self.alert_sound_file:
            return

        audio_path = os.path.join(ALERTS_AUDIO_FOLDER, self.alert_sound_file)
        self._play_alert_sound(audio_path, use_cooldown=True)

    def open_settings_window(self):
        # If already in settings view, do nothing
        if self._settings_view_active:
            return

        # Store pack info for all profile page widgets before hiding them
        self._profile_widgets_pack_info = []
        for widget in self.container.winfo_children():
            pack_info = widget.pack_info()
            self._profile_widgets_pack_info.append((widget, pack_info))
            widget.pack_forget()

        # Hide the container itself to bypass its padding
        self._original_container_pack_info = self.container.pack_info()
        self.container.pack_forget()

        # Create settings frame directly in the parent frame (bypassing container)
        self._settings_frame = tk.Frame(self.frame, bg=DARK_BG)
        self._settings_frame.pack(padx=10, pady=6, fill="both", expand=True)
        self._settings_view_active = True
        ProfileTab._global_settings_open = True  # Mark settings as globally open
        
        # Disable other profile tabs
        update_profile_tabs_state()

        # Add profile name editor at top
        tk.Label(
            self._settings_frame,
            text="Profile Name:",
            bg=DARK_BG,
            fg=DARK_FG,
            font=(FONT_NAME, BASE_FONT_SIZE, "bold")
        ).pack(pady=(0, 4))
        
        # Store initial profile name for change detection (stripped once)
        initial_profile_name = self.profile_name_var.get().strip()
        
        self.profile_name_entry = tk.Entry(
            self._settings_frame,
            textvariable=self.profile_name_var,
            font=(FONT_NAME, BASE_FONT_SIZE),
            justify="center",
            width=20
        )
        self.profile_name_entry.pack(pady=(0, 4))
        
        # Apply button for profile name
        def check_profile_name_changes():
            """Check if profile name has changed from initial value."""
            current_name = self.profile_name_var.get().strip()
            return current_name != initial_profile_name
        
        def update_profile_name_apply_button_color():
            """Update Apply button color based on whether name has changed."""
            try:
                if check_profile_name_changes():
                    profile_name_apply_btn.config(bg=START_ACTIVE_COLOR, activebackground=START_ACTIVE_COLOR)
                else:
                    profile_name_apply_btn.config(bg=DARK_BUTTON, activebackground=DARK_BUTTON)
            except tk.TclError:
                # Button has been destroyed (settings closed), ignore
                pass
        
        def apply_profile_name_changes():
            """Apply profile name changes - validate and save."""
            nonlocal initial_profile_name
            current = self.profile_name_var.get().strip()
            
            # Check if empty
            if not current:
                self.profile_name_var.set(self.default_tab_name)
                self.set_tab_title()
                self.mark_dirty()
                initial_profile_name = self.default_tab_name.strip()
                update_profile_name_apply_button_color()
                return
            
            # Check for duplicate names (excluding current profile)
            all_profiles = globals().get('profiles', [])
            current_lower = current.lower()
            for other_profile in all_profiles:
                if other_profile is self:
                    continue
                other_name = other_profile.profile_name_var.get().strip()
                if other_name.lower() == current_lower:
                    # Duplicate found - show error and revert
                    show_custom_error(
                        "duplicate_name",
                        "Duplicate Profile Name",
                        f"Profile name '{current}' is already in use by another profile.\nPlease choose a different name."
                    )
                    self.profile_name_var.set(initial_profile_name)
                    update_profile_name_apply_button_color()
                    return
            
            # Valid name - update and save
            self.set_tab_title()
            # Save immediately instead of waiting for autosave so name persists when navigating menus
            self.save_settings_silent()
            initial_profile_name = current
            # Update the instance variable so it persists when navigating menus
            self.profile_name = current
            update_profile_name_apply_button_color()
        
        profile_name_apply_btn = tk.Button(
            self._settings_frame,
            text="Apply",
            command=apply_profile_name_changes,
            height=BUTTON_HEIGHT
        )
        profile_name_apply_btn.pack(pady=(0, 12), ipadx=10)  # 20px wider than before (10px per side)
        
        # Initialize button color first
        update_profile_name_apply_button_color()
        
        # Bind trace to detect changes (note: trace is on instance var, will be cleaned up with instance)
        # Added after initialization to avoid triggering during setup
        self.profile_name_var.trace_add("write", lambda *args: update_profile_name_apply_button_color())

        def open_hotkeys_from_settings():
            self._validate_and_fix_profile_name()
            self._reset_profile_name_to_saved()  # Discard unapplied changes
            self._clear_profile_name_focus()  # Clear focus from profile name entry
            open_hotkeys_inline(self)

        def open_configure_from_settings():
            self._validate_and_fix_profile_name()
            self._reset_profile_name_to_saved()  # Discard unapplied changes
            self._clear_profile_name_focus()  # Clear focus from profile name entry
            self.open_configure_inline()

        def open_rpc_from_settings():
            self._validate_and_fix_profile_name()
            self._reset_profile_name_to_saved()  # Discard unapplied changes
            self._clear_profile_name_focus()  # Clear focus from profile name entry
            self.open_rpc_inline()

        def open_alerts_from_settings():
            self._validate_and_fix_profile_name()
            self._reset_profile_name_to_saved()  # Discard unapplied changes
            self._clear_profile_name_focus()  # Clear focus from profile name entry
            self.open_alert_settings_inline()

        def open_reset_from_settings():
            self._validate_and_fix_profile_name()
            self._reset_profile_name_to_saved()  # Discard unapplied changes
            self._clear_profile_name_focus()  # Clear focus from profile name entry
            self.open_reset_profile_inline()

        def open_report_bug_from_settings():
            self._validate_and_fix_profile_name()
            self._reset_profile_name_to_saved()  # Discard unapplied changes
            self._clear_profile_name_focus()  # Clear focus from profile name entry
            self.open_report_bug_inline()
        
        def open_credits_from_settings():
            self._validate_and_fix_profile_name()
            self._reset_profile_name_to_saved()  # Discard unapplied changes
            self._clear_profile_name_focus()  # Clear focus from profile name entry
            self.open_credits_inline()

        tk.Button(
            self._settings_frame,
            text="Configure Alerts",
            command=open_alerts_from_settings,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=BUTTON_HEIGHT
        ).pack(pady=STANDARD_BUTTON_PADY, ipadx=STANDARD_BUTTON_IPADX)

        tk.Button(
            self._settings_frame,
            text="Configure Auto",
            command=open_configure_from_settings,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=BUTTON_HEIGHT
        ).pack(pady=STANDARD_BUTTON_PADY, ipadx=STANDARD_BUTTON_IPADX)

        tk.Button(
            self._settings_frame,
            text="Configure RPC",
            command=open_rpc_from_settings,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=BUTTON_HEIGHT
        ).pack(pady=STANDARD_BUTTON_PADY, ipadx=STANDARD_BUTTON_IPADX)

        tk.Button(
            self._settings_frame,
            text="Hotkeys",
            command=open_hotkeys_from_settings,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=BUTTON_HEIGHT
        ).pack(pady=STANDARD_BUTTON_PADY, ipadx=STANDARD_BUTTON_IPADX)

        tk.Button(
            self._settings_frame,
            text="Reset Profile",
            command=open_reset_from_settings,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=BUTTON_HEIGHT
        ).pack(pady=STANDARD_BUTTON_PADY, ipadx=STANDARD_BUTTON_IPADX)

        # Blank line between Reset Profile and Report a Bug (5x bigger = 50px)
        spacer = tk.Frame(self._settings_frame, bg=DARK_BG, height=50)
        spacer.pack()

        tk.Button(
            self._settings_frame,
            text="Report a Bug",
            command=open_report_bug_from_settings,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=BUTTON_HEIGHT
        ).pack(pady=STANDARD_BUTTON_PADY, ipadx=STANDARD_BUTTON_IPADX)
        
        tk.Button(
            self._settings_frame,
            text="Credits",
            command=open_credits_from_settings,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=BUTTON_HEIGHT
        ).pack(pady=STANDARD_BUTTON_PADY, ipadx=STANDARD_BUTTON_IPADX)

        tooltip_var = tk.BooleanVar(value=TOOLTIP_ENABLED)

        def on_toggle_tooltips():
            global TOOLTIP_ENABLED
            TOOLTIP_ENABLED = tooltip_var.get()
            save_tooltip_enabled(TOOLTIP_ENABLED)

        tk.Checkbutton(
            self._settings_frame,
            text="Enable Tooltips",
            variable=tooltip_var,
            command=on_toggle_tooltips,
            bg=DARK_BG,
            fg=DARK_FG,
            activebackground=DARK_BG,
            activeforeground=DARK_FG,
            selectcolor=DARK_BG
        ).pack(pady=STANDARD_BUTTON_PADY)

        def close_settings():
            self.close_settings_view()

        # Back button at bottom with larger size - pack with side="bottom" FIRST
        tk.Button(
            self._settings_frame,
            text="Back",
            command=close_settings,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=2
        ).pack(pady=STANDARD_BUTTON_PADY, side="bottom", ipadx=STANDARD_BUTTON_IPADX)

        # Add expanding spacer after Back button to fill remaining space
        spacer_settings = tk.Frame(self._settings_frame, bg=DARK_BG)
        spacer_settings.pack(fill="both", expand=True)
        
        # Make settings frame and all non-interactive children draggable (after all widgets created)
        self._bind_drag_recursively(self._settings_frame)

    def close_settings_view(self):
        """Close the settings view and restore the profile page."""
        if not self._settings_view_active:
            return

        # Reset profile name to saved value (discard any unapplied changes)
        self._reset_profile_name_to_saved()
        
        # Clear focus from profile name entry
        self._clear_profile_name_focus()

        # Destroy the settings frame
        if self._settings_frame:
            self._settings_frame.destroy()
            self._settings_frame = None
        
        # Destroy any sub-setting frame
        if hasattr(self, '_sub_setting_frame') and self._sub_setting_frame:
            try:
                self._sub_setting_frame.destroy()
            except tk.TclError:
                pass
            self._sub_setting_frame = None

        self._settings_view_active = False
        ProfileTab._global_settings_open = False  # Mark settings as globally closed
        ProfileTab._global_sub_setting_active = None  # Also clear any sub-setting flag
        self._current_sub_setting = None  # Clear tracking
        
        # Re-enable all profile tabs
        update_profile_tabs_state()
        
        # Restore the container with its original pack info
        if hasattr(self, '_original_container_pack_info'):
            self.container.pack(**self._original_container_pack_info)

        # Restore all profile page widgets with their original pack info
        if hasattr(self, '_profile_widgets_pack_info'):
            for widget, pack_info in self._profile_widgets_pack_info:
                if widget.winfo_exists():
                    widget.pack(**pack_info)
            self._profile_widgets_pack_info = []

    def _show_sub_setting(self, title=""):
        """Hide settings menu and prepare to show a sub-setting."""
        # Close any existing sub-setting frame first to prevent duplicates
        if hasattr(self, '_sub_setting_frame') and self._sub_setting_frame:
            try:
                self._sub_setting_frame.destroy()
            except tk.TclError:
                pass
            self._sub_setting_frame = None
            # Force UI update to ensure old frame is removed
            try:
                self.frame.update_idletasks()
            except tk.TclError:
                pass
        
        if self._settings_frame and self._settings_frame.winfo_exists():
            self._settings_frame.pack_forget()
        
        # Create sub-setting frame
        self._sub_setting_frame = tk.Frame(self.frame, bg=DARK_BG)
        self._sub_setting_frame.pack(padx=10, pady=6, fill="both", expand=True)
        
        return self._sub_setting_frame
    
    def _finalize_sub_setting(self):
        """Apply drag binding to sub-setting frame after all widgets are created."""
        if hasattr(self, '_sub_setting_frame') and self._sub_setting_frame:
            self._bind_drag_recursively(self._sub_setting_frame)

    def _close_sub_setting(self):
        """Close sub-setting and return to settings menu."""
        if hasattr(self, '_sub_setting_frame') and self._sub_setting_frame:
            try:
                self._sub_setting_frame.destroy()
            except tk.TclError:
                pass
            self._sub_setting_frame = None
        
        # Clear global sub-setting flag
        ProfileTab._global_sub_setting_active = None
        self._current_sub_setting = None  # Clear tracking
        
        # Restore settings menu frame
        if self._settings_frame and self._settings_frame.winfo_exists():
            self._settings_frame.pack(padx=10, pady=6, fill="both", expand=True)

    def _sync_settings_state(self):
        """Sync settings menu state when switching tabs - directly manipulate widgets"""
        # Removed early return - was blocking sync on profiles with existing frames
        # Let sync logic handle all cases properly
        
        # Check if widgets are actually packed (not just flag values)
        settings_frame_packed = (
            hasattr(self, '_settings_frame') and 
            self._settings_frame and 
            self._settings_frame.winfo_manager()
        )
        profile_frame_packed = (
            hasattr(self, '_profile_frame') and 
            self._profile_frame and 
            self._profile_frame.winfo_manager()
        )
        
        if ProfileTab._global_settings_open:
            # Settings should be visible
            if not settings_frame_packed:
                # Force flag to opposite state to bypass early return
                self._settings_view_active = False
                self.open_settings_window()
            # Make sure profile frame is hidden
            if profile_frame_packed:
                self._profile_frame.pack_forget()
            
            # Check if a sub-setting should be open
            if ProfileTab._global_sub_setting_active:
                sub_setting = ProfileTab._global_sub_setting_active
                # Only open if different from what's currently open
                current_sub = getattr(self, '_current_sub_setting', None)
                if current_sub != sub_setting:
                    # Open the appropriate sub-setting for this profile
                    if sub_setting == "alerts":
                        self.open_alert_settings_inline()
                    elif sub_setting == "auto":
                        self.open_configure_inline()
                    elif sub_setting == "rpc":
                        self.open_rpc_inline()
                    elif sub_setting == "hotkeys":
                        open_hotkeys_inline(self)
                    elif sub_setting == "reset":
                        self.open_reset_profile_inline()
            else:
                # No sub-setting should be open - close any existing sub-setting
                # Note: We don't call _close_sub_setting() here to avoid redundantly setting
                # _global_sub_setting_active = None (it's already None in this branch)
                if hasattr(self, '_sub_setting_frame') and self._sub_setting_frame:
                    try:
                        self._sub_setting_frame.destroy()
                    except tk.TclError:
                        pass
                    self._sub_setting_frame = None
                    self._current_sub_setting = None  # Clear tracking
                    # Ensure main settings frame is visible
                    if self._settings_frame and self._settings_frame.winfo_exists():
                        self._settings_frame.pack(padx=10, pady=6, fill="both", expand=True)
        else:
            # Settings should be hidden
            if settings_frame_packed:
                # Force flag to opposite state to bypass early return
                self._settings_view_active = True
                self.close_settings_view()
            # Make sure profile frame is visible
            if not profile_frame_packed and hasattr(self, '_profile_frame') and self._profile_frame:
                self._profile_frame.pack(fill="both", expand=True)

    def open_alert_settings_window(self, parent_grab=None):
        if self.alert_window and self.alert_window.winfo_exists():
            self.alert_window.lift()
            return

        self.alert_window = tk.Toplevel(self.frame)
        apply_window_style(self.alert_window)
        self.alert_window.resizable(False, False)
        self.alert_window.configure(bg=DARK_BG)
        self.alert_window.geometry("400x450")

        self._enter_modal(self.alert_window)
        if parent_grab and parent_grab.winfo_exists():
            set_window_disabled(parent_grab, True)

        container = tk.Frame(self.alert_window, bg=DARK_BG)
        container.pack(padx=12, pady=12)

        enable_alerts_var = self.audio_enabled_var

        tk.Label(container, text="Select Alert Sound:", font=(FONT_NAME, BASE_FONT_SIZE, "bold")).pack(
            anchor="w", pady=(0, 6)
        )

        list_frame = tk.Frame(container, bg=DARK_BG)
        list_frame.pack(fill="both", expand=True)

        if self._alert_icon_selected is None:
            try:
                self._alert_icon_selected = tk.PhotoImage(
                    file=resource_path(os.path.join("assets", "ui", "audio_selected.png"))
                )
            except Exception:
                self._alert_icon_selected = None
        if self._alert_icon_unselected is None:
            try:
                self._alert_icon_unselected = tk.PhotoImage(
                    file=resource_path(os.path.join("assets", "ui", "audio_not_selected.png"))
                )
            except Exception:
                self._alert_icon_unselected = None

        tree = ttk.Treeview(list_frame, show="tree", selectmode="browse", height=4, style="AlertSound.Treeview")
        tree.pack(side="left", fill="both", expand=True)
        tree.column("#0", width=260, minwidth=200, anchor="w", stretch=True)
        tree._img_refs = [self._alert_icon_selected, self._alert_icon_unselected]

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)

        audio_files = []
        if os.path.isdir(ALERTS_AUDIO_FOLDER):
            for filename in os.listdir(ALERTS_AUDIO_FOLDER):
                if filename.lower().endswith(".wav"):
                    audio_files.append(filename)
        audio_files.sort(key=str.lower)

        display_to_file = {}
        item_ids = {}
        tree.tag_configure("alert", background=DARK_ACCENT, foreground=DARK_FG, font=(FONT_NAME, BASE_FONT_SIZE + 1))
        tree.tag_configure("alert-selected", background=START_ACTIVE_COLOR, foreground=DARK_FG, font=(FONT_NAME, BASE_FONT_SIZE + 1))
        suppress_initial_play = True
        def clear_initial_suppress():
            nonlocal suppress_initial_play
            suppress_initial_play = False
        padding_prefix = ""
        try:
            space_width = tkfont.Font(family=FONT_NAME, size=BASE_FONT_SIZE + 1).measure(" ")
            spaces = max(1, round(10 / max(space_width, 1)))
            padding_prefix = " " * spaces
        except Exception:
            padding_prefix = "  "

        if not audio_files:
            tree.insert("", "end", text="(No .wav files found)")
            tree.state(["disabled"])
        else:
            for filename in audio_files:
                display_name = os.path.splitext(filename)[0]
                display_to_file[display_name] = filename
                item_ids[display_name] = tree.insert(
                    "", "end", text=f"{padding_prefix}{display_name}", image=self._alert_icon_unselected, tags=("alert",)
                )

        def update_icons(selected_display):
            if not item_ids:
                return
            for name, item_id in item_ids.items():
                icon = self._alert_icon_selected if name == selected_display else self._alert_icon_unselected
                tree.item(item_id, image=icon or "")
                tree.item(item_id, tags=("alert-selected",) if name == selected_display else ("alert",))

        def on_select(_event=None):
            nonlocal suppress_initial_play
            if not audio_files:
                return
            selection = tree.selection()
            if not selection:
                return
            item_id = selection[0]
            # Find display name from item_ids
            selected_display = None
            for name, iid in item_ids.items():
                if iid == item_id:
                    selected_display = name
                    break
            if not selected_display:
                return
            selected = display_to_file.get(selected_display, "")
            if not selected:
                return
            self.alert_sound_file = selected
            update_icons(selected_display)
            if suppress_initial_play:
                return
            self._play_alert_sound(os.path.join(ALERTS_AUDIO_FOLDER, selected), use_cooldown=False)

        if self.alert_sound_file in audio_files:
            display_name = os.path.splitext(self.alert_sound_file)[0]
            if display_name in item_ids:
                try:
                    tree.selection_set(item_ids[display_name])
                    tree.see(item_ids[display_name])
                    update_icons(display_name)
                except Exception:
                    pass
        tree.after_idle(clear_initial_suppress)

        tk.Label(container, text="Play Alert For:", font=(FONT_NAME, BASE_FONT_SIZE, "bold")).pack(
            anchor="w", pady=(8, 4)
        )

        manual_var = tk.BooleanVar(value=self.alert_play_manual)
        hotkey_var = tk.BooleanVar(value=self.alert_play_hotkey)
        auto_var = tk.BooleanVar(value=self.alert_play_auto)

        # Track initial state for change detection
        initial_enabled = enable_alerts_var.get()
        initial_sound_file = self.alert_sound_file
        initial_manual = manual_var.get()
        initial_hotkey = hotkey_var.get()
        initial_auto = auto_var.get()

        def check_for_changes():
            """Check if any alert settings have changed"""
            if enable_alerts_var.get() != initial_enabled:
                return True
            if self.alert_sound_file != initial_sound_file:
                return True
            if manual_var.get() != initial_manual:
                return True
            if hotkey_var.get() != initial_hotkey:
                return True
            if auto_var.get() != initial_auto:
                return True
            return False

        def update_apply_button_color():
            """Update Apply button color based on whether changes exist"""
            if check_for_changes():
                apply_button.config(bg=START_ACTIVE_COLOR, activebackground=START_ACTIVE_COLOR)
            else:
                apply_button.config(bg=DARK_BUTTON, activebackground=DARK_BUTTON)

        manual_check = tk.Checkbutton(
            container,
            text="Manual Increment",
            variable=manual_var,
            command=update_apply_button_color,
            takefocus=0
        )
        manual_check.pack(anchor="w")

        hotkey_check = tk.Checkbutton(
            container,
            text="Hotkey Increment",
            variable=hotkey_var,
            command=update_apply_button_color,
            takefocus=0
        )
        hotkey_check.pack(anchor="w")

        auto_check = tk.Checkbutton(
            container,
            text="Automatic Increment",
            variable=auto_var,
            command=update_apply_button_color,
            takefocus=0
        )
        auto_check.pack(anchor="w")

        # Checkbox removed - functionality moved to icon button on main screen
        # enable_alerts_check.config(command=update_alerts_enabled_state)

        def apply_changes():
            """Save all alert settings"""
            # Save enabled state
            is_enabled = enable_alerts_var.get()
            self.audio_enabled = is_enabled
            self.update_config_value(CONFIG_KEY_ALERT_ENABLED, "1" if is_enabled else "0")
            
            # Save sound file selection
            if self.alert_sound_file:
                self.update_config_value(CONFIG_KEY_ALERT_SOUND, self.alert_sound_file)
            
            # Save play settings
            self.alert_play_manual = manual_var.get()
            self.alert_play_hotkey = hotkey_var.get()
            self.alert_play_auto = auto_var.get()
            self.update_config_value(CONFIG_KEY_ALERT_PLAY_MANUAL, "1" if self.alert_play_manual else "0")
            self.update_config_value(CONFIG_KEY_ALERT_PLAY_HOTKEY, "1" if self.alert_play_hotkey else "0")
            self.update_config_value(CONFIG_KEY_ALERT_PLAY_AUTO, "1" if self.alert_play_auto else "0")
            
            self.mark_dirty()
            
            # Close window
            if self.alert_window:
                self.alert_window.destroy()
            self.alert_window = None
            self._exit_modal()
            if parent_grab and parent_grab.winfo_exists():
                set_window_disabled(parent_grab, False)
                parent_grab.grab_set()
                parent_grab.focus_force()

        button_row = tk.Frame(container, bg=DARK_BG)
        button_row.pack(pady=(10, 0))

        button_row.grid_columnconfigure(0, weight=1)
        button_row.grid_columnconfigure(1, weight=1)

        def close_alerts():
            if self.alert_window:
                self.alert_window.destroy()
            self.alert_window = None
            self._exit_modal()
            if parent_grab and parent_grab.winfo_exists():
                set_window_disabled(parent_grab, False)
                parent_grab.grab_set()
                parent_grab.focus_force()

        apply_button = tk.Button(
            button_row,
            text="Apply",
            command=apply_changes,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=BUTTON_HEIGHT
        )
        apply_button.grid(row=0, column=0, padx=(0, 4), sticky="e")

        tk.Button(
            button_row,
            text="Close",
            command=close_alerts,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=BUTTON_HEIGHT
        ).grid(row=0, column=1, padx=(4, 0), sticky="w")

        # Update selection to track changes
        def on_select_with_tracking(_event=None):
            on_select(_event)
            update_apply_button_color()
        
        tree.bind("<<TreeviewSelect>>", on_select_with_tracking)

        # Initial state setup (after button creation)
        update_apply_button_color()

        self.alert_window.protocol("WM_DELETE_WINDOW", close_alerts)

        center_window(self.alert_window, self.frame.winfo_toplevel())

    def open_alert_settings_inline(self):
        """Open alert settings as an inline view (not popup)."""
        ProfileTab._global_sub_setting_active = "alerts"  # Set global flag
        container = self._show_sub_setting("Configure Alerts")
        self._current_sub_setting = "alerts"  # Track current sub-setting
        
        enable_alerts_var = self.audio_enabled_var

        tk.Label(container, text="Select Alert Sound:", font=(FONT_NAME, BASE_FONT_SIZE, "bold")).pack(
            anchor="w", pady=(0, 6), padx=12
        )

        list_frame = tk.Frame(container, bg=DARK_BG)
        list_frame.pack(fill="both", expand=True, padx=12)

        if self._alert_icon_selected is None:
            try:
                self._alert_icon_selected = tk.PhotoImage(
                    file=resource_path(os.path.join("assets", "ui", "audio_selected.png"))
                )
            except Exception:
                self._alert_icon_selected = None
        if self._alert_icon_unselected is None:
            try:
                self._alert_icon_unselected = tk.PhotoImage(
                    file=resource_path(os.path.join("assets", "ui", "audio_not_selected.png"))
                )
            except Exception:
                self._alert_icon_unselected = None

        tree = ttk.Treeview(list_frame, show="tree", selectmode="browse", height=4, style="AlertSound.Treeview")
        tree.pack(side="left", fill="both", expand=True)
        tree.column("#0", width=260, minwidth=200, anchor="w", stretch=True)
        tree._img_refs = [self._alert_icon_selected, self._alert_icon_unselected]

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)

        audio_files = []
        if os.path.isdir(ALERTS_AUDIO_FOLDER):
            for filename in os.listdir(ALERTS_AUDIO_FOLDER):
                if filename.lower().endswith(".wav"):
                    audio_files.append(filename)
        audio_files.sort(key=str.lower)

        display_to_file = {}
        item_ids = {}
        tree.tag_configure("alert", background=DARK_ACCENT, foreground=DARK_FG, font=(FONT_NAME, BASE_FONT_SIZE + 1))
        tree.tag_configure("alert-selected", background=START_ACTIVE_COLOR, foreground=DARK_FG, font=(FONT_NAME, BASE_FONT_SIZE + 1))
        suppress_initial_play = True
        def clear_initial_suppress():
            nonlocal suppress_initial_play
            suppress_initial_play = False
        padding_prefix = ""
        try:
            space_width = tkfont.Font(family=FONT_NAME, size=BASE_FONT_SIZE + 1).measure(" ")
            spaces = max(1, round(10 / max(space_width, 1)))
            padding_prefix = " " * spaces
        except Exception:
            padding_prefix = "  "

        if not audio_files:
            tree.insert("", "end", text="(No .wav files found)")
            tree.state(["disabled"])
        else:
            for filename in audio_files:
                display_name = os.path.splitext(filename)[0]
                display_to_file[display_name] = filename
                item_ids[display_name] = tree.insert(
                    "", "end", text=f"{padding_prefix}{display_name}", image=self._alert_icon_unselected, tags=("alert",)
                )

        def update_icons(selected_display):
            if not item_ids:
                return
            for name, item_id in item_ids.items():
                icon = self._alert_icon_selected if name == selected_display else self._alert_icon_unselected
                tree.item(item_id, image=icon or "")
                tree.item(item_id, tags=("alert-selected",) if name == selected_display else ("alert",))

        def on_select(_event=None):
            nonlocal suppress_initial_play
            if not audio_files:
                return
            selection = tree.selection()
            if not selection:
                return
            item_id = selection[0]
            selected_display = None
            for name, iid in item_ids.items():
                if iid == item_id:
                    selected_display = name
                    break
            if not selected_display:
                return

            selected = display_to_file.get(selected_display, "")
            if not selected:
                return

            self.alert_sound_file = selected
            update_icons(selected_display)
            if suppress_initial_play:
                return
            self._play_alert_sound(os.path.join(ALERTS_AUDIO_FOLDER, selected), use_cooldown=False)

        if self.alert_sound_file in audio_files:
            display_name = os.path.splitext(self.alert_sound_file)[0]
            if display_name in item_ids:
                try:
                    tree.selection_set(item_ids[display_name])
                    tree.see(item_ids[display_name])
                    update_icons(display_name)
                except Exception:
                    pass
        tree.after_idle(clear_initial_suppress)

        tk.Label(container, text="", bg=DARK_BG).pack(anchor="w", padx=12, pady=(2, 2))

        tk.Label(container, text="Play Alert For:", font=(FONT_NAME, BASE_FONT_SIZE, "bold")).pack(
            anchor="w", pady=(8, 4), padx=12
        )

        manual_var = tk.BooleanVar(value=self.alert_play_manual)
        hotkey_var = tk.BooleanVar(value=self.alert_play_hotkey)
        auto_var = tk.BooleanVar(value=self.alert_play_auto)

        # Track initial state for change detection
        initial_enabled = enable_alerts_var.get()
        initial_sound_file = self.alert_sound_file
        initial_manual = manual_var.get()
        initial_hotkey = hotkey_var.get()
        initial_auto = auto_var.get()

        def check_for_changes():
            if enable_alerts_var.get() != initial_enabled:
                return True
            if self.alert_sound_file != initial_sound_file:
                return True
            if manual_var.get() != initial_manual:
                return True
            if hotkey_var.get() != initial_hotkey:
                return True
            if auto_var.get() != initial_auto:
                return True
            return False

        def update_apply_button_color():
            changed = check_for_changes()
            if changed:
                apply_button.config(bg=START_ACTIVE_COLOR, activebackground=START_ACTIVE_COLOR)
            else:
                apply_button.config(bg=DARK_BUTTON, activebackground=DARK_BUTTON)

        checkbox_frame = tk.Frame(container, bg=DARK_BG)
        checkbox_frame.pack(anchor="w", padx=12)

        manual_check = tk.Checkbutton(
            checkbox_frame,
            text="Manual Increment",
            variable=manual_var,
            command=update_apply_button_color,
            takefocus=0
        )
        manual_check.pack(anchor="w")

        hotkey_check = tk.Checkbutton(
            checkbox_frame,
            text="Hotkey Increment",
            variable=hotkey_var,
            command=update_apply_button_color,
            takefocus=0
        )
        hotkey_check.pack(anchor="w")

        auto_check = tk.Checkbutton(
            checkbox_frame,
            text="Automatic Increment",
            variable=auto_var,
            command=update_apply_button_color,
            takefocus=0
        )
        auto_check.pack(anchor="w")

        def apply_changes():
            nonlocal initial_enabled, initial_sound_file, initial_manual, initial_hotkey, initial_auto
            is_enabled = enable_alerts_var.get()
            self.audio_enabled = is_enabled
            self.update_config_value(CONFIG_KEY_ALERT_ENABLED, "1" if is_enabled else "0")
            
            if self.alert_sound_file:
                self.update_config_value(CONFIG_KEY_ALERT_SOUND, self.alert_sound_file)
            
            self.alert_play_manual = manual_var.get()
            self.alert_play_hotkey = hotkey_var.get()
            self.alert_play_auto = auto_var.get()
            self.update_config_value(CONFIG_KEY_ALERT_PLAY_MANUAL, "1" if self.alert_play_manual else "0")
            self.update_config_value(CONFIG_KEY_ALERT_PLAY_HOTKEY, "1" if self.alert_play_hotkey else "0")
            self.update_config_value(CONFIG_KEY_ALERT_PLAY_AUTO, "1" if self.alert_play_auto else "0")
            
            self.mark_dirty()
            initial_enabled = enable_alerts_var.get()
            initial_sound_file = self.alert_sound_file
            initial_manual = manual_var.get()
            initial_hotkey = hotkey_var.get()
            initial_auto = auto_var.get()
            update_apply_button_color()

        def on_select_with_tracking(_event=None):
            on_select(_event)
            update_apply_button_color()
        
        tree.bind("<<TreeviewSelect>>", on_select_with_tracking)

        # Spacer to push buttons to bottom
        spacer = tk.Frame(container, bg=DARK_BG)
        spacer.pack(fill="both", expand=True)

        # Back button at bottom - 420px wide standard button
        tk.Button(
            container,
            text="Back",
            command=self._close_sub_setting,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=2
        ).pack(pady=STANDARD_BUTTON_PADY, side="bottom", ipadx=STANDARD_BUTTON_IPADX)

        # Apply button above Back - 420px wide standard button
        apply_button = tk.Button(
            container,
            text="Apply",
            command=apply_changes,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=BUTTON_HEIGHT
        )
        apply_button.pack(pady=STANDARD_BUTTON_PADY, side="bottom", ipadx=STANDARD_BUTTON_IPADX)

        # Initial state setup
        update_apply_button_color()
        
        # Make sub-setting draggable after all widgets created
        self._finalize_sub_setting()

    # ---------- Autosave helpers ----------
    def mark_dirty(self):
        if not self._loading_config:
            self._dirty = True

    def schedule_autosave(self):
        if self._autosave_after_id is not None:
            self.frame.after_cancel(self._autosave_after_id)
        self._autosave_after_id = self.frame.after(2000, self._autosave_check)

    def _autosave_check(self):
        if self._dirty:
            self.save_settings_silent()
            self._dirty = False
        self.schedule_autosave()

    def _sanitize_increment_value(self, value):
        if value < MIN_INCREMENT:
            return MIN_INCREMENT
        if value > MAX_INCREMENT:
            return MAX_INCREMENT
        return value

    def save_settings_silent(self):
        profile_name = self.profile_name_var.get().strip()[:PROFILE_NAME_MAX_LENGTH]
        if not profile_name:
            profile_name = self.default_tab_name
            self.profile_name_var.set(profile_name)

        title = self.title_var.get().strip()
        cooldown = int(self.cooldown_var.get())
        frequency = float(self.frequency_var.get())
        threshold = float(self.threshold_var.get())
        increment_amount = self.increment_var.get().strip() or str(MIN_INCREMENT)

        self.update_config_value(CONFIG_KEY_PROFILE_NAME, profile_name)
        self.update_config_value(CONFIG_KEY_TITLE, title)
        self.update_config_value(CONFIG_KEY_COOLDOWN, cooldown)
        self.update_config_value(CONFIG_KEY_FREQUENCY, frequency)
        self.update_config_value(CONFIG_KEY_THRESHOLD, threshold)
        self.update_config_value(CONFIG_KEY_IMAGE, self.selected_image_path)
        self.update_config_value(CONFIG_KEY_TEXT, self.selected_text_path)
        self.update_config_value(CONFIG_KEY_INCREMENT, increment_amount)
        self.update_config_value(CONFIG_KEY_RPC_ENABLED, "1" if self.rpc_enabled else "0")
        self.update_config_value(CONFIG_KEY_RPC_SUFFIX, self.rpc_counter_suffix)
        self.update_config_value(CONFIG_KEY_COUNT_PLUS, self.count_plus_hotkey)
        self.update_config_value(CONFIG_KEY_COUNT_MINUS, self.count_minus_hotkey)
        self.update_config_value(CONFIG_KEY_ALERT_SOUND, self.alert_sound_file)
        self.update_config_value(CONFIG_KEY_ALERT_ENABLED, "1" if self.audio_enabled_var.get() else "0")
        self.update_config_value(CONFIG_KEY_ALERT_PLAY_MANUAL, "1" if self.alert_play_manual else "0")
        self.update_config_value(CONFIG_KEY_ALERT_PLAY_HOTKEY, "1" if self.alert_play_hotkey else "0")
        self.update_config_value(CONFIG_KEY_ALERT_PLAY_AUTO, "1" if self.alert_play_auto else "0")

        self.set_tab_title()

    # ---------- Config helpers ----------
    def load_config_value(self, key, default_value):
        if not os.path.exists(self.config_path):
            return default_value

        with open(self.config_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.lower().startswith(key):
                    return line.split(":", 1)[1].strip()

        return default_value

    def update_config_value(self, key, value):
        lines = []
        found = False

        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

        for i, line in enumerate(lines):
            if line.lower().startswith(key):
                lines[i] = f"{key} {value}\n"
                found = True
                break

        if not found:
            lines.append(f"{key} {value}\n")

        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

    def _get_increment_amount(self):
        try:
            value = int(self.increment_var.get().strip() or str(MIN_INCREMENT))
        except ValueError:
            return MIN_INCREMENT
        return self._sanitize_increment_value(value)

    def set_count_hotkeys(self, plus_hotkey, minus_hotkey):
        self.count_plus_hotkey = plus_hotkey
        self.count_minus_hotkey = minus_hotkey
        self.update_config_value(CONFIG_KEY_COUNT_PLUS, plus_hotkey)
        self.update_config_value(CONFIG_KEY_COUNT_MINUS, minus_hotkey)
        self.mark_dirty()
        if hotkey_manager:
            hotkey_manager.refresh_profile_hotkeys()

    def _update_manual_buttons(self):
        if self.auto_count_var.get():
            self.btn_decrement.config(text="-1")
            self.btn_increment.config(text="+1")
        else:
            increment = self._get_increment_amount()
            self.btn_decrement.config(text=f"-{increment}")
            self.btn_increment.config(text=f"+{increment}")

    def _on_auto_count_toggle(self, *_):
        self._update_manual_buttons()
        self.set_settings_state(not self.is_running)

    def _on_increment_focus_out(self, _event=None):
        raw_value = self.increment_var.get().strip()
        if not raw_value:
            value = MIN_INCREMENT
        else:
            try:
                value = int(raw_value)
            except ValueError:
                value = MIN_INCREMENT
        value = self._sanitize_increment_value(value)
        self.increment_var.set(str(value))
        self.mark_dirty()
        self._update_manual_buttons()

    def _on_increment_change(self, *_):
        if self._loading_config:
            return
        self.mark_dirty()
        if not self.auto_count_var.get():
            self._update_manual_buttons()

    def _on_image_path_change(self, *_):
        self.selected_image_path = self.image_path_var.get().strip()
        self.mark_dirty()

    def _is_text_path_in_use(self, new_path):
        if not new_path:
            return False
        try:
            new_abs = os.path.abspath(new_path)
        except Exception:
            return False

        for profile in get_profiles():
            if profile is self:
                continue
            existing = profile.text_path_var.get().strip() or profile.selected_text_path
            if not existing:
                continue
            try:
                if os.path.abspath(existing) == new_abs:
                    return True
            except Exception:
                continue
        return False

    def _on_text_path_change(self, *_):
        if self._suppress_text_path_change:
            return

        new_path = self.text_path_var.get().strip()

        if not self._loading_config and new_path and self._is_text_path_in_use(new_path):
            show_custom_error(
                "count_error",
                "Error ID 10865961: Invalid File",
                "The counter file is currently being used on another profile. Please select another file.",
                parent=self.frame.winfo_toplevel()
            )
            self._suppress_text_path_change = True
            self.text_path_var.set(self._last_text_path)
            self._suppress_text_path_change = False
            return

        if not self._loading_config and self._last_text_path:
            if os.path.abspath(new_path) != os.path.abspath(self._last_text_path):
                self.reset_rpc_options()

        self.selected_text_path = new_path
        self._last_text_path = new_path
        self.mark_dirty()
        if new_path and os.path.isfile(new_path):
            try:
                current_value = read_number_from_file(new_path)
                self.lbl_current_count.config(text=str(current_value))
            except Exception:
                self.lbl_current_count.config(text="(invalid)")

    def _on_title_change(self, *_):
        self.mark_dirty()

    def _on_profile_name_change(self, *_):
        """Handle profile name changes on keystroke - only enforce max length."""
        current = self.profile_name_var.get().strip()
        if len(current) > PROFILE_NAME_MAX_LENGTH:
            current = current[:PROFILE_NAME_MAX_LENGTH]
            self.profile_name_var.set(current)
        # Don't auto-update tab title or mark dirty on keystroke
        # All validation and updates happen on focus out instead
    
    def _validate_and_fix_profile_name(self):
        """Validate profile name and set to default if empty/whitespace.
        
        This should be called before opening sub-menus to ensure the profile
        name is valid before rendering content that uses it.
        """
        current = self.profile_name_var.get().strip()
        if not current:
            # Set to default if empty or whitespace-only
            self.profile_name_var.set(self.default_tab_name)
            self.set_tab_title()
            self.mark_dirty()
    
    def _reset_profile_name_to_saved(self):
        """Reset profile name StringVar to saved config value, discarding unapplied changes."""
        saved_profile_name = self.load_config_value(CONFIG_KEY_PROFILE_NAME, "")
        if saved_profile_name:
            self.profile_name_var.set(saved_profile_name[:PROFILE_NAME_MAX_LENGTH])
        else:
            self.profile_name_var.set(self.default_tab_name)
    
    def _clear_profile_name_focus(self):
        """Clear focus from profile name entry field."""
        try:
            if hasattr(self, 'profile_name_entry') and self.profile_name_entry.winfo_exists():
                self.profile_name_entry.selection_clear()
                self.profile_name_entry.icursor(0)  # Reset cursor to start position
                # Move focus to the settings frame itself
                if self._settings_frame and self._settings_frame.winfo_exists():
                    self._settings_frame.focus_set()
        except tk.TclError:
            # Widget destroyed, ignore
            pass
    
    def _on_profile_name_focus_out(self, *_):
        """Validate profile name when user clicks outside the field."""
        current = self.profile_name_var.get().strip()
        
        # Check if empty (strip already handles whitespace-only)
        if not current:
            # Reset to default only when focus is lost with empty field
            self.profile_name_var.set(self.default_tab_name)
            self.set_tab_title()
            self.mark_dirty()
            return
        
        # Check for duplicate names (excluding current profile)
        all_profiles = globals().get('profiles', [])
        current_lower = current.lower()  # Convert once for efficiency
        for other_profile in all_profiles:
            if other_profile is self:
                continue  # Skip self
            other_name = other_profile.profile_name_var.get().strip()
            if other_name.lower() == current_lower:
                # Duplicate found - show error and revert
                show_custom_error(
                    "duplicate_name",
                    "Duplicate Profile Name",
                    f"Profile name '{current}' is already in use by another profile.\nPlease choose a different name."
                )
                # Revert to default name
                self.profile_name_var.set(self.default_tab_name)
                self.set_tab_title()
                self.mark_dirty()
                return
        
        # Valid name - update tab and save
        self.set_tab_title()
        self.mark_dirty()

    def reset_rpc_options(self):
        if self.rpc_is_running:
            self.stop_broadcast()

        self.rpc_game_id = ""
        self.rpc_target = ""
        self.rpc_odds = 8192
        self.rpc_enabled = False
        self.rpc_enabled_var.set(False)
        self.rpc_counter_suffix = "Encounters"

        self.update_config_value(CONFIG_KEY_RPC_GAME, "")
        self.update_config_value(CONFIG_KEY_RPC_TARGET, "")
        self.update_config_value(CONFIG_KEY_RPC_ODDS, "")
        self.update_config_value(CONFIG_KEY_RPC_ENABLED, "0")
        self.update_config_value(CONFIG_KEY_RPC_SUFFIX, self.rpc_counter_suffix)
        self.mark_dirty()

    def _on_root_drag_start(self, event):
        if self._modal_depth > 0:
            return
        if is_interactive_click(event):
            return
        self.frame.winfo_toplevel().focus_set()
        self._root_drag_offset = (event.x_root, event.y_root)

    def _on_root_drag(self, event):
        root = self.frame.winfo_toplevel()
        x = root.winfo_x() + (event.x_root - self._root_drag_offset[0])
        y = root.winfo_y() + (event.y_root - self._root_drag_offset[1])
        root.geometry(f"+{x}+{y}")
        self._root_drag_offset = (event.x_root, event.y_root)

    def _bind_root_drag(self, widget):
        widget.bind("<ButtonPress-1>", self._on_root_drag_start)
        widget.bind("<B1-Motion>", self._on_root_drag)
    
    def _bind_drag_recursively(self, widget):
        """Recursively bind drag events to widget and all non-interactive children."""
        # Use the global constant to ensure consistency and include all interactive widgets
        interactive_types = INTERACTIVE_DRAG_WIDGETS
        
        # Bind to the widget itself if it's not interactive
        if not isinstance(widget, interactive_types):
            self._bind_root_drag(widget)
        
        # Recursively bind to all children
        try:
            for child in widget.winfo_children():
                self._bind_drag_recursively(child)
        except AttributeError:
            # Widget doesn't have children
            pass

    def on_reset_profile(self):
        # Get current profile name for the dialog
        profile_name = self.profile_name_var.get() or self.default_tab_name
        
        # Show custom reset confirmation dialog
        if not show_reset_confirmation(profile_name, parent=self.frame.winfo_toplevel()):
            return

        if self.rpc_is_running:
            self.stop_broadcast()

        self.is_running = False
        self.btn_start.config(text="Start", bg=DARK_BUTTON, activebackground=DARK_BUTTON)

        self._loading_config = True
        self.auto_count_var.set(False)
        self.profile_name_var.set(self.default_tab_name)
        self.update_config_value(CONFIG_KEY_PROFILE_NAME, self.default_tab_name)
        self.title_var.set("")
        self.image_path_var.set("")
        self.text_path_var.set("")
        self.increment_var.set(str(MIN_INCREMENT))
        self.cooldown_var.set(5)
        self.frequency_var.set(0.5)
        self.threshold_var.set(0.9)

        self.count_plus_hotkey = ""
        self.count_minus_hotkey = ""

        # Reset global hotkeys to defaults
        if hotkey_manager:
            hotkey_manager.set_global_enabled(False)
            hotkey_manager.set_hotkeys(DEFAULT_HOTKEYS.copy())
            save_hotkeys_config(hotkey_manager.hotkeys, False)

        self.rpc_game_id = ""
        self.rpc_target = ""
        self.rpc_odds = 8192
        self.rpc_enabled = False
        self.rpc_enabled_var.set(False)
        self.rpc_counter_suffix = "Encounters"

        self.audio_enabled = False
        self.audio_enabled_var.set(False)
        self.alert_sound_file = "Notify.wav"
        self.alert_last_play_time = 0.0
        self.alert_play_manual = True
        self.alert_play_hotkey = True
        self.alert_play_auto = True

        self.selected_image_path = ""
        self.selected_text_path = ""
        self._last_text_path = ""
        self.last_match_time = 0.0
        self.lbl_current_count.config(text="0")

        self._loading_config = False

        self.update_config_value(CONFIG_KEY_RPC_GAME, "")
        self.update_config_value(CONFIG_KEY_RPC_TARGET, "")
        self.update_config_value(CONFIG_KEY_RPC_ODDS, "")
        self.update_config_value(CONFIG_KEY_RPC_SUFFIX, self.rpc_counter_suffix)
        self.update_config_value(CONFIG_KEY_RPC_ENABLED, "0")
        self.update_config_value(CONFIG_KEY_COUNT_PLUS, "")
        self.update_config_value(CONFIG_KEY_COUNT_MINUS, "")
        self.update_config_value(CONFIG_KEY_ALERT_SOUND, self.alert_sound_file)
        self.update_config_value(CONFIG_KEY_ALERT_ENABLED, "0")
        self.update_config_value(CONFIG_KEY_ALERT_PLAY_MANUAL, "1")
        self.update_config_value(CONFIG_KEY_ALERT_PLAY_HOTKEY, "1")
        self.update_config_value(CONFIG_KEY_ALERT_PLAY_AUTO, "1")

        self.save_settings_silent()
        self._update_manual_buttons()
        self.set_settings_state(True)
        self._set_inactive_icons()
        if hotkey_manager:
            hotkey_manager.refresh_profile_hotkeys()

    # ---------- Configure window dragging ----------
    def _on_configure_drag_start(self, event):
        self._drag_active = False
        self._drag_offset = (0, 0)
        return

    def _on_configure_drag(self, event):
        return

    # ---------- Test window dragging ----------
    def _on_test_drag_start(self, event):
        self._test_drag_offset = (0, 0)
        return

    def _on_test_drag(self, event):
        return

    # ---------- Window positioning ----------
    def _position_popup_near_root(self, window):
        root = self.frame.winfo_toplevel()
        root.update_idletasks()
        x = root.winfo_rootx() + 40
        y = root.winfo_rooty() + 60
        window.geometry(f"+{x}+{y}")

    def on_pick_window(self):
        picker = tk.Toplevel(self.frame)
        apply_window_style(picker)
        picker.resizable(False, False)
        picker.transient(self.frame.winfo_toplevel())
        picker.grab_set()

        frame = tk.Frame(picker, bg=DARK_BG)
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        listbox = tk.Listbox(frame, width=60, height=12)
        listbox.pack(side="left", fill="both", expand=True)

        # Dark mode styled scrollbar
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=listbox.yview, style="Rpc.Vertical.TScrollbar")
        scrollbar.pack(side="right", fill="y")
        listbox.config(yscrollcommand=scrollbar.set)

        # Track initial window title for change detection
        initial_title = self.title_var.get()

        def refresh_list():
            listbox.delete(0, tk.END)
            for title in list_window_titles():
                listbox.insert(tk.END, title)

        def update_use_selected_button():
            # Update button color based on whether selection differs from initial
            selection = listbox.curselection()
            if selection:
                chosen = listbox.get(selection[0])
                if chosen != initial_title:
                    use_selected_btn.config(bg=START_ACTIVE_COLOR, activebackground=START_ACTIVE_COLOR)
                else:
                    use_selected_btn.config(bg=DARK_BUTTON, activebackground=DARK_BUTTON)
            else:
                use_selected_btn.config(bg=DARK_BUTTON, activebackground=DARK_BUTTON)

        def apply_selection():
            selection = listbox.curselection()
            if not selection:
                return
            chosen = listbox.get(selection[0])
            self.title_var.set(chosen)
            picker.destroy()
            self.frame.winfo_toplevel().focus_force()

        def close_picker():
            picker.destroy()
            self.frame.winfo_toplevel().focus_force()

        refresh_list()

        # Bind selection event to update button color
        listbox.bind("<<ListboxSelect>>", lambda e: update_use_selected_button())

        button_row = tk.Frame(picker, bg=DARK_BG)
        button_row.pack(padx=10, pady=(0, 10))

        button_row.grid_columnconfigure(0, weight=1)
        button_row.grid_columnconfigure(1, weight=1)
        button_row.grid_columnconfigure(2, weight=1)

        use_selected_btn = tk.Button(
            button_row,
            text="Use Selected",
            command=apply_selection,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=BUTTON_HEIGHT
        )
        use_selected_btn.grid(row=0, column=0, padx=4)
        
        tk.Button(
            button_row,
            text="Refresh",
            command=refresh_list,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=BUTTON_HEIGHT
        ).grid(row=0, column=1, padx=4)
        tk.Button(
            button_row,
            text="Close",
            command=close_picker,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=BUTTON_HEIGHT
        ).grid(row=0, column=2, padx=4)

        center_window(picker, self.frame.winfo_toplevel())

    # ---------- UI ----------
    def build_ui(self):
        frame = self.frame

        self.container = tk.Frame(frame, bg=DARK_BG)
        self.container.pack(pady=(6, 0), anchor="n")  # Only top padding, no bottom padding
        self._bind_root_drag(self.container)

        def make_row(pady=5):
            row = tk.Frame(self.container, bg=DARK_BG)
            row.pack(pady=pady, anchor="center")
            self._bind_root_drag(row)
            return row

        # Capture Window
        row_title_label = make_row(pady=0)
        row_title_label.pack_configure(fill="x")

        self.label_title = tk.Label(row_title_label, text="Capture Window:", font=(FONT_NAME, BASE_FONT_SIZE, "bold"))
        self.label_title.pack(anchor="center", padx=10)
        add_tooltip(self.label_title, "When auto is enabled, Rotom will use this window to scan for the provided reference frame.")

        row_title = make_row()
        self.entry_title = tk.Entry(row_title, width=40, textvariable=self.title_var)
        self.entry_title.pack(side="left", padx=(10, 0))  # No right padding to attach to browse button
        self.btn_pick_window = tk.Button(
            row_title,
            text="...",
            command=self.on_pick_window,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=BUTTON_HEIGHT,
            font=(FONT_NAME, SMALL_BUTTON_FONT_SIZE)
        )
        self.btn_pick_window.pack(side="left", padx=(0, 0))

        spacer_capture_ref = tk.Frame(self.container, bg=DARK_BG, height=10)
        spacer_capture_ref.pack(pady=6)
        self._bind_root_drag(spacer_capture_ref)

        # Reference Frame
        row_image_label = make_row(pady=0)
        self.lbl_image = tk.Label(row_image_label, text="Reference Frame:", font=(FONT_NAME, BASE_FONT_SIZE, "bold"))
        self.lbl_image.pack(side="left", padx=10)
        add_tooltip(self.lbl_image, "When auto is enabled, Rotom will scan for this reference frame in the provided window.")

        row_image = make_row()
        self.entry_image_path = tk.Entry(row_image, width=40, textvariable=self.image_path_var)
        self.entry_image_path.pack(side="left", padx=(10, 0))  # No right padding to attach to browse button
        self.btn_browse_image = tk.Button(
            row_image,
            text="...",
            command=self.on_browse_image,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=BUTTON_HEIGHT,
            font=(FONT_NAME, SMALL_BUTTON_FONT_SIZE)
        )
        self.btn_browse_image.pack(side="left", padx=(0, 0))

        row_capture_button = make_row(pady=5)
        self.btn_capture_image = tk.Button(
            row_capture_button,
            text="Capture New Reference Frame",
            command=self.on_capture_reference,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=BUTTON_HEIGHT,
            font=(FONT_NAME, SMALL_BUTTON_FONT_SIZE)
        )
        self.btn_capture_image.pack(side="left", padx=10)

        spacer_ref_counter = tk.Frame(self.container, bg=DARK_BG, height=18)
        spacer_ref_counter.pack(pady=10)
        self._bind_root_drag(spacer_ref_counter)

        # Counter File
        row_text_label = make_row(pady=0)
        self.lbl_text = tk.Label(row_text_label, text="Counter File:", font=(FONT_NAME, BASE_FONT_SIZE, "bold"))
        self.lbl_text.pack(side="left", padx=10)
        add_tooltip(self.lbl_text, "This file will be used for Rotom to update your count, whenever it is incremented.")

        row_text = make_row()
        self.entry_text_path = tk.Entry(row_text, width=40, textvariable=self.text_path_var)
        self.entry_text_path.pack(side="left", padx=(10, 0))  # No right padding to attach to browse button
        self.btn_browse_text = tk.Button(
            row_text,
            text="...",
            command=self.on_browse_text,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=BUTTON_HEIGHT,
            font=(FONT_NAME, SMALL_BUTTON_FONT_SIZE)
        )
        self.btn_browse_text.pack(side="left", padx=(0, 0))

        spacer_counter_increment = tk.Frame(self.container, bg=DARK_BG, height=10)
        spacer_counter_increment.pack(pady=6)
        self._bind_root_drag(spacer_counter_increment)

        # Increment + Counter Row
        row_counter_increment = make_row()
        self.btn_decrement = tk.Button(
            row_counter_increment,
            text="-1",
            width=6,
            height=COUNTER_BUTTON_HEIGHT,
            font=(FONT_NAME, BASE_FONT_SIZE, "bold"),
            command=lambda: self.on_manual_adjust(-1, source="manual")
        )
        self.btn_decrement.pack(side="left", padx=(4, 0))
        self.lbl_current_count = tk.Label(
            row_counter_increment,
            text="0",
            font=(FONT_NAME, LARGE_FONT_SIZE, "bold"),
            width=7,
            relief="solid",
            bd=1,
            padx=8,
            pady=2
        )
        self.lbl_current_count.pack(side="left", padx=0)
        self.btn_increment = tk.Button(
            row_counter_increment,
            text="+1",
            width=6,
            height=COUNTER_BUTTON_HEIGHT,
            font=(FONT_NAME, BASE_FONT_SIZE, "bold"),
            command=lambda: self.on_manual_adjust(1, source="manual")
        )
        self.btn_increment.pack(side="left", padx=(0, 12))

        self.lbl_increment = tk.Label(row_counter_increment, text="Increment:", font=(FONT_NAME, BASE_FONT_SIZE, "bold"))
        self.lbl_increment.pack(side="left", padx=(0, 4))
        add_tooltip(self.lbl_increment, "Rotom will increase or decrease the current count by this number, each time there is a change.")
        self.entry_increment = tk.Entry(row_counter_increment, width=3, textvariable=self.increment_var, justify="center")
        # 5px left padding to match spacing, 10px right padding for visual separation from next element
        self.entry_increment.pack(side="left", padx=(5, 10))
        self.entry_increment.bind("<FocusOut>", self._on_increment_focus_out)

        spacer_increment_to_rpc = tk.Frame(self.container, bg=DARK_BG, height=0)
        spacer_increment_to_rpc.pack(pady=0)
        self._bind_root_drag(spacer_increment_to_rpc)

        row_rpc_enable = make_row(pady=0)
        row_rpc_enable.grid_columnconfigure(0, weight=1, uniform="icons")
        row_rpc_enable.grid_columnconfigure(1, weight=1, uniform="icons")
        row_rpc_enable.grid_columnconfigure(2, weight=1, uniform="icons")

        self.rpc_icon_img = self._load_icon_image(ICON_RPC_INACTIVE_PATH)
        self.count_icon_img = self._load_icon_image(ICON_COUNT_INACTIVE_PATH)
        self.audio_icon_img = self._load_icon_image(ICON_AUDIO_INACTIVE_PATH)

        # Audio icon (leftmost)
        self.lbl_audio_icon = tk.Label(row_rpc_enable, image=self.audio_icon_img, bg=DARK_BG, cursor="hand2")
        self.lbl_audio_icon.grid(row=0, column=0, padx=10, pady=(0, 2), sticky="n")

        # Count/Auto icon (middle)
        self.lbl_count_icon = tk.Label(row_rpc_enable, image=self.count_icon_img, bg=DARK_BG, cursor="hand2")
        self.lbl_count_icon.grid(row=0, column=1, padx=10, pady=(0, 2), sticky="n")

        # RPC icon (rightmost)
        self.lbl_rpc_icon = tk.Label(row_rpc_enable, image=self.rpc_icon_img, bg=DARK_BG, cursor="hand2")
        self.lbl_rpc_icon.grid(row=0, column=2, padx=10, pady=(0, 2), sticky="n")

        # Define toggle functions BEFORE creating buttons that use them
        def _toggle_auto_count():
            self.auto_count_var.set(not self.auto_count_var.get())
            self._on_auto_count_toggle()

        def _toggle_rpc_enabled():
            self.rpc_enabled_var.set(not self.rpc_enabled_var.get())
            self.on_toggle_rpc_enabled()

        self._toggle_auto_count = _toggle_auto_count
        self._toggle_rpc_enabled = _toggle_rpc_enabled

        # Create text labels below icons
        self.lbl_audio_text = tk.Label(row_rpc_enable, text="Alerts", bg=DARK_BG, fg=DARK_FG)
        self.lbl_audio_text.grid(row=1, column=0, padx=10, sticky="n")
        add_tooltip(self.lbl_audio_text, "When enabled, Rotom will give you audio alerts when the counter is incremented.")
        
        self.lbl_count_text = tk.Label(row_rpc_enable, text="Auto", bg=DARK_BG, fg=DARK_FG)
        self.lbl_count_text.grid(row=1, column=1, padx=10, sticky="n")
        add_tooltip(self.lbl_count_text, "When enabled, Rotom will scan a window automatically for a reference frame and increment the counter when it is detected.")

        self.rpc_enabled_var = tk.BooleanVar(value=False)
        self.lbl_rpc_text = tk.Label(row_rpc_enable, text="RPC", bg=DARK_BG, fg=DARK_FG)
        self.lbl_rpc_text.grid(row=1, column=2, padx=10, sticky="n")
        add_tooltip(self.lbl_rpc_text, "When enabled, Rotom will broadcast your current hunt details to Discord Rich Presence.")

        # Update icon appearance based on state
        def update_auto_icon_appearance(*args):
            # Only update if not running - running state is handled by _set_active_icons
            if not self.is_running:
                if self.auto_count_var.get():
                    # Enabled but not running
                    self.count_icon_img = self._load_icon_image(ICON_COUNT_ENABLED_PATH)
                    if self.count_icon_img:
                        self.lbl_count_icon.config(image=self.count_icon_img)
                else:
                    # Disabled
                    self.count_icon_img = self._load_icon_image(ICON_COUNT_INACTIVE_PATH)
                    if self.count_icon_img:
                        self.lbl_count_icon.config(image=self.count_icon_img)

        def update_rpc_icon_appearance(*args):
            # Only update if not running - running state is handled by _set_active_icons
            if not self.is_running:
                if self.rpc_enabled_var.get():
                    # Enabled but not running
                    self.rpc_icon_img = self._load_icon_image(ICON_RPC_ENABLED_PATH)
                    if self.rpc_icon_img:
                        self.lbl_rpc_icon.config(image=self.rpc_icon_img)
                else:
                    # Disabled
                    self.rpc_icon_img = self._load_icon_image(ICON_RPC_INACTIVE_PATH)
                    if self.rpc_icon_img:
                        self.lbl_rpc_icon.config(image=self.rpc_icon_img)
        
        def update_audio_icon_appearance(*args):
            # Only update if not running - running state is handled by _set_active_icons
            if not self.is_running:
                if self.audio_enabled_var.get():
                    # Enabled but not running
                    self.audio_icon_img = self._load_icon_image(ICON_AUDIO_ENABLED_PATH)
                    if self.audio_icon_img:
                        self.lbl_audio_icon.config(image=self.audio_icon_img)
                else:
                    # Disabled
                    self.audio_icon_img = self._load_icon_image(ICON_AUDIO_INACTIVE_PATH)
                    if self.audio_icon_img:
                        self.lbl_audio_icon.config(image=self.audio_icon_img)

        # Trace variable changes to update icon appearance
        self.auto_count_var.trace_add("write", update_auto_icon_appearance)
        self.rpc_enabled_var.trace_add("write", update_rpc_icon_appearance)
        self.audio_enabled_var.trace_add("write", update_audio_icon_appearance)

        # Initialize icon appearance
        update_auto_icon_appearance()
        update_rpc_icon_appearance()
        update_audio_icon_appearance()

        def enable_auto_from_icon(_event):
            if self.is_running:
                return
            self.auto_count_var.set(not self.auto_count_var.get())

        def enable_rpc_from_icon(_event):
            if self.is_running:
                return
            self.rpc_enabled_var.set(not self.rpc_enabled_var.get())
            self.on_toggle_rpc_enabled()
        
        def enable_audio_from_icon(_event):
            if self.is_running:
                return
            self.audio_enabled_var.set(not self.audio_enabled_var.get())

        self.lbl_audio_icon.bind("<Button-1>", enable_audio_from_icon)
        self.lbl_count_icon.bind("<Button-1>", enable_auto_from_icon)
        self.lbl_rpc_icon.bind("<Button-1>", enable_rpc_from_icon)

        spacer_rpc_settings = tk.Frame(self.container, bg=DARK_BG, height=10)
        spacer_rpc_settings.pack(pady=5)
        self._bind_root_drag(spacer_rpc_settings)

        # Settings button (above start button) - 420px wide standard button
        self.btn_settings = tk.Button(
            self.container,
            text="Settings",
            command=self.open_settings_window,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=1
        )
        self.btn_settings.pack(pady=STANDARD_BUTTON_PADY, padx=10, ipadx=STANDARD_BUTTON_IPADX)

        # Start button (below settings) - 420px wide standard button
        self.btn_start = tk.Button(
            self.container,
            text="Start",
            command=self.on_toggle_start,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=2
        )
        self.btn_start.pack(pady=(2, 8), padx=10, ipadx=STANDARD_BUTTON_IPADX)  # 8px bottom padding for spacing

        self.cooldown_var = tk.IntVar(value=5)
        self.frequency_var = tk.DoubleVar(value=0.5)
        self.threshold_var = tk.DoubleVar(value=0.9)

        self.cooldown_var.trace_add("write", lambda *_: self.mark_dirty())
        self.frequency_var.trace_add("write", lambda *_: self.mark_dirty())
        self.threshold_var.trace_add("write", lambda *_: self.mark_dirty())

    # ---------- State helpers ----------
    def set_settings_state(self, enabled):
        auto_controls_state = "normal" if enabled and self.auto_count_var.get() else "disabled"
        state = "normal" if enabled else "disabled"

        self.entry_title.config(state=auto_controls_state, disabledbackground="#d3d3d3")
        self.btn_pick_window.config(state=auto_controls_state)
        self.entry_image_path.config(state=auto_controls_state, disabledbackground="#d3d3d3")
        self.btn_browse_image.config(state=auto_controls_state)
        self.btn_capture_image.config(state=auto_controls_state)

        self.entry_text_path.config(state=state, disabledbackground="#d3d3d3")
        self.btn_browse_text.config(state=state)
        self.entry_increment.config(state=state, disabledbackground="#d3d3d3")
        # Icons are always visible, just change their appearance based on enabled state
        if hasattr(self, "btn_settings") and self.btn_settings:
            self.btn_settings.config(state=state)
        # Keep Start/Stop enabled so Stop is clickable.

        if self.configure_window and self.configure_window.winfo_exists():
            widgets = self.configure_window.winfo_children()
            for widget in widgets:
                if isinstance(widget, tk.Scale):
                    widget.config(state=auto_controls_state)

    def set_tab_title(self):
        """Set the notebook tab title and show a left-side badge image that differs by running state.

        Shows a filled orange circle when active and a hollow circle when inactive.
        """
        name = self.profile_name_var.get().strip() or self.default_tab_name

        # Remove any legacy leading bullet from stored names
        if name.startswith("● "):
            name = name[2:]

        # Use globally-created badge images (created before tabs are added)
        active_img = globals().get("TAB_BADGE_ACTIVE")
        inactive_img = globals().get("TAB_BADGE_INACTIVE")
        img = active_img if self.is_running else inactive_img

        if img:
            # Use the image on the left and the name to the right.
            # Prepending a space gives the image a little breathing room.
            self.notebook.tab(self.frame, text=f" {name}", image=img, compound="left")
        else:
            # Fallback to plain text (active uses a bullet) if images aren't available
            if self.is_running:
                self.notebook.tab(self.frame, text=f"● {name}", image="")
            else:
                self.notebook.tab(self.frame, text=name, image="")

    def validate_required_inputs(self, show_popup=True):
        increment_text = self.entry_increment.get().strip()

        if not self.selected_text_path:
            if show_popup:
                show_custom_error(
                    "count_error",
                    "Error ID 30604057: Missing File",
                    "No text file selected. Rotom needs a document to count in."
                )
            return False, None

        if not os.path.isfile(self.selected_text_path):
            if show_popup:
                show_custom_error(
                    "count_error",
                    "Error ID 70020494: Missing File",
                    "The selected text file no longer exists."
                )
            return False, None

        if not is_counter_file_numeric(self.selected_text_path):
            if show_popup:
                show_custom_error(
                    "count_error",
                    "Error ID 90518840: Invalid File Contents",
                    "The selected text file contains non-numeric text. Please select a new file."
                )
            return False, None

        if not self.auto_count_var.get():
            return True, None

        if not self.selected_image_path:
            if show_popup:
                show_custom_error(
                    "count_error",
                    "Error ID 68915449: Missing File",
                    "No image file selected. Auto mode requires Rotom to have a reference image."
                )
            return False, None

        if not os.path.isfile(self.selected_image_path):
            if show_popup:
                show_custom_error(
                    "count_error",
                    "Error ID 07281901: Missing File",
                    "The selected image file no longer exists."
                )
            return False, None

        try:
            increment_amount = int(increment_text)
        except ValueError:
            if show_popup:
                show_custom_error(
                    "count_error",
                    "Error ID 12282823: Invalid Increment",
                    "Increment amount must be a number between 1 and 99."
                )
            return False, None

        if not (MIN_INCREMENT <= increment_amount <= MAX_INCREMENT):
            if show_popup:
                show_custom_error(
                    "count_error",
                    "Error ID 27444533: Invalid Increment",
                    "Increment amount must be a number between 1 and 99."
                )
            return False, None

        return True, increment_amount

    # ---------- UI actions ----------
    def on_profile_name_change(self, event=None):
        pass

    def on_browse_image(self):
        path = filedialog.askopenfilename(
            title="Choose Image to Compare",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        if path:
            self.image_path_var.set(path)

    def on_browse_text(self):
        path = filedialog.askopenfilename(
            title="Choose Text File",
            filetypes=[("Text Files", "*.txt")]
        )
        if path:
            self.text_path_var.set(path)

    def on_capture_reference(self):
        if self.capture_window and self.capture_window.winfo_exists():
            self.capture_window.lift()
            return

        title = self.title_var.get().strip()
        if not title:
            show_custom_error(
                "count_error",
                "Error ID 92242558: Invalid Window",
                "Rotom was unable to find a window with the name you have entered, please ensure it's not minimized."
            )
            return

        hwnd = find_window_by_title_exact(title)
        if not hwnd:
            show_custom_error(
                "count_error",
                "Error ID 29149918: Invalid Window",
                "Rotom was unable to find a window with the name you have entered, please ensure it's not minimized."
            )
            return

        if is_window_minimized(hwnd):
            show_custom_error(
                "count_error",
                "Error ID 47630893: Invalid Window",
                "Rotom was unable to find a window with the name you have entered, please ensure it's not minimized."
            )
            return

        try:
            screenshot_img = grab_window_image(hwnd)
        except Exception as exc:
            show_custom_error(
                "count_error",
                "Error ID 64066158: Invalid Window",
                "Rotom was unable to capture the window specified. Please try again."
            )
            return

        self.capture_window = tk.Toplevel(self.frame)
        apply_window_style(self.capture_window)
        crop_win = self.capture_window
        crop_win.resizable(False, False)

        self._enter_modal(self.capture_window)

        max_w, max_h = 900, 600
        orig_w, orig_h = screenshot_img.size
        scale = min(max_w / orig_w, max_h / orig_h, 1.0)
        display_w = max(1, int(orig_w * scale))
        display_h = max(1, int(orig_h * scale))
        display_img = screenshot_img if scale == 1.0 else screenshot_img.resize((display_w, display_h), Image.LANCZOS)

        tk_img = ImageTk.PhotoImage(display_img)

        canvas = tk.Canvas(crop_win, width=display_w, height=display_h, highlightthickness=0)
        canvas.pack(padx=10, pady=10)
        canvas.create_image(0, 0, anchor="nw", image=tk_img)
        canvas.image = tk_img

        crop_state = {"start": None, "rect": None, "box": None}

        def on_press(event):
            crop_state["start"] = (event.x, event.y)
            if crop_state["rect"]:
                canvas.delete(crop_state["rect"])
                crop_state["rect"] = None

        def on_drag(event):
            if not crop_state["start"]:
                return
            x0, y0 = crop_state["start"]
            x1, y1 = event.x, event.y
            if crop_state["rect"]:
                canvas.coords(crop_state["rect"], x0, y0, x1, y1)
            else:
                crop_state["rect"] = canvas.create_rectangle(x0, y0, x1, y1, outline="#ff4d4d", width=2)

        def on_release(event):
            if not crop_state["start"]:
                return
            x0, y0 = crop_state["start"]
            x1, y1 = event.x, event.y
            crop_state["box"] = (x0, y0, x1, y1)

        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)

        def save_crop():
            if not crop_state["box"]:
                show_custom_error(
                    "count_error",
                    "Error ID 38319817: Invalid Crop",
                    "No crop has been selected. Please use the cursor to select an area of the image which you would like to crop and save."
                )
                return

            x0, y0, x1, y1 = crop_state["box"]
            left = min(x0, x1)
            right = max(x0, x1)
            top = min(y0, y1)
            bottom = max(y0, y1)

            if right - left < 2 or bottom - top < 2:
                show_custom_error(
                    "count_error",
                    "Error ID 32712951: Invalid Crop",
                    "Designated crop area is too small. Please try again."
                )
                return

            scale_x = orig_w / display_w
            scale_y = orig_h / display_h

            crop_left = max(0, int(left * scale_x))
            crop_right = min(orig_w, int(right * scale_x))
            crop_top = max(0, int(top * scale_y))
            crop_bottom = min(orig_h, int(bottom * scale_y))

            if crop_right <= crop_left or crop_bottom <= crop_top:
                show_custom_error(
                    "count_error",
                    "Error ID 04172198: Invalid Crop",
                    "Designated crop area is invalid. Please try again."
                )
                return

            cropped = screenshot_img.crop((crop_left, crop_top, crop_right, crop_bottom))
            filename = f"profile_{self.profile_index}.png"
            path = os.path.join(REFERENCES_FOLDER, filename)
            try:
                cropped.save(path, format="PNG")
            except Exception as exc:
                show_custom_error(
                    "count_error",
                    "Error ID 00812349: Unable to Save",
                    "Rotom was unable to save the reference frame."
                )
                return

            self.image_path_var.set(path)
            self.capture_window.destroy()
            self.capture_window = None
            self._exit_modal()
            self.frame.winfo_toplevel().focus_force()

        def close_capture():
            self.capture_window.destroy()
            self.capture_window = None
            self._exit_modal()
            self.frame.winfo_toplevel().focus_force()

        buttons = tk.Frame(crop_win, bg=DARK_BG)
        buttons.pack(padx=10, pady=(0, 10), fill="x")

        buttons.grid_columnconfigure(0, weight=1)
        buttons.grid_columnconfigure(1, weight=1)

        tk.Button(
            buttons,
            text="Save Crop",
            command=save_crop,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=BUTTON_HEIGHT
        ).grid(row=0, column=0, padx=(0, 8), sticky="e")
        tk.Button(
            buttons,
            text="Cancel",
            command=close_capture,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=BUTTON_HEIGHT
        ).grid(row=0, column=1, padx=(8, 0), sticky="w")
        crop_win.protocol("WM_DELETE_WINDOW", close_capture)

        center_window(crop_win, self.frame.winfo_toplevel())

    def on_test_image(self):
        if self.test_window and self.test_window.winfo_exists():
            self.test_window.lift()
            return

        title = self.title_var.get().strip()
        if not title:
            show_custom_error(
                "count_error",
                "Error ID 92242558: Invalid Window",
                "Rotom was unable to find a window with the name you have entered, please ensure it's not minimized."
            )
            return

        if not self.selected_image_path:
            show_custom_error(
                "count_error",
                "Error ID 68915449: Missing File",
                "No image file selected. Auto mode requires Rotom to have a reference image."
            )
            return

        if not os.path.isfile(self.selected_image_path):
            show_custom_error(
                "count_error",
                "Error ID 07281901: Missing File",
                "The selected image file no longer exists."
            )
            return

        # If test window already exists for this profile, don't create another (keeps button orange)
        if hasattr(self, 'test_window') and self.test_window and self.test_window.winfo_exists():
            return
        
        self._update_test_image_button_color(START_ACTIVE_COLOR)
        
        self.test_window = tk.Toplevel(self.frame)
        apply_window_style(self.test_window)
        self.test_window.geometry("280x300")  # Reduced height by 20px
        self.test_window.resizable(False, False)
        self._position_popup_near_root(self.test_window)

        # Add profile name label at the top
        # Use getattr to safely get profile name with fallback
        profile_name = getattr(self, 'profile_name', f"Profile {self.profile_index}")
        profile_label = tk.Label(
            self.test_window, 
            text=f"{profile_name}",
            font=(FONT_NAME, BASE_FONT_SIZE, "bold")
        )
        profile_label.pack(padx=20, pady=(10, 5))

        # Load images for visible/not visible states
        try:
            visible_img = Image.open(os.path.join(os.path.dirname(__file__), "assets", "rotom", "image_test", "visible.png"))
            visible_img = visible_img.resize((100, 100), Image.Resampling.LANCZOS)
            visible_photo = ImageTk.PhotoImage(visible_img)
            
            not_visible_img = Image.open(os.path.join(os.path.dirname(__file__), "assets", "rotom", "image_test", "not_visible.png"))
            not_visible_img = not_visible_img.resize((100, 100), Image.Resampling.LANCZOS)
            not_visible_photo = ImageTk.PhotoImage(not_visible_img)
        except Exception as e:
            # Fallback if images can't be loaded
            visible_photo = None
            not_visible_photo = None

        # Image label (will show visible or not_visible image)
        image_label = tk.Label(self.test_window)
        image_label.pack(pady=5)
        
        # Keep references to prevent garbage collection
        image_label.visible_photo = visible_photo
        image_label.not_visible_photo = not_visible_photo

        # Status text label
        status_label = tk.Label(self.test_window, text="Checking...")
        status_label.pack(pady=5)

        is_active = {"running": True}

        def on_close():
            is_active["running"] = False
            self.test_window.destroy()
            self.test_window = None
            self._update_test_image_button_color(DARK_BUTTON)
            self.frame.winfo_toplevel().focus_force()

        self.test_window.protocol("WM_DELETE_WINDOW", on_close)

        def update_result():
            if not is_active["running"]:
                return

            # Update profile name in case it changed (use getattr for safety)
            profile_name = getattr(self, 'profile_name', f"Profile {self.profile_index}")
            profile_label.config(text=f"{profile_name}")

            hwnd = find_window_by_title_exact(title)
            if not hwnd:
                # Show not visible image
                if not_visible_photo:
                    image_label.config(image=not_visible_photo)
                status_label.config(text="Not detected\nWindow not found")
            elif is_window_minimized(hwnd):
                # Show not visible image
                if not_visible_photo:
                    image_label.config(image=not_visible_photo)
                status_label.config(text="Not detected\nWindow is minimized")
            else:
                try:
                    screenshot_img = grab_window_image(hwnd)
                    is_match, confidence = compare_images(
                        screenshot_img, self.selected_image_path, threshold=float(self.threshold_var.get())
                    )
                    percent = max(0.0, min(1.0, confidence)) * 100
                    
                    if is_match:
                        # Show visible image
                        if visible_photo:
                            image_label.config(image=visible_photo)
                        status_label.config(text=f"Image detected\nMatch: {percent:.1f}%")
                    else:
                        # Show not visible image
                        if not_visible_photo:
                            image_label.config(image=not_visible_photo)
                        status_label.config(text=f"Not detected\nMatch: {percent:.1f}%")
                except Exception as exc:
                    # If template image can't be loaded (e.g., profile reset), close window
                    if "Failed to load template image" in str(exc):
                        on_close()
                        return
                    # Show not visible image on error
                    if not_visible_photo:
                        image_label.config(image=not_visible_photo)
                    status_label.config(text=f"Error\n{exc}")

            self.test_window.after(200, update_result)

        # Add Close button at the bottom
        close_button = tk.Button(
            self.test_window,
            text="Close",
            command=on_close,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=BUTTON_HEIGHT
        )
        close_button.pack(pady=(10, 20))

        update_result()

    def on_save_settings(self):
        self.save_settings_silent()
        messagebox.showinfo("Saved", f"Settings saved to {os.path.basename(self.config_path)}")

    def on_toggle_rpc_enabled(self):
        self.rpc_enabled = self.rpc_enabled_var.get()
        self.update_config_value(CONFIG_KEY_RPC_ENABLED, "1" if self.rpc_enabled else "0")
        self.mark_dirty()

        if not self.rpc_enabled and self.rpc_is_running:
            self.stop_broadcast()

    def on_toggle_start(self):
        # Validate and sanitize increment value before starting (caps at 99, like focus out)
        self._on_increment_focus_out()
        
        if not self.is_running:
            is_valid, _ = self.validate_required_inputs(show_popup=True)
            if not is_valid:
                return

            if self.auto_count_var.get():
                title = self.title_var.get().strip()
                if not title:
                    show_custom_error(
                        "count_error",
                        "Error ID 92242558: Invalid Window",
                        "Rotom was unable to find a window with the name you have entered, please ensure it's not minimized."
                    )
                    return

                hwnd = find_window_by_title_exact(title)
                if not hwnd:
                    show_custom_error(
                        "count_error",
                        "Error ID 29149918: Invalid Window",
                        "Rotom was unable to find a window with the name you have entered, please ensure it's not minimized."
                    )
                    return

                if is_window_minimized(hwnd):
                    show_custom_error(
                        "count_error",
                        "Error ID 47630893: Invalid Window",
                        "Rotom was unable to find a window with the name you have entered, please ensure it's not minimized."
                    )
                    return

            if self.rpc_enabled:
                if time.monotonic() - self.rpc_last_stop_time < 30:
                    show_custom_error(
                        "rpc_error",
                        "Error ID 67554378: Active Session",
                        "The RPC session is still active. If you have recently closed the session please wait 30 seconds and try again."
                    )
                    return
                if ACTIVE_BROADCAST_PROFILE is not None and ACTIVE_BROADCAST_PROFILE != self.profile_index:
                    show_custom_error(
                        "count_error",
                        "Error ID 77970901: Active Broadcast",
                        "Another channel is broadcasting. If you see this error please contact au.xiii on Discord for support."
                    )
                    return
                if not self.rpc_game_id:
                    show_custom_error(
                        "rpc_error",
                        "Error ID 67601627: Missing or Invalid RPC Settings",
                        "Rotom is unable to start the RPC session. Please review your RPC settings and try again."
                    )
                    return
                self.start_broadcast_async(self.rpc_game_id, self.rpc_target, self.rpc_odds)

        self.is_running = not self.is_running
        if self.is_running:
            # Play start sound
            play_ui_sound(UI_SOUND_START_PATH)
            self.btn_start.config(text="Stop", bg=START_ACTIVE_COLOR, activebackground=START_ACTIVE_COLOR)
            self.set_settings_state(False)
            self._set_active_icons()
            self._set_counter_button_colors(True)
            self.set_tab_title()
            if self.auto_count_var.get():
                self.auto_check_loop()
        else:
            # Play stop sound
            play_ui_sound(UI_SOUND_STOP_PATH)
            self.btn_start.config(text="Start", bg=DARK_BUTTON, activebackground=DARK_BUTTON)
            self.set_settings_state(True)
            self._set_inactive_icons()
            self._set_counter_button_colors(False)
            self.set_tab_title()
            if self.rpc_is_running:
                self.stop_broadcast()

    def on_manual_adjust(self, delta, source="manual"):
        if not self.selected_text_path:
            show_custom_error(
                "count_error",
                "Error ID 53959337: Invalid File",
                "No text file selected. Rotom needs a document to count in."
            )
            return
        if not os.path.isfile(self.selected_text_path):
            show_custom_error(
                "count_error",
                "Error ID 70020494: Missing File",
                "The selected text file no longer exists."
            )
            return

        if self.auto_count_var.get():
            amount = delta
        else:
            amount = delta * self._get_increment_amount()

        try:
            new_value = increment_number_in_file(self.selected_text_path, amount)
            self.lbl_current_count.config(text=str(new_value))
            if amount > 0 and self._should_play_alert_for(source):
                self._maybe_play_alert()
        except Exception:
            self.lbl_current_count.config(text="(invalid)")

    def on_reset_count(self):
        if not self.selected_text_path:
            show_custom_error(
                "count_error",
                "Error ID 53959337: Invalid File",
                "No text file selected. Rotom needs a document to count in."
            )
            return
        if not os.path.isfile(self.selected_text_path):
            show_custom_error(
                "count_error",
                "Error ID 70020494: Missing File",
                "The selected text file no longer exists."
            )
            return
        if not messagebox.askyesno("Reset Counter", "Reset the count to 0?"):
            return
        try:
            with open(self.selected_text_path, "w", encoding="utf-8") as f:
                f.write("0")
            self.lbl_current_count.config(text="0")
        except Exception:
            self.lbl_current_count.config(text="(invalid)")

    def on_rpc_options(self, parent_grab=None):
        if Presence is None:
            show_custom_error(
                "count_error",
                "Error ID 70210912: Missing Package",
                "Some important files are missing. Please delete the program and download it again from the official GitHub page."
            )
            return

        rpc_open_options(self, parent_grab=parent_grab)

    def open_rpc_inline(self):
        """Open RPC configuration as an inline view with tables and sprites."""
        ProfileTab._global_sub_setting_active = "rpc"  # Set global flag
        if Presence is None:
            show_custom_error(
                "count_error",
                "Error ID 70210912: Missing Package",
                "Some important files are missing. Please delete the program and download it again from the official GitHub page."
            )
            return
        
        container = self._show_sub_setting("Configure RPC")
        self._current_sub_setting = "rpc"  # Track current sub-setting
        
        # Store initial values
        initial_game_id = self.rpc_game_id
        initial_target = self.rpc_target
        initial_odds = self.rpc_odds
        initial_suffix = self.rpc_counter_suffix
        
        # ===== CREATE SCROLLABLE CONTENT AREA =====
        # Create canvas with scrollbar for scrollable content
        canvas_frame = tk.Frame(container, bg=DARK_BG)
        canvas_frame.pack(fill="both", expand=True)
        
        # Scrollbar on the right
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", style="Rpc.Vertical.TScrollbar")
        scrollbar.pack(side="right", fill="y")
        
        # Canvas for scrollable content
        canvas = tk.Canvas(
            canvas_frame,
            bg=DARK_BG,
            highlightthickness=0,
            yscrollcommand=scrollbar.set
        )
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=canvas.yview)
        
        # Content frame inside canvas with padding
        content_frame = tk.Frame(canvas, bg=DARK_BG, padx=6, pady=6)
        canvas_window = canvas.create_window((0, 0), window=content_frame, anchor="nw")
        
        # Configure scroll region when content frame changes size
        def configure_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        content_frame.bind("<Configure>", configure_scroll_region)
        
        # Make canvas adjust content frame width to match canvas width
        def configure_canvas_width(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind("<Configure>", configure_canvas_width)
        
        # Configure grid weights
        content_frame.grid_columnconfigure(1, weight=1)
        
        # ===== GAME SELECTION (Treeview with icons) =====
        tk.Label(content_frame, text="Game:").grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
        
        # Game tree frame
        tree_frame = tk.Frame(content_frame, width=420)
        tree_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 6), sticky="nsew")
        
        # Filter below game tree
        tk.Label(content_frame, text="Filter:").grid(row=2, column=0, padx=10, pady=(0, 6), sticky="w")
        filter_entry = tk.Entry(content_frame, width=30)
        filter_entry.grid(row=2, column=1, padx=10, pady=(0, 6), sticky="ew")
        
        # Empty row for spacing
        tk.Label(content_frame, text="").grid(row=3, column=0)
        
        # Dark mode styling
        style = ttk.Style(container)
        style.configure(
            "Rpc.Vertical.TScrollbar",
            background=DARK_ACCENT,
            troughcolor=DARK_BG,
            bordercolor=DARK_BG,
            arrowcolor=DARK_FG
        )
        style.map(
            "Rpc.Vertical.TScrollbar",
            background=[("active", DARK_FG), ("!active", DARK_ACCENT)]
        )
        
        style.configure(
            "Rpc.Treeview",
            font=(FONT_NAME, BASE_FONT_SIZE),
            rowheight=42
        )
        
        # Create scrollbar for game tree
        game_scrollbar = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            style="Rpc.Vertical.TScrollbar"
        )
        game_scrollbar.pack(side="right", fill="y")
        
        tree = ttk.Treeview(
            tree_frame,
            show="tree",
            selectmode="browse",
            yscrollcommand=game_scrollbar.set,
            height=4,
            style="Rpc.Treeview"
        )
        tree.pack(side="left", fill="both", expand=True)
        game_scrollbar.config(command=tree.yview)
        
        # Configure selection colors
        style.map(
            "Rpc.Treeview",
            background=[("selected", START_ACTIVE_COLOR)],
            foreground=[("selected", "white")]
        )
        
        # Storage for icons and data
        rpc_icons = []
        game_data = []
        
        # Load all game data
        for game_id in rpc_find_game_configs():
            display_name = game_id
            icon_image = None
            config_path = os.path.join(RPC_CONFIG_FOLDER, f"{game_id}.txt")
            
            try:
                cfg = rpc_read_config(config_path)
                if cfg.get("game"):
                    display_name = cfg["game"]
                
                icon_name = cfg.get("icon", "")
                if icon_name:
                    icon_path = os.path.join(SCRIPT_FOLDER, "assets", "game_icon", f"{icon_name}.png")
                    if os.path.isfile(icon_path):
                        image = Image.open(icon_path).resize((RPC_ICON_SIZE, RPC_ICON_SIZE), Image.LANCZOS)
                        icon_image = ImageTk.PhotoImage(image)
                        rpc_icons.append(icon_image)
            except Exception:
                pass
            
            game_data.append({
                'id': game_id,
                'name': display_name,
                'icon': icon_image
            })
        
        def populate_tree(filter_text=""):
            """Populate tree with games matching the filter"""
            for item in tree.get_children():
                tree.delete(item)
            
            filter_lower = filter_text.lower()
            for game in game_data:
                if not filter_text or filter_lower in game['name'].lower():
                    tree.insert("", "end", iid=game['id'], text=f"  {game['name']}", image=game['icon'])
        
        def on_filter_change(*args):
            """Update tree when filter text changes"""
            populate_tree(filter_entry.get())
        
        # Initial population
        populate_tree()
        filter_entry.bind("<KeyRelease>", on_filter_change)
        
        if self.rpc_game_id:
            try:
                tree.selection_set(self.rpc_game_id)
                tree.see(self.rpc_game_id)
            except Exception:
                pass
        
        # ===== POKEMON SELECTION (Canvas grid with sprites) =====
        tk.Label(content_frame, text="Target:").grid(row=4, column=0, padx=10, pady=(0, 0), sticky="w")
        
        # Frame for pokemon canvas
        pokemon_container = tk.Frame(content_frame, bg=DARK_BG)
        pokemon_container.grid(row=5, column=0, columnspan=2, padx=10, pady=(0, 6), sticky="nsew")
        
        # Filter entry for Pokemon
        tk.Label(content_frame, text="Filter:").grid(row=6, column=0, padx=10, pady=(0, 6), sticky="w")
        pokemon_filter_entry = tk.Entry(content_frame, width=30)
        pokemon_filter_entry.grid(row=6, column=1, padx=10, pady=(0, 6), sticky="ew")
        
        # Empty row for spacing
        tk.Label(content_frame, text="").grid(row=7, column=0)
        
        # Create pokemon canvas (3 columns × 1 row, 130×130 cells = 390×130 canvas, increased to 410×130)
        pokemon_canvas = tk.Canvas(
            pokemon_container,
            width=410,
            height=130,
            bg=DARK_ACCENT,
            highlightthickness=0
        )
        pokemon_canvas.pack(side="left", fill="both", expand=True)
        
        # Storage for Pokemon data
        pokemon_data = []
        pokemon_icons = []
        pokemon_grid_sprites = []
        filtered_pokemon = []
        selected_pokemon_name = ""
        loaded_sprites = {}
        current_game_generation = 9
        
        # Helper functions
        def format_pokemon_name(name):
            """Format Pokemon name: replace hyphens with spaces and title case"""
            return name.replace("-", " ").title()
        
        def load_pokemon_sprite(pokemon_name, pokemon_id):
            """Load Pokemon sprite from assets/pokemon_icons/ at original 128x128 size"""
            if not pokemon_name or not pokemon_id:
                return None
            
            try:
                sprite_filename = f"{pokemon_id}_{pokemon_name}.png"
                sprite_path = resource_path(os.path.join("assets", "pokemon_icons", sprite_filename))
                
                if os.path.exists(sprite_path):
                    image = Image.open(sprite_path)
                    return ImageTk.PhotoImage(image)
                return None
            except Exception as e:
                print(f"DEBUG: Failed to load sprite for {pokemon_name}: {e}")
                return None
        
        def get_game_generation(game_name):
            """Get the Pokemon generation for a given game"""
            game_lower = game_name.lower()
            
            if any(x in game_lower for x in ["red", "blue", "yellow", "green"]):
                return 1
            if any(x in game_lower for x in ["gold", "silver", "crystal"]):
                return 2
            if any(x in game_lower for x in ["ruby", "sapphire", "emerald", "firered", "leafgreen"]):
                return 3
            if any(x in game_lower for x in ["diamond", "pearl", "platinum", "heartgold", "soulsilver"]):
                return 4
            if any(x in game_lower for x in ["black", "white"]):
                return 5
            if any(x in game_lower for x in ["x ", "y ", " x", " y", "omega ruby", "alpha sapphire"]):
                return 6
            if any(x in game_lower for x in ["sun", "moon", "ultra sun", "ultra moon"]):
                return 7
            if any(x in game_lower for x in ["sword", "shield", "brilliant diamond", "shining pearl", "legends arceus", "legends: arceus"]):
                return 8
            if any(x in game_lower for x in ["scarlet", "violet"]):
                return 9
            
            return 9  # Default to all Pokemon
        
        def get_pokemon_generation(pokemon_id):
            """Get generation number from Pokemon ID"""
            if pokemon_id <= 151:
                return 1
            elif pokemon_id <= 251:
                return 2
            elif pokemon_id <= 386:
                return 3
            elif pokemon_id <= 493:
                return 4
            elif pokemon_id <= 649:
                return 5
            elif pokemon_id <= 721:
                return 6
            elif pokemon_id <= 809:
                return 7
            elif pokemon_id <= 905:
                return 8
            else:
                return 9
        
        # Load Pokemon list
        pokemon_list_raw = rpc_load_pokemon_list()
        
        # Check if has icons (3-tuples)
        try:
            has_icons = (pokemon_list_raw and isinstance(pokemon_list_raw[0], tuple) and 
                         len(pokemon_list_raw[0]) == 3)
        except (IndexError, TypeError):
            has_icons = False
        
        if has_icons:
            for pokemon_name, pokemon_id, icon_url in pokemon_list_raw:
                pokemon_data.append({
                    'original': pokemon_name,
                    'formatted': format_pokemon_name(pokemon_name),
                    'icon': None,
                    'id': pokemon_id,
                    'sprite': None
                })
        else:
            for pokemon_name, pokemon_id in pokemon_list_raw:
                pokemon_data.append({
                    'original': pokemon_name,
                    'formatted': format_pokemon_name(pokemon_name),
                    'icon': None,
                    'id': pokemon_id,
                    'sprite': None
                })
        
        def draw_grid_cell(canvas, pokemon, x, y, width, height):
            """Draw a single Pokemon grid cell with sprite and name"""
            canvas.create_rectangle(
                x, y, x + width, y + height,
                fill=DARK_ACCENT,
                outline=DARK_BORDER,
                width=1
            )
            
            # Load sprite on-demand if not already loaded
            if 'sprite' not in pokemon or pokemon['sprite'] is None:
                sprite_image = load_pokemon_sprite(pokemon['original'], pokemon['id'])
                if sprite_image:
                    pokemon['sprite'] = sprite_image
                    pokemon_grid_sprites.append(sprite_image)
            
            # Draw sprite (128×128 centered in 130px cell)
            if pokemon.get('sprite'):
                sprite_x = x + width // 2
                sprite_y = y + 65  # Center 128px sprite vertically in 130px cell
                canvas.create_image(sprite_x, sprite_y, image=pokemon['sprite'])
            
            # Draw Pokemon name (bottom of cell)
            name_y = y + height - 10
            canvas.create_text(
                x + width // 2, name_y,
                text=pokemon['formatted'],
                fill=DARK_FG,
                font=(FONT_NAME, 11),
                anchor="s"
            )
        
        def highlight_selected_pokemon():
            """Draw orange highlight box around selected Pokemon"""
            nonlocal selected_pokemon_name
            canvas = pokemon_canvas
            
            canvas.delete("highlight")
            
            if not selected_pokemon_name:
                return
            
            selected_index = -1
            selected_pokemon = None
            for i, pokemon in enumerate(filtered_pokemon):
                if pokemon['original'] == selected_pokemon_name:
                    selected_index = i
                    selected_pokemon = pokemon
                    break
            
            if selected_index == -1 or selected_index >= 3 or not selected_pokemon:
                return
            
            cols = 3
            cell_width = 130
            cell_height = 130
            
            row = selected_index // cols
            col = selected_index % cols
            x = col * cell_width
            y = row * cell_height
            
            # Draw orange filled highlight box
            canvas.create_rectangle(
                x, y, x + cell_width, y + cell_height,
                fill=START_ACTIVE_COLOR,
                outline=START_ACTIVE_COLOR,
                width=0,
                tags="highlight"
            )
            
            # Redraw sprite on orange background (128×128 in 130px cell)
            if selected_pokemon.get('sprite'):
                sprite_x = x + cell_width // 2
                sprite_y = y + 65  # Center 128px sprite vertically in 130px cell
                canvas.create_image(sprite_x, sprite_y, image=selected_pokemon['sprite'], tags="highlight")
            
            # Redraw Pokemon name in white
            name_y = y + cell_height - 10
            canvas.create_text(
                x + cell_width // 2, name_y,
                text=selected_pokemon['formatted'],
                fill="white",
                font=(FONT_NAME, 11),
                anchor="s",
                tags="highlight"
            )
        
        def on_pokemon_grid_click(event):
            """Handle click on Pokemon grid cell"""
            nonlocal selected_pokemon_name
            canvas = pokemon_canvas
            
            canvas_x = canvas.canvasx(event.x)
            canvas_y = canvas.canvasy(event.y)
            
            cols = 3
            cell_width = 130
            cell_height = 130
            
            col = int(canvas_x // cell_width)
            row = int(canvas_y // cell_height)
            index = row * cols + col
            
            if 0 <= index < len(filtered_pokemon) and index < 3:
                pokemon = filtered_pokemon[index]
                selected_pokemon_name = pokemon['original']
                highlight_selected_pokemon()
                update_apply_button_color()
        
        def populate_pokemon_grid(filter_text=""):
            """Populate Pokemon grid with first 3 Pokemon matching filter and generation"""
            nonlocal filtered_pokemon, current_game_generation, selected_pokemon_name
            canvas = pokemon_canvas
            
            canvas.delete("all")
            
            max_generation = current_game_generation
            
            # Filter by generation
            filtered_by_gen = []
            for pokemon in pokemon_data:
                pokemon_id = pokemon.get('id', 0)
                pokemon_gen = get_pokemon_generation(pokemon_id)
                
                if pokemon_gen <= max_generation:
                    filtered_by_gen.append(pokemon)
            
            # Apply search filter
            if filter_text:
                filter_lower = filter_text.lower()
                
                starts_with = [p for p in filtered_by_gen 
                              if p['formatted'].lower().startswith(filter_lower)]
                
                contains = [p for p in filtered_by_gen 
                           if filter_lower in p['formatted'].lower() 
                           and not p['formatted'].lower().startswith(filter_lower)]
                
                filtered_pokemon = starts_with + contains
            else:
                filtered_pokemon = filtered_by_gen
            
            # If there's a selected Pokemon, move it to the front of the list
            current_target = selected_pokemon_name if selected_pokemon_name else ""
            if current_target:
                for i, pokemon in enumerate(filtered_pokemon):
                    if pokemon['original'].lower() == current_target.lower():
                        # Remove from current position and insert at front
                        filtered_pokemon.insert(0, filtered_pokemon.pop(i))
                        break
            
            # Show only first 3 Pokemon
            display_pokemon = filtered_pokemon[:3]
            
            cols = 3
            cell_width = 130
            cell_height = 130
            
            current_target = selected_pokemon_name if selected_pokemon_name else ""
            
            for i, pokemon in enumerate(display_pokemon):
                row = i // cols
                col = i % cols
                x = col * cell_width
                y = row * cell_height
                
                draw_grid_cell(canvas, pokemon, x, y, cell_width, cell_height)
            
            # Select current target if matches
            if current_target:
                for pokemon in filtered_pokemon:
                    if pokemon['original'].lower() == current_target.lower():
                        selected_pokemon_name = pokemon['original']
                        highlight_selected_pokemon()
                        break
            
            # If no selection, select first
            if not selected_pokemon_name and filtered_pokemon:
                selected_pokemon_name = filtered_pokemon[0]['original']
                highlight_selected_pokemon()
        
        def on_pokemon_filter_change(*args):
            """Update Pokemon grid when filter text changes"""
            populate_pokemon_grid(pokemon_filter_entry.get())
        
        def on_game_selection_change(event):
            """Update Pokemon generation filter and load ALL config values when game is selected"""
            nonlocal current_game_generation, selected_pokemon_name, initial_game_id, initial_target, initial_odds, initial_suffix
            selected_items = tree.selection()
            if selected_items:
                selected_game_id = selected_items[0]
                
                # Load config file for selected game to get all settings
                config_path = os.path.join(RPC_CONFIG_FOLDER, f"{selected_game_id}.txt")
                target_pokemon = ""
                new_odds = 8192
                new_suffix = "Encounters"
                
                try:
                    cfg = rpc_read_config(config_path)
                    target_pokemon = cfg.get("target", "")
                    new_odds = cfg.get("odds", 8192)
                    new_suffix = cfg.get("counter_suffix", "Encounters")
                except Exception:
                    pass
                
                # Update selected Pokemon to match the config's target (or clear if none)
                selected_pokemon_name = target_pokemon if target_pokemon else None
                
                # Update odds UI
                odds_found = False
                for display, value in odds_display_map.items():
                    if value == new_odds:
                        odds_var.set(display)
                        odds_found = True
                        break
                if not odds_found:
                    odds_var.set("Custom")
                    custom_odds_var.set(new_odds)
                
                # Update suffix UI
                suffix_label = suffix_to_label.get(new_suffix, "Default / Other")
                suffix_var.set(suffix_label)
                
                # Update initial values to new game's config (so Apply button turns gray)
                initial_game_id = selected_game_id
                initial_target = target_pokemon
                initial_odds = new_odds
                initial_suffix = new_suffix
                
                # Find game name and update generation
                for game in game_data:
                    if game['id'] == selected_game_id:
                        current_game_generation = get_game_generation(game['name'])
                        print(f"DEBUG: Game '{game['name']}' -> Generation {current_game_generation}")
                        populate_pokemon_grid(pokemon_filter_entry.get())
                        highlight_selected_pokemon()  # Highlight the selected Pokemon from config
                        update_apply_button_color()
                        break
        
        # Bind events
        pokemon_filter_entry.bind("<KeyRelease>", on_pokemon_filter_change)
        pokemon_canvas.bind("<Button-1>", on_pokemon_grid_click)
        tree.bind("<<TreeviewSelect>>", on_game_selection_change)
        
        # Initial population
        populate_pokemon_grid()
        
        # ===== SUFFIX/METHOD SELECTION =====
        tk.Label(content_frame, text="Method:").grid(row=8, column=0, padx=10, pady=(0, 6), sticky="w")
        
        # Create label/suffix mappings
        suffix_to_label = {suffix: label for label, suffix in RPC_COUNTER_OPTIONS}
        label_to_suffix = {label: suffix for label, suffix in RPC_COUNTER_OPTIONS}
        selected_suffix_label = suffix_to_label.get(self.rpc_counter_suffix, "Default / Other")
        
        # Configure combobox styling for suffix
        style = ttk.Style()
        style.configure(
            "Rpc.TCombobox",
            font=(FONT_NAME, BASE_FONT_SIZE),
            fieldbackground=DARK_ACCENT,
            background=DARK_ACCENT,
            foreground=DARK_FG,
            arrowcolor=DARK_FG
        )
        style.map(
            "Rpc.TCombobox",
            fieldbackground=[("readonly", DARK_ACCENT)],
            background=[("readonly", DARK_ACCENT)],
            foreground=[("readonly", DARK_FG)]
        )
        
        suffix_var = tk.StringVar(value=selected_suffix_label)
        suffix_combo = ttk.Combobox(
            content_frame,
            textvariable=suffix_var,
            values=[label for label, _ in RPC_COUNTER_OPTIONS],
            state="readonly",
            width=18,
            style="Rpc.TCombobox"
        )
        suffix_combo.grid(row=8, column=1, padx=10, pady=(0, 6), sticky="w")
        
        # ===== ODDS SELECTION =====
        tk.Label(content_frame, text="Odds:").grid(row=9, column=0, padx=10, pady=(0, 6), sticky="w")
        
        odds_options = ["1/512", "1/1024", "1/4096", "1/8192", "Custom"]
        odds_display_map = {
            "1/512": 512,
            "1/1024": 1024,
            "1/4096": 4096,
            "1/8192": 8192
        }
        
        odds_var = tk.StringVar()
        current_odds_display = None
        for display, value in odds_display_map.items():
            if value == self.rpc_odds:
                current_odds_display = display
                break
        if current_odds_display:
            odds_var.set(current_odds_display)
        else:
            odds_var.set("Custom")
        
        odds_combo = ttk.Combobox(
            content_frame,
            textvariable=odds_var,
            values=odds_options,
            state="readonly",
            width=8,
            style="Rpc.TCombobox"
        )
        odds_combo.grid(row=9, column=1, padx=10, pady=(0, 6), sticky="w")
        
        # Custom odds entry (only shown when Custom selected)
        tk.Label(content_frame, text="Custom Odds:").grid(row=10, column=0, padx=10, pady=(0, 6), sticky="w")
        custom_odds_var = tk.IntVar(value=self.rpc_odds if current_odds_display is None else 8192)
        custom_odds_entry = tk.Entry(content_frame, textvariable=custom_odds_var, width=8)
        custom_odds_entry.grid(row=10, column=1, padx=10, pady=(0, 6), sticky="w")
        
        def on_odds_change(*args):
            if odds_var.get() == "Custom":
                custom_odds_entry.config(state="normal")
            else:
                custom_odds_entry.config(state="disabled")
        
        odds_var.trace_add("write", on_odds_change)
        on_odds_change()  # Initial state
        
        # ===== CHANGE DETECTION AND APPLY =====
        def check_for_changes():
            selected_items = tree.selection()
            selected_game_id = selected_items[0] if selected_items else ""
            
            selected_target = selected_pokemon_name
            
            selected_odds_display = odds_var.get()
            if selected_odds_display == "Custom":
                try:
                    selected_odds = custom_odds_var.get()
                except (tk.TclError, ValueError):
                    # If custom odds is invalid during change detection, treat as no change
                    # User will get proper error dialog when they try to apply
                    selected_odds = initial_odds
            else:
                selected_odds = odds_display_map.get(selected_odds_display, 8192)
            
            selected_suffix = label_to_suffix.get(suffix_var.get(), "Encounters")
            
            if selected_game_id != initial_game_id:
                return True
            if selected_target != initial_target:
                return True
            if selected_odds != initial_odds:
                return True
            if selected_suffix != initial_suffix:
                return True
            return False
        
        def update_apply_button_color():
            if check_for_changes():
                apply_button.config(bg=START_ACTIVE_COLOR, activebackground=START_ACTIVE_COLOR)
            else:
                apply_button.config(bg=DARK_BUTTON, activebackground=DARK_BUTTON)
        
        # Bind change detection
        odds_var.trace_add("write", lambda *args: update_apply_button_color())
        custom_odds_var.trace_add("write", lambda *args: update_apply_button_color())
        suffix_var.trace_add("write", lambda *args: update_apply_button_color())
        
        def apply_changes():
            nonlocal initial_game_id, initial_target, initial_odds, initial_suffix
            
            selected_items = tree.selection()
            selected_game_id = selected_items[0] if selected_items else ""
            
            if not selected_game_id:
                return  # Can't save without a game selected
            
            # Preserve existing target if user didn't select a new Pokemon
            selected_target = selected_pokemon_name
            if not selected_target and selected_game_id:
                # Load current config to preserve existing target
                config_path = os.path.join(os.path.dirname(__file__), "rpc_config", f"{selected_game_id}.txt")
                cfg = rpc_read_config(config_path)
                selected_target = cfg.get("target", "")
            
            # Validate that a target Pokemon is selected
            if not selected_target:
                messagebox.showerror("RPC Configuration Error", 
                                    "No target selected, please select a target Pokemon.")
                return
            
            selected_odds_display = odds_var.get()
            if selected_odds_display == "Custom":
                # Validate custom odds input
                try:
                    selected_odds = custom_odds_var.get()
                except (tk.TclError, ValueError):
                    # Show error for invalid input (non-integer like "8192a")
                    show_custom_error(
                        "rpc_error",
                        "Error ID 60155152: NaN",
                        "Rotom can only compute odds that are a whole number.\n(e.g. 1/8192 = \"8192\")",
                        parent=self.frame.winfo_toplevel()
                    )
                    return  # Don't apply changes if validation fails
            else:
                selected_odds = odds_display_map.get(selected_odds_display, 8192)
            
            selected_suffix = label_to_suffix.get(suffix_var.get(), "Encounters")
            
            # Update instance variables
            self.rpc_game_id = selected_game_id
            self.rpc_target = selected_target
            self.rpc_odds = selected_odds
            self.rpc_counter_suffix = selected_suffix
            
            # Update main config (for instance variables persistence)
            self.update_config_value(CONFIG_KEY_RPC_GAME, self.rpc_game_id)
            self.update_config_value(CONFIG_KEY_RPC_TARGET, self.rpc_target)
            self.update_config_value(CONFIG_KEY_RPC_ODDS, str(self.rpc_odds))
            self.update_config_value(CONFIG_KEY_RPC_SUFFIX, self.rpc_counter_suffix)
            
            # Save main config immediately
            self.save_settings_silent()
            
            # ALSO save to the game-specific RPC config file
            config_path = os.path.join(os.path.dirname(__file__), "rpc_config", f"{selected_game_id}.txt")
            cfg = rpc_read_config(config_path)
            cfg["target"] = selected_target
            cfg["odds"] = selected_odds
            cfg["counter_suffix"] = selected_suffix
            rpc_write_config(config_path, cfg)
            
            # Update initial values to match saved values so Apply button returns to gray
            initial_game_id = selected_game_id
            initial_target = selected_target
            initial_odds = selected_odds
            initial_suffix = selected_suffix
            
            # Refresh Apply button color (should be gray now since no changes)
            update_apply_button_color()
            
            # Don't auto-close - user must click Back button
        
        # ===== BUTTONS AT BOTTOM (FIXED, NOT SCROLLING) =====
        # Create button frame at bottom (outside scrollable area)
        button_frame = tk.Frame(container, bg=DARK_BG)
        button_frame.pack(side="bottom", fill="x", pady=0)
        
        # Apply button (packed first, appears at top of button_frame)
        apply_button = tk.Button(
            button_frame,
            text="Apply",
            command=apply_changes,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=BUTTON_HEIGHT
        )
        apply_button.pack(pady=STANDARD_BUTTON_PADY, ipadx=STANDARD_BUTTON_IPADX)
        
        # Back button below Apply
        tk.Button(
            button_frame,
            text="Back",
            command=self._close_sub_setting,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=2
        ).pack(pady=STANDARD_BUTTON_PADY, ipadx=STANDARD_BUTTON_IPADX)
        
        # Initial button color
        update_apply_button_color()
        
        # Make sub-setting draggable after all widgets created
        self._finalize_sub_setting()

    def open_reset_profile_inline(self):
        """Open reset profile confirmation inline (replaces settings menu)"""
        ProfileTab._global_sub_setting_active = "reset"  # Set global flag
        # Hide settings menu, show reset confirmation view
        container = self._show_sub_setting()
        self._current_sub_setting = "reset"  # Track current sub-setting
        
        profile_name = self.profile_name_var.get() or self.default_tab_name
        
        # Create simple content frame (no scrollbar needed for concise text)
        content_frame = tk.Frame(container, bg=DARK_BG, pady=20)  # Removed padx to allow full 420px button width
        content_frame.pack(fill="both", expand=True)
        
        # Load reset icon
        icon = load_error_icon(ICON_RESET_PATH)
        if icon:
            icon_label = tk.Label(content_frame, image=icon, bg=DARK_BG)
            icon_label.pack(pady=(10, 10))
            # Store reference to prevent garbage collection
            container._reset_icon = icon
        
        # Warning title
        profile_name = self.profile_name_var.get() or self.default_tab_name
        tk.Label(
            content_frame,
            text=f"Reset Profile: {profile_name}",
            bg=DARK_BG,
            fg=START_ACTIVE_COLOR,
            font=(FONT_NAME, BASE_FONT_SIZE + 4, "bold")
        ).pack(pady=(10, 20))
        
        # Explanation
        # Warning message in text box (matching original dialog)
        text_box = tk.Text(
            content_frame,
            width=45,
            height=3,
            wrap="word",
            bg=DARK_ACCENT,
            fg=DARK_FG,
            bd=1,
            relief="solid",
            font=(FONT_NAME, BASE_FONT_SIZE - 1)
        )
        text_box.insert("1.0", "WARNING: This change cannot be undone.\n")
        text_box.insert("end", "Enter profile name in the box below to confirm.")
        text_box.tag_configure("warning", foreground=START_ACTIVE_COLOR)
        text_box.tag_add("warning", "1.0", "1.end")  # Apply orange to warning line
        text_box.tag_configure("center", justify="center")
        text_box.tag_add("center", "1.0", "end")
        text_box.config(state="disabled")
        text_box.pack(padx=20, pady=(0, 10), anchor="center")
        
        # Entry field for profile name verification
        entry_var = tk.StringVar()
        entry = tk.Entry(
            content_frame,
            textvariable=entry_var,
            width=30,
            font=(FONT_NAME, BASE_FONT_SIZE)
        )
        entry.pack(pady=(0, 10), anchor="center")
        entry.focus_set()  # Focus for immediate typing
        
        # Button frame at bottom (fixed)
        button_frame = tk.Frame(container, bg=DARK_BG)
        button_frame.pack(side="bottom", fill="x", pady=0)  # Removed padx to allow full 420px button width
        
        def confirm_reset():
            # Extra validation - must match profile name
            if entry_var.get() != profile_name:
                return
            
            # Perform the reset
            if self.rpc_is_running:
                self.stop_broadcast()
            
            self.is_running = False
            self.btn_start.config(text="Start", bg=DARK_BUTTON, activebackground=DARK_BUTTON)
            
            self._loading_config = True
            self.auto_count_var.set(False)
            self.profile_name_var.set(self.default_tab_name)
            self.update_config_value(CONFIG_KEY_PROFILE_NAME, self.default_tab_name)
            self.title_var.set("")
            self.image_path_var.set("")
            self.text_path_var.set("")
            self.increment_var.set(str(MIN_INCREMENT))
            self.cooldown_var.set(5)
            self.frequency_var.set(0.5)
            self.threshold_var.set(0.9)
            
            self.count_plus_hotkey = ""
            self.count_minus_hotkey = ""
            
            # Reset global hotkeys to defaults
            if hotkey_manager:
                hotkey_manager.set_global_enabled(False)
                hotkey_manager.set_hotkeys(DEFAULT_HOTKEYS.copy())
                save_hotkeys_config(hotkey_manager.hotkeys, False)
            
            self.rpc_game_id = ""
            self.rpc_target = ""
            self.rpc_odds = 8192
            self.rpc_enabled = False
            self.rpc_enabled_var.set(False)
            self.rpc_counter_suffix = "Encounters"
            
            self.audio_enabled = False
            self.audio_enabled_var.set(False)
            self.alert_sound_file = "Notify.wav"
            self.alert_last_play_time = 0.0
            self.alert_play_manual = True
            self.alert_play_hotkey = True
            self.alert_play_auto = True
            
            self.selected_image_path = ""
            self.selected_text_path = ""
            self._last_text_path = ""
            self.last_match_time = 0.0
            self.lbl_current_count.config(text="0")
            
            self._loading_config = False
            
            self.update_config_value(CONFIG_KEY_RPC_GAME, "")
            self.update_config_value(CONFIG_KEY_RPC_TARGET, "")
            self.update_config_value(CONFIG_KEY_RPC_ODDS, "")
            self.update_config_value(CONFIG_KEY_RPC_SUFFIX, self.rpc_counter_suffix)
            self.update_config_value(CONFIG_KEY_RPC_ENABLED, "0")
            self.update_config_value(CONFIG_KEY_COUNT_PLUS, "")
            self.update_config_value(CONFIG_KEY_COUNT_MINUS, "")
            self.update_config_value(CONFIG_KEY_ALERT_SOUND, self.alert_sound_file)
            self.update_config_value(CONFIG_KEY_ALERT_ENABLED, "0")
            self.update_config_value(CONFIG_KEY_ALERT_PLAY_MANUAL, "1")
            self.update_config_value(CONFIG_KEY_ALERT_PLAY_HOTKEY, "1")
            self.update_config_value(CONFIG_KEY_ALERT_PLAY_AUTO, "1")
            
            # Save settings and update UI state (fixes RPC checkbox defaulting to true)
            self.save_settings_silent()
            self._update_manual_buttons()
            self.set_settings_state(True)
            self._set_inactive_icons()
            if hotkey_manager:
                hotkey_manager.refresh_profile_hotkeys()
            
            # Close reset view and return to settings menu
            self._close_sub_setting()
        
        def cancel_reset():
            # Just return to settings menu
            self._close_sub_setting()
        
        def validate_entry():
            """Validate entry and update confirm button state/color."""
            matches = entry_var.get() == profile_name  # Case-sensitive
            if matches:
                confirm_btn.config(
                    bg=START_ACTIVE_COLOR,
                    activebackground=START_ACTIVE_COLOR,
                    state="normal"
                )
            else:
                confirm_btn.config(
                    bg=DARK_BUTTON,
                    activebackground=DARK_BUTTON,
                    state="disabled"
                )
        
        # Confirm Reset button (starts disabled) - 420px wide standard button
        confirm_btn = tk.Button(
            button_frame,
            text="Confirm Reset",
            command=confirm_reset,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            bg=DARK_BUTTON,
            fg=DARK_FG,
            activebackground=DARK_BUTTON,
            activeforeground=DARK_FG,
            height=BUTTON_HEIGHT,
            font=(FONT_NAME, BASE_FONT_SIZE, "bold"),
            state="disabled"  # Start disabled
        )
        confirm_btn.pack(pady=STANDARD_BUTTON_PADY, ipadx=STANDARD_BUTTON_IPADX)
        
        # Bind validation to entry changes
        entry_var.trace_add("write", lambda *args: validate_entry())
        
        # Initialize validation state
        validate_entry()
        
        # Back button (was Cancel) - 420px wide standard button
        tk.Button(
            button_frame,
            text="Back",
            command=cancel_reset,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=2
        ).pack(pady=STANDARD_BUTTON_PADY, ipadx=STANDARD_BUTTON_IPADX)
        
        # Make sub-setting draggable after all widgets created
        self._finalize_sub_setting()

    def open_report_bug_inline(self):
        """Open the Report a Bug inline view with Discord link."""
        self._show_sub_setting()
        
        # Version information at top (gray, smaller font)
        version_label = tk.Label(
            self._sub_setting_frame,
            text="Current Version: Release v1.0.0",
            bg=DARK_BG,
            fg="#888888",
            font=(FONT_NAME, BASE_FONT_SIZE - 1),
            justify="center"
        )
        version_label.pack(pady=(10, 20))
        
        # First paragraph - instructional text (centered, wrapped)
        text_label1 = tk.Label(
            self._sub_setting_frame,
        text="If you have found a bug or issue that needs reporting, please join the Rotom Repository Discord and let me know.",
            bg=DARK_BG,
            fg=DARK_FG,
            font=(FONT_NAME, BASE_FONT_SIZE),
            justify="center",
            wraplength=400  # Wrap text to prevent cutoff at window edge
        )
        text_label1.pack(pady=(20, 10))
        
        # Second paragraph - special badge text (centered, wrapped)
        text_label2 = tk.Label(
            self._sub_setting_frame,
            text="If this is not a known bug or issue I'll give you a special badge!",
            bg=DARK_BG,
            fg=DARK_FG,
            font=(FONT_NAME, BASE_FONT_SIZE),
            justify="center",
            wraplength=400  # Wrap text to prevent cutoff at window edge
        )
        text_label2.pack(pady=(10, 10))
        
        # Discord link (clickable, centered, styled - no underline)
        discord_url = "https://discord.gg/fQJNabqqzE"
        link_label = tk.Label(
            self._sub_setting_frame,
            text=discord_url,
            bg=DARK_BG,
            fg=START_ACTIVE_COLOR,
            font=(FONT_NAME, BASE_FONT_SIZE),  # No underline
            cursor="hand2",
            justify="center",
            wraplength=400  # Wrap text to prevent cutoff at window edge
        )
        link_label.pack(pady=(10, 5))
        
        # Make link clickable
        def open_discord_link(event):
            opened = False
            try:
                opened = webbrowser.open_new(discord_url)
            except Exception:
                opened = False
            if not opened:
                try:
                    top = self.frame.winfo_toplevel()
                    top.clipboard_clear()
                    top.clipboard_append(discord_url)
                except Exception:
                    pass
                messagebox.showinfo("Open Discord", f"If your browser didn't open, use this invite:\n{discord_url}\n\n(Invite copied to clipboard when possible.)")
        
        link_label.bind("<Button-1>", open_discord_link)
        
        # Help text for manual Discord join (gray, smaller font)
        help_text = tk.Label(
            self._sub_setting_frame,
            text='(If the link doesn\'t work, on Discord click "Add Server" > "Join a Server" and just type in the invite code "fQJNabqqzE")',
            bg=DARK_BG,
            fg="#888888",
            font=(FONT_NAME, BASE_FONT_SIZE - 2),
            justify="center",
            wraplength=400
        )
        help_text.pack(pady=(5, 20))
        
        # Back button at bottom - 420px wide standard button
        tk.Button(
            self._sub_setting_frame,
            text="Back",
            command=self._close_sub_setting,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=2
        ).pack(pady=STANDARD_BUTTON_PADY, side="bottom", ipadx=STANDARD_BUTTON_IPADX)
        
        # Add flexible bottom spacer for drag area at bottom of window
        bottom_spacer = tk.Frame(self._sub_setting_frame, bg=DARK_BG)
        bottom_spacer.pack(side="bottom", fill="both", expand=True)
        
        # Make sub-setting draggable after all widgets created
        self._finalize_sub_setting()
    
    def open_credits_inline(self):
        """Open the Credits inline view with attribution and Discord link."""
        self._show_sub_setting()
        
        # First paragraph - Credits (centered, wrapped)
        text_label1 = tk.Label(
            self._sub_setting_frame,
            text="Art / Programming - Aux/XIII (au.xiii)\nAll sprites used were sourced from PokeAPI.",
            bg=DARK_BG,
            fg=DARK_FG,
            font=(FONT_NAME, BASE_FONT_SIZE),
            justify="center",
            wraplength=400  # Wrap text to prevent cutoff at window edge
        )
        text_label1.pack(pady=(20, 10))
        
        # Second paragraph - Program motivation (centered, wrapped)
        text_label2 = tk.Label(
            self._sub_setting_frame,
            text="I made this program for the shiny hunting community, as a fellow hunter I had some issues with the previous counting program I was using and wanted to make a more user-friendly version.",
            bg=DARK_BG,
            fg=DARK_FG,
            font=(FONT_NAME, BASE_FONT_SIZE),
            justify="center",
            wraplength=400  # Wrap text to prevent cutoff at window edge
        )
        text_label2.pack(pady=(10, 10))
        
        # Third paragraph - Thank you message (centered, wrapped)
        text_label3 = tk.Label(
            self._sub_setting_frame,
            text="Thank you for using my app and I hope it's helped with your hunts! If you have any suggestions for future updates please feel free to message on the Rotom Repository Discord, I'm already working on more projects to give back to this community.",
            bg=DARK_BG,
            fg=DARK_FG,
            font=(FONT_NAME, BASE_FONT_SIZE),
            justify="center",
            wraplength=400  # Wrap text to prevent cutoff at window edge
        )
        text_label3.pack(pady=(10, 10))
        
        # Discord link (clickable, centered, styled - no underline)
        discord_url = "https://discord.gg/fQJNabqqzE"
        link_label = tk.Label(
            self._sub_setting_frame,
            text=discord_url,
            bg=DARK_BG,
            fg=START_ACTIVE_COLOR,
            font=(FONT_NAME, BASE_FONT_SIZE),  # No underline
            cursor="hand2",
            justify="center",
            wraplength=400  # Wrap text to prevent cutoff at window edge
        )
        link_label.pack(pady=(10, 5))
        
        # Make link clickable
        def open_discord_link(event):
            opened = False
            try:
                opened = webbrowser.open_new(discord_url)
            except Exception:
                opened = False
            if not opened:
                try:
                    top = self.frame.winfo_toplevel()
                    top.clipboard_clear()
                    top.clipboard_append(discord_url)
                except Exception:
                    pass
                messagebox.showinfo("Open Discord", f"If your browser didn't open, use this invite:\n{discord_url}\n\n(Invite copied to clipboard when possible.)")
        
        link_label.bind("<Button-1>", open_discord_link)
        
        # Help text for manual Discord join (gray, smaller font)
        help_text = tk.Label(
            self._sub_setting_frame,
            text='(If the link doesn\'t work, on Discord click "Add Server" > "Join a Server" and just type in the invite code "fQJNabqqzE")',
            bg=DARK_BG,
            fg="#888888",
            font=(FONT_NAME, BASE_FONT_SIZE - 2),
            justify="center",
            wraplength=400
        )
        help_text.pack(pady=(5, 20))
        
        # Back button at bottom - 420px wide standard button with height=2
        button_frame = tk.Frame(self._sub_setting_frame, bg=DARK_BG)
        button_frame.pack(side="bottom", fill="x", pady=0)
        
        tk.Button(
            button_frame,
            text="Back",
            command=self._close_sub_setting,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=2  # Taller like other back buttons
        ).pack(side="bottom", pady=STANDARD_BUTTON_PADY, ipadx=STANDARD_BUTTON_IPADX)
        
        # Add flexible bottom spacer for drag area at bottom of window
        bottom_spacer = tk.Frame(self._sub_setting_frame, bg=DARK_BG)
        bottom_spacer.pack(side="bottom", fill="both", expand=True)
        
        # Make sub-setting draggable after all widgets created
        self._finalize_sub_setting()



    def start_broadcast_async(self, game_id, target, odds):
        global ACTIVE_BROADCAST_PROFILE

        config_path = os.path.join(RPC_CONFIG_FOLDER, f"{game_id}.txt")
        cfg = rpc_read_config(config_path)

        if not cfg.get("application_id"):
            show_custom_error(
                "rpc_error",
                "Error ID 80756697: Missing Application ID",
                "Rotom is unable to connect to the application ID. This may be due to maintenance."
            )
            return

        if not self.selected_text_path or not os.path.isfile(self.selected_text_path):
            show_custom_error(
                "count_error",
                "Error ID 96030679: Missing File",
                "No text file selected. Rotom needs a document to count in."
            )
            return

        self.rpc_stop_event.clear()

        def loop():
            while not self.rpc_stop_event.is_set():
                try:
                    with open(self.selected_text_path, "r") as f:
                        encounters = int(f.readline() or 0)
                except Exception:
                    encounters = 0

                conf, status = rpc_shiny_confidence(encounters, self.rpc_odds)
                # Format Pokemon name for display (capitalize properly)
                formatted_target = self.rpc_target.replace("-", " ").title() if self.rpc_target else ""
                try:
                    self.rpc.update(
                        details=f"✦ {formatted_target} • {encounters} {self.rpc_counter_suffix or 'Encounters'}",
                        state=f"{status} Confidence: {conf * 100:.2f}% ",
                        large_image=cfg["icon"],
                        large_text=cfg["game"]
                    )
                except Exception:
                    pass

                self.rpc_stop_event.wait(15)

        def worker():
            try:
                rpc = Presence(cfg["application_id"])
                rpc.connect()
            except Exception as exc:
                self.frame.after(
                    0,
                    lambda: show_custom_error(
                        "rpc_error",
                        "Error ID 02098276: Unable to Connect",
                        "Rotom is unable to connect to Discord. Please check your internet connection and that the Discord application is running."
                    )
                )
                return

            def on_connected():
                if self.rpc_stop_event.is_set():
                    try:
                        rpc.clear()
                        rpc.close()
                    except Exception:
                        pass
                    return

                self.rpc = rpc
                self.rpc_game_id = game_id
                self.rpc_target = target
                self.rpc_odds = odds
                self.rpc_is_running = True
                ACTIVE_BROADCAST_PROFILE = self.profile_index
                self.rpc_thread = threading.Thread(target=loop, daemon=True)
                self.rpc_thread.start()

            self.frame.after(0, on_connected)

        threading.Thread(target=worker, daemon=True).start()

    def stop_broadcast(self):
        global ACTIVE_BROADCAST_PROFILE

        self.rpc_stop_event.set()

        if self.rpc_thread and self.rpc_thread.is_alive():
            self.rpc_thread.join(timeout=0.5)

        try:
            if self.rpc:
                self.rpc.clear()
                self.rpc.close()
        except Exception:
            pass

        self.rpc = None
        self.rpc_is_running = False
        self.rpc_last_stop_time = time.monotonic()

        if ACTIVE_BROADCAST_PROFILE == self.profile_index:
            ACTIVE_BROADCAST_PROFILE = None

    def stop_running_with_error(self, title, message):
        self.is_running = False
        self.btn_start.config(text="Start", bg=DARK_BUTTON, activebackground=DARK_BUTTON)
        self.set_settings_state(True)
        self._set_inactive_icons()
        self._set_counter_button_colors(False)
        self.set_tab_title()
        if title == "Window Minimized":
            show_custom_error(
                "count_error",
                "Error ID 56162577: Invalid Window",
                "The reference window was minimized. Rotom is unable to see minimized windows."
            )
        else:
            show_custom_error(
                "count_error",
                "Error ID 89361661: Invalid Settings",
                "Some settings are missing or invalid."
            )

    def auto_check_loop(self):
        if not self.is_running:
            return

        if not self.auto_count_var.get():
            return

        is_valid, increment_amount = self.validate_required_inputs(show_popup=True)
        if not is_valid:
            self.stop_running_with_error("Invalid Settings", "Please fix the missing or invalid settings.")
            return

        frequency_seconds = max(0.1, float(self.frequency_var.get()))
        cooldown_seconds = max(1.0, float(self.cooldown_var.get()))
        threshold = float(self.threshold_var.get())

        self.frame.after(int(frequency_seconds * 1000), self.auto_check_loop)

        title = self.title_var.get().strip()
        if not title:
            self.stop_running_with_error("Invalid Window Title", "Please enter an OBS window title.")
            return

        hwnd = find_window_by_title_exact(title)
        if not hwnd:
            self.stop_running_with_error("Invalid Window Title", "No visible window found with that title.")
            return

        if is_window_minimized(hwnd):
            self.stop_running_with_error("Window Minimized", "OBS window was minimized. Monitoring stopped.")
            return

        now = time.monotonic()
        if now - self.last_match_time < cooldown_seconds:
            return

        try:
            screenshot_img = grab_window_image(hwnd)
            is_match, _ = compare_images(screenshot_img, self.selected_image_path, threshold=threshold)
            if is_match:
                new_value = increment_number_in_file(self.selected_text_path, increment_amount)
                self.last_match_time = now
                self.lbl_current_count.config(text=str(new_value))
                if self._should_play_alert_for("auto"):
                    self._maybe_play_alert()
        except Exception:
            return

    def open_configure_window(self, parent_grab=None):
        if self.configure_window and self.configure_window.winfo_exists():
            self.configure_window.lift()
            return

        self.configure_window = tk.Toplevel(self.frame)
        apply_window_style(self.configure_window)
        self.configure_window.resizable(False, False)
        self.configure_window.geometry("380x500")
        self.configure_window.minsize(380, 500)
        self._position_popup_near_root(self.configure_window)
        self.configure_window.configure(bg=DARK_BG)
        self.configure_window.grid_columnconfigure(0, minsize=320)
        self.configure_window.grid_columnconfigure(0, weight=1)

        self._enter_modal(self.configure_window)
        if parent_grab and parent_grab.winfo_exists():
            set_window_disabled(parent_grab, True)

        # Store initial values for change detection
        initial_cooldown = self.cooldown_var.get()
        initial_frequency = self.frequency_var.get()
        initial_threshold = self.threshold_var.get()

        # Create temporary variables to track changes without auto-saving
        temp_cooldown_var = tk.IntVar(value=initial_cooldown)
        temp_frequency_var = tk.DoubleVar(value=initial_frequency)
        temp_threshold_var = tk.DoubleVar(value=initial_threshold)

        def check_for_changes():
            """Check if any configure settings have changed"""
            if temp_cooldown_var.get() != initial_cooldown:
                return True
            if temp_frequency_var.get() != initial_frequency:
                return True
            if temp_threshold_var.get() != initial_threshold:
                return True
            return False

        def update_apply_button_color():
            """Update Apply button color based on whether changes exist"""
            if check_for_changes():
                apply_button.config(bg=START_ACTIVE_COLOR, activebackground=START_ACTIVE_COLOR)
            else:
                apply_button.config(bg=DARK_BUTTON, activebackground=DARK_BUTTON)

        lbl_cooldown = tk.Label(self.configure_window, text="Cooldown (seconds):")
        lbl_cooldown.grid(row=0, column=0, sticky="w", padx=12, pady=6)

        cooldown_slider = tk.Scale(
            self.configure_window, from_=1, to=10, resolution=1, orient="horizontal", 
            variable=temp_cooldown_var, command=lambda v: update_apply_button_color()
        )
        cooldown_slider.grid(row=1, column=0, padx=12, pady=4, sticky="we")

        lbl_frequency = tk.Label(self.configure_window, text="Frequency (seconds):")
        lbl_frequency.grid(row=2, column=0, sticky="w", padx=12, pady=6)

        frequency_slider = tk.Scale(
            self.configure_window, from_=0.1, to=5.0, resolution=0.1, orient="horizontal", 
            variable=temp_frequency_var, command=lambda v: update_apply_button_color()
        )
        frequency_slider.grid(row=3, column=0, padx=12, pady=4, sticky="we")

        lbl_threshold = tk.Label(self.configure_window, text="Match Threshold (%):")
        lbl_threshold.grid(row=4, column=0, sticky="w", padx=12, pady=6)

        threshold_slider = tk.Scale(
            self.configure_window, from_=0.5, to=1.0, resolution=0.01, orient="horizontal", 
            variable=temp_threshold_var, command=lambda v: update_apply_button_color()
        )
        threshold_slider.grid(row=5, column=0, padx=12, pady=4, sticky="we")

        def apply_changes():
            """Apply the changes to the actual variables and save"""
            self.cooldown_var.set(temp_cooldown_var.get())
            self.frequency_var.set(temp_frequency_var.get())
            self.threshold_var.set(temp_threshold_var.get())
            # The trace_add on these vars will trigger mark_dirty()
            
            # Close the window
            self.configure_window.destroy()
            self.configure_window = None
            self.test_image_button = None
            self._exit_modal()
            if parent_grab and parent_grab.winfo_exists():
                set_window_disabled(parent_grab, False)
                if not (self.test_window and self.test_window.winfo_exists()):
                    parent_grab.grab_set()
                    parent_grab.focus_force()

        def on_close():
            self.configure_window.destroy()
            self.configure_window = None
            self.test_image_button = None
            self._exit_modal()
            if parent_grab and parent_grab.winfo_exists():
                set_window_disabled(parent_grab, False)
                # Only re-grab parent if the test window is not open
                if not (self.test_window and self.test_window.winfo_exists()):
                    parent_grab.grab_set()
                    parent_grab.focus_force()

        test_button = tk.Button(
            self.configure_window,
            text="Test Image",
            command=self.on_test_image,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=BUTTON_HEIGHT
        )
        test_button.grid(row=6, column=0, padx=12, pady=(8, 12))
        
        # Save reference to button so we can change its color when test window is open
        self.test_image_button = test_button
        
        # If test window is already open, set button to orange (persists through menu changes)
        if hasattr(self, 'test_window') and self.test_window and self.test_window.winfo_exists():
            self._update_test_image_button_color(START_ACTIVE_COLOR)

        button_row = tk.Frame(self.configure_window, bg=DARK_BG)
        button_row.grid(row=7, column=0, padx=12, pady=(0, 12))

        button_row.grid_columnconfigure(0, weight=1)
        button_row.grid_columnconfigure(1, weight=1)

        apply_button = tk.Button(
            button_row,
            text="Apply",
            command=apply_changes,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=BUTTON_HEIGHT
        )
        apply_button.grid(row=0, column=0, padx=(0, 4), sticky="e")

        close_button = tk.Button(
            button_row,
            text="Close",
            command=on_close,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=BUTTON_HEIGHT
        )
        close_button.grid(row=0, column=1, padx=(4, 0), sticky="w")

        # Initial button color
        update_apply_button_color()

        self.configure_window.protocol("WM_DELETE_WINDOW", on_close)

    def open_configure_inline(self):
        """Open configure (auto) settings as an inline view (not popup)."""
        ProfileTab._global_sub_setting_active = "auto"  # Set global flag
        container = self._show_sub_setting("Configure Auto")
        self._current_sub_setting = "auto"  # Track current sub-setting
        
        # Store initial values for change detection
        initial_cooldown = self.cooldown_var.get()
        initial_frequency = self.frequency_var.get()
        initial_threshold = self.threshold_var.get()

        # Create temporary variables to track changes
        temp_cooldown_var = tk.IntVar(value=initial_cooldown)
        temp_frequency_var = tk.DoubleVar(value=initial_frequency)
        temp_threshold_var = tk.DoubleVar(value=initial_threshold)

        def check_for_changes():
            if temp_cooldown_var.get() != initial_cooldown:
                return True
            if temp_frequency_var.get() != initial_frequency:
                return True
            if temp_threshold_var.get() != initial_threshold:
                return True
            return False

        def update_apply_button_color():
            if check_for_changes():
                apply_button.config(bg=START_ACTIVE_COLOR, activebackground=START_ACTIVE_COLOR)
            else:
                apply_button.config(bg=DARK_BUTTON, activebackground=DARK_BUTTON)

        # Content frame for scrollable content
        content_frame = tk.Frame(container, bg=DARK_BG)
        content_frame.pack(fill="both", expand=True, padx=12, pady=6)

        lbl_cooldown = tk.Label(content_frame, text="Cooldown (seconds):", bg=DARK_BG)
        lbl_cooldown.pack(anchor="w", pady=(0, 2))

        cooldown_slider = tk.Scale(
            content_frame, from_=1, to=10, resolution=1, orient="horizontal",
            variable=temp_cooldown_var, command=lambda v: update_apply_button_color()
        )
        cooldown_slider.pack(fill="x", pady=(0, 8))

        lbl_frequency = tk.Label(content_frame, text="Frequency (seconds):", bg=DARK_BG)
        lbl_frequency.pack(anchor="w", pady=(0, 2))

        frequency_slider = tk.Scale(
            content_frame, from_=0.1, to=5.0, resolution=0.1, orient="horizontal",
            variable=temp_frequency_var, command=lambda v: update_apply_button_color()
        )
        frequency_slider.pack(fill="x", pady=(0, 8))

        lbl_threshold = tk.Label(content_frame, text="Match Threshold (%):", bg=DARK_BG)
        lbl_threshold.pack(anchor="w", pady=(0, 2))

        threshold_slider = tk.Scale(
            content_frame, from_=0.5, to=1.0, resolution=0.01, orient="horizontal",
            variable=temp_threshold_var, command=lambda v: update_apply_button_color()
        )
        threshold_slider.pack(fill="x", pady=(0, 8))

        slider_defaults = {
            cooldown_slider: (
                DARK_BG,
                DARK_BUTTON
            ),
            frequency_slider: (
                DARK_BG,
                DARK_BUTTON
            ),
            threshold_slider: (
                DARK_BG,
                DARK_BUTTON
            ),
        }

        for slider in (cooldown_slider, frequency_slider, threshold_slider):
            slider.configure(
                background=DARK_BG,
                activebackground=DARK_BUTTON,
                troughcolor=DARK_ACCENT,
                highlightthickness=0,
                sliderrelief="ridge",
                sliderlength=16,
                borderwidth=1
            )

        def refresh_slider_colors():
            slider_states = [
                (cooldown_slider, temp_cooldown_var.get(), initial_cooldown),
                (frequency_slider, temp_frequency_var.get(), initial_frequency),
                (threshold_slider, temp_threshold_var.get(), initial_threshold),
            ]
            for slider, current, initial in slider_states:
                default_bg, default_active = slider_defaults.get(slider, (DARK_BG, DARK_BUTTON))
                is_changed = current != initial
                slider.configure(
                    background=START_ACTIVE_COLOR if is_changed else default_bg,
                    activebackground=START_ACTIVE_COLOR if is_changed else default_active,
                    troughcolor=DARK_ACCENT,
                    highlightthickness=0,
                    sliderrelief="ridge",
                    sliderlength=16,
                    borderwidth=1
                )

        test_button = tk.Button(
            content_frame,
            text="Test Image",
            command=self.on_test_image,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=BUTTON_HEIGHT
        )
        test_button.pack(pady=8)
        
        # Save reference to button so we can change its color when test window is open
        self.test_image_button = test_button
        
        # If test window is already open, set button to orange (persists through menu changes)
        if hasattr(self, 'test_window') and self.test_window and self.test_window.winfo_exists():
            self._update_test_image_button_color(START_ACTIVE_COLOR)

        def apply_changes():
            nonlocal initial_cooldown, initial_frequency, initial_threshold
            self.cooldown_var.set(temp_cooldown_var.get())
            self.frequency_var.set(temp_frequency_var.get())
            self.threshold_var.set(temp_threshold_var.get())
            initial_cooldown = temp_cooldown_var.get()
            initial_frequency = temp_frequency_var.get()
            initial_threshold = temp_threshold_var.get()
            update_apply_button_color()
            refresh_slider_colors()

        # Spacer to push buttons to bottom
        spacer = tk.Frame(container, bg=DARK_BG)
        spacer.pack(fill="both", expand=True)

        # Back button at bottom - 420px wide standard button
        tk.Button(
            container,
            text="Back",
            command=self._close_sub_setting,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=2
        ).pack(pady=STANDARD_BUTTON_PADY, side="bottom", ipadx=STANDARD_BUTTON_IPADX)

        # Apply button above Back - 420px wide standard button
        apply_button = tk.Button(
            container,
            text="Apply",
            command=apply_changes,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY,
            height=BUTTON_HEIGHT
        )
        apply_button.pack(pady=STANDARD_BUTTON_PADY, side="bottom", ipadx=STANDARD_BUTTON_IPADX)

        # Initial button color
        update_apply_button_color()
        
        # Make sub-setting draggable after all widgets created
        self._finalize_sub_setting()

    # ---------- Load settings ----------
    def load_from_config(self):
        self._loading_config = True

        saved_profile_name = self.load_config_value(CONFIG_KEY_PROFILE_NAME, "")
        if saved_profile_name:
            self.profile_name_var.set(saved_profile_name[:PROFILE_NAME_MAX_LENGTH])
        self.set_tab_title()

        saved_title = self.load_config_value(CONFIG_KEY_TITLE, "")
        if saved_title:
            self.title_var.set(saved_title)

        saved_image = self.load_config_value(CONFIG_KEY_IMAGE, "")
        if saved_image:
            self.image_path_var.set(saved_image)

        saved_text = self.load_config_value(CONFIG_KEY_TEXT, "")
        if saved_text:
            self.text_path_var.set(saved_text)

        cooldown = self.load_config_value(CONFIG_KEY_COOLDOWN, "5")
        try:
            self.cooldown_var.set(int(float(cooldown)))
        except ValueError:
            self.cooldown_var.set(5)

        frequency = self.load_config_value(CONFIG_KEY_FREQUENCY, "0.5")
        try:
            self.frequency_var.set(float(frequency))
        except ValueError:
            self.frequency_var.set(0.5)

        threshold = self.load_config_value(CONFIG_KEY_THRESHOLD, "0.9")
        try:
            self.threshold_var.set(float(threshold))
        except ValueError:
            self.threshold_var.set(0.9)

        increment = self.load_config_value(CONFIG_KEY_INCREMENT, str(MIN_INCREMENT))
        try:
            increment_value = int(increment)
        except ValueError:
            increment_value = MIN_INCREMENT
        increment_value = self._sanitize_increment_value(increment_value)
        self.increment_var.set(str(increment_value))

        self.rpc_game_id = self.load_config_value(CONFIG_KEY_RPC_GAME, "")
        self.rpc_target = self.load_config_value(CONFIG_KEY_RPC_TARGET, "")
        rpc_odds = self.load_config_value(CONFIG_KEY_RPC_ODDS, "8192")
        try:
            self.rpc_odds = int(rpc_odds)
        except ValueError:
            self.rpc_odds = 8192

        # Always start with RPC disabled, regardless of saved config
        self.rpc_enabled = False
        self.rpc_enabled_var.set(False)

        rpc_suffix = self.load_config_value(CONFIG_KEY_RPC_SUFFIX, "Encounters")
        self.rpc_counter_suffix = rpc_suffix or "Encounters"

        self.count_plus_hotkey = normalize_hotkey_display(
            self.load_config_value(CONFIG_KEY_COUNT_PLUS, "")
        )
        self.count_minus_hotkey = normalize_hotkey_display(
            self.load_config_value(CONFIG_KEY_COUNT_MINUS, "")
        )

        self.alert_sound_file = self.load_config_value(CONFIG_KEY_ALERT_SOUND, "Notify.wav")
        if not self.alert_sound_file and os.path.isfile(os.path.join(ALERTS_AUDIO_FOLDER, "Notify.wav")):
            self.alert_sound_file = "Notify.wav"
            self.update_config_value(CONFIG_KEY_ALERT_SOUND, self.alert_sound_file)

        # Always start with alerts disabled, regardless of saved config
        self.audio_enabled_var.set(False)
        self.audio_enabled = False
        self.alert_play_manual = self.load_config_value(CONFIG_KEY_ALERT_PLAY_MANUAL, "1") == "1"
        self.alert_play_hotkey = self.load_config_value(CONFIG_KEY_ALERT_PLAY_HOTKEY, "1") == "1"
        self.alert_play_auto = self.load_config_value(CONFIG_KEY_ALERT_PLAY_AUTO, "1") == "1"

        self._last_text_path = self.selected_text_path
        self._loading_config = False
        
        # Update button text after config is loaded
        self._update_manual_buttons()


# =========================
# MAIN UI
# =========================
register_font(FONT_PATH)
TOOLTIP_ENABLED = load_tooltip_enabled()

root = tk.Tk()
apply_window_style(root)
apply_dark_theme(root)
install_unfocus_on_click(root)

# Create tab badge images (must exist before creating tabs so set_tab_title can use them)
# Active: filled orange circle. Inactive: hollow circle in a neutral gray.
TAB_BADGE_ACTIVE = build_tab_badge(size=12, color=START_ACTIVE_COLOR, filled=True)
TAB_BADGE_INACTIVE = build_tab_badge(size=12, color="#6b6b6b", filled=False)

notebook = ttk.Notebook(root, width=462)  # Increased to accommodate container padding (12px) + button padding (20px)
notebook.pack(anchor="nw", fill="x")  # Fill horizontally only, don't expand vertically to keep Start button at bottom

profiles = []
for i in range(1, 4):
    tab = ProfileTab(notebook, i)
    notebook.add(tab.frame, text=f"Profile {i}")
    tab.load_from_config()
    profiles.append(tab)

# Function to enable/disable profile tabs based on settings state
def update_profile_tabs_state():
    """Enable or disable profile tabs based on whether settings are open."""
    try:
        current_index = notebook.index(notebook.select())
    except Exception:
        current_index = 0
    
    if ProfileTab._global_settings_open:
        # Settings are open - disable other tabs
        for i in range(len(profiles)):
            state = "normal" if i == current_index else "disabled"
            notebook.tab(i, state=state)
    else:
        # Settings are closed - enable all tabs
        for i in range(len(profiles)):
            notebook.tab(i, state="normal")

# Add tab change handler to sync settings menu state across profiles
def on_tab_changed(event):
    """Handle tab changes to sync settings menu state"""
    try:
        # Get the index of the currently selected tab
        current_index = notebook.index(notebook.select())
        # Access the ProfileTab directly using the index
        if 0 <= current_index < len(profiles):
            profiles[current_index]._sync_settings_state()
    except Exception:
        pass

# Removed - merged into on_profile_tab_change below

root.update_idletasks()
root.geometry("462x802")  #  WINDOW SIZE (reduced by 8px from 810)
root.minsize(462, 802)
root.maxsize(462, 802)
root.resizable(False, False)


def get_active_profile():
    if not profiles:
        return None
    try:
        idx = notebook.index(notebook.select())
    except Exception:
        return profiles[0]
    if 0 <= idx < len(profiles):
        return profiles[idx]
    return profiles[0]


def get_profiles():
    return profiles


def on_rename_profile(_event=None):
    profile = get_active_profile()
    if not profile:
        return

    current_name = profile.profile_name_var.get().strip() or profile.default_tab_name

    # Build a custom modal dialog so we can set the window title and icon
    dlg = tk.Toplevel(root)
    apply_window_style(dlg, title="RotomCamRPC")
    dlg.transient(root)
    dlg.resizable(False, False)
    dlg.grab_set()

    container = tk.Frame(dlg, bg=DARK_BG)
    container.pack(padx=12, pady=12)

    tk.Label(
        container,
        text="Profile Name:",
        bg=DARK_BG,
        fg=DARK_FG,
        font=(FONT_NAME, BASE_FONT_SIZE)
    ).pack(pady=(0, 8))

    # Use StringVar for change tracking
    name_var = tk.StringVar(value=current_name)
    
    entry = tk.Entry(container, width=28, font=(FONT_NAME, BASE_FONT_SIZE), textvariable=name_var)
    entry.pack()
    entry.select_range(0, "end")
    entry.focus_set()

    result = {"value": None}

    def do_ok(_event=None):
        val = name_var.get()
        if val is None:
            val = ""
        val = val.strip()
        if not val:
            # Treat empty as cancel (match previous behavior)
            dlg.destroy()
            return
        val = val[:PROFILE_NAME_MAX_LENGTH]
        result["value"] = val
        dlg.destroy()

    def do_cancel(_event=None):
        dlg.destroy()

    btn_row = tk.Frame(container, bg=DARK_BG)
    btn_row.pack(pady=(12, 0))
    
    # Use grid layout for equal-width buttons
    btn_row.grid_columnconfigure(0, weight=1)
    btn_row.grid_columnconfigure(1, weight=1)

    apply_btn = tk.Button(
        btn_row,
        text="Apply",
        command=do_ok,
        padx=BUTTON_PADX,
        pady=BUTTON_PADY,
        height=BUTTON_HEIGHT
    )
    apply_btn.grid(row=0, column=0, padx=(0, 4), sticky="e")

    close_btn = tk.Button(
        btn_row,
        text="Close",
        command=do_cancel,
        padx=BUTTON_PADX,
        pady=BUTTON_PADY,
        height=BUTTON_HEIGHT
    )
    close_btn.grid(row=0, column=1, padx=(4, 0), sticky="w")
    
    # Change detection - make Apply button orange when name changes
    def check_for_changes(*args):
        has_changes = name_var.get() != current_name
        if has_changes:
            apply_btn.config(bg=START_ACTIVE_COLOR, activebackground=START_ACTIVE_COLOR)
        else:
            apply_btn.config(bg=DARK_BUTTON, activebackground=DARK_BUTTON)
    
    name_var.trace_add("write", check_for_changes)
    check_for_changes()  # Initialize button color

    dlg.bind("<Return>", do_ok)
    dlg.bind("<Escape>", do_cancel)

    center_window(dlg, root)
    dlg.wait_window()

    if result["value"] is None:
        return

    profile.profile_name_var.set(result["value"])


def on_profile_tab_change(_event=None):
    """Handle tab changes - sync settings and refresh hotkeys"""
    try:
        current_index = notebook.index(notebook.select())
        if 0 <= current_index < len(profiles):
            # Sync settings menu state
            profiles[current_index]._sync_settings_state()
    except Exception:
        pass
    
    # Refresh hotkeys
    if hotkey_manager:
        hotkey_manager.refresh_profile_hotkeys()


# Profile name editing has been moved to the settings menu
# notebook.bind("<Double-Button-1>", on_rename_profile)
notebook.bind("<<NotebookTabChanged>>", on_profile_tab_change)

hotkeys, global_enabled = load_hotkeys_config()
hotkey_manager = HotkeyManager(root, get_active_profile, get_profiles)
hotkey_manager.set_hotkeys(hotkeys)
hotkey_manager.set_global_enabled(global_enabled)
hotkey_manager.register_local_hotkeys()

root.mainloop()
