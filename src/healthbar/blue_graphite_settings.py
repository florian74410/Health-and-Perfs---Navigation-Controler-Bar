"""Blue Graphite settings skin with RedBlack's cut-chrome geometry.

Only decorates the existing SettingsDialog. Real Qt controls, forms, page
signals, save/apply actions and the desktop remain owned by their original code.
"""
from __future__ import annotations
import re
from functools import lru_cache
from PySide6.QtCore import QRectF, QPointF, Qt
from PySide6.QtGui import QColor, QPainterPath, QPen, QLinearGradient

BLUE = "#168CFF"
ELECTRIC = "#31DFFF"
ICE = "#DFF9FF"
GRAPHITE = "#0A1019"

def enabled(theme):
    return theme in ("blue-neon", "cyber-futuriste")

def _rgba(value, alpha):
    c=QColor(value)
    c.setAlpha(max(0,min(255,round(alpha))))
    return c

def _chamfer(r, cut=20):
    x,y,w,h=r.x(),r.y(),r.width(),r.height()
    c=min(cut,h*.27,w*.16)
    path=QPainterPath(QPointF(x+c,y))
    if w>=260:
        for px,py in ((x+w*.38,y),(x+w*.40,y+6),
                      (x+w*.59,y+6),(x+w*.61,y)):
            path.lineTo(px,py)
    for px,py in ((x+w-c,y),(x+w,y+c),(x+w,y+h-c),(x+w-c,y+h),
                  (x+c,y+h),(x,y+h-c),(x,y+c)):
        path.lineTo(px,py)
    path.closeSubpath()
    return path

def _trace(p,coords,alpha=120,width=.9):
    path=QPainterPath(QPointF(*coords[0]))
    for q in coords[1:]:
        path.lineTo(QPointF(*q))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QPen(_rgba(ELECTRIC,alpha),width))
    p.drawPath(path)
    tip=QPointF(*coords[-1])
    p.setBrush(_rgba(BLUE,180))
    p.drawEllipse(tip,2.1,2.1)

def paint_settings(painter,rect,phase=0.0):
    """DarkRed mechanical layout, reworked in graphite/electric-blue materials."""
    r=QRectF(rect)
    if r.width()<110 or r.height()<110:
        return
    p=painter
    p.save()
    p.setRenderHint(p.RenderHint.Antialiasing,True)
    outer=_chamfer(r)
    shell=QLinearGradient(0,r.top(),0,r.bottom())
    for position,shade in ((0,"#394754"),(.055,"#14202C"),(.17,"#08111B"),
                           (.77,"#080F17"),(.94,"#162B3A"),(1,"#354553")):
        shell.setColorAt(position,QColor(shade))
    p.fillPath(outer,shell)
    p.setClipPath(outer)
    inset=r.adjusted(5,5,-5,-5)
    cavity=_chamfer(inset,16)
    p.fillPath(cavity,_rgba(GRAPHITE,238))
    # Very small graphite/carbon finish: inside rim only, away from text.
    p.fillRect(QRectF(r.left()+29,r.top()+6,max(0,r.width()-58),3),
               _rgba("#25303A",120))
    p.fillRect(QRectF(r.left()+29,r.bottom()-9,max(0,r.width()-58),3),
               _rgba("#202A34",100))
    shine=QLinearGradient(0,r.top()+8,0,r.top()+86)
    shine.setColorAt(0,_rgba("#A1E4FF",49))
    shine.setColorAt(.38,_rgba("#247BBA",27))
    shine.setColorAt(1,_rgba("#061521",0))
    p.fillRect(QRectF(r.left()+11,r.top()+8,r.width()-22,78),shine)
    x,y,w,h=r.x(),r.y(),r.width(),r.height()
    # PCB paths in the edge rails: no faked sensor values, no controls covered.
    tracks=(
        ((x+8,y+54),(x+20,y+54),(x+35,y+39),(x+72,y+39)),
        ((x+w-8,y+55),(x+w-21,y+55),(x+w-36,y+40),(x+w-74,y+40)),
        ((x+8,y+h-44),(x+22,y+h-44),(x+37,y+h-29),(x+80,y+h-29)),
        ((x+w-9,y+h-43),(x+w-24,y+h-43),(x+w-39,y+h-28),(x+w-80,y+h-28))
    )
    for i,coords in enumerate(tracks):
        _trace(p,coords,alpha=105+i*15)
    # Traveling electric current restricted to the metal upper rail.
    phase=float(phase)%1
    px=x+30+(w-60)*phase
    pulse=QLinearGradient(px-35,y+8,px+20,y+8)
    pulse.setColorAt(0,_rgba(BLUE,0))
    pulse.setColorAt(.45,_rgba(BLUE,70))
    pulse.setColorAt(.81,_rgba(ICE,200))
    pulse.setColorAt(1,_rgba(ELECTRIC,0))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(pulse)
    p.drawRoundedRect(QRectF(px-35,y+5,55,2.5),1,1)
    p.setClipping(False)
    p.setBrush(Qt.BrushStyle.NoBrush)
    for thickness,alpha,shade in ((9,14,BLUE),(4,58,BLUE),
                                   (1.5,205,ELECTRIC),(.6,210,ICE)):
        p.setPen(QPen(_rgba(shade,alpha),thickness))
        p.drawPath(outer)
    p.setPen(QPen(_rgba("#508BA8",120),.7))
    p.drawPath(cavity)
    p.restore()

