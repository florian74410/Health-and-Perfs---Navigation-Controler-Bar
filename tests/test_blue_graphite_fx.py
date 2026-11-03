import unittest
from PySide6.QtGui import QImage, QPainter, QColor
from PySide6.QtCore import Qt, QRectF
from healthbar.blue_fx import GRAPHITE, BLUE, paint_electron_rail

class BlueGraphiteFX(unittest.TestCase):
    def test_palette_is_graphite_and_blue(self):
        self.assertEqual(GRAPHITE,"#11151B")
        self.assertTrue(QColor(BLUE).isValid())

    def test_rail_preserves_corner_transparency(self):
        frame=QImage(320,36,QImage.Format.Format_ARGB32_Premultiplied)
        frame.fill(Qt.GlobalColor.transparent)
        painter=QPainter(frame)
        paint_electron_rail(painter,QRectF(15,4,290,14),.3)
        painter.end()
        self.assertEqual(frame.pixelColor(0,0).alpha(),0)
        self.assertEqual(frame.pixelColor(319,35).alpha(),0)

    def test_no_paint_on_tiny_frame(self):
        frame=QImage(20,15,QImage.Format.Format_ARGB32)
        frame.fill(Qt.GlobalColor.transparent)
        p=QPainter(frame)
        paint_electron_rail(p,QRectF(0,0,20,15),0)
        p.end()
        self.assertEqual(frame.pixelColor(10,7).alpha(),0)
