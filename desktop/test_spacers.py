"""Regression tests for TS3 server-spacer syntax without network access."""
import unittest

from spacers import parse_spacer, spacer_display


def measure(value: str) -> int:
    return len(value) * 8


class TestTeamSpeakSpacers(unittest.TestCase):
    def test_separator_from_live_ts_heerlen(self):
        spacer = parse_spacer("[*spacer619]──")
        self.assertIsNotNone(spacer)
        self.assertEqual(spacer.align, "*")
        rendered = spacer_display(spacer, 416, measure)
        self.assertGreater(len(rendered), 20)
        self.assertTrue(set(rendered) == {"─"})
        self.assertLessEqual(measure(rendered), 416)
        self.assertNotIn("[*spacer", rendered.lower())

    def test_separator_special_types(self):
        cases = {
            "[*spacer0]___": "━",
            "[*spacer1]---": "╌",
            "[*spacer2]...": "·",
            "[*spacer3]-.-": "┄",
            "[*spacer4]-..": "┄",
            "[*spacer5]=": "=",
        }
        for name, char in cases.items():
            with self.subTest(name=name):
                spacer = parse_spacer(name)
                text = spacer_display(spacer, 321, measure)
                self.assertGreater(len(text), 8)
                self.assertEqual(set(text), {char})

    def test_centre_left_right(self):
        center = parse_spacer("[cSpAcEr0]WELKOM TO TS-HEERLEN")
        self.assertEqual(center.align, "c")
        centered = spacer_display(center, 420, measure)
        self.assertTrue(centered.startswith(" "))
        self.assertEqual(centered.strip(), "WELKOM TO TS-HEERLEN")
        right = spacer_display(parse_spacer("[rSpacer42]Right"), 300, measure)
        self.assertTrue(right.startswith(" "))
        self.assertTrue(right.endswith("Right"))
        self.assertEqual(spacer_display(parse_spacer("[lspacer1]Links"), 300, measure), "Links")

    def test_blank_and_non_spacer_names(self):
        self.assertEqual(spacer_display(parse_spacer("[rspacer0]."), 300, measure), "")
        self.assertEqual(spacer_display(parse_spacer("[cspacer3]"), 300, measure), "")
        self.assertIsNone(parse_spacer("CONTROL ROOM"))
        self.assertIsNone(parse_spacer("[notspacer]Kanaal"))

    def test_width_tracks_resize(self):
        spacer = parse_spacer("[*spacer619]──")
        short = spacer_display(spacer, 160, measure)
        long = spacer_display(spacer, 600, measure)
        self.assertGreater(len(long), len(short))
        self.assertLessEqual(measure(long), 600)


if __name__ == "__main__":
    unittest.main()
