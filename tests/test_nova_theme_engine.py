"""Standard-library tests: python3 -m unittest discover -s tests -p 'test_nova_theme_engine.py'."""
import json
import tempfile
import unittest
from pathlib import Path

from nova_nexus.theme_engine import (
    ThemeError, get_default_theme, load_theme, qt_stylesheet, save_theme, validate_theme,
)


class ThemeEngineTests(unittest.TestCase):
    def test_default_and_qt_css(self):
        theme = validate_theme(get_default_theme())
        self.assertIn("#00CBF3", qt_stylesheet(theme))

    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "theme.json"
            save_theme(path, get_default_theme())
            self.assertEqual(load_theme(path), get_default_theme())

    def test_reject_invalid_color(self):
        data = get_default_theme()
        data["colors"]["primary"] = "red; } QPushButton {"
        with self.assertRaises(ThemeError):
            validate_theme(data)

    def test_reject_unknown_keys(self):
        data = get_default_theme()
        data["run_command"] = "rm -rf /"
        with self.assertRaises(ThemeError):
            validate_theme(data)

    def test_reject_bad_range(self):
        data = get_default_theme()
        data["effects"]["glow"] = 9
        with self.assertRaises(ThemeError):
            validate_theme(data)

    def test_no_aliasing(self):
        a = get_default_theme()
        a["colors"]["primary"] = "#FFFFFF"
        self.assertEqual(get_default_theme()["colors"]["primary"], "#00CBF3")


if __name__ == "__main__":
    unittest.main()
