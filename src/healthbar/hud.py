"""Resolution-independent HUD artwork. Read-only live hardware readings (missing means unavailable)."""
import math
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

CYAN = "#00d9ff"
BLUE = "#1860ff"
WHITE = "#e7f3ff"


def line(p, points, color=CYAN, width=1):
    path = QPainterPath(QPointF(*points[0]))
    for xy in points[1:]:
        path.lineTo(*xy)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QPen(QColor(color), width))
    p.drawPath(path)


def text(p, x, y, value, size=18, color=WHITE, bold=True):
    font = QFont("DejaVu Sans", size)
    font.setPixelSize(size)
    font.setBold(bold)
    p.setFont(font)
    p.setPen(QColor(color))
    p.drawText(QPointF(x, y), value)


def outline(p, path, fill=None):
    p.setBrush(QColor(fill) if fill else Qt.BrushStyle.NoBrush)
    for width, alpha in ((10, 13), (5, 30), (2, 150), (0.8, 255)):
        color = QColor(CYAN)
        color.setAlpha(alpha)
        p.setPen(QPen(color, width))
        p.drawPath(path)
        p.setBrush(Qt.BrushStyle.NoBrush)


def module_background(opacity):
    color = QColor("#061020")
    color.setAlpha(round(255*opacity/100))
    return color


def panel(p, x, w, background):
    path = QPainterPath()
    path.addPolygon(QPolygonF([QPointF(x+20, 27), QPointF(x+65, 27),
        QPointF(x+76, 18), QPointF(x+w-26, 18), QPointF(x+w-8, 35),
        QPointF(x+w-8, 162), QPointF(x+w-28, 183), QPointF(x+24, 183),
        QPointF(x+8, 166), QPointF(x+8, 45)]))
    path.closeSubpath()
    outline(p, path, background)
    line(p, [(x+21, 38), (x+35, 27), (x+58, 27)], BLUE, 2)
    line(p, [(x+25, 174), (x+55, 174), (x+63, 182), (x+w-28, 182)], BLUE, 2)
    for i in range(3):
        line(p, [(x+w-19, 61+i*12), (x+w-13, 65+i*12), (x+w-13, 70+i*12)], "#155ba2")


def icon(p, kind, x, y, size=36):
    p.save()
    p.translate(x, y)
    p.scale(size/40, size/40)
    p.setPen(QPen(QColor(CYAN), 1.8))
    p.setBrush(Qt.BrushStyle.NoBrush)
    if kind in ("cpu", "gpu"):
        p.drawRoundedRect(QRectF(5, 6, 30, 28), 3, 3)
        p.drawRect(QRectF(11, 12, 18, 16))
        for i in range(6):
            k = 8+i*5
            p.drawLine(QPointF(k, 1), QPointF(k, 6))
            p.drawLine(QPointF(k, 34), QPointF(k, 39))
            p.drawLine(QPointF(0, k), QPointF(5, k))
            p.drawLine(QPointF(35, k), QPointF(40, k))
        if kind == "gpu":
            p.drawEllipse(QRectF(13, 14, 14, 12))
            p.drawLine(QPointF(14, 16), QPointF(26, 24))
            p.drawLine(QPointF(26, 16), QPointF(14, 24))
        else:
            text(p, 16, 25, "3", 14, CYAN)
    elif kind in ("ram", "storage"):
        p.drawRoundedRect(QRectF(7, 1, 26, 38), 3, 3)
        for i in range(3):
            p.drawRect(QRectF(12, 6+i*9, 9, 5))
        for i in range(5):
            p.drawLine(QPointF(27, 6+i*6), QPointF(31, 6+i*6))
    elif kind == "fans":
        p.drawEllipse(QRectF(17, 17, 6, 6))
        for i in range(4):
            p.save()
            p.translate(20, 20)
            p.rotate(i*90)
            blade = QPainterPath(QPointF(0, -3))
            blade.cubicTo(-19, -25, 14, -25, 5, -3)
            p.drawPath(blade)
            p.restore()
    elif kind == "network":
        p.drawEllipse(QRectF(2, 2, 36, 36))
        p.drawEllipse(QRectF(12, 2, 16, 36))
        p.drawLine(QPointF(2, 20), QPointF(38, 20))
        p.drawLine(QPointF(7, 10), QPointF(33, 10))
        p.drawLine(QPointF(7, 30), QPointF(33, 30))
    p.restore()


def meter(p, x, y, w, ratio):
    p.setPen(QPen(QColor("#0685ff"), 1))
    p.setBrush(QColor("#031529"))
    p.drawRoundedRect(QRectF(x, y, w, 15), 7, 7)
    grad = QLinearGradient(x, y, x+w*ratio, y)
    grad.setColorAt(0, QColor("#00a3ff"))
    grad.setColorAt(1, QColor("#61f6ff"))
    p.setBrush(grad)
    p.drawRoundedRect(QRectF(x+2, y+2, max(2, (w-4)*ratio), 11), 5, 5)
    for i in range(int((w-4)*ratio/12)):
        line(p, [(x+9+i*12, y+3), (x+4+i*12, y+12)], "#b1ffff", 1)


