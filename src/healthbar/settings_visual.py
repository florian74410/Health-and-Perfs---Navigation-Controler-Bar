"""Painted lightweight Cyber-Neon settings shell; no texture assets, web API or timer."""
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QDialog, QWidget
from .xfce_panel_skin import PALETTES
from .theme_overrides import load as load_theme_overrides


def _palette(theme):
    preset=PALETTES.get(theme, PALETTES["blue-neon"])
    custom=load_theme_overrides().get(theme,{})
    return (custom.get("primary",preset[0]),custom.get("secondary",preset[1]),
            custom.get("background","#041426"))


def settings_stylesheet(theme):
    primary,secondary,_=_palette(theme)
    return """
    QDialog#novaSettings { background: transparent; color: #EAF6FF; }
    QLabel { color:#D7EDFF; background:transparent; font-size:13px; }
    QLabel#title { color:%s; font-size:27px; font-weight:700; }
    QLabel#sectionHeader { color:%s; font-size:16px; font-weight:700; padding:12px 5px 7px; }
    QWidget#generalContent, QWidget#settingsPages {
        background:rgba(2,14,32,175);border:1px solid %s;border-radius:13px;
    }
    QTabWidget, QTabWidget::pane, QTabWidget QWidget, QScrollArea, QScrollArea QWidget,
    QScrollArea::viewport { background: transparent; border: none; }
    QListWidget#settingsNavigation {
        color:#DDF2FF;background:rgba(2,16,37,215);
        border:1px solid %s;border-radius:12px;padding:12px;outline:0px;
    }
    QListWidget#settingsNavigation::item { height:33px; padding:7px 9px; border-radius:6px; }
    QListWidget#settingsNavigation::item:selected {
        background:rgba(4,95,151,190);border:1px solid %s;color:#FFFFFF;
    }
    QListWidget#settingsNavigation::item:hover {
        background:rgba(0,112,170,95);
    }
    QLineEdit, QComboBox, QSpinBox {
        color:#EDF8FF;background:rgba(5,32,59,232);
        border:1px solid %s;border-radius:7px;padding:8px 10px;min-height:23px;
    }
    QComboBox QAbstractItemView {
        background:#061B33;color:#E7F6FF;border:1px solid %s;
        selection-background-color:#124B7B;selection-color:#FFFFFF;
    }
    QPushButton {
        color:#E6F7FF;background:rgba(5,40,74,210);
        border:1px solid %s;border-radius:8px;padding:9px 13px;min-height:20px;
    }
    QPushButton:hover {
        color:#FFFFFF;border:1px solid %s;background:rgba(9,85,126,230);
    }
    QPushButton:pressed { background:rgba(9,112,155,230); }
    QPushButton:disabled { color:#60768B;background:rgba(3,21,40,175);border-color:#21425B; }
    QCheckBox { color:#D9F3FF;spacing:10px;background:transparent; }
    QCheckBox::indicator {width:17px;height:17px;border:1px solid %s;border-radius:5px;
        background:rgba(1,23,43,240);}
    QCheckBox::indicator:checked {background:%s;border-color:%s;}
    QSlider::groove:horizontal {height:5px;background:#14446A;border-radius:2px;}
    QSlider::handle:horizontal {width:15px;margin:-6px 0;background:%s;border-radius:7px;}
    QScrollBar:vertical {width:9px;background:rgba(2,18,38,180);border:0;}
    QScrollBar::handle:vertical {background:#14648C;border-radius:4px;min-height:30px;}
    QScrollBar:horizontal {height:8px;background:rgba(2,18,38,160);}
    QScrollBar::handle:horizontal {background:#14648C;border-radius:4px;}
    QDialogButtonBox {background:transparent;}
    """ % (primary,primary,secondary,secondary,primary,secondary,secondary,
            secondary,secondary,primary,secondary,primary,primary)


