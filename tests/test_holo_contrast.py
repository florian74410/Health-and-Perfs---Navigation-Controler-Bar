import unittest
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication
from healthbar.holo import HoloLabel

class HoloContrastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def test_glyphs_have_opaque_dark_outline_and_light_interior_without_a_backplate(self):
        label=HoloLabel('24.5 ms')
        label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        label.setStyleSheet('color:#ffffff;background:transparent;font-size:20px;font-weight:700;')
        label.resize(160,40);label.show();self.app.processEvents()
        image=label.grab().toImage()
        pixels=[image.pixelColor(x,y) for x in range(image.width()) for y in range(image.height())]
        self.assertGreater(sum(c.alpha()==255 and c.lightness()<30 for c in pixels),50)
        self.assertGreater(sum(c.alpha()==255 and c.lightness()>220 for c in pixels),50)
        self.assertEqual(image.pixelColor(150,20).alpha(),0)
        label.close()
