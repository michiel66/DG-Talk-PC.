"""TeamSpeak 3 spacer channel grammar and pixel-accurate text layout.

Channel names:
    [cspacer0]Welcome      centred
    [lspacer3]Heading      left
    [rspacer2]Right        right
    [*spacer619]──         repeat across the full available channel-tree width

The normal channel names must remain unchanged for all protocol operations.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Callable

SPACER_RE = re.compile(r"^\[([lcr*]?)spacer([^\]]*)\](.*)$", re.IGNORECASE | re.DOTALL)
LINE_TOKENS = {
    "___": "━",
    "---": "╌",
    "...": "·",
    "-.-": "┄",
    "-..": "┄",
}


@dataclass(frozen=True)
class Spacer:
    align: str
    body: str


def parse_spacer(channel_name: str) -> Spacer | None:
    """Recognize the exact TS3 spacer prefix, case-insensitively."""
    match = SPACER_RE.match(channel_name)
    if match is None:
        return None
    kind, _unique_id, body = match.groups()
    return Spacer(align=(kind or "l").lower(), body=body)


def spacer_display(
    spacer: Spacer,
    width_px: int,
    measure: Callable[[str], int],
) -> str:
    """Render spacer for the current Treeview width using real font pixel metrics.

    The original literal [*spacer#] is never shown. Width must exclude the
    tree indentation and the expander. The output is text only: no UI coupling.
    """
    width_px = max(0, int(width_px))
    if width_px < 10:
        return ""

    value = spacer.body.strip()
    if spacer.align == "*":
        if not value:
            return ""
        unit = LINE_TOKENS.get(value, value)
        # A line must not overflow the available channel-tree width.
        unit_px = max(1, measure(unit))
        count = max(1, width_px // unit_px)
        result = unit * count
        while result and measure(result) > width_px:
            result = result[:-1]
        return result

    # TS3 lets [rspacer#]. act as an effectively blank spacer row.
    if not value or (spacer.align == "r" and value == "."):
        return ""
    if spacer.align == "l":
        return value

    # Actual Tk font measurement prevents ugly misalignment on 4K/high DPI.
    blank_px = max(1, measure(" "))
    free = max(0, width_px - measure(value))
    padding_spaces = max(0, int(free / blank_px))
    if spacer.align == "c":
        return " " * (padding_spaces // 2) + value
    return " " * padding_spaces + value
