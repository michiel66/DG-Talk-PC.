"""Windows GUI smoke test: proves custom radio rows and actual spacer lines render.

No TeamSpeak server required: an in-memory snapshot exercises the radio dashboard,
click targets, live TX state and screenshot-ready channel drawing.
"""
from __future__ import annotations

from types import SimpleNamespace as NS
import tkinter as tk
from PIL import ImageTk

from color_icons import draw_icon
from radio_console import RadioConsole


class FakeBackend:
    config = {
        "theme": "standard", "nickname": "Testgebruiker",
        "mic_muted": False, "output_muted": False,
    }

    def snapshot(self):
        return NS(
            name="TS-HEERLEN",
            own_channel_id=2,
            own_client_id=10,
            channels=[
                NS(id=1, parent_id=0, name="[*spacer619]──",
                   has_password=False),
                NS(id=2, parent_id=0, name="CONTROL ROOM",
                   has_password=False),
                NS(id=3, parent_id=0, name="[cspacer0]WELKOM TO TS-HEERLEN",
                   has_password=False),
                NS(id=4, parent_id=0, name="QSO KANAAL ROOM 1",
                   has_password=True),
            ],
            clients=[
                NS(id=10, channel_id=2, name="Testgebruiker",
                   input_muted=False, talking=False),
                NS(id=11, channel_id=2, name="Zender",
                   input_muted=False, talking=True),
            ]
        )


def run():
    root = tk.Tk()
    root.title("DG-Talk native radio UI smoke test")
    root.geometry("1150x800")
    root.update_idletasks()
    icons = {}
    def icon(name, size):
        key = name, size
        if key not in icons:
            icons[key] = ImageTk.PhotoImage(draw_icon(name, size), master=root)
        return icons[key]

    calls = []
    screen = RadioConsole(
        root, FakeBackend(), {}, icon,
        on_settings=lambda: calls.append("settings"),
        on_chat=lambda: calls.append("chat"),
        on_mic=lambda: calls.append("mic"),
        on_speaker=lambda: calls.append("speaker"),
        on_disconnect=lambda: calls.append("disconnect"),
        on_ptt_down=lambda: calls.append("down"),
        on_ptt_up=lambda: calls.append("up"),
        on_join_channel=lambda cid: calls.append(("join", cid)),
        on_private_chat=lambda uid, name: calls.append(("private", uid, name)),
        dpi_scale=1.0
    )
    screen.pack(fill="both", expand=True)
    root.update()
    screen._draw()
    root.update()

    canvas = screen.canvas
    all_shapes = canvas.find_all()
    assert len(all_shapes) >= 10, "No vector channel rows were drawn"
    real_lines = [item for item in all_shapes if canvas.type(item) == "line"]
    assert real_lines, "The [*spacer] line must be a vector line"
    rendered_texts = [str(canvas.itemcget(item, "text")) for item in all_shapes
                      if canvas.type(item) == "text"]
    assert not any("[*spacer" in s or "[cspacer" in s for s in rendered_texts)
    assert any("CONTROL ROOM" in s for s in rendered_texts)
    assert any("WELKOM" in s for s in rendered_texts)

    screen.set_tx(True)
    assert "TX" in screen.mode_text.cget("text")
    screen.set_tx(False)
    assert screen.mode_text.cget("text") == "RX"

    screen._ptt_press()
    screen._ptt_release()
    assert calls == ["down", "up"], calls

    screen.on_join_channel(2)
    screen.on_private_chat(11, "Zender")
    assert calls[-2:] == [("join", 2), ("private", 11, "Zender")]

    canvas.config(width=400)
    root.update()
    screen._draw()
    assert any(canvas.type(item) == "line" for item in canvas.find_all())
    root.destroy()
    print("PASS: native DG-Talk radio console, TS3 line, click, PTT, dynamic layout")


if __name__ == "__main__":
    run()
