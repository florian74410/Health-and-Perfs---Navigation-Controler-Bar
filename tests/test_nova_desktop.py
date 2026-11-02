"""Static theme export tests; do not alter XFCE or require PySide6."""
import tempfile
import unittest
from pathlib import Path
from nova_nexus.desktop_theme import export_gtk_theme
from nova_nexus.xfwm4 import export_xfwm4_theme


class ExportTests(unittest.TestCase):
    def test_gtk_theme(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = export_gtk_theme(Path(tmp) / "NOVA-NEXUS-HD")
            css = (target / "gtk-3.0" / "gtk.css").read_text()
            self.assertIn("#00CBF3", css)
            self.assertIn("button:hover", css)

    def test_window_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = export_xfwm4_theme(Path(tmp))
            self.assertTrue((dest / "themerc").is_file())
            content = (dest / "close-active.xpm").read_text()
            self.assertIn("24 24", content)
            self.assertTrue((dest / "title-1-inactive.xpm").exists())


if __name__ == "__main__":
    unittest.main()
