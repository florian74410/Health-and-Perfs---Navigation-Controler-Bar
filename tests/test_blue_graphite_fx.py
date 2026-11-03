"""Offscreen smoke checks for the isolated Blue Neon decorative painter."""
import os
import unittest
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QImage, QPainter
from healthbar.blue_graphite_fx import paint_edge_fx


class BlueGraphiteFxTests(unittest.TestCase):
    def _render(self, phase):
        image = QImage(300, 90, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        paint_edge_fx(painter, QRectF(0, 0, 300, 90), phase)
        painter.end()
        return image

    def test_transparent_exterior(self):
        image = self._render(.4)
        for x,y in ((0,0),(299,0),(0,89),(299,89),(150,45)):
            self.assertEqual(image.pixelColor(x,y).alpha(), 0)

    def test_effects_visible(self):
        image = self._render(.25)
        self.assertTrue(any(image.pixelColor(x,7).alpha() > 0 for x in range(20,280)))

    def test_small_rect_is_safe(self):
        image=QImage(15,12,QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)
        p=QPainter(image)
        paint_edge_fx(p,QRectF(0,0,15,12),.6)
        p.end()
        self.assertEqual(image.pixelColor(7,5).alpha(),0)


if __name__=="__main__":
    unittest.main()
