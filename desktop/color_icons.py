"""Full-colour DG-Talk PC pictograms: drawn as RGBA pixels, not font emoji.

Tkinter/ttk on Windows frequently displays emoji as monochrome glyphs. These
vector-like Pillow drawings are rendered to actual coloured PNG-backed Tk
PhotoImages, independent of the selected Windows font or emoji availability.
The same DG-Talk radio design is exported to a multi-resolution Windows ICO.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from PIL import Image, ImageDraw

ICON_TYPES = (
    "app", "radio", "settings", "chat", "mic", "mic_off", "headphones",
    "headphones_off", "hangup", "ptt", "server", "channel", "channel_locked",
    "user", "user_talking", "user_muted", "tree", "snowman", "gift",
    "snowflake", "truck", "antenna", "planet", "rocket", "star",
    "satellite", "left", "right", "back", "test",
)


def draw_icon(name: str, size: int = 28, accent: str = "#1A91D0") -> Image.Image:
    """Draw an anti-aliased coloured icon with transparent background."""
    if name not in ICON_TYPES:
        raise ValueError("Unknown icon: " + name)
    canvas = max(256, size * 4)
    image = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    mul = canvas / 100
    blue = accent
    light = "#54CFFD"
    gold = "#FFC649"
    dark = "#102139"
    green = "#44CB7E"
    red = "#F04452"
    white = "#EAF7FF"
    violet = "#AD7DFF"

    def P(coords):
        return tuple(int(round(v * mul)) for v in coords)

    def oval(box, fill, outline=None, width=1):
        d.ellipse(P(box), fill=fill, outline=outline, width=max(1, round(width * mul)))

    def rect(box, fill, radius=0, outline=None, width=1):
        d.rounded_rectangle(P(box), radius=round(radius * mul), fill=fill,
                            outline=outline, width=max(1, round(width * mul)))

    def line(points, color, width=5, joint="curve"):
        d.line([P(pt) for pt in points], fill=color, width=max(1, round(width * mul)),
               joint=joint)

    def poly(points, fill, outline=None):
        d.polygon([P(pt) for pt in points], fill=fill)
        if outline:
            line(points + [points[0]], outline, 2)

    def arc(box, start, end, color, width=6):
        d.arc(P(box), start=start, end=end, fill=color, width=max(1, round(width * mul)))

    if name in ("app", "radio", "server"):
        if name == "app":
            rect((2, 2, 98, 98), dark, 24, "#186D98", 3)
            oval((77, 13, 89, 25), red)
        line([(27, 29), (19, 12)], gold, 5)
        oval((15, 10, 22, 17), gold)
        rect((18, 27, 86, 83), "#21354B", 12, blue, 4)
        rect((29, 35, 73, 57), "#0A222E", 4, light, 2)
        rect((33, 39, 53, 43), green, 2)
        rect((33, 47, 66, 50), gold, 1)
        for x in (35, 43, 51, 59, 67):
            line([(x, 67), (x, 72)], "#8CB3C5", 3)
        oval((73, 62, 82, 71), red)
        if name == "app":
            arc((5, 19, 45, 63), 180, 259, gold, 4)
            arc((2, 12, 53, 72), 183, 251, light, 3)

    elif name in ("mic", "mic_off", "ptt"):
        oval((35, 12, 65, 59), light, "#137BB2", 2)
        rect((35, 25, 65, 59), blue, 15)
        arc((22, 28, 78, 81), 8, 172, gold, 7)
        line([(50, 79), (50, 89)], green, 6)
        line([(33, 89), (67, 89)], green, 6)
        if name == "ptt":
            oval((68, 11, 91, 34), green)
            oval((74, 17, 85, 28), white)
        if name == "mic_off":
            line([(17, 82), (84, 16)], red, 10)
            line([(17, 82), (84, 16)], white, 2)

    elif name in ("headphones", "headphones_off"):
        arc((16, 12, 84, 88), 179, 361, light, 9)
        rect((13, 50, 31, 82), blue, 7, gold, 2)
        rect((69, 50, 87, 82), blue, 7, gold, 2)
        rect((20, 54, 27, 79), gold, 2)
        rect((73, 54, 80, 79), gold, 2)
        if name == "headphones_off":
            line([(17, 85), (85, 16)], red, 10)
            line([(17, 85), (85, 16)], white, 2)

    elif name == "hangup":
        poly([(9, 49), (19, 35), (33, 30), (39, 43), (35, 52),
              (43, 59), (57, 59), (65, 52), (61, 43), (67, 30),
              (81, 35), (91, 49), (85, 63), (73, 73), (27, 73),
              (15, 63)], gold)
        line([(31, 40), (37, 54), (61, 54), (69, 40)], red, 3)

    elif name == "settings":
        import math
        center = (50, 50)
        points = []
        for i in range(24):
            rad = (i / 24.0) * math.tau
            radius = 40 if i % 3 == 1 else 32
            points.append((50 + math.cos(rad) * radius,
                           50 + math.sin(rad) * radius))
        poly(points, blue)
        oval((26, 26, 74, 74), "#123048")
        oval((39, 39, 61, 61), gold)

    elif name == "chat":
        rect((10, 16, 89, 69), blue, 16)
        poly([(19, 64), (21, 88), (46, 66)], blue)
        for x in (32, 49, 66):
            oval((x-5, 38, x+5, 48), gold)

    elif name == "channel" or name == "channel_locked":
        rect((8, 31, 93, 79), blue, 9, "#78D5FF", 3)
        poly([(13, 30), (13, 22), (41, 22), (53, 32)], "#4CB8F4")
        rect((15, 43, 84, 72), "#1C6687", 4)
        if name == "channel_locked":
            arc((42, 41, 72, 72), 180, 360, gold, 6)
            rect((40, 57, 75, 84), gold, 5)
            oval((54, 64, 60, 70), dark)

    elif name in ("user", "user_talking", "user_muted"):
        oval((33, 12, 67, 46), green, "#C0FFD8", 2)
        arc((13, 49, 87, 96), 180, 360, blue, 11)
        if name == "user_talking":
            arc((60, 9, 93, 62), 300, 70, gold, 6)
            oval((79, 12, 91, 24), gold)
        if name == "user_muted":
            line([(16, 85), (87, 14)], red, 9)

    elif name == "tree":
        line([(49, 68), (49, 93)], "#9B6328", 11)
        poly([(50, 5), (11, 53), (28, 53), (8, 75), (92, 75), (72, 53),
              (89, 53)], "#279E56", "#9FF6AC")
        for x, y, fill in ((32, 48, red), (64, 40, gold), (49, 64, light), (69, 64, red)):
            oval((x-5, y-5, x+5, y+5), fill)
        poly([(50, 2), (54, 14), (66, 14), (57, 21),
              (61, 32), (50, 24), (39, 32), (43, 21),
              (34, 14), (46, 14)], gold)

    elif name == "snowman":
        oval((20, 42, 80, 96), white, "#93D3F1", 3)
        oval((29, 15, 72, 63), white, "#93D3F1", 3)
        rect((33, 7, 68, 24), dark, 3)
        line([(28, 24), (76, 24)], gold, 5)
        for x in (42, 61):
            oval((x, 33, x+5, 38), dark)
        poly([(51, 41), (69, 45), (51, 49)], "#FCA137")
        for y in (65, 77):
            oval((49, y, 56, y+7), blue)

    elif name == "gift":
        rect((16, 35, 84, 90), red, 7, "#F6A3A3", 3)
        rect((12, 29, 88, 47), "#EF6360", 5)
        rect((44, 30, 56, 90), gold, 2)
        line([(19, 49), (81, 49)], gold, 4)
        arc((24, 7, 54, 39), 45, 285, green, 6)
        arc((48, 7, 78, 39), 255, 495, green, 6)

    elif name == "snowflake":
        for deg in (0, 60, 120):
            import math
            angle = math.radians(deg)
            dx, dy = math.cos(angle) * 35, math.sin(angle) * 35
            line([(50-dx, 50-dy), (50+dx, 50+dy)], light, 6)
        oval((44, 44, 56, 56), gold)

    elif name == "truck":
        rect((8, 33, 63, 77), "#E78A24", 7)
        poly([(63, 46), (76, 46), (94, 64), (94, 79), (63, 79)], gold)
        rect((70, 51, 80, 63), "#156A90", 2)
        for x in (27, 74):
            oval((x-12, 69, x+12, 93), dark, light, 3)
            oval((x-4, 77, x+4, 85), gold)

    elif name == "antenna":
        line([(50, 90), (50, 24)], gold, 6)
        line([(27, 90), (72, 90)], blue, 7)
        oval((44, 14, 56, 27), red)
        for rad in (26, 41):
            arc((50-rad, 23-rad, 50+rad, 23+rad), 105, 255, green, 5)
            arc((50-rad, 23-rad, 50+rad, 23+rad), 285, 435, green, 5)

    elif name == "planet":
        oval((25, 24, 77, 76), violet, "#DABEFF", 2)
        oval((37, 31, 51, 44), "#6E53C9")
        oval((56, 55, 71, 66), blue)
        arc((6, 32, 95, 72), 0, 180, gold, 7)
        arc((6, 32, 95, 72), 180, 360, gold, 4)

    elif name == "rocket":
        poly([(50, 8), (69, 35), (65, 75), (35, 75), (31, 35)], light)
        poly([(50, 8), (69, 35), (50, 35)], "#B4F1FF")
        oval((41, 33, 59, 51), blue, dark, 3)
        poly([(34, 59), (16, 82), (38, 75)], violet)
        poly([(66, 59), (84, 82), (62, 75)], violet)
        poly([(43, 73), (50, 96), (57, 73)], "#FF8726")
        poly([(46, 73), (50, 87), (54, 73)], gold)

    elif name == "star":
        import math
        points = []
        for i in range(10):
            r = 42 if i % 2 == 0 else 19
            a = -math.pi / 2 + i * math.pi / 5
            points.append((50 + math.cos(a) * r, 50 + math.sin(a) * r))
        poly(points, gold)
        oval((40, 38, 46, 44), white)

    elif name == "satellite":
        rect((38, 34, 61, 66), gold, 4)
        for x0 in (5, 68):
            rect((x0, 36, x0 + 28, 64), blue, 2, light, 2)
            line([(x0 + 14, 36), (x0 + 14, 64)], light, 2)
        line([(50, 36), (58, 17)], gold, 4)
        oval((54, 12, 65, 23), red)

    elif name in ("left", "back", "right"):
        if name == "right":
            line([(29, 22), (67, 50), (29, 78)], light, 10)
        else:
            line([(70, 22), (32, 50), (70, 78)], light, 10)
        oval((44, 43, 57, 57), gold)

    elif name == "test":
        poly([(32, 14), (81, 50), (32, 86)], green)
        poly([(41, 34), (65, 50), (41, 67)], gold)

    return image.resize((size, size), Image.Resampling.LANCZOS)


def write_windows_icon(target: str | Path) -> Path:
    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    image = draw_icon("app", 512)
    image.save(path, format="ICO",
               sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                      (64, 64), (128, 128), (256, 256)])
    return path


def test_color_icons():
    """Assert pixels are genuinely coloured, not grayscale emoji glyphs."""
    for name in ICON_TYPES:
        im = draw_icon(name, 48)
        assert im.size == (48, 48), name
        assert im.getbbox(), name
        coloured = any(
            a > 90 and max(r, g, b) - min(r, g, b) > 28
            for r, g, b, a in im.getdata()
        )
        assert coloured, name
    print("DG-Talk: checked %d fully coloured icons" % len(ICON_TYPES))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", help="Save a multi-size Windows .ico file")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    if args.test:
        test_color_icons()
    if args.write:
        print(write_windows_icon(args.write))
