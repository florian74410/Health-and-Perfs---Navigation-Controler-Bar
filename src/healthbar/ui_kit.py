"""Shared Holo palette, PCB routing and NovaBar chip identity."""
import re
from PySide6.QtGui import QColor as QtColor, QPainterPath, QPen
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter

THEMES = {"blue-neon": "Blue Neon", "green-matrix": "Green Matrix", "red-blood": "Red Blood"}
_active = "blue-neon"

def set_theme(theme):
    global _active
    _active = theme if theme in THEMES else "blue-neon"

def QColor(*args):
    """Retint decorative blue/cyan; preserve semantic warning colors."""
    color = QtColor(*args)
    h, saturation, value, alpha = color.getHsvF()
    if _active != "blue-neon" and .46 <= h <= .70 and saturation > .12:
        color.setHsvF(.37 if _active == "green-matrix" else .98, saturation, value, alpha)
    return color

def holo_background():
    """Uniform theme-tinted glass: 85% opaque, 15% desktop visible."""
    color = QColor('#061224')
    color.setAlpha(217)
    return color


def stylesheet(text):
    # Theme controls frames and surfaces; information keeps its own readable palette.
    def retint(match):
        prefix=text[max(0,match.start()-40):match.start()]
        if re.search(r"(?<![-\w])color\s*:\s*$",prefix):
            return match[0]
        return QColor(match[0]).name()
    result=re.sub(r"#[0-9a-fA-F]{6}\b",retint,text)
    # Titles are the only text role inheriting the decorative accent.
    return re.sub(r"(QLabel#holoTitle\s*\{[^}]*?\bcolor\s*:\s*)(#[0-9a-fA-F]{6})",
                  lambda m:m[1]+QColor(m[2]).name(),result)


def pcb(p, bounds):
    """Routes reach both endpoints of the full window, including the action area."""
    w, h = bounds.width(), bounds.height()
    p.save()
    for i in range(6):
        y = 2 + i * 3
        path = QPainterPath(QPointF(0, y))
        x = 0
        while x < w:
            path.lineTo(min(x+38,w),y)
            path.lineTo(min(x+48,w),y+6)
            path.lineTo(min(x+76,w),y+6)
            path.lineTo(min(x+86,w),y)
            x += 130
        path.lineTo(w,y)
        for width, alpha in ((5,22),(2,90),(.7,210)):
            color=QColor("#25cfff");color.setAlpha(alpha)
            p.setPen(QPen(color,width));p.drawPath(path)
        p.translate(0,h-2*y)
        p.drawPath(path)
        p.translate(0,-(h-2*y))
    p.restore()

def chip(p, rect):
    p.save();p.translate(rect.center());scale=min(rect.width(),rect.height())/64;p.scale(scale,scale)
    p.setPen(QPen(QColor("#34dfff"),1.4))
    for side in range(4):
        for x in (-12,-4,4,12):
            p.drawLine(QPointF(x,-18),QPointF(x,-27))
        p.rotate(90)
    p.setBrush(QColor("#061224"));p.drawRoundedRect(QRectF(-18,-18,36,36),4,4)
    p.drawRect(QRectF(-11,-11,22,22));p.drawText(QRectF(-11,-11,22,22),0x84,"N")
    p.restore()

class ChipLogo(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent);self.setMinimumHeight(0);self.setToolTip("NovaBar · La Puce")
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);chip(p,QRectF(self.rect()));p.end()
