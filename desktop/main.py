"""DG-Talk PC: original Android-inspired Windows radio interface.

Native Tk window: same dark TeamSpeak-style channel tree, header and bottom
Mic / Headphone / Push-to-talk / Disconnect dock. NOT a web or browser frontend.
"""
from __future__ import annotations

import queue
import sys
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import ttk, messagebox, simpledialog
from tkinter.scrolledtext import ScrolledText

from backend import Backend, THEMES
from color_icons import draw_icon
from spacers import parse_spacer, spacer_display
from radio_console import RadioConsole

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None


PAL = {
    "standard": dict(bg="#111111", surface="#181A1C", high="#212325", border="#34383C", accent="#1A91D0", soft="#14709F", green="#4CAF50", yellow="#FFC107"),
    "christmas": dict(bg="#091B17", surface="#112721", high="#19372B", border="#42634D", accent="#D83746", soft="#AF2937", green="#36BA61", yellow="#FFCC53"),
    "27mc": dict(bg="#0F1415", surface="#232522", high="#34352E", border="#67624C", accent="#FFAE39", soft="#C67A1B", green="#95B64B", yellow="#FFD365"),
    "space": dict(bg="#080D25", surface="#141B39", high="#202B4E", border="#45538A", accent="#36CEFA", soft="#1585BA", green="#4FDAD7", yellow="#FFC86B"),
}
TEXT = "#E6E8EA"
FAINT = "#9BA1A6"
RED = "#F44336"
NAMES = {"standard": "Standaard", "christmas": "Kerst", "27mc": "27MC", "space": "Space"}
TREE_ICONS = {
    "christmas": ("tree", "snowman", "gift", "snowflake"),
    "27mc": ("radio", "antenna", "truck"),
    "space": ("planet", "rocket", "star", "satellite"),
}


def enable_high_dpi_windows():
    """Ask Windows to paint Tk controls at native monitor resolution.

    With no DPI declaration Windows bitmap-upscales the entire 525px window,
    making colour icons and text appear fuzzy on 1440p/4K monitors.
    """
    if sys.platform != "win32":
        return
    import ctypes
    try:
        # Windows 10+: per-monitor v2 DPI awareness; -4 = DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2.
        if ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
            return
    except (AttributeError, OSError, ValueError):
        pass
    try:
        # Windows 8.1 fallback.
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError, ValueError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError, ValueError):
            pass


