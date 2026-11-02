"""NOVA PCB overlay integration checks."""
from pathlib import Path
import xml.etree.ElementTree as ET
import unittest

ROOT = Path(__file__).resolve().parent.parent
OVERLAY = ROOT / "Assets" / "Overlays" / "nova_pcb_overlay.svg"

class OverlayTests(unittest.TestCase):
    def test_transparent_svg_routes(self):
        tree = ET.parse(OVERLAY)
        root = tree.getroot()
        self.assertTrue(root.tag.endswith("svg"))
        paths = [x for x in root.iter() if x.tag.endswith("path")]
        self.assertGreaterEqual(len(paths), 20)
        text = OVERLAY.read_text(encoding="utf-8")
        self.assertNotIn("<rect", text)  # no solid opaque backing
    def test_integrated_not_old_routes(self):
        src = (ROOT / "src" / "nova_nexus" / "chrome_v3.py").read_text(encoding="utf-8")
        self.assertIn("nova_pcb_overlay.svg", src)
        self.assertNotIn("enumerate(routes(", src)

if __name__ == "__main__":
    unittest.main()