# Reuse all of RedBlack's actual Qt widget selectors and sizing, rather than
# inventing replacement controls. Re-map EVERY stylistic red/pink into blue.
@lru_cache(maxsize=1)
def control_stylesheet():
    from .redblack_shell import control_stylesheet as darkred_css
    source=darkred_css()
    def recolor(m):
        c=QColor(m.group(0))
        h,s,v,a=c.getHsvF()
        # Whites and neutral graphite remain neutral, pink surfaces become
        # dark slate blue. Saturated reds become electric blue/cyan.
        if s<.12:
            return c.name().upper()
        if v<.40:
            target=QColor("#10273D")
            target.setHsvF(.59,min(.85,max(.29,s)),v,a)
        elif v<.72:
            target=QColor("#167FCC")
            target.setHsvF(.58,min(.90,max(.42,s)),v,a)
        else:
            target=QColor("#2CCFFF")
            target.setHsvF(.53,min(.83,max(.36,s)),v,a)
        return target.name().upper()
    css=re.sub(r"#[0-9A-Fa-f]{6}\b",recolor,source)
    # RedBlack's opaque dialog surfaces remain dark; use translucent slate
    # interiors while retaining the sharp cut perimeter and contrast.
    css += """
    QDialog#novaSettings {background:transparent;color:#E7F7FF;}
    QWidget#generalContent,QWidget#settingsPages {
       background:rgba(6,17,29,226);border:1px solid #1769A8;}
    QListWidget#settingsNavigation {
       background:rgba(5,14,25,236);border:1px solid #1672B3;}
    QToolTip {background:#0B1D2F;color:#F2FBFF;border:1px solid #2DCEFF;}
    """
    return css

class BlueGraphiteNotice:
    """Factory for native transparent non-modal Turbo notifications.

    The widget is deliberately created lazily to avoid Qt app creation at import.
    """
    @staticmethod
    def create(title,message,parent=None,success=True):
        from PySide6.QtCore import QTimer
        from PySide6.QtGui import QPainter
        from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
        class Notice(QDialog):
            def __init__(self):
                super().__init__(parent)
                self.setWindowFlags(Qt.WindowType.Tool |
                                    Qt.WindowType.FramelessWindowHint |
                                    Qt.WindowType.WindowStaysOnTopHint)
                self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground,True)
                self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
                self.setFixedSize(440,148)
                self._phase=0.0
                self._timer=QTimer(self)
                self._timer.setInterval(85)
                self._timer.timeout.connect(self.advance)
                layout=QVBoxLayout(self)
                layout.setContentsMargins(29,25,29,22)
                top=QHBoxLayout()
                label=QLabel(("◈ " if success else "⚠ ")+str(title))
                label.setStyleSheet("color:#43DEFF;font-size:15px;"
                                    "font-weight:900;background:transparent;")
                top.addWidget(label,1)
                close=QPushButton("✕")
                close.setFixedSize(29,27)
                close.setStyleSheet("QPushButton {background:#10273B;"
                                    "color:#F0FBFF;border:1px solid #27BFFF;}"
                                    "QPushButton:hover {background:#185681;}")
                close.clicked.connect(self.close)
                top.addWidget(close)
                layout.addLayout(top)
                text=QLabel(str(message))
                text.setWordWrap(True)
                text.setStyleSheet("color:#E1F4FF;font-size:12px;"
                                   "background:transparent;")
                layout.addWidget(text,1)
                QTimer.singleShot(6000,self.close)
            def advance(self):
                if self.isVisible():
                    self._phase=(self._phase+.008)%1
                    self.update()
                else:
                    self._timer.stop()
            def showEvent(self,event):
                super().showEvent(event)
                self._timer.start()
            def hideEvent(self,event):
                self._timer.stop()
                super().hideEvent(event)
            def paintEvent(self,event):
                p=QPainter(self)
                p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
                p.fillRect(self.rect(),Qt.GlobalColor.transparent)
                p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
                paint_settings(p,QRectF(self.rect()).adjusted(4,4,-4,-4),self._phase)
                p.end()
        return Notice()
