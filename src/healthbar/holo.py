"""CPU Holographic Details: neon-framed native Qt popup, no external plugin code executed."""
import math
import time
from PySide6.QtCore import Qt, QRect, QRectF, QPoint, QEasingCurve, QPropertyAnimation, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QLinearGradient, QPainterPath, QFont, QKeyEvent
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
                               QGridLayout, QPushButton, QGraphicsOpacityEffect, QSizePolicy)

BLUE = "#007CFF"
CYAN = "#5EEBFF"
INK = "#030B1D"

def readout(number, unit, precision=1):
    if number is None or not isinstance(number, (int, float)) or not math.isfinite(number):
        return "—"
    return f"{number:.{precision}f} {unit}"

class CpuHoloPanel(QWidget):
    """Persistent, screen-bounded CPU hologram; receives readings from the host."""

    closed = Signal()
    pin_changed = Signal(bool)

    def __init__(self, parent=None):
        # A top-level tool window can extend beyond the thin bar's own geometry.
        super().__init__(parent, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint |
                         Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setObjectName("cpuHolo")
        self.setWindowTitle("NovaBar · CPU CORE MATRIX")
        self.setMinimumSize(380, 300)
        self.resize(570, 440)
        self.pinned = False
        self._readings = {}
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._phase = 0
        self.visual_timer = QTimer(self)
        self.visual_timer.setInterval(60)
        self.visual_timer.timeout.connect(self.advance_light)
        self._fade = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._fade)
        self._opacity_anim = QPropertyAnimation(self._fade, b"opacity", self)
        self._opacity_anim.setDuration(210)
        self._opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.setStyleSheet("""
            QLabel {color: #DBEEFF; background: transparent; border: 0;}
            QLabel#holoTitle { color: #91EEFF; font-size: 19px; font-weight: 900; letter-spacing: 2px; }
            QLabel#holoSubtitle {color:#6CBFD9; font-size: 11px;}
            QLabel#holoHeading {color:#5EEBFF; font-size: 11px; font-weight: 700;}
            QLabel#holoValue {color:#EAF7FF; font-size: 13px; font-weight: 700;}
            QLabel#holoFoot {color:#80B2CA; font-size: 10px;}
            QPushButton {background: transparent; color:#9FEAFF; border: 1px solid #1AB8EF;
                         border-radius: 6px; padding: 3px 8px;}
            QPushButton:hover {color:#FFFFFF; border: 1px solid #C8FFFF;}
            QScrollArea {background: transparent; border: 0;}
            QScrollBar:vertical {width:6px;background:#031229;}
            QScrollBar::handle:vertical {background:#129BD8;border-radius:3px;}
        """)
        root = QVBoxLayout(self)
        root.setContentsMargins(27, 24, 27, 24)
        root.setSpacing(11)
        top = QHBoxLayout()
        title = QLabel("◈ CPU CORE MATRIX")
        title.setObjectName("holoTitle")
        top.addWidget(title)
        top.addStretch()
        self.pin_button = QPushButton("◇  ÉPINGLER")
        self.pin_button.setAccessibleName("Épingler ou libérer l'hologramme CPU")
        self.pin_button.setCheckable(True)
        self.pin_button.clicked.connect(self.toggle_pin)
        top.addWidget(self.pin_button)
        close = QPushButton("✕")
        close.setAccessibleName("Fermer les détails CPU")
        close.clicked.connect(self.close_panel)
        top.addWidget(close)
        root.addLayout(top)
        self.cpu_name = QLabel("Processeur · données locales")
        self.cpu_name.setObjectName("holoSubtitle")
        self.cpu_name.setWordWrap(True)
        root.addWidget(self.cpu_name)
        self.summary = QLabel("PACKAGE   TEMP —   •   FRÉQUENCE —   •   CHARGE —   •   PUISSANCE —")
        self.summary.setObjectName("holoHeading")
        self.summary.setWordWrap(True)
        root.addWidget(self.summary)
        self.topology = QLabel("Topology: —")
        self.topology.setObjectName("holoSubtitle")
        root.addWidget(self.topology)
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background: rgba(55,204,255,95);")
        root.addWidget(line)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.grid_widget = QWidget()
        self.grid = QGridLayout(self.grid_widget)
        self.grid.setContentsMargins(1, 6, 1, 6)
        self.grid.setVerticalSpacing(9)
        self.grid.setHorizontalSpacing(12)
        self.scroll.setWidget(self.grid_widget)
        root.addWidget(self.scroll, 1)
        self.note = QLabel("W = puissance instantanée si mesurée • TDP nominal ≠ puissance par cœur.  — = capteur indisponible")
        self.note.setObjectName("holoFoot")
        self.note.setWordWrap(True)
        root.addWidget(self.note)
        self.set_telemetry({})

    def advance_light(self):
        self._phase = (self._phase + 0.018) % 1
        if self.isVisible():
            self.update()

    def toggle_pin(self, pinned):
        self.pinned = pinned
        self.pin_button.setText("◆  ÉPINGLÉ" if pinned else "◇  ÉPINGLER")
        self.pin_changed.emit(pinned)

    def close_panel(self):
        self.visual_timer.stop()
        self.hide()
        self.closed.emit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close_panel()
            event.accept()
            return
        super().keyPressEvent(event)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        if not self.pinned:
            # Close when another app receives focus; a pinned window remains visible.
            QTimer.singleShot(120, self._close_if_inactive)

    def _close_if_inactive(self):
        if self.isVisible() and not self.pinned and not self.isActiveWindow():
            self.close_panel()

    def show_at(self, anchor, screen_rect, position="top"):
        """Place adjacent to clicked slot, keeping all edges on the active display."""
        width = min(max(380, self.width()), max(260, screen_rect.width() - 12))
        height = min(max(290, self.height()), max(220, screen_rect.height() - 12))
        self.resize(width, height)
        if position == "bottom":
            candidate = QRect(anchor.center().x() - width//2, anchor.top() - height - 10, width, height)
        elif position == "left":
            candidate = QRect(anchor.right() + 10, anchor.center().y() - height//2, width, height)
        elif position == "right":
            candidate = QRect(anchor.left() - width - 10, anchor.center().y() - height//2, width, height)
        else:
            candidate = QRect(anchor.center().x() - width//2, anchor.bottom() + 10, width, height)
        candidate.moveLeft(max(screen_rect.left() + 6,
                               min(candidate.left(), screen_rect.right() - width - 5)))
        candidate.moveTop(max(screen_rect.top() + 6,
                              min(candidate.top(), screen_rect.bottom() - height - 5)))
        self.setGeometry(candidate)
        self._fade.setOpacity(0)
        self.show()
        self.raise_()
        self.setFocus()
        self._opacity_anim.stop()
        self._opacity_anim.setStartValue(0.12)
        self._opacity_anim.setEndValue(1.0)
        self._opacity_anim.start()
        self.visual_timer.start()

    def _add_cell(self, value, row, col, header=False):
        label = QLabel(str(value))
        label.setObjectName("holoHeading" if header else "holoValue")
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.grid.addWidget(label, row, col)

    def set_telemetry(self, readings):
        self._readings = readings or {}
        data = self._readings
        self.cpu_name.setText(str(data.get("cpu_model") or "CPU · processeur non identifié"))
        physical = data.get("cpu_physical_cores")
        logical = data.get("cpu_logical_cores")
        self.topology.setText(f"CORES : {physical if physical is not None else '—'}  /  THREADS : {logical if logical is not None else '—'}")
        self.summary.setText(
            f"TEMP {readout(data.get('cpu_temperature_c'), '°C',0)}     "
            f"FREQ {readout(data.get('cpu_frequency_ghz'), 'GHz',2)}     "
            f"LOAD {readout(data.get('cpu_percent'), '%',0)}     "
            f"PACKAGE {readout(data.get('cpu_power_w'), 'W',1)}")
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        for col, heading in enumerate(("CŒUR / THREAD", "FRÉQUENCE", "TEMPÉRATURE", "PUISSANCE")):
            self._add_cell(heading, 0, col, True)
        cores = data.get("cpu_cores") or []
        for index, core in enumerate(cores[:128], 1):
            self._add_cell(core.get("label","Core "+str(index)), index, 0)
            self._add_cell(readout(core.get("frequency_ghz"), "GHz",2), index, 1)
            self._add_cell(readout(core.get("temperature_c"), "°C",0), index, 2)
            self._add_cell(readout(core.get("power_w"), "W",1), index, 3)
        final = len(cores[:128]) + 1
        for col, total in enumerate(("PACKAGE / TOTAL",
                                     readout(data.get("cpu_frequency_ghz"),"GHz",2),
                                     readout(data.get("cpu_temperature_c"),"°C",0),
                                     readout(data.get("cpu_power_w"),"W",1))):
            self._add_cell(total, final, col, True)
        self.note.setText("FRÉQUENCE PACKAGE = moyenne/lecture OS, non somme des GHz.  "
                          "TDP nominal ≠ puissance instantanée par cœur.  — = indisponible.")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(12,12,-12,-12)
        path = QPainterPath()
        cut = 16
        path.moveTo(rect.left()+cut,rect.top())
        path.lineTo(rect.right()-cut,rect.top())
        path.lineTo(rect.right(),rect.top()+cut)
        path.lineTo(rect.right(),rect.bottom()-cut)
        path.lineTo(rect.right()-cut,rect.bottom())
        path.lineTo(rect.left()+cut,rect.bottom())
        path.lineTo(rect.left(),rect.bottom()-cut)
        path.lineTo(rect.left(),rect.top()+cut)
        path.closeSubpath()
        painter.fillPath(path,QColor(2,9,26,230))
        glass = QLinearGradient(rect.topLeft(), rect.bottomRight())
        glass.setColorAt(0,QColor(0,150,255,45))
        glass.setColorAt(0.5,QColor(0,24,73,20))
        glass.setColorAt(1,QColor(76,210,255,13))
        painter.fillPath(path,glass)
        # Glass reflection in the upper rim; luminous details follow the same
        # electric-cyan language as NovaBar slim, with no opaque outer backdrop.
        gloss=QLinearGradient(rect.left(),rect.top(),rect.left(),rect.top()+75)
        gloss.setColorAt(0,QColor(187,247,255,63))
        gloss.setColorAt(.25,QColor(25,146,230,24))
        gloss.setColorAt(1,QColor(5,24,46,0))
        painter.fillPath(path,gloss)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for width,rgba in ((21,(0,64,255,12)),(13,(0,145,255,34)),(7,(0,194,255,58)),
                           (3,(2,120,255,190)),(1.2,(129,241,255,245))):
            painter.setPen(QPen(QColor(*rgba),width))
            painter.drawPath(path)
        # Segmented circuit traces and travelling electric node, independent of text.
        track = QRectF(rect.left()+9,rect.top()+9,rect.width()-18,rect.height()-18)
        painter.setPen(QPen(QColor(0,168,255,115),1))
        painter.drawLine(track.left()+30,track.top(),track.right()-60,track.top())
        painter.drawLine(track.left(),track.bottom()-26,track.left(),track.top()+50)
        pos = track.left()+30+((track.width()-90)*self._phase)
        painter.setPen(QPen(QColor(170,255,255,225),2))
        painter.drawLine(QPoint(int(pos-16),int(track.top())),QPoint(int(pos+16),int(track.top())))
        painter.end()
