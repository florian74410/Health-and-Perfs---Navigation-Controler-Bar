"""Lightweight Blue Neon/Graphite painter primitives.

75% dark graphite, 20% electric blue, 5% polished silver highlights.
Painter calls are static and rely on existing widget timers.
"""
from __future__ import annotations
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPen

GRAPHITE = "#11151B"
GRAPHITE_DARK = "#090D12"
BLUE = "#14BFFE"
CYAN = "#8CEBFF"
STEEL = "#8995A7"

def paint_electron_rail(painter, bounds, phase):
    """A clipped, moving bright node atop a very thin blue optical guide."""
    if bounds.width()<=40 or bounds.height()<=0:
        return
    pos=bounds.left()+18+(bounds.width()-36)*(float(phase)%1)
    painter.save()
    painter.setClipRect(bounds)
    painter.setPen(QPen(QColor(17,138,210,75),.8))
    painter.drawLine(bounds.left(),bounds.center().y(),bounds.right(),bounds.center().y())
    gradient=QLinearGradient(pos-28,bounds.top(),pos+28,bounds.top())
    gradient.setColorAt(0,QColor(20,191,254,0))
    gradient.setColorAt(.40,QColor(20,191,254,115))
    gradient.setColorAt(.50,QColor(215,250,255,235))
    gradient.setColorAt(.60,QColor(20,191,254,115))
    gradient.setColorAt(1,QColor(20,191,254,0))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.fillRect(QRectF(pos-28,bounds.center().y()-1,56,2),gradient)
    painter.restore()
