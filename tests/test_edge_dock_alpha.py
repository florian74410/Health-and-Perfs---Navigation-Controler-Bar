"""Offscreen alpha regression for the chamfered NOVA side docks."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication
from healthbar.edge_docks import PCBDockFrame


class DummySettings:
    theme = "blue-neon"


def test_sidebar_corners_are_transparent():
    app = QApplication.instance() or QApplication([])
    frame = PCBDockFrame(DummySettings())
    frame.resize(250, 360)
    frame.show()
    app.processEvents()
    image = QImage(frame.size(), QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    frame.render(painter)
    painter.end()
    for x, y in ((0, 0), (249, 0), (0, 359), (249, 359),
                 (4, 4), (245, 4), (4, 355), (245, 355)):
        assert image.pixelColor(x, y).alpha() == 0, (x, y, image.pixelColor(x, y).name())
    assert image.pixelColor(125, 125).alpha() > 0
    frame.close()
