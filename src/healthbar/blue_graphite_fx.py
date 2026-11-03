"""Graphite Blue Neon: decorative, low-cost Qt painter effects.

Draws only in narrow panel edges; telemetry and hitboxes are untouched.
The parent widget owns the timer: this module never creates timers.
"""
from __future__ import annotations
import math
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainterPath, QPen

CYAN = "#24DFFF"
ELECTRIC = "#178AFF"
GRAPHITE = "#080D14"

def _shade(hex_color, alpha):
    c = QColor(hex_color)
    c.setAlpha(max(0, min(255, int(alpha))))
    return c

def paint_edge_fx(p, rect, phase=0.0, strength=0.75):
    """Two moving light pulses, PCB vias and quiet border reflection.

    No full-window fill: preserves ARGB transparency and readable contents.
    Rendering is deterministic for a given phase (0..1).
    """
    r = QRectF(rect).adjusted(4, 4, -4, -4)
    if r.width() < 54 or r.height() < 18:
        return
    phase = float(phase) % 1.0
    strength = max(0.0, min(1.0, float(strength)))
    p.save()
    p.setRenderHint(p.RenderHint.Antialiasing, True)
    x, y, w, h = r.x(), r.y(), r.width(), r.height()
    # Short, static PCB corner tracks: never cross readings or controls.
    segments = (
        ((x+8,y+7),(x+22,y+7),(x+29,y+14),(x+42,y+14)),
        ((x+w-8,y+h-7),(x+w-22,y+h-7),(x+w-29,y+h-14),(x+w-42,y+h-14)),
    )
    for i, points in enumerate(segments):
        path = QPainterPath(QPointF(*points[0]))
        for point in points[1:]:
            path.lineTo(QPointF(*point))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(_shade(ELECTRIC, 70*strength), 1.15))
        p.drawPath(path)
        p.setPen(QPen(_shade(CYAN, 140*strength), 0.65))
        p.drawPath(path)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(_shade(CYAN, 140*strength))
        end = QPointF(*points[-1])
        p.drawEllipse(end, 1.65, 1.65)
    # Current travelling along the top and bottom rails with a soft tail.
    for edge, t in ((0,phase),(1,(phase+0.54)%1.0)):
        travel = x+18+(w-36)*t
        yy = y+3 if edge==0 else y+h-3
        gradient = QLinearGradient(travel-33,yy,travel+18,yy)
        gradient.setColorAt(0,_shade(ELECTRIC,0))
        gradient.setColorAt(.55,_shade(CYAN,80*strength))
        gradient.setColorAt(.86,_shade("#D8FCFF",210*strength))
        gradient.setColorAt(1,_shade(CYAN,0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(gradient)
        p.drawRoundedRect(QRectF(travel-33,yy-1.1,51,2.2),1.1,1.1)
    # Gentle breathing in the corners, not an intrusive global flash.
    pulse=.5+.5*math.sin(2*math.pi*phase)
    p.setBrush(_shade("#96F3FF",(36+54*pulse)*strength))
    p.drawRoundedRect(QRectF(x+8,y+2,14,1.5),.75,.75)
    p.drawRoundedRect(QRectF(x+w-22,y+h-3.5,14,1.5),.75,.75)
    p.restore()
