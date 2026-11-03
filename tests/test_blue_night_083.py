"""Blue Neon Dark Night: offscreen visual and regression smoke checks."""
import os
import unittest
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from PySide6.QtCore import Qt,QRectF
from PySide6.QtGui import QImage,QPainter
from PySide6.QtWidgets import QApplication
from healthbar import __version__
from healthbar.ui_kit import THEMES,set_theme,active_theme
from healthbar.blue_night_shell import paint_surface,active,control_stylesheet,asset_frames

app=QApplication.instance() or QApplication([])

class BlueNight083Test(unittest.TestCase):
    def test_version_and_registered_theme(self):
        self.assertEqual(__version__,"0.8.3")
        self.assertIn("blue-night-083",THEMES)
    def test_switch_and_restore(self):
        set_theme("blue-night-083")
        self.assertTrue(active())
        set_theme("blue-neon")
        self.assertFalse(active())
    def test_surface_respects_argb_outside(self):
        im=QImage(320,220,QImage.Format.Format_ARGB32_Premultiplied)
        im.fill(Qt.GlobalColor.transparent)
        p=QPainter(im)
        paint_surface(p,QRectF(8,8,304,204),"holo",.45,opacity=.85)
        p.end()
        for x,y in ((0,0),(319,0),(0,219),(319,219),(160,0)):
            self.assertEqual(im.pixelColor(x,y).alpha(),0)
        self.assertGreater(im.pixelColor(160,110).alpha(),0)
    def test_tiny_geometry_is_safe(self):
        im=QImage(10,10,QImage.Format.Format_ARGB32_Premultiplied)
        im.fill(Qt.GlobalColor.transparent)
        p=QPainter(im);paint_surface(p,QRectF(0,0,9,9));p.end()
        self.assertEqual(im.pixelColor(5,5).alpha(),0)
    def test_missing_assets_are_optional(self):
        self.assertEqual(asset_frames("../../../etc/passwd"),())
    def test_native_controls_present(self):
        css=control_stylesheet()
        self.assertIn("QPushButton:hover",css)
        self.assertIn("QScrollBar:vertical",css)

if __name__=="__main__":
    unittest.main()
