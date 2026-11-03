"""Smoke/regression checks for the Blue Graphite settings-only fork."""
import os
import unittest
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QImage,QPainter
from PySide6.QtWidgets import QApplication

from healthbar.blue_graphite_settings import (
    enabled,paint_settings,control_stylesheet,BlueGraphiteNotice
)
from healthbar.settings_visual import PCBSettingsDialog,settings_stylesheet

app=QApplication.instance() or QApplication([])

class SettingsGraphiteTest(unittest.TestCase):
    def test_only_classic_blue(self):
        self.assertTrue(enabled("blue-neon"))
        self.assertTrue(enabled("cyber-futuriste"))
        self.assertFalse(enabled("redblack-0822"))

    def test_css_is_blue_and_has_native_controls(self):
        sheet=control_stylesheet()
        self.assertIn("QPushButton",sheet)
        self.assertIn("QScrollBar",sheet)
        self.assertIn("#2DCEFF",sheet)
        self.assertEqual(settings_stylesheet("blue-neon"),sheet)

    def test_transparent_corners(self):
        image=QImage(620,420,QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)
        p=QPainter(image)
        paint_settings(p,QRectF(10,10,600,400),.34)
        p.end()
        for x,y in ((0,0),(619,0),(0,419),(619,419),(310,0)):
            self.assertEqual(image.pixelColor(x,y).alpha(),0)
        self.assertGreater(image.pixelColor(310,210).alpha(),0)

    def test_settings_widget_is_renderable(self):
        d=PCBSettingsDialog()
        d.use_pcb_theme("blue-neon")
        d.resize(700,500)
        d.show()
        app.processEvents()
        self.assertFalse(d.grab().isNull())
        d.close()

    def test_transparent_cpu_notification(self):
        notice=BlueGraphiteNotice.create("MODE NORMAL",
                "Commande confirmée par le contrôleur",None,True)
        notice.show()
        app.processEvents()
        self.assertFalse(notice.grab().isNull())
        notice.close()

if __name__=="__main__":
    unittest.main()