def gauge(p, cx, cy, radius, value, unit, warm=False, max_value=3.5):
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QPen(QColor("#1142b0"), 2))
    p.drawEllipse(QPointF(cx, cy), radius+9, radius+9)
    for j in range(39):
        a = math.radians(140+j*6.8)
        r1, r2 = radius-10, radius
        fraction = j / 38
        lo, hi = ((2/3.5, 3/3.5) if warm is True else
                  (.60, .85) if warm == "gpu" else (1, 1))
        color = QColor("#00d7ff" if fraction <= lo else
                       "#ffca62" if fraction <= hi else "#ff4c56")
        if j < 18 or warm:
            p.setPen(QPen(color, 4))
        else:
            p.setPen(QPen(QColor("#164b97"), 4))
        p.drawLine(QPointF(cx+math.cos(a)*r1, cy+math.sin(a)*r1),
                   QPointF(cx+math.cos(a)*r2, cy+math.sin(a)*r2))
    for i in range(6 if radius > 65 else 0):
        a = math.radians(140+i*52)
        tx, ty = cx+math.cos(a)*(radius-23), cy+math.sin(a)*(radius-23)
        text(p, tx-6, ty+4, str(round(i*max_value/5, 1)), 10, "#8cbaff")
    text(p, cx-30, cy+9, value, 34)
    text(p, cx-21, cy+31, unit, 15, "#a6c8ff")