class DGWindow:
    def __init__(self):
        self.backend = Backend()
        self.root = tk.Tk()
        self.root.title("DG-Talk PC")
        # Sizes are screen pixels: DPI aware on Windows, so scale the window and
        # bitmaps explicitly to preserve their apparent size without blur.
        self.dpi_scale = max(1.0, min(3.0, float(self.root.winfo_fpixels("1i")) / 96.0))
        max_width = max(360, self.root.winfo_screenwidth() - int(70 * self.dpi_scale))
        max_height = max(540, self.root.winfo_screenheight() - int(115 * self.dpi_scale))
        # A desktop radio console, instead of a tall phone-like window.
        width = min(round(1120 * self.dpi_scale), max_width)
        height = min(round(800 * self.dpi_scale), max_height)
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(min(round(730 * self.dpi_scale), max_width),
                          min(round(620 * self.dpi_scale), max_height))
        self._spacer_font = tkfont.Font(master=self.root, family="Segoe UI", size=10, weight="bold")
        self._spacer_items = {}
        self._spacer_refresh_job = None
        self.root.configure(bg=PAL["standard"]["bg"])
        self._icons = {}  # Keep native RGBA PhotoImage references alive
        self.root.iconphoto(True, self._photo("app", 64))
        exe_assets = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "assets"
        try:
            if (exe_assets / "DG-Talk-PC.ico").is_file():
                self.root.iconbitmap(default=str(exe_assets / "DG-Talk-PC.ico"))
        except tk.TclError:
            pass
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.page = "server"
        self.palette = PAL.get(self.backend.config.get("theme"), PAL["standard"])
        self.tree = None
        self.radio_console = None
        self.tx = False
        self.ptt_widget = None
        self.status_string = "Offline"
        self.selected_preview = THEMES.index(self.backend.config["theme"]) if self.backend.config["theme"] in THEMES else 0
        self.picture_cache = {}
        self.chat_messages = []
        self.chat_target = "channel"
        self.chat_client_id = None
        self.chat_client_name = ""
        self.talkers = set()
        self._last_tree = None
        self._setup_styles()
        self.render()
        self.root.after(85, self.poll)
        self.root.after(1000, self.refresh_tree)
        self.root.mainloop()

    def _setup_styles(self):
        p = self.palette
        self.root.configure(bg=p["bg"])
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("DG.Treeview", background=p["bg"], foreground=TEXT, fieldbackground=p["bg"],
                        borderwidth=0, relief="flat", rowheight=round(30 * self.dpi_scale), font=("Segoe UI", 10))
        style.map("DG.Treeview", foreground=[("selected", "#FFFFFF")],
                  background=[("selected", p["soft"])])
        style.configure("DG.Vertical.TScrollbar", background=p["high"], troughcolor=p["bg"],
                        bordercolor=p["bg"], arrowcolor=FAINT)
        style.configure("DG.TCombobox", fieldbackground=p["high"], foreground=TEXT,
                        background=p["high"], arrowcolor=TEXT)

    def _photo(self, name, size=22):
        # Real RGBA pixel art. Tk/Windows often turns emoji into white glyphs.
        pixel_size = round(size * self.dpi_scale)
        key = (name, pixel_size, self.backend.config.get("theme", "standard"))
        if key not in self._icons:
            colour = PAL.get(self.backend.config.get("theme"), PAL["standard"])["accent"]
            self._icons[key] = ImageTk.PhotoImage(draw_icon(name, pixel_size, colour), master=self.root)
        return self._icons[key]

    def label(self, parent, text, size=10, bold=False, color=None, bg=None, **kw):
        return tk.Label(parent, text=text, bg=bg or parent.cget("bg"),
                        fg=color or TEXT, font=("Segoe UI", size, "bold" if bold else "normal"),
                        anchor="w", **kw)

    def button(self, parent, text, command, color=None, foreground="#FFFFFF",
               size=10, icon=None, icon_size=23, **kw):
        picture = self._photo(icon, icon_size) if icon else None
        return tk.Button(parent, text=text, command=command, bg=color or self.palette["high"],
                         image=picture, compound="left" if text else "center",
                         fg=foreground, activebackground=self.palette["soft"], activeforeground="#FFFFFF",
                         font=("Segoe UI", size, "bold"), relief="flat", borderwidth=0,
                         cursor="hand2", padx=15, pady=10, **kw)

    def clear(self):
        for child in self.root.winfo_children():
            child.destroy()
        self.ptt_widget = None
        self.tree = None
        self.radio_console = None
        self._spacer_items = {}
        if self._spacer_refresh_job is not None:
            self.root.after_cancel(self._spacer_refresh_job)
            self._spacer_refresh_job = None
        self.root.configure(bg=self.palette["bg"])

    def render(self):
        self.palette = PAL.get(self.backend.config.get("theme"), PAL["standard"])
        self._setup_styles()
        self.clear()
        if self.page == "server" and self.backend.connected:
            # The custom desktop console has its own header and TX controls.
            self.server_page()
            return
        self.header()
        if self.page == "settings":
            self.settings_page()
        elif self.page == "chat":
            self.chat_page()
        else:
            self.server_page()
        if self.backend.connected:
            self.dock()

    def header(self):
        p = self.palette
        header = tk.Frame(self.root, bg=p["bg"], height=82)
        header.pack(fill="x")
        header.pack_propagate(False)
        logo = tk.Label(header, image=self._photo("radio", 46), bg=p["bg"])
        logo.pack(side="left", padx=(15, 10))
        middle = tk.Frame(header, bg=p["bg"])
        middle.pack(side="left", fill="both", expand=True)
        self.label(middle, "DG-Talk PC", 15, True).pack(anchor="w", pady=(8, 0))
        detail = self.status_string
        self.label(middle, detail, 9, color=p["green"] if self.backend.connected else FAINT).pack(anchor="w")
        if self.page == "settings":
            self.button(header, "", lambda: self.navigate("server"), icon="back", size=13).pack(side="right", padx=10)
        else:
            self.button(header, "", lambda: self.navigate("settings"), icon="settings", size=13).pack(side="right", padx=(3, 12))
            if self.backend.connected:
                self.button(header, "", lambda: self.navigate("chat"), icon="chat", size=12).pack(side="right", padx=3)
        tk.Frame(self.root, height=1, bg=p["border"]).pack(fill="x")

    def navigate(self, page):
        if self.page == page:
            return
        self.page = page
        self.render()

    def server_page(self):
        p = self.palette
        if not self.backend.connected:
            # Custom landscape login screen: consistent with the radio console.
            bg, panel, accent = "#091522", "#101E2E", "#32CBE8"
            outer = tk.Frame(self.root, bg=bg)
            outer.pack(expand=True, fill="both", padx=round(26 * self.dpi_scale),
                       pady=round(25 * self.dpi_scale))
            hero = tk.Frame(outer, bg=bg)
            hero.pack(side="left", fill="both", expand=True,
                      padx=(round(18 * self.dpi_scale), round(26 * self.dpi_scale)))
            self.label(hero, "WELCOME TO DG-TALK", 12, True,
                       color=accent, bg=bg).pack(anchor="w", pady=(round(35 * self.dpi_scale), 15))
            self.label(hero, "DESKTOP\nRADIO CONSOLE", 28, True,
                       color="#EAF3FA", bg=bg).pack(anchor="w")
            tk.Frame(hero, bg=accent, width=125, height=3).pack(anchor="w", pady=20)
            self.label(hero, "TeamSpeak 3 • Live kanalen • Echte audio", 11,
                       color="#97ACBF", bg=bg).pack(anchor="w")
            self.label(hero, "Een eigen mobilofoon-interface voor Windows, met\n"
                       "zichtbare kanaalscheidingen en fysieke PTT.", 10,
                       color="#97ACBF", bg=bg).pack(anchor="w", pady=(14, 19))
            tk.Label(hero, image=self._photo("radio", 115), bg=bg).pack(anchor="w", pady=16)
            self.label(hero, "TS3 DIGITAL  /  48 kHz  /  Opus", 10, True,
                       color=accent, bg=bg).pack(anchor="w")

            login = tk.Frame(outer, bg=panel, width=round(400 * self.dpi_scale))
            login.pack(side="right", fill="y")
            login.pack_propagate(False)
            card = tk.Frame(login, bg=panel, padx=round(23 * self.dpi_scale),
                            pady=round(25 * self.dpi_scale))
            card.pack(fill="both", expand=True)
            self.label(card, "VERBINDEN", 18, True, color="#EAF3FA",
                       bg=panel).pack(anchor="w", pady=(6, 2))
            self.label(card, "Vul je TeamSpeak-gegevens in om online te gaan", 9,
                       color="#97ACBF", bg=panel).pack(anchor="w", pady=(0, 25))
            self.label(card, "SERVER", 9, True, color=accent, bg=panel).pack(anchor="w")
            self.server_var = tk.StringVar(
                value=self.backend.config.get("server", "heerlen.mijnts3.nl"))
            self.entry(card, self.server_var).pack(fill="x", pady=(5, 20), ipady=8)
            self.label(card, "GEBRUIKERSNAAM", 9, True, color=accent, bg=panel).pack(anchor="w")
            self.nick_var = tk.StringVar(value=self.backend.config.get("nickname", ""))
            self.entry(card, self.nick_var).pack(fill="x", pady=(5, 20), ipady=8)
            self.label(card, "SERVERWACHTWOORD (OPTIONEEL)", 9, True,
                       color=accent, bg=panel).pack(anchor="w")
            self.pw_var = tk.StringVar()
            self.entry(card, self.pw_var, show="*").pack(fill="x", pady=(5, 27), ipady=8)
            self.button(card, " VERBINDEN MET TEAM SPEAK", self.connect,
                        color="#147E9B", icon="radio", size=11).pack(fill="x", ipady=7)
            self.label(card, "RX STANDBY    •    WINDOWS 10 / 11", 9, True,
                       color="#64D6A6", bg=panel).pack(anchor="w", pady=(20, 5))
            return

        self.radio_console = RadioConsole(
            self.root, self.backend, p, self._photo,
            on_settings=lambda: self.navigate("settings"),
            on_chat=lambda: self.navigate("chat"),
            on_mic=self.toggle_mic, on_speaker=self.toggle_speaker,
            on_disconnect=self.backend.disconnect,
            on_ptt_down=lambda: self.backend.ptt_down("screen"),
            on_ptt_up=lambda: self.backend.ptt_up("screen"),
            on_join_channel=self.join_radio_channel,
            on_private_chat=self.open_radio_private,
            dpi_scale=self.dpi_scale,
        )
        self.radio_console.pack(fill="both", expand=True)
        self.radio_console.set_tx(self.tx)
        self._last_tree = None

    def join_radio_channel(self, channel_id):
        snap = self.backend.snapshot()
        if snap is None:
            return
        channel = next((c for c in snap.channels if int(c.id) == int(channel_id)), None)
        if channel is None or parse_spacer(channel.name) is not None:
            return
        password = None
        if channel.has_password:
            password = simpledialog.askstring(
                "Kanaalwachtwoord", "Wachtwoord voor " + channel.name,
                parent=self.root, show="*")
            if password is None:
                return
        try:
            self.backend.move_channel(int(channel_id), password)
        except Exception as error:
            messagebox.showerror("TeamSpeak-kanaal", str(error), parent=self.root)

    def open_radio_private(self, client_id, client_name):
        self.chat_client_id = int(client_id)
        self.chat_client_name = client_name
        self.chat_target = "private"
        self.navigate("chat")

    def entry(self, parent, variable, **kw):
        return tk.Entry(parent, textvariable=variable, bg=self.palette["high"], fg=TEXT,
                        insertbackground=TEXT, relief="flat", font=("Segoe UI", 11),
                        highlightthickness=1, highlightbackground=self.palette["border"],
                        highlightcolor=self.palette["accent"], **kw)

    def connect(self):
        self.backend.connect(self.server_var.get(), self.nick_var.get(), self.pw_var.get())
        self.status_string = "Verbinding maken…"
        self.render()

    def populate_tree(self, snap):
        if self.tree is None:
            return
        tree = self.tree
        for item in tree.get_children():
            tree.delete(item)
        self._spacer_items = {}
        if snap is None:
            tree.insert("", "end", text="Verbinding maken…")
            return
        channels = list(snap.channels)
        users = list(snap.clients)
        nodes = {}
        theme_icons = TREE_ICONS.get(self.backend.config["theme"], ())
        srv_id = tree.insert("", "end", iid="server", text="  " + snap.name,
                             image=self._photo("server", 22), open=True)
        for ch in channels:
            parent = nodes.get(int(ch.parent_id), srv_id)
            spacer = parse_spacer(ch.name)
            if spacer is not None:
                # Preserve the channel ID/order, but never show raw [*spacerNNN] tags.
                # Lines and headings are measured again on resize.
                tag = "spacer_line" if spacer.align == "*" else "spacer_heading"
                item = tree.insert(parent, "end", iid="c:" + str(ch.id),
                                   text="", open=False, tags=(tag,))
                nodes[int(ch.id)] = item
                depth = 0
                ancestor = parent
                while ancestor and ancestor != srv_id:
                    depth += 1
                    ancestor = tree.parent(ancestor)
                self._spacer_items[item] = (spacer, depth)
                continue
            # Other TeamSpeak channels retain the original icon/label and order.
            icon_name = "channel_locked" if ch.has_password else (
                theme_icons[int(ch.id) % len(theme_icons)] if theme_icons else "channel"
            )
            item = tree.insert(parent, "end", iid="c:" + str(ch.id),
                               text="  " + ch.name, image=self._photo(icon_name, 20), open=True)
            nodes[int(ch.id)] = item
            for user in (u for u in users if int(u.channel_id) == int(ch.id)):
                role = "user_muted" if user.input_muted else (
                    "user_talking" if user.talking or int(user.id) in self.talkers else "user"
                )
                own = "  [ik]" if int(user.id) == int(snap.own_client_id) else ""
                tree.insert(item, "end", iid="u:" + str(user.id),
                            text=f"  {user.name}{own}", image=self._photo(role, 20))
        for user in users:
            if int(user.channel_id) not in nodes:
                tree.insert(srv_id, "end", iid="u:" + str(user.id),
                            text="  " + user.name, image=self._photo("user", 20))
        self._refresh_spacers()

    def _schedule_spacer_refresh(self, event=None):
        # When the window is resized, extend/re-align spacer lines to the new width.
        if self._spacer_refresh_job is not None:
            self.root.after_cancel(self._spacer_refresh_job)
        self._spacer_refresh_job = self.root.after(90, self._refresh_spacers)

    def _refresh_spacers(self):
        self._spacer_refresh_job = None
        tree = self.tree
        if tree is None or not tree.winfo_exists():
            return
        available = tree.winfo_width()
        for item, (spacer, depth) in self._spacer_items.items():
            if not tree.exists(item):
                continue
            # Indentation, left-side tree toggles and padding reserve real pixels.
            content_width = max(0, available - round((75 + depth * 24) * self.dpi_scale))
            new_text = spacer_display(spacer, content_width, self._spacer_font.measure)
            if tree.item(item, "text") != new_text:
                tree.item(item, text=new_text)

    def refresh_tree(self):
        if self.page == "server" and self.backend.connected and self.radio_console:
            snap = self.backend.snapshot()
            if snap:
                signature = (
                    snap.name, snap.own_channel_id,
                    tuple((x.id, x.parent_id, x.name, x.client_count) for x in snap.channels),
                    tuple((u.id, u.channel_id, u.name, u.input_muted, u.talking) for u in snap.clients),
                    tuple(sorted(self.talkers)),
                )
                if self._last_tree != signature:
                    self.radio_console.update_snapshot(snap)
                    self._last_tree = signature
        self.root.after(1100, self.refresh_tree)

    def activate_tree(self, event=None):
        if not self.tree:
            return
        chosen = self.tree.selection()
        if not chosen:
            return
        item = chosen[0]
        if item in self._spacer_items:
            # Decorative TeamSpeak spacer channels are not joinable.
            return
        if item.startswith("c:"):
            snap = self.backend.snapshot()
            chan_id = int(item[2:])
            channel = next((c for c in snap.channels if int(c.id) == chan_id), None) if snap else None
            password = None
            if channel and channel.has_password:
                password = simpledialog.askstring("Kanaalwachtwoord", "Wachtwoord voor " + channel.name,
                                                  parent=self.root, show="*")
                if password is None:
                    return
            self.backend.move_channel(chan_id, password)
        if item.startswith("u:"):
            client_id = int(item[2:])
            snap = self.backend.snapshot()
            user = next((u for u in snap.clients if int(u.id) == client_id), None) if snap else None
            if user and client_id != int(snap.own_client_id):
                self.chat_client_id = client_id
                self.chat_client_name = user.name
                self.chat_target = "private"
                self.navigate("chat")

    def tree_menu(self, event):
        if not self.tree:
            return
        hit = self.tree.identify_row(event.y)
        if not hit or hit in self._spacer_items:
            return
        self.tree.selection_set(hit)
        menu = tk.Menu(self.root, tearoff=False, bg=self.palette["high"], fg=TEXT)
        if hit.startswith("c:"):
            menu.add_command(label="Kanaal betreden", command=self.activate_tree)
        elif hit.startswith("u:"):
            menu.add_command(label="Privébericht", command=self.activate_tree)
        else:
            menu.add_command(label="Serverchat", command=lambda: self.open_chat("server"))
        menu.tk_popup(event.x_root, event.y_root)

    def open_chat(self, target):
        self.chat_target = target
        self.navigate("chat")

    def chat_page(self):
        p = self.palette
        box = tk.Frame(self.root, bg=p["bg"])
        box.pack(fill="both", expand=True, padx=14, pady=10)
        self.button(box, " Kanalen", lambda: self.navigate("server"), icon="back").pack(anchor="w", pady=(0, 10))
        tabs = tk.Frame(box, bg=p["bg"])
        tabs.pack(fill="x", pady=(0, 8))
        for target, name in (("channel", "Kanaal"), ("server", "Server"), ("private", "Privé")):
            disabled = target == "private" and self.chat_client_id is None
            name = name + (" · " + self.chat_client_name if target == "private" and self.chat_client_name else "")
            button = self.button(tabs, name, lambda x=target: self.switch_chat(x), size=9,
                                 color=p["soft"] if self.chat_target == target else p["high"])
            button.pack(side="left", padx=(0, 6))
            if disabled:
                button.configure(state="disabled")
        self.chat_view = ScrolledText(box, bg=p["surface"], fg=TEXT, relief="flat", borderwidth=0,
                                      font=("Segoe UI", 10), wrap="word", padx=10, pady=8,
                                      insertbackground=TEXT)
        self.chat_view.pack(fill="both", expand=True)
        self.chat_view.configure(state="disabled")
        row = tk.Frame(box, bg=p["bg"])
        row.pack(fill="x", pady=(10, 0))
        self.chat_entry = tk.Entry(row, bg=p["high"], fg=TEXT, insertbackground=TEXT, relief="flat",
                                   font=("Segoe UI", 11))
        self.chat_entry.pack(side="left", fill="x", expand=True, ipady=10)
        self.chat_entry.bind("<Return>", lambda e: self.send_message())
        self.button(row, "Verstuur", self.send_message, color=p["accent"]).pack(side="right", padx=(7, 0))
        self.show_chat()

    def switch_chat(self, target):
        self.chat_target = target
        self.render()

    def show_chat(self):
        if not hasattr(self, "chat_view") or self.page != "chat":
            return
        self.chat_view.configure(state="normal")
        self.chat_view.delete("1.0", "end")
        for target, sender, msg in self.chat_messages:
            if target == self.chat_target.upper() or (self.chat_target == "private" and target.startswith("CLIENT")):
                self.chat_view.insert("end", sender + ": " + msg + "\n")
        self.chat_view.see("end")
        self.chat_view.configure(state="disabled")

    def send_message(self):
        value = self.chat_entry.get().strip()
        if not value:
            return
        try:
            self.backend.send_chat(value, self.chat_target, self.chat_client_id)
            self.chat_entry.delete(0, "end")
        except Exception as exc:
            messagebox.showerror("Chat", str(exc), parent=self.root)

    def dock(self):
        p = self.palette
        tk.Frame(self.root, height=1, bg=p["border"]).pack(fill="x")
        outer = tk.Frame(self.root, bg=p["bg"], padx=13, pady=12)
        outer.pack(fill="x", side="bottom")
        inner = tk.Frame(outer, bg=p["surface"], padx=8, pady=8)
        inner.pack(fill="x")
        self.button(
            inner, "", self.toggle_mic,
            color="#7C292B" if self.backend.config["mic_muted"] else p["high"],
            icon="mic_off" if self.backend.config["mic_muted"] else "mic",
            icon_size=28,
        ).pack(side="left", padx=(0, 5))
        self.button(
            inner, "", self.toggle_speaker,
            color="#7C292B" if self.backend.config["output_muted"] else p["high"],
            icon="headphones_off" if self.backend.config["output_muted"] else "headphones",
            icon_size=28,
        ).pack(side="left", padx=(0, 8))
        self.ptt_widget = tk.Label(
            inner, text=" PUSH TO TALK", image=self._photo("ptt", 22), compound="left",
            bg=p["green"] if self.tx else p["accent"], fg="#FFFFFF",
            font=("Segoe UI", 11, "bold"), cursor="hand2", padx=8, pady=15,
        )
        self.ptt_widget.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.ptt_widget.bind("<ButtonPress-1>", self.ptt_start)
        self.ptt_widget.bind("<ButtonRelease-1>", self.ptt_release)
        self.ptt_widget.bind("<Leave>", self.ptt_release)
        self.button(inner, "", self.backend.disconnect, color=RED,
                    icon="hangup", icon_size=28).pack(side="right")

    def ptt_start(self, event=None):
        self.backend.ptt_down("screen")

    def ptt_release(self, event=None):
        self.backend.ptt_up("screen")

    def toggle_mic(self):
        self.backend.toggle_mic()
        self.render()

    def toggle_speaker(self):
        self.backend.toggle_speaker()
        self.render()

    def settings_page(self):
        p = self.palette
        area = tk.Frame(self.root, bg=p["bg"])
        area.pack(fill="both", expand=True)
        outer = tk.Canvas(area, bg=p["bg"], highlightthickness=0, borderwidth=0)
        scrollbar = ttk.Scrollbar(area, orient="vertical", command=outer.yview)
        outer.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        outer.pack(side="left", fill="both", expand=True)
        content = tk.Frame(outer, bg=p["bg"], padx=14, pady=15)
        frame_id = outer.create_window((0, 0), window=content, anchor="nw")
        content.bind("<Configure>", lambda e: outer.configure(scrollregion=outer.bbox("all")))
        outer.bind("<Configure>", lambda e: outer.itemconfigure(frame_id, width=e.width))
        outer.bind_all("<MouseWheel>", lambda e: outer.yview_scroll(int(-e.delta / 120), "units")
                                  if self.page == "settings" else None)

        self.label(content, "Instellingen", 18, True).pack(anchor="w", pady=(0, 12))
        box = self.card(content, "1. Thema kiezen")
        self.label(box, "Veeg of blader door de voorbeeldafbeeldingen.", 9, color=FAINT,
                   wraplength=350).pack(anchor="w", pady=(0, 8))
        browser = tk.Frame(box, bg=p["surface"])
        browser.pack(fill="x")
        self.button(browser, "", lambda: self.change_preview(-1), size=14, icon="left").pack(side="left")
        self.preview_container = tk.Frame(browser, bg=p["surface"])
        self.preview_container.pack(side="left", fill="both", expand=True, padx=6)
        self.button(browser, "", lambda: self.change_preview(1), size=14, icon="right").pack(side="right")
        self.paint_preview()
        self.button(box, "Thema toepassen", self.apply_preview, color=p["accent"]).pack(fill="x", pady=(9, 0))
        self.label(box, "Het huidige Android-achtige scherm blijft qua bediening gelijk.",
                   9, color=FAINT, wraplength=390).pack(anchor="w", pady=(8, 0))

        box = self.card(content, "2. Externe PTT-knop")
        self.ext_var = tk.BooleanVar(value=self.backend.config["external_ptt"])
        self.check(box, "Externe PTT inschakelen", self.ext_var, lambda: self.backend.setting(
            "external_ptt", self.ext_var.get()))
        self.key_status = self.label(box, "Toegewezen toets: " + self.backend.config["ptt_key"].upper(), 10, color=FAINT)
        self.key_status.pack(anchor="w", pady=(9, 5))
        self.button(box, "Fysieke / Bluetooth-toets instellen", self.learn_button).pack(fill="x")
        self.label(box, "Houd de toets ingedrukt om te zenden; loslaten is ontvangen. "
                   "Bluetooth-HID moet eerst gekoppeld zijn in Windows.",
                   9, color=FAINT, wraplength=370).pack(anchor="w", pady=(8, 0))

        box = self.card(content, "3. Rogerpiep – 3 tonen")
        self.roger_var = tk.BooleanVar(value=self.backend.config["roger"])
        self.check(box, "3-tonige rogerpiep inschakelen", self.roger_var,
                   lambda: self.backend.setting("roger", self.roger_var.get()))
        self.label(box, "Meegestuurd bij loslaten van PTT: hoorbaar voor anderen in het kanaal.",
                   9, color=FAINT, wraplength=360).pack(anchor="w", pady=(7, 9))
        self.button(box, " Test 3-tonige piep in kanaal", self.test_roger, icon="test").pack(fill="x")

        box = self.card(content, "Spraakmodus")
        self.voice_var = tk.StringVar(value=self.backend.config["voice_mode"])
        for val, caption in (("ptt", "Push to talk"), ("vad", "Spraakactivatie"),
                             ("continuous", "Microfoon continu open")):
            tk.Radiobutton(box, text=caption, value=val, variable=self.voice_var,
                           command=lambda: self.backend.setting("voice_mode", self.voice_var.get()),
                           bg=p["surface"], fg=TEXT, selectcolor=p["high"], activebackground=p["surface"],
                           activeforeground=TEXT, font=("Segoe UI", 10)).pack(anchor="w")

        box = self.card(content, "Windows audioapparaten")
        self.device_picker(box, want_input=True, label="Microfoon")
        self.device_picker(box, want_input=False, label="Luidsprekers")
        self.label(box, "Alle audiobronnen worden door Windows beheerd, niet door Android.",
                   9, color=FAINT).pack(anchor="w", pady=(8, 0))
        self.label(content, "DG-Talk PC • dezelfde Rust TeamSpeak 3-kern als DG-Talk Android",
                   9, color=FAINT, wraplength=360).pack(anchor="w", pady=14)

    def card(self, parent, title):
        box = tk.Frame(parent, bg=self.palette["surface"], padx=14, pady=13)
        box.pack(fill="x", pady=(0, 13))
        self.label(box, title, 12, True, color=self.palette["accent"]).pack(anchor="w", pady=(0, 10))
        return box

    def check(self, parent, text, var, command):
        tk.Checkbutton(parent, text=text, variable=var, command=command, bg=self.palette["surface"],
                       fg=TEXT, activebackground=self.palette["surface"], activeforeground=TEXT,
                       selectcolor=self.palette["high"], font=("Segoe UI", 10)).pack(anchor="w")

    def paint_preview(self):
        for child in self.preview_container.winfo_children():
            child.destroy()
        theme = THEMES[self.selected_preview]
        p = PAL[theme]
        title = self.label(self.preview_container, NAMES[theme], 11, True, bg=self.palette["surface"])
        title.pack(anchor="center", pady=(0, 5))
        path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "assets" / (
            "dg_theme_" + theme + "_preview.jpg")
        if Image is not None and path.is_file():
            try:
                im = Image.open(path)
                im.thumbnail((215, 274))
                # Retain the same portrait proportions as Android in the preview gallery.
                im = im.resize((125, 270), Image.Resampling.LANCZOS)
                pic = ImageTk.PhotoImage(im, master=self.root)
                label = tk.Label(self.preview_container, image=pic, bg=self.palette["surface"])
                label.image = pic
                label.pack(anchor="center")
                return
            except Exception:
                pass
        demo = tk.Frame(self.preview_container, bg=p["bg"], width=150, height=230)
        demo.pack()
        demo.pack_propagate(False)
        self.label(demo, "DG-TALK", 13, True, color=p["accent"], bg=p["bg"]).pack(pady=12)
        self.label(demo, NAMES[theme], 12, bg=p["bg"]).pack(pady=15)
        self.label(demo, "◉  Kanalen\n  ●  Gebruikers", 10, bg=p["bg"]).pack(pady=7)
        self.button(demo, "PTT", lambda: None, color=p["accent"]).pack(pady=10)

    def change_preview(self, step):
        self.selected_preview = (self.selected_preview + step) % len(THEMES)
        self.paint_preview()

    def apply_preview(self):
        theme = THEMES[self.selected_preview]
        self.backend.setting("theme", theme)
        self.render()

    def learn_button(self):
        self.backend.learn_key = True
        self.key_status.config(text="Druk op de fysieke PTT-toets…", fg=self.palette["yellow"])

    def test_roger(self):
        if not self.backend.test_roger():
            messagebox.showinfo("Rogerpiep", "Verbind eerst met TeamSpeak, activeer de microfoon "
                                "en kies de Push-to-talk-modus.", parent=self.root)

    def device_picker(self, parent, want_input, label):
        self.label(parent, label, 9, color=FAINT).pack(anchor="w", pady=(6, 4))
        options = [("Standaard Windows-apparaat", None)] + [
            (f"{i} · {name}", i) for i, name in self.backend.devices(want_input)]
        names = [x[0] for x in options]
        setting = "mic_device" if want_input else "speaker_device"
        stored = self.backend.config.get(setting)
        sel = next((i for i, (_, value) in enumerate(options) if value == stored), 0)
        combo = ttk.Combobox(parent, values=names, state="readonly", style="DG.TCombobox")
        combo.current(sel)
        combo.pack(fill="x")
        def changed(event):
            self.backend.setting(setting, options[combo.current()][1])
        combo.bind("<<ComboboxSelected>>", changed)

    def poll(self):
        changed = False
        for _ in range(60):
            try:
                event, payload = self.backend.events.get_nowait()
            except queue.Empty:
                break
            if event == "status":
                status, message = payload
                self.status_string = {
                    "CONNECTED": "Verbonden met TeamSpeak",
                    "CONNECTING": "Verbinden…",
                    "RECONNECTING": "Opnieuw verbinden…",
                    "DISCONNECTED": "Niet verbonden"
                }.get(status, status)
                if status in ("CONNECTED", "DISCONNECTED"):
                    self.page = "server"
                changed = True
            elif event == "state":
                self._last_tree = None
            elif event == "tx":
                self.tx = bool(payload)
                if self.radio_console is not None:
                    self.radio_console.set_tx(self.tx)
                if self.ptt_widget:
                    self.ptt_widget.configure(text=" ZENDEN · TX" if self.tx else " PUSH TO TALK",
                                              bg=self.palette["green"] if self.tx else self.palette["accent"])
            elif event == "chat":
                target, sender, msg, sender_id = payload
                self.chat_messages.append((target, sender, msg))
                self.chat_messages = self.chat_messages[-300:]
                if self.page == "chat":
                    self.show_chat()
            elif event == "talk":
                user_id, talking, whisper = payload
                if talking:
                    self.talkers.add(int(user_id))
                else:
                    self.talkers.discard(int(user_id))
                self._last_tree = None
            elif event == "error":
                self.status_string = "⚠ " + str(payload)[:56]
                # Errors stay visible without blocking audio threads with a modal.
                changed = True
            elif event == "key_learned":
                if self.page == "settings" and hasattr(self, "key_status"):
                    self.key_status.config(text="Toegewezen toets: " + str(payload).upper(), fg=self.palette["green"])
        if changed:
            self.render()
        self.root.after(85, self.poll)

    def close(self):
        self.backend.stop_audio()
        import threading
        threading.Thread(target=self.backend.close, daemon=True).start()
        self.root.destroy()


if __name__ == "__main__":
    enable_high_dpi_windows()
    DGWindow()
