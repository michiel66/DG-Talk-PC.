"""DG-Talk PC Radio Console: native vector-drawn Windows radio UI.

This is deliberately NOT another ttk.Treeview with emoji-based separators.
The TS3 channel list is painted on a native Tk Canvas. Server-provided spacer
names become actual horizontal lines, which scale on resize and on 4K screens.
The original backend remains responsible for the live connection and audio.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog

from spacers import parse_spacer

THEME_ACCENTS = {
    "standard": ("#32CBE8", "#E6A851"),
    "christmas": ("#E66F71", "#70D5A0"),
    "27mc": ("#FFB85C", "#9FCB78"),
    "space": ("#83B8FF", "#C59AFF"),
}

BG = "#091522"
PANEL = "#101E2E"
PANEL_HIGH = "#15283D"
LIST_BG = "#0C1928"
DIVIDER = "#243B53"
TEXT = "#EAF3FA"
MUTED = "#97ACBF"
GREEN = "#64D6A6"
RED = "#FF6A76"


class RadioConsole(tk.Frame):
    """One resilient native radio dashboard, independent of TS3 network threads."""

    def __init__(self, parent, backend, palette, photo, on_settings, on_chat,
                 on_mic, on_speaker, on_disconnect, on_ptt_down, on_ptt_up,
                 on_join_channel, on_private_chat, dpi_scale=1.0):
        super().__init__(parent, bg=BG)
        self.backend = backend
        self.photo = photo
        self.on_settings = on_settings
        self.on_chat = on_chat
        self.on_mic = on_mic
        self.on_speaker = on_speaker
        self.on_disconnect = on_disconnect
        self.on_ptt_down = on_ptt_down
        self.on_ptt_up = on_ptt_up
        self.on_join_channel = on_join_channel
        self.on_private_chat = on_private_chat
        self.theme = backend.config.get("theme", "standard")
        self.accent, self.accent_secondary = THEME_ACCENTS.get(
            self.theme, THEME_ACCENTS["standard"])
        self.s = min(2.75, max(1.0, float(dpi_scale)))
        self.snapshot = None
        self.rows = []
        self.search = tk.StringVar()
        self.selected = None
        self.collapsed = set()
        self.tx = False
        self._pending = None
        self._ptt_held = False
        self._init_ui()
        self.search.trace_add("write", lambda *_: self._draw())
        self.update_snapshot(backend.snapshot(), force=True)

    def dim(self, px):
        return max(1, round(px * self.s))

    def text(self, parent, value, size=10, bold=False, color=TEXT, bg=None):
        return tk.Label(parent, text=value, bg=bg or parent.cget("bg"), fg=color,
                        font=("Segoe UI", size, "bold" if bold else "normal"),
                        anchor="w", justify="left")

    def icon_button(self, parent, icon, command, caption="", fill=PANEL_HIGH):
        picture = self.photo(icon, 22)
        return tk.Button(
            parent, text=("  " + caption) if caption else "",
            image=picture, compound="left" if caption else "center", command=command,
            bg=fill, fg=TEXT, activebackground=DIVIDER, activeforeground=TEXT,
            relief="flat", bd=0, cursor="hand2", padx=self.dim(12), pady=self.dim(9),
            font=("Segoe UI", 10, "bold"),
        )

    def _init_ui(self):
        self._header = tk.Frame(self, bg=PANEL, height=self.dim(88))
        self._header.pack(fill="x")
        self._header.pack_propagate(False)

        logo = tk.Label(self._header, image=self.photo("app", 45), bg=PANEL)
        logo.pack(side="left", padx=(self.dim(20), self.dim(13)))
        brand = tk.Frame(self._header, bg=PANEL)
        brand.pack(side="left", fill="y", pady=self.dim(12))
        self.text(brand, "DG / TALK", 19, True, color=TEXT).pack(anchor="w")
        self.text(brand, "DESKTOP RADIO CONSOLE", 9, True, color=self.accent).pack(anchor="w")

        header_actions = tk.Frame(self._header, bg=PANEL)
        header_actions.pack(side="right", padx=self.dim(16))
        self.icon_button(header_actions, "chat", self.on_chat, "CHAT").pack(side="left", padx=self.dim(5))
        self.icon_button(header_actions, "settings", self.on_settings, "INSTELLINGEN").pack(side="left", padx=self.dim(5))

        self.connection_label = self.text(
            self._header, "●  ONLINE  ·  TEAM SPEAK 3", 10, True, color=GREEN
        )
        self.connection_label.pack(side="right", padx=self.dim(18))

        tk.Frame(self, bg=self.accent, height=self.dim(3)).pack(fill="x")

        content = tk.Frame(self, bg=BG)
        content.pack(fill="both", expand=True, padx=self.dim(15), pady=self.dim(16))

        right = tk.Frame(content, bg=PANEL, width=self.dim(308))
        right.pack(side="right", fill="y", padx=(self.dim(13), 0))
        right.pack_propagate(False)
        self._right_panel(right)

        left = tk.Frame(content, bg=PANEL)
        left.pack(side="left", fill="both", expand=True)
        list_heading = tk.Frame(left, bg=PANEL)
        list_heading.pack(fill="x", padx=self.dim(16), pady=(self.dim(15), self.dim(8)))
        self.text(list_heading, "KANALEN & GEBRUIKERS", 12, True).pack(side="left")
        self.counter = self.text(list_heading, "LIVE", 9, True, color=self.accent)
        self.counter.pack(side="right")

        searchbox = tk.Frame(left, bg=PANEL)
        searchbox.pack(fill="x", padx=self.dim(15), pady=(0, self.dim(10)))
        self.text(searchbox, "ZOEK", 9, True, color=MUTED).pack(side="left", padx=(0, self.dim(10)))
        entry = tk.Entry(searchbox, textvariable=self.search,
                         font=("Segoe UI", 10), relief="flat", bd=0,
                         bg=PANEL_HIGH, fg=TEXT, insertbackground=TEXT,
                         highlightthickness=self.dim(1),
                         highlightbackground=DIVIDER, highlightcolor=self.accent)
        entry.pack(side="left", fill="x", expand=True, ipady=self.dim(7))

        tree_holder = tk.Frame(left, bg=LIST_BG)
        tree_holder.pack(fill="both", expand=True, padx=self.dim(8), pady=(0, self.dim(8)))
        self.canvas = tk.Canvas(tree_holder, bg=LIST_BG, highlightthickness=0,
                                bd=0, takefocus=True)
        scrollbar = tk.Scrollbar(tree_holder, orient="vertical", command=self.canvas.yview,
                                 bg=PANEL_HIGH, troughcolor=LIST_BG, activebackground=self.accent,
                                 highlightthickness=0, bd=0)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Configure>", self._queue_draw)
        self.canvas.bind("<MouseWheel>", self._wheel)
        self.canvas.bind("<Button-4>", lambda e: self._scroll(-3))
        self.canvas.bind("<Button-5>", lambda e: self._scroll(3))

        footer = tk.Frame(left, bg=PANEL)
        footer.pack(fill="x", padx=self.dim(15), pady=(0, self.dim(12)))
        self.user_count = self.text(footer, "0 gebruikers", 9, color=MUTED)
        self.user_count.pack(side="left")
        self.text(footer, "DUBBELKLIK = KANAAL BETREDEN", 8, color=MUTED).pack(side="right")
        self.bind("<Destroy>", self._cleanup, add="+")

    def _right_panel(self, parent):
        self.text(parent, "RADIO / CONTROL", 11, True, color=self.accent).pack(
            anchor="w", padx=self.dim(20), pady=(self.dim(19), self.dim(8))
        )
        display = tk.Frame(parent, bg="#07131D", highlightbackground=DIVIDER,
                           highlightthickness=self.dim(1))
        display.pack(fill="x", padx=self.dim(13), pady=(0, self.dim(14)))

        self.text(display, "CONNECTED  /  TS3 DIGITAL", 9, True,
                  color=GREEN, bg="#07131D").pack(anchor="w", padx=self.dim(14),
                                                   pady=(self.dim(14), self.dim(7)))
        self.mode_text = self.text(display, "RX", 31, True, color=self.accent, bg="#07131D")
        self.mode_text.pack(anchor="w", padx=self.dim(14))
        self.channel_label = self.text(display, "KANAAL: -", 10, True,
                                       color=TEXT, bg="#07131D")
        self.channel_label.pack(anchor="w", padx=self.dim(14), pady=(0, self.dim(5)))
        self.nickname_label = self.text(display, "CALLSIGN: -", 9,
                                        color=MUTED, bg="#07131D")
        self.nickname_label.pack(anchor="w", padx=self.dim(14),
                                 pady=(0, self.dim(13)))
        self.meter = tk.Canvas(parent, bg=PANEL, height=self.dim(52),
                               highlightthickness=0, bd=0)
        self.meter.pack(fill="x", padx=self.dim(14), pady=(0, self.dim(11)))
        self.meter.bind("<Configure>", lambda e: self._meter_draw())

        self.text(parent, "ZENDEN / ONTVANGEN", 9, True, color=MUTED).pack(
            anchor="w", padx=self.dim(16), pady=(0, self.dim(8)))
        self.ptt_button = tk.Label(parent, text="  PUSH TO TALK",
                                   image=self.photo("ptt", 34), compound="left",
                                   bg=self.accent, fg="#061524", cursor="hand2",
                                   font=("Segoe UI", 16, "bold"), padx=self.dim(12),
                                   pady=self.dim(22), relief="flat")
        self.ptt_button.pack(fill="x", padx=self.dim(14), pady=(0, self.dim(5)))
        self.ptt_button.bind("<ButtonPress-1>", self._ptt_press)
        self.ptt_button.bind("<ButtonRelease-1>", self._ptt_release)
        self.ptt_button.bind("<Leave>", self._ptt_release)
        self.text(parent, "INGEDRUKT = TX  /  LOSLATEN = RX", 8, color=MUTED).pack(
            anchor="center", pady=(0, self.dim(17)))

        self.text(parent, "AUDIO / BEDIENING", 9, True, color=MUTED).pack(
            anchor="w", padx=self.dim(16), pady=(0, self.dim(7)))
        tools = tk.Frame(parent, bg=PANEL)
        tools.pack(fill="x", padx=self.dim(14))
        self.mic_button = self.icon_button(tools, "mic", self.on_mic, "MIC")
        self.mic_button.pack(side="left", fill="x", expand=True, padx=(0, self.dim(5)))
        self.speaker_button = self.icon_button(tools, "headphones", self.on_speaker, "AUDIO")
        self.speaker_button.pack(side="right", fill="x", expand=True)
        self.disconnect_button = self.icon_button(
            parent, "hangup", self.on_disconnect, "VERBINDING VERBREKEN", fill="#7E2634")
        self.disconnect_button.pack(side="bottom", fill="x", padx=self.dim(14),
                                    pady=self.dim(17))
        self._update_audio_buttons()

    def _update_audio_buttons(self):
        mic = self.backend.config.get("mic_muted", False)
        output = self.backend.config.get("output_muted", False)
        self.mic_button.configure(
            image=self.photo("mic_off" if mic else "mic", 22),
            text="  MIC UIT" if mic else "  MIC")
        self.speaker_button.configure(
            image=self.photo("headphones_off" if output else "headphones", 22),
            text="  UIT" if output else "  AUDIO")

    def _meter_draw(self):
        self.meter.delete("all")
        width = max(self.dim(80), self.meter.winfo_width())
        for i in range(15):
            x = self.dim(5) + i * (width - self.dim(14)) / 15
            height = self.dim(9 + (i % 5) * 5) if self.tx else self.dim(9)
            colour = RED if self.tx else (self.accent if i < 7 else DIVIDER)
            self.meter.create_rectangle(
                x, self.dim(39) - height, x + max(2, self.dim(9)),
                self.dim(39), fill=colour, outline="")
        self.meter.create_text(self.dim(5), self.dim(48), anchor="sw",
                               text="TX LEVEL" if self.tx else "RX READY",
                               fill=MUTED, font=("Consolas", 8, "bold"))

    def set_tx(self, transmitting: bool):
        self.tx = bool(transmitting)
        self.mode_text.configure(text="TX  •  ON AIR" if self.tx else "RX",
                                 fg=RED if self.tx else self.accent)
        self.ptt_button.configure(text="  ZENDEN / TX" if self.tx else "  PUSH TO TALK",
                                  fg=TEXT if self.tx else "#061524",
                                  bg="#A73545" if self.tx else self.accent)
        self._meter_draw()

    def _ptt_press(self, _event=None):
        if not self._ptt_held:
            self._ptt_held = True
            self.on_ptt_down()

    def _ptt_release(self, _event=None):
        if self._ptt_held:
            self._ptt_held = False
            self.on_ptt_up()

    def _cleanup(self, event):
        if event.widget is self and self._ptt_held:
            self._ptt_release()

    def _wheel(self, event):
        if event.delta:
            self._scroll(-int(event.delta / 120) * 3)
            return "break"

    def _scroll(self, delta):
        if delta:
            self.canvas.yview_scroll(int(delta), "units")
        return "break"

    def _queue_draw(self, _event=None):
        if self._pending is None:
            self._pending = self.after(60, self._draw)

    def update_snapshot(self, snapshot, force=False):
        if snapshot is None:
            return
        self.snapshot = snapshot
        self._update_audio_buttons()
        self.nickname_label.configure(
            text="CALLSIGN: " + self.backend.config.get("nickname", "-"))
        own_channel = next(
            (c.name for c in snapshot.channels if c.id == snapshot.own_channel_id), "Onbekend")
        spacer = parse_spacer(own_channel)
        if spacer:
            own_channel = "KANAAL"
        # Keep labels short enough for a narrow side-panel; full names remain in the list.
        self.channel_label.configure(
            text="KANAAL: " + (own_channel[:29] + "…" if len(own_channel) > 30 else own_channel))
        self.counter.configure(text=f"{len(snapshot.channels)} KANALEN")
        self.user_count.configure(text=f"{len(snapshot.clients)} GEBRUIKERS ONLINE")
        if force:
            self._draw()
        else:
            self._queue_draw()

    def _flatten(self):
        if self.snapshot is None:
            return []
        channels = list(self.snapshot.channels)
        users = list(self.snapshot.clients)
        query = self.search.get().strip().casefold()
        grouped = {}
        by_id = {}
        for c in channels:
            cid = int(c.id)
            by_id[cid] = c
            grouped.setdefault(int(c.parent_id), []).append(c)
        members = {}
        for u in users:
            members.setdefault(int(u.channel_id), []).append(u)
        rows = []
        seen = set()
        def visit(channel, depth=0):
            cid = int(channel.id)
            if cid in seen:
                return
            seen.add(cid)
            spacer = parse_spacer(channel.name)
            direct_users = members.get(cid, ())
            children = grouped.get(cid, ())
            matched = (not query or query in channel.name.casefold()
                       or any(query in u.name.casefold() for u in direct_users))
            if query and not matched:
                matched = any(query in child.name.casefold() for child in children)
            if query and not matched:
                return
            rows.append(("spacer" if spacer else "channel", channel, depth, spacer,
                         bool(children), cid in self.collapsed))
            if cid in self.collapsed and not query:
                return
            for user in direct_users:
                if not query or query in user.name.casefold() or query in channel.name.casefold():
                    rows.append(("user", user, depth + 1, None, False, False))
            for child in children:
                visit(child, depth + 1)
        for channel in channels:
            pid = int(channel.parent_id)
            if pid == 0 or pid not in by_id:
                visit(channel)
        # Defensive fallback for unordered or cyclic TS3 snapshots.
        for channel in channels:
            if int(channel.id) not in seen and not query:
                visit(channel)
        return rows

    def _draw(self):
        self._pending = None
        canvas = self.canvas
        if not canvas.winfo_exists():
            return
        view = canvas.yview()
        canvas.delete("all")
        self.rows = self._flatten()
        width = max(self.dim(280), canvas.winfo_width())
        top = self.dim(9)
        channel_h = self.dim(40)
        user_h = self.dim(33)
        spacer_h = self.dim(30)
        indent = self.dim(18)
        for index, (kind, obj, depth, spacer, has_children, collapsed) in enumerate(self.rows):
            is_spacer = kind == "spacer"
            height = spacer_h if is_spacer else user_h if kind == "user" else channel_h
            y = top
            tag = "line:" + str(index)
            inset = min(self.dim(22) + depth * indent, width - self.dim(60))
            if kind == "channel":
                background = PANEL_HIGH if self.selected == ("channel", int(obj.id)) else (
                    "#14273B" if index % 2 == 0 else LIST_BG)
                canvas.create_rectangle(0, y, width, y + height, fill=background,
                                        outline="", tags=(tag,))
                if self.selected == ("channel", int(obj.id)):
                    canvas.create_rectangle(0, y, self.dim(4), y + height,
                                            fill=self.accent, outline="", tags=(tag,))
                icon = "channel_locked" if obj.has_password else "channel"
                canvas.create_image(inset + self.dim(13), y + height // 2,
                                    image=self.photo(icon, 18), tags=(tag,))
                canvas.create_text(inset + self.dim(31), y + height // 2,
                                   text=obj.name, anchor="w", fill=TEXT,
                                   font=("Segoe UI", 10, "bold"), tags=(tag,))
                if has_children:
                    toggle = "collapse:" + str(int(obj.id))
                    cx = max(self.dim(8), inset - self.dim(8))
                    arrow = "▸" if collapsed else "▾"
                    canvas.create_text(cx, y + height // 2, text=arrow, fill=self.accent,
                                       font=("Segoe UI Symbol", 11), tags=(tag, toggle))
                    canvas.tag_bind(toggle, "<Button-1>",
                                    lambda e, cid=int(obj.id): self._toggle(cid))
                canvas.tag_bind(tag, "<Button-1>",
                                lambda e, cid=int(obj.id): self._select_channel(cid))
                canvas.tag_bind(tag, "<Double-Button-1>",
                                lambda e, cid=int(obj.id): self.on_join_channel(cid))
                canvas.tag_bind(tag, "<Button-3>",
                                lambda e, cid=int(obj.id): self._channel_context(e, cid))
            elif kind == "user":
                background = "#0E1E30" if index % 2 else LIST_BG
                canvas.create_rectangle(0, y, width, y + height, fill=background,
                                        outline="", tags=(tag,))
                icon = "user_muted" if obj.input_muted else (
                    "user_talking" if obj.talking else "user")
                canvas.create_image(inset + self.dim(13), y + height // 2,
                                    image=self.photo(icon, 17), tags=(tag,))
                own = "   /  IK" if int(obj.id) == int(self.snapshot.own_client_id) else ""
                canvas.create_text(inset + self.dim(31), y + height // 2,
                                   text=obj.name + own, anchor="w", fill=GREEN if obj.talking else MUTED,
                                   font=("Segoe UI", 10), tags=(tag,))
                canvas.tag_bind(tag, "<Double-Button-1>",
                                lambda e, uid=int(obj.id): self._open_private(uid))
                canvas.tag_bind(tag, "<Button-3>",
                                lambda e, uid=int(obj.id): self._user_context(e, uid))
            else:
                # Draw actual geometric lines, never a repeated Unicode string
                # that Windows may render incorrectly or turn into white icons.
                x1 = inset + self.dim(6)
                x2 = width - self.dim(19)
                center = y + height // 2
                body = spacer.body.strip() if spacer else ""
                if spacer and spacer.align == "*":
                    if body and x2 > x1:
                        dotted = body in ("...", "-.-", "-..", "---")
                        dash = (self.dim(6), self.dim(5)) if dotted else None
                        canvas.create_line(x1, center, x2, center, fill=self.accent_secondary,
                                           width=max(1, self.dim(2)), dash=dash, tags=(tag,))
                        canvas.create_oval(x1-self.dim(2), center-self.dim(2),
                                           x1+self.dim(2), center+self.dim(2),
                                           fill=self.accent, outline="", tags=(tag,))
                elif body and body != ".":
                    if spacer.align == "c":
                        x, anchor = (x1 + x2) / 2, "center"
                    elif spacer.align == "r":
                        x, anchor = x2, "e"
                    else:
                        x, anchor = x1, "w"
                    canvas.create_text(x, center, text=body, anchor=anchor,
                                       font=("Segoe UI", 10, "bold"),
                                       fill=self.accent_secondary, tags=(tag,))
                canvas.tag_bind(tag, "<Button-1>", lambda e: None)
            top += height
        canvas.configure(scrollregion=(0, 0, width, top + self.dim(15)))
        if view and top > canvas.winfo_height():
            canvas.yview_moveto(view[0])

    def _select_channel(self, cid):
        self.selected = ("channel", cid)
        self._draw()

    def _toggle(self, cid):
        if cid in self.collapsed:
            self.collapsed.remove(cid)
        else:
            self.collapsed.add(cid)
        self._draw()
        return "break"

    def _open_private(self, uid):
        if not self.snapshot or uid == int(self.snapshot.own_client_id):
            return
        person = next((u for u in self.snapshot.clients if int(u.id) == uid), None)
        if person is not None:
            self.on_private_chat(uid, person.name)

    def _channel_context(self, event, cid):
        menu = tk.Menu(self, tearoff=False, bg=PANEL_HIGH, fg=TEXT)
        menu.add_command(label="Kanaal betreden", command=lambda: self.on_join_channel(cid))
        menu.tk_popup(event.x_root, event.y_root)

    def _user_context(self, event, uid):
        if self.snapshot and uid != int(self.snapshot.own_client_id):
            menu = tk.Menu(self, tearoff=False, bg=PANEL_HIGH, fg=TEXT)
            menu.add_command(label="Privébericht", command=lambda: self._open_private(uid))
            menu.tk_popup(event.x_root, event.y_root)