class HudCanvas(QWidget):
    def __init__(self, registry, vertical=False, parent=None):
        super().__init__(parent)
        self.registry = registry
        self.vertical = vertical
        self.module_opacity = 88
        self.labels = {}
        self.readings = None
        self.refresh_plugins()
        self.setToolTip("Mesures réelles si sonde disponible • tiret = indisponible")

    def set_telemetry(self, readings):
        self.readings = readings
        self.update()

    def value(self, key, demo, places=0):
        if self.readings is None:
            return str(demo)
        val = self.readings.get(key)
        return f"{val:.{places}f}" if isinstance(val, (int, float)) else "—"

    def fraction(self, key, demo):
        if self.readings is None:
            return demo
        v = self.readings.get(key)
        return max(0, min(1, v/100)) if isinstance(v, (int, float)) else 0

    def used_free(self, prefix, demo):
        if self.readings is None:
            return demo
        a = self.readings.get(prefix + "_used_gb")
        b = self.readings.get(prefix + ("_available_gb" if prefix == "ram" else "_free_gb"))
        return f"{a:.1f} / {b:.1f} GB" if a is not None and b is not None else "—"

    def gpu_ghz(self):
        if self.readings is None:
            return "1.6"
        val = self.readings.get("gpu_clock_mhz")
        return f"{val / 1000:.2f}" if val is not None else "—"

    def gpu_vram(self):
        if self.readings is None:
            return "4.2 / 8.0 GB"
        a, b = self.readings.get("vram_used_gb"), self.readings.get("vram_total_gb")
        return f"{a:.1f} / {b:.1f} GB" if a is not None and b is not None else "VRAM —"

    def fans(self):
        if self.readings is None:
            return [{"name":"CPU","rpm":1240},{"name":"GPU","rpm":1580},{"name":"SYS","rpm":980}]
        return self.readings.get("fans") or []

    def refresh_plugins(self):
        self.labels = {item["slot"]: item["name"] for item in self.registry.installed() if item["enabled"]}
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.vertical:
            self.paint_vertical(p)
        elif self.width() < 950:
            self.paint_compact(p)
        else:
            p.scale(self.width()/1580, self.height()/200)
            self.paint_horizontal(p)
        p.end()

    def paint_horizontal(self, p):
        line(p, [(2, 44), (29, 11), (150, 11), (164, 4), (211, 4), (223, 14),
                 (412, 14), (425, 6), (698, 6), (708, 12), (1110, 12), (1120, 5), (1567, 5)], BLUE, 2)
        line(p, [(2, 160), (26, 196), (1550, 196), (1578, 165)], CYAN, 1.4)
        for i in range(25):
            x = 30+i*61
            line(p, [(x, 12), (x+19, 12), (x+25, 18), (x+44, 18)], "#084a8c")
            p.setPen(QPen(QColor(CYAN), 1))
            p.drawEllipse(QPointF(x, 12), 2.5, 2.5)
        sections = [(0, 380, "cpu", "CPU"), (380, 350, "gpu", "GPU"),
                    (730, 210, "ram", "RAM"), (940, 235, "storage", "SSD NVMe"),
                    (1175, 240, "fans", "FANS"), (1415, 165, "network", "NETWORK")]
        for x, w, kind, title in sections:
            panel(p, x, w, module_background(self.module_opacity))
            icon(p, kind, x+23, 45, 45 if kind != "network" else 34)
            text(p, x+(67 if kind == "network" else 81), 68,
                 self.labels.get(kind, title)[:13], 12 if kind == "network" else 23)
        text(p, 100, 123, self.value("cpu_temperature_c", 52), 37)
        text(p, 151, 119, "°C", 20)
        cpu_load = self.readings.get("cpu_percent") if self.readings else None
        cpu_color = "#ff4455" if cpu_load is not None and cpu_load >= 85 else CYAN
        text(p, 113, 162, self.value("cpu_percent", 18) + "%", 26, cpu_color)
        gauge(p, 279, 105, 79, self.value("cpu_frequency_ghz", 2.4, 1), "GHz", True)
        text(p, 466, 121, self.value("gpu_temperature_c", 48), 37)
        text(p, 519, 117, "°C", 20)
        text(p, 469, 161, self.value("gpu_percent", 32) + "%", 26, CYAN)
        gauge(p, 630, 98, 58, self.gpu_ghz(), "GHz", "gpu")
        text(p, 603, 173, self.gpu_vram(), 15, "#b6cfff")
        for x, w, percent, detail in [(754, 162, "44%", "14.2 / 32.0 GB"),
                                       (964, 185, "62%", "372 / 1.0 TB")]:
            text(p, x+w-59, 109, percent, 27)
            meter(p, x, 122, w, .44 if percent == "44%" else .62)
            text(p, x, 166, detail, 20)
        for i, label in enumerate(("CPU", "GPU", "SYS")):
            y = 96+i*29
            text(p, 1193, y+11, label, 17)
            meter(p, 1238, y, 69, (.68, .54, .42)[i])
            text(p, 1318, y+10, ("1240", "1580", "980")[i]+" RPM", 12, "#b7cfff")
        text(p, 1432, 115, "↓", 22, CYAN)
        text(p, 1454, 114, self.value("net_down_mbs", 12.8, 1) + " MB/s", 15)
        text(p, 1432, 143, "↑", 22, CYAN)
        text(p, 1454, 142, self.value("net_up_mbs", 1.6, 1) + " MB/s", 15)
        points = [(1434+i*5, 166+math.sin(i*1.7)*3+math.cos(i*.5)*2) for i in range(25)]
        line(p, points, CYAN, 1.3)
        text(p, 26, 191, "DÉMO" if self.readings is None else "CAPTEURS LOCAUX", 8, "#78aad0", False)

    def paint_compact(self, p):
        columns = 2 if self.width() < 520 else 3
        rows = math.ceil(6/columns)
        cell_w, cell_h = self.width()/columns, self.height()/rows
        entries = [("cpu", "CPU", "52 °C  /  2.4 GHz"), ("gpu", "GPU", "48 °C  /  1.6 GHz"),
                   ("ram", "RAM", "14.2 / 32 GB"), ("storage", "SSD", "372 / 1000 GB"),
                   ("fans", "FANS", "1240 RPM"), ("network", "NETWORK", "↓12.8 ↑1.6 MB/s")]
        for i, (kind, label, value) in enumerate(entries):
            x, y = (i % columns)*cell_w, (i // columns)*cell_h
            path = QPainterPath()
            path.addRoundedRect(QRectF(x+3, y+3, cell_w-7, cell_h-7), 8, 8)
            outline(p, path, module_background(self.module_opacity))
            icon(p, kind, x+12, y+10, 21)
            text(p, x+42, y+26, self.labels.get(kind, label)[:12], 12)
            text(p, x+12, y+cell_h-15, value, 12 if cell_w < 210 else 16)

    def paint_vertical(self, p):
        scale = self.width()/240
        p.scale(scale, scale)
        h = self.height()/scale
        entries = [("cpu", "CPU", "52 °C  •  2.4 GHz"), ("gpu", "GPU", "48 °C  •  1.6 GHz"),
                   ("ram", "RAM", "14.2 / 32.0 GB"), ("storage", "SSD NVMe", "372 / 1.0 TB"),
                   ("fans", "FANS", "CPU   1240 RPM"), ("network", "NETWORK", "↓12.8   ↑1.6 MB/s")]
        cell = h/6
        for i, (kind, title, value) in enumerate(entries):
            y = i*cell
            path = QPainterPath()
            path.addPolygon(QPolygonF([QPointF(16, y+4), QPointF(222, y+4),
                QPointF(234, y+16), QPointF(234, y+cell-16), QPointF(222, y+cell-4),
                QPointF(16, y+cell-4), QPointF(6, y+cell-16), QPointF(6, y+16)]))
            path.closeSubpath()
            outline(p, path, module_background(self.module_opacity))
            icon_size = 25 if cell < 95 else 34
            icon(p, kind, 20, y+13, icon_size)
            text(p, 62, y+33, self.labels.get(kind, title)[:13], 18)
            text(p, 20, y+cell-29, value, 17)
            meter(p, 20, y+cell-22, 195, .44)