class PCBSettingsDialog(QDialog):
    """One translucent glass paint pass; trace geometry recalculated only on repaint."""
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setObjectName("novaSettings")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground,True)
        self._pcb_theme="blue-neon"

    def use_pcb_theme(self,theme):
        self._pcb_theme=theme
        self.setStyleSheet(settings_stylesheet(theme))
        self.update()

    def paintEvent(self,event):
        painter=QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing,True)
        rect=QRectF(self.rect()).adjusted(7,7,-7,-7)
        if rect.width()<110 or rect.height()<110:return
        path=QPainterPath()
        cut=22
        path.moveTo(rect.left()+cut,rect.top())
        for x,y in ((rect.right()-cut,rect.top()),(rect.right(),rect.top()+cut),
                    (rect.right(),rect.bottom()-cut),(rect.right()-cut,rect.bottom()),
                    (rect.left()+cut,rect.bottom()),(rect.left(),rect.bottom()-cut),
                    (rect.left(),rect.top()+cut)):
            path.lineTo(x,y)
        path.closeSubpath()
        primary,secondary,background=_palette(self._pcb_theme)
        glass=QColor(background);glass.setAlpha(236)
        painter.fillPath(path,glass)
        painter.setClipPath(path)
        # Trace pattern is deliberately static. It never consumes a frame timer.
        painter.setPen(QPen(QColor(primary),1.15))
        w=rect.width();h=rect.height()
        for i in range(13):
            x=rect.left()+25+i*max(44,w/13)
            y=rect.top()+30+(i%4)*27
            trace=QPainterPath(QPointF(x,rect.top()+2))
            trace.lineTo(x,y)
            trace.lineTo(x+16,y+16)
            trace.lineTo(min(rect.right()-15,x+min(170,w*.16)),y+16)
            painter.drawPath(trace)
            painter.setBrush(QColor(primary))
            painter.drawEllipse(QPointF(min(rect.right()-15,x+min(170,w*.16)),y+16),2.3,2.3)
            painter.setBrush(Qt.BrushStyle.NoBrush)
        for i in range(7):
            x=rect.left()+30+i*max(70,w/7)
            y=rect.bottom()-25-(i%3)*22
            trace=QPainterPath(QPointF(x,rect.bottom()))
            trace.lineTo(x,y+10)
            trace.lineTo(x+11,y)
            trace.lineTo(min(rect.right()-20,x+95),y)
            painter.drawPath(trace)
        painter.setClipping(False)
        for width,opacity in ((9,22),(4,64),(1.4,230)):
            color=QColor(primary);color.setAlpha(opacity)
            painter.setPen(QPen(color,width))
            painter.drawPath(path)
        painter.end()


class BarPreview(QWidget):
    """Static mini-preview. No timer, no sensors and no GPU-heavy effects."""
    def __init__(self,theme="blue-neon",parent=None):
        super().__init__(parent)
        self._theme=theme
        self.setMinimumHeight(138)
        self.setMinimumWidth(310)

    def change_theme(self,theme):
        self._theme=theme
        self.update()

    def paintEvent(self,event):
        p=QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing,True)
        primary,secondary,_=_palette(self._theme)
        rect=QRectF(self.rect()).adjusted(4,4,-4,-4)
        p.setPen(QPen(QColor(primary),1.2))
        p.setBrush(QColor(2,17,36,210))
        p.drawRoundedRect(rect,11,11)
        p.setPen(QPen(QColor(215,239,255),1))
        font=p.font();font.setPixelSize(12);font.setBold(True);p.setFont(font)
        p.drawText(QRectF(18,10,rect.width()-25,27),"APERÇU  /  TOP HUD + NAVIGATION")
        for i,y in enumerate((46,91)):
            box=QRectF(18,y,rect.width()-37,33)
            p.setBrush(QColor(4,34,60,220))
            p.setPen(QPen(QColor(secondary),1))
            p.drawRoundedRect(box,8,8)
            p.setPen(QPen(QColor(primary),1.1))
            if i==0:
                p.drawText(box.adjusted(12,0,-8,0),"◈ CPU   12 %     RAM  23 %      NORMAL MODE")
            else:
                p.drawText(box.adjusted(12,0,-8,0),"⌂ Accueil     ▦ Apps     ⚙ Réglages     +2")
        p.end()
