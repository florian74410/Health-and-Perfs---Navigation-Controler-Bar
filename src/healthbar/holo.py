"""CPU Holographic Details: neon-framed native Qt popup, no external plugin code executed."""
import math
import time
from PySide6.QtCore import Qt, QRect, QRectF, QPoint, QEasingCurve, QPropertyAnimation, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QLinearGradient, QPainterPath, QFont, QKeyEvent, QTextLayout, QTextOption, QPalette
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
                               QGridLayout, QPushButton, QGraphicsOpacityEffect, QSizePolicy, QStyleOptionButton, QStyle)

from .ui_kit import QColor

BLUE = "#007CFF"
CYAN = "#5EEBFF"
INK = "#030B1D"

def readout(number, unit, precision=1):
    if number is None or not isinstance(number, (int, float)) or not math.isfinite(number):
        return "—"
    return f"{number:.{precision}f} {unit}"


def outlined_text(painter, point, font, text, color):
    path = QPainterPath(); path.addText(point, font, text)
    # A dark, opaque glyph outline works on white and on dark desktop content.
    painter.setPen(QPen(QColor("#010813"), 3, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.setBrush(color); painter.drawPath(path)
    painter.setPen(Qt.PenStyle.NoPen); painter.drawPath(path)


class HoloLabel(QLabel):
    def paintEvent(self, event):
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.contentsRect().adjusted(2, 0, -2, 0)
        layout = QTextLayout(self.text(), self.font())
        option = QTextOption()
        option.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere if self.wordWrap() else QTextOption.WrapMode.NoWrap)
        layout.setTextOption(option); layout.beginLayout(); lines = []
        while True:
            line = layout.createLine()
            if not line.isValid(): break
            line.setLineWidth(max(1, rect.width())); lines.append(line)
        layout.endLayout()
        height = sum(line.height() for line in lines)
        y = rect.top() + (max(0, (rect.height()-height)/2) if self.alignment() & Qt.AlignmentFlag.AlignVCenter else 0)
        for line in lines:
            value = self.text()[line.textStart():line.textStart()+line.textLength()]
            outlined_text(painter, QPoint(rect.left(), round(y+line.ascent())), self.font(), value,
                          self.palette().color(QPalette.ColorRole.WindowText))
            y += line.height()
        painter.end()


class HoloButton(QPushButton):
    def paintEvent(self, event):
        option = QStyleOptionButton(); self.initStyleOption(option)
        value = option.text; option.text = ""
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.style().drawControl(QStyle.ControlElement.CE_PushButton, option, painter, self)
        metrics = self.fontMetrics()
        outlined_text(painter, QPoint(round((self.width()-metrics.horizontalAdvance(value))/2),
                                      round((self.height()-metrics.height())/2+metrics.ascent())),
                      self.font(), value, self.palette().color(QPalette.ColorRole.ButtonText))
        painter.end()

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
        self.setMinimumSize(320, 240)
        self.resize(460, 330)
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
        from .ui_kit import stylesheet
        self.base_style = """
            QLabel {color: #DBEEFF; background: transparent; border: 0;}
            QLabel#holoTitle { color: #91EEFF; font-size: 14px; font-weight: 900; letter-spacing: 2px; }
            QLabel#holoSubtitle {color:#6CBFD9; font-size: 12px;}
            QLabel#holoHeading {color:#5EEBFF; font-size: 12px; font-weight: 700;}
            QLabel#holoValue {color:#EAF7FF; font-size: 12px; font-weight: 700;}
            QLabel#holoFoot {color:#80B2CA; font-size: 11px;}
            QPushButton {background: transparent; color:#9FEAFF; border: 1px solid #1AB8EF;
                         border-radius: 6px; padding: 3px 8px;}
            QPushButton:hover {color:#FFFFFF; border: 1px solid #C8FFFF;}
            QWidget#cpuHolo, QScrollArea, QScrollArea QWidget {background: transparent; border: 0;}
            QScrollBar:vertical {width:6px;background:transparent;}
            QScrollBar::handle:vertical {background:#129BD8;border-radius:3px;}
        """
        self.setStyleSheet(stylesheet(self.base_style))
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(6)
        top = QHBoxLayout()
        title = HoloLabel("◈ CPU CORE MATRIX")
        title.setObjectName("holoTitle")
        top.addWidget(title)
        top.addStretch()
        self.pin_button = HoloButton("◇  ÉPINGLER")
        self.pin_button.setAccessibleName("Épingler ou libérer l'hologramme CPU")
        self.pin_button.setCheckable(True)
        self.pin_button.clicked.connect(self.toggle_pin)
        top.addWidget(self.pin_button)
        close = HoloButton("✕")
        close.setAccessibleName("Fermer les détails CPU")
        close.clicked.connect(self.close_panel)
        top.addWidget(close)
        root.addLayout(top)
        self.cpu_name = HoloLabel("Processeur · données locales")
        self.cpu_name.setObjectName("holoSubtitle")
        self.cpu_name.setWordWrap(True)
        root.addWidget(self.cpu_name)
        self.summary = HoloLabel("PACKAGE   TEMP —   •   FRÉQUENCE —   •   CHARGE —   •   PUISSANCE —")
        self.summary.setObjectName("holoHeading")
        self.summary.setWordWrap(True)
        root.addWidget(self.summary)
        self.topology = HoloLabel("Topology: —")
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
        self.grid.setVerticalSpacing(5)
        self.grid.setHorizontalSpacing(8)
        self.scroll.setWidget(self.grid_widget)
        self.scroll.viewport().setAutoFillBackground(False)
        self.grid_widget.setAutoFillBackground(False)
        self.grid_widget.setStyleSheet("background: transparent;")
        root.addWidget(self.scroll, 1)
        self.note = HoloLabel("W = puissance instantanée si mesurée • TDP nominal ≠ puissance par cœur.  — = capteur indisponible")
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
        width = min(max(320, self.width()), max(260, screen_rect.width() - 12))
        height = min(max(240, self.height()), max(220, screen_rect.height() - 12))
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
        label = HoloLabel(str(value))
        label.setObjectName("holoHeading" if header else "holoValue")
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        label.setContentsMargins(2, 1, 2, 1)
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
        # The desktop remains visible through every Holo surface.
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


class SensorHoloPanel(CpuHoloPanel):
    """Host-rendered detail view for sensor plugins; no plugin code execution."""
    FIELDS = {
        "gpu": (("gpu_percent", "%"), ("gpu_temperature_c", "°C"), ("gpu_clock_mhz", "MHz"), ("vram_used_gb", "GB"), ("gpu_power_w", "W")),
        "ram": (("ram_percent", "%"), ("ram_used_gb", "GB"), ("ram_available_gb", "GB")),
        "storage": (("disk_used_gb", "GB"), ("disk_free_gb", "GB"), ("disk_read_mbs", "MB/s"), ("disk_write_mbs", "MB/s")),
        "network": (("net_down_mbs", "MB/s"), ("net_up_mbs", "MB/s")),
        "fans": (),
    }
    def __init__(self, slot, parent=None):
        self.slot = slot; super().__init__(parent)
        self.findChild(QLabel, "holoTitle").setText("◈ " + slot.upper() + " HOLO")
        self.cpu_name.setText("Capteurs locaux · " + slot.upper())
        self.topology.hide()
        self.resize(380, 280)
        if slot == 'network':
            from .network_chart import NetworkChart
            self.chart = NetworkChart(self)
            self.layout().insertWidget(5, self.chart)
            self.resize(460, 360)
        self.note.setText("— = capteur indisponible · données système locales")
        self.setWindowTitle("NovaBar · " + slot.upper())
    def record_sample(self, data):
        if hasattr(self, 'chart'):
            self.chart.record(data)

    def set_telemetry(self, data):
        self.record_sample(data or {})
        from .network_detail import format_rate, format_ping
        data = data or {}
        self._readings = data
        labels = {"gpu_percent":"Charge GPU", "gpu_temperature_c":"Température GPU",
                  "gpu_clock_mhz":"Fréquence GPU", "vram_used_gb":"VRAM utilisée", "gpu_power_w":"Puissance GPU",
                  "ram_percent":"Charge mémoire", "ram_used_gb":"RAM utilisée", "ram_available_gb":"RAM disponible",
                  "disk_used_gb":"Stockage utilisé", "disk_free_gb":"Stockage libre", "disk_read_mbs":"Lecture disque",
                  "disk_write_mbs":"Écriture disque", "net_down_mbs":"Réception réseau", "net_up_mbs":"Envoi réseau"}
        rows = [(labels[key], readout(data.get(key), unit))
                for key, unit in self.FIELDS[self.slot]]
        totals = {"gpu": ("vram_total_gb", "VRAM totale"),
                  "ram": ("ram_total_gb", "RAM totale"),
                  "storage": ("disk_total_gb", "Capacité volume système")}
        if self.slot in totals:
            key, label = totals[self.slot]
            rows.append((label, readout(data.get(key), "GB")))
        if self.slot == "network":
            self.cpu_name.setText('INTERFACE : ' + (data.get('net_interface') or 'en détection'))
            rows = [("Réception", format_rate(data.get('net_down_mbs'))),
                    ("Envoi", format_rate(data.get('net_up_mbs'))),
                    ("Ping · " + data.get('net_ping_target', '1.1.1.1'), format_ping(data)),
                    ("État ICMP", data.get('net_ping_status', 'En attente'))]
            for interface in data.get("net_interfaces", []):
                name = interface.get("name", "Interface")
                rows.extend([(name, "CONNECTÉE" if interface.get("isup") else "DÉCONNECTÉE" if interface.get("isup") is False else "ÉTAT INCONNU"),
                             ("  Vitesse lien", readout(interface.get("speed_mbps"), "Mbit/s", 0)),
                             ("  Réception", format_rate(interface.get("down_mbs"))),
                             ("  Envoi", format_rate(interface.get("up_mbs")))])
        if self.slot == "fans":
            rows = [(str(f.get("name", "Fan")), readout(f.get("rpm"), "RPM", 0))
                    for f in data.get("fans", [])] or [("Ventilateurs", "—")]
        while self.grid.count():
            widget = self.grid.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        for index, (label, value) in enumerate(rows):
            self._add_cell(label, index, 0, True)
            self._add_cell(value, index, 1)
        self.summary.setText("MESURES EN DIRECT · " + self.slot.upper())
        self.note.setText("— = capteur indisponible · données système locales" +
                          (" · Ping ICMP toutes les 10 s ; absence de réponse ≠ coupure Internet" if self.slot == "network" else
                           " · I/O : tous disques ; capacité : volume système" if self.slot == "storage" else ""))
