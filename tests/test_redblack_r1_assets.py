"""The R1 cosmetic layer does not change any telemetry/actions/setting behavior."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QImage, QPainter, QColor
from PySide6.QtWidgets import QApplication

from healthbar import redblack_r1_assets as art

class R1AssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication(["novabar-r1-tests"])

    def tearDown(self):
        art.reset_cache()

    def test_no_pack_uses_existing_chrome_fallback(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(art,"asset_root",return_value=Path(tmp)):
            art.reset_cache()
            self.assertFalse(art.installed())
            image=QImage(300,160,QImage.Format.Format_ARGB32_Premultiplied)
            image.fill(Qt.GlobalColor.transparent)
            p=QPainter(image)
            self.assertFalse(art.paint_asset_layer(p,"settings",QRectF(5,5,290,150)))
            p.end()

    def test_nine_slice_preserves_alpha_corners_and_center(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            manifest={"id":"redblack-r1","slices":{"window-chrome.png":[45,35,45,35]}}
            (root/"manifest.json").write_text(json.dumps(manifest),encoding="utf-8")
            original=QImage(299,143,QImage.Format.Format_ARGB32)
            original.fill(QColor("#1E080E"))
            # Transparent outer corners intentionally differ from the black center.
            for y in range(30):
                for x in range(30):
                    for xx,yy in ((x,y),(298-x,y),(x,142-y),(298-x,142-y)):
                        original.setPixelColor(xx,yy,QColor(0,0,0,0))
            self.assertTrue(original.save(str(root/"window-chrome.png"),"PNG"))
            with patch.object(art,"asset_root",return_value=root):
                art.reset_cache()
                self.assertTrue(art.installed())
                for width,height in ((500,280),(180,100),(65,45)):
                    dest=QImage(width,height,QImage.Format.Format_ARGB32_Premultiplied)
                    dest.fill(Qt.GlobalColor.transparent)
                    painter=QPainter(dest)
                    self.assertTrue(art.paint_nine_slice(painter,"window-chrome.png",
                                                         QRectF(0,0,width,height)))
                    painter.end()
                    self.assertEqual(dest.pixelColor(0,0).alpha(),0)
                    self.assertEqual(dest.pixelColor(width-1,0).alpha(),0)
                    # Red material is deliberately faded over opaque graphite.
                    alpha=dest.pixelColor(width//2,height//2).alpha()
                    self.assertGreater(alpha,70)
                    self.assertLess(alpha,150)

    def test_cannot_load_arbitrary_paths_or_nonalpha_textures(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"manifest.json").write_text(json.dumps({"id":"redblack-r1","slices":{}}))
            with patch.object(art,"asset_root",return_value=root):
                art.reset_cache()
                self.assertFalse(art.paint_nine_slice(QPainter(),"../../other.png",QRectF(0,0,100,70)))

if __name__=="__main__":
    unittest.main()
