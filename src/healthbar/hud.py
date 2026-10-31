"""Resolution-independent HUD artwork. Read-only live hardware readings (missing means unavailable)."""
import math
import time
from PySide6.QtCore import Qt, QPointF, QRectF, QRect, Signal, QTimer
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QPolygonF, QImage, QRadialGradient, QConicalGradient, QBrush, QFontMetricsF
from PySide6.QtWidgets import QWidget

CYAN = "#00d9ff"
from .ui_kit import QColor

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
    glyphs=QPainterPath();glyphs.addText(QPointF(x,y),font,str(value))
    glow=QColor(color);glow.setAlpha(45)
    p.setBrush(Qt.BrushStyle.NoBrush);p.setPen(QPen(glow,2.3));p.drawPath(glyphs)
    p.setPen(QColor(color))
    p.drawText(QPointF(x, y), str(value))


def fitted_text(p,x,y,value,width,size=18,color=WHITE,bold=True):
    font=QFont("DejaVu Sans");font.setBold(bold)
    size=max(8,size)
    while size>8:
        font.setPixelSize(size)
        if QFontMetricsF(font).horizontalAdvance(str(value))<=width:
            break
        size-=1
    font.setPixelSize(size)
    visible=QFontMetricsF(font).elidedText(str(value),Qt.TextElideMode.ElideRight,max(1,int(width)))
    text(p,x,y,visible,size,color,bold)


def outline(p, path, fill=None):
    # Glass stays inside each module. The surrounding desktop is never painted.
    if fill is not None:
        background=QColor(fill)
        p.fillPath(path,background)
        bounds=path.boundingRect()
        reflection=QLinearGradient(bounds.left(),bounds.top(),bounds.left(),bounds.top()+24)
        strength=background.alphaF()
        reflection.setColorAt(0,QColor(174,238,255,round(42*strength)))
        reflection.setColorAt(.22,QColor(66,161,255,round(18*strength)))
        reflection.setColorAt(1,QColor(0,0,0,0))
        p.fillPath(path,reflection)
    p.setBrush(Qt.BrushStyle.NoBrush)
    for width, color, alpha in ((22,BLUE,9),(14,BLUE,21),(8,CYAN,27),
                                 (3.4,BLUE,190),(1.5,CYAN,255),(.55,"#dcffff",235)):
        neon=QColor(color);neon.setAlpha(alpha)
        pen=QPen(neon,width);pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen);p.drawPath(path)


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
    line(p,[(x+6,y+4),(x+max(6,(w-4)*ratio-2),y+4)],"#c4ffff",.7)
    for i in range(int((w-4)*ratio/12)):
        line(p, [(x+9+i*12, y+3), (x+4+i*12, y+12)], "#b1ffff", 1)


def gauge(p, cx, cy, radius, value, unit, warm=False, max_value=3.5):
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QPen(QColor("#1142b0"), 2))
    p.drawEllipse(QPointF(cx, cy), radius+9, radius+9)
    ring=QConicalGradient(QPointF(cx,cy),35)
    for stop,shade in ((0,"#0552dc"),(.22,"#b6fcff"),(.34,"#00bbff"),(.62,"#091d51"),(.82,"#168dff"),(1,"#0552dc")):
        ring.setColorAt(stop,QColor(shade))
    p.setPen(QPen(QBrush(ring),2.5));p.drawEllipse(QPointF(cx,cy),radius+7,radius+7)
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


def tachometer(p, bounds, value, maximum, unit):
    """Circular dial in device pixels: no nonuniform scaling, no invented sample."""
    p.save()
    radius = min(bounds.width(), bounds.height()) / 2 - 3
    center = bounds.center()
    valid = isinstance(value, (int, float)) and math.isfinite(value)
    fraction = min(1, max(0, value / maximum)) if valid and maximum > 0 else None
    p.setBrush(Qt.BrushStyle.NoBrush)
    for i in range(29):
        angle = math.radians(140 + i * 260 / 28)
        color = "#ff4c56" if i > 24 else "#ffca62" if i > 19 else CYAN
        if fraction is None or i / 28 > fraction:
            color = "#164b97"
        p.setPen(QPen(QColor(color), 1.8))
        p.drawLine(center + QPointF(math.cos(angle), math.sin(angle)) * (radius - 4),
                   center + QPointF(math.cos(angle), math.sin(angle)) * radius)
    if fraction is not None:
        angle = math.radians(140 + fraction * 260)
        p.setPen(QPen(QColor("#a6faff"), 1.4))
        p.drawLine(center, center + QPointF(math.cos(angle), math.sin(angle)) * (radius - 7))
    p.setPen(QPen(QColor(CYAN), 1))
    p.drawEllipse(center, radius + 1, radius + 1)
    size = max(8, min(12, int(radius * .48)))
    font = QFont("DejaVu Sans"); font.setPixelSize(size); font.setBold(True)
    p.setFont(font); p.setPen(QColor(WHITE))
    number = (f"{value:.0f}" if unit == "%" else f"{value:.1f}") if valid else "—"
    p.drawText(QRectF(bounds.left(), center.y()+2, bounds.width(), radius*.65),
               Qt.AlignmentFlag.AlignCenter, number)
    font.setPixelSize(8); p.setFont(font); p.setPen(QColor("#abdaed"))
    p.drawText(QRectF(bounds.left(), bounds.bottom()-10, bounds.width(), 10),
               Qt.AlignmentFlag.AlignCenter, unit)
    p.restore()


class HudCanvas(QWidget):
    layout_changed = Signal(list)
    module_activated = Signal(str)
    ORIGINAL = ["cpu", "gpu", "ram", "storage", "fans", "network"]
    WIDTHS = {"cpu":380, "gpu":350, "ram":210, "storage":235, "fans":240, "network":165}
    def __init__(self, registry, vertical=False, parent=None):
        super().__init__(parent)
        self.registry = registry
        self.vertical = vertical
        self.module_opacity = 88
        self.labels = {}
        self.readings = None
        self.slot_order = self.ORIGINAL.copy()
        self._drag_origin = None
        self._drag_start = None
        self._hover_slot = None
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.visual_timer=QTimer(self)
        self.visual_timer.setInterval(50)
        self.visual_timer.timeout.connect(self.animate_neon)
        self.visual_timer.start()
        self.refresh_plugins()
        self.setToolTip("Mesures réelles si sonde disponible • tiret = indisponible")

    def animate_neon(self):
        if self.isVisible() and not getattr(self.window(),"retracted",False):
            self.update()

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
        self.labels = {item["slot"]: item["name"] for item in self.registry.installed() if item["enabled"] and item["api_version"] == 1}
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setClipRect(self.rect().adjusted(1,1,-1,-1))
        if self.vertical:
            self.paint_vertical(p)
        elif self.height() <= 150:
            self.paint_slim(p)
        elif self.width() < 1400:
            self.paint_compact(p)
        else:
            scale=min(self.width()/1580,self.height()/200)
            p.translate((self.width()-1580*scale)/2,0)
            p.scale(scale,scale)
            if self.slot_order == self.ORIGINAL:
                self.paint_horizontal(p)
            else:
                self.paint_reordered(p)
        p.resetTransform()
        for kind in self.slot_order:
            bounds = self.module_icon_rect(kind)
            icon(p,kind,bounds.x(),bounds.y(),bounds.width())
        p.end()

    def paint_reordered(self, painter):
        layer = QImage(1580, 200, QImage.Format.Format_ARGB32_Premultiplied)
        layer.fill(Qt.GlobalColor.transparent)
        source = QPainter(layer)
        source.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.paint_horizontal(source)
        source.end()
        old = {}
        offset = 0
        for kind in self.ORIGINAL:
            old[kind] = offset
            offset += self.WIDTHS[kind]
        offset = 0
        for kind in self.slot_order:
            width = self.WIDTHS[kind]
            painter.drawImage(QRectF(offset, 0, width, 200), layer,
                              QRectF(old[kind], 0, width, 200))
            offset += width

    def module_at(self, pos):
        if self.vertical:
            return min(5, max(0, int(pos.y() * 6/max(1, self.height()))))
        if self.height() <= 150:
            columns=6 if self.width()>=840 else 3
            rows=(6+columns-1)//columns
            col=min(columns-1,max(0,int(pos.x()*columns/max(1,self.width()))))
            row=min(rows-1,max(0,int(pos.y()*rows/max(1,self.height()))))
            return min(5,row*columns+col)
        if self.width() < 1400:
            columns = 2 if self.width() < 520 else 3
            rows = (6 + columns - 1)//columns
            col = min(columns-1, max(0, int(pos.x()*columns/max(1,self.width()))))
            row = min(rows-1, max(0, int(pos.y()*rows/max(1,self.height()))))
            return min(5,row*columns+col)
        scale=min(self.width()/1580,self.height()/200)
        left=(self.width()-1580*scale)/2
        x=max(0,min(1580,(pos.x()-left)/max(.01,scale)))
        width = 0
        for i, kind in enumerate(self.slot_order):
            width += self.WIDTHS[kind]
            if x < width:
                return i
        return 5

    def module_rect(self,kind):
        """Single geometry contract for drawing, clicks, dragging and plugin popovers."""
        index=self.slot_order.index(kind)
        if self.vertical:
            top=round(index*self.height()/6);bottom=round((index+1)*self.height()/6)
            return QRect(0,top,self.width(),bottom-top)
        if self.height()<=150 or self.width()<1400:
            columns=(6 if self.width()>=840 else 3) if self.height()<=150 else (2 if self.width()<520 else 3)
            rows=(6+columns-1)//columns
            col,row=index%columns,index//columns
            left,right=round(col*self.width()/columns),round((col+1)*self.width()/columns)
            top,bottom=round(row*self.height()/rows),round((row+1)*self.height()/rows)
            return QRect(left,top,right-left,bottom-top)
        scale=min(self.width()/1580,self.height()/200)
        left=(self.width()-1580*scale)/2
        offset=sum(self.WIDTHS[slot] for slot in self.slot_order[:index])
        return QRect(round(left+offset*scale),0,round(self.WIDTHS[kind]*scale),round(200*scale))

    def module_icon_rect(self, kind):
        """Top-right plugin logo: the sole Holo trigger in every layout."""
        bounds = self.module_rect(kind)
        size = max(10, min(22, bounds.height()-10, bounds.width()//4))
        return QRect(bounds.right()-size-8, bounds.top()+6, size, size)

    def module_global_rect(self, kind):
        bounds=self.module_rect(kind)
        return QRect(self.mapToGlobal(bounds.topLeft()),bounds.size())

    def mouseMoveEvent(self, event):
        hover = self.slot_order[self.module_at(event.position())]
        if hover != self._hover_slot:
            self._hover_slot = hover
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        if self._hover_slot is not None:
            self._hover_slot = None
            self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_origin = self.module_at(event.position())
            self._drag_start = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self._drag_origin is not None and self._drag_start is not None:
            index = self.module_at(event.position())
            moved = (event.position().toPoint() - self._drag_start).manhattanLength() > 10
            if moved and index != self._drag_origin:
                slot = self.slot_order.pop(self._drag_origin)
                self.slot_order.insert(index, slot)
                self.layout_changed.emit(self.slot_order.copy())
                self.update()
            elif (not moved and index == self._drag_origin and
                  self.module_icon_rect(self.slot_order[index]).contains(event.position().toPoint()) and
                  self.module_icon_rect(self.slot_order[index]).contains(self._drag_start)):
                self.module_activated.emit(self.slot_order[index])
        self._drag_origin = None
        self._drag_start = None
        super().mouseReleaseEvent(event)

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
        if cpu_load is not None and cpu_load >= 95:
            cpu_color = "#ff4455" if int(time.monotonic()*2) % 2 else "#f4faff"
        text(p, 113, 162, self.value("cpu_percent", 18) + "%", 26, cpu_color)
        gauge(p, 279, 105, 79, self.value("cpu_frequency_ghz", 2.4, 1), "GHz", True)
        text(p, 466, 121, self.value("gpu_temperature_c", 48), 37)
        text(p, 519, 117, "°C", 20)
        text(p, 469, 161, self.value("gpu_percent", 32) + "%", 26, CYAN)
        gauge(p, 630, 98, 58, self.gpu_ghz(), "GHz", "gpu")
        text(p, 603, 173, self.gpu_vram(), 15, "#b6cfff")
        for x, w, key, demo, detail in [
            (754, 162, "ram", "44", "14.2 / 17.8 GB"),
            (964, 185, "disk", "62", "372 / 628 GB")
        ]:
            text(p, x+w-62, 109, self.value(key + "_percent", demo) + "%", 25)
            meter(p, x, 122, w, self.fraction(key + "_percent", .44 if key == "ram" else .62))
            text(p, x, 166, self.used_free(key, detail), 17)
        if self.readings:
            read, write = self.readings.get("disk_read_mbs"), self.readings.get("disk_write_mbs")
            info = f"↓{read:.1f}  ↑{write:.1f} MB/s" if read is not None and write is not None else "I/O —"
            text(p, 966, 179, info, 10, "#b6cfff")
            power = self.readings.get("gpu_power_w")
            if power is not None:
                text(p, 466, 182, f"{power:.0f} W", 12, "#b6cfff")
        for i, fan in enumerate(self.fans()[:3]):
            y = 96+i*29
            text(p, 1193, y+11, fan["name"][:5].upper(), 14)
            meter(p, 1238, y, 69, min(1, max(0, fan["rpm"]/2500)))
            text(p, 1318, y+10, str(fan["rpm"])+" RPM", 12, "#b7cfff")
        if len(self.fans()) > 3:
            text(p, 1193, 180, f"+{len(self.fans()) - 3} fans", 10, "#b7cfff")
        text(p, 1432, 115, "↓", 22, CYAN)
        text(p, 1454, 114, self.value("net_down_mbs", 12.8, 1) + " MB/s", 15)
        text(p, 1432, 143, "↑", 22, CYAN)
        text(p, 1454, 142, self.value("net_up_mbs", 1.6, 1) + " MB/s", 15)
        points = [(1434+i*5, 166+math.sin(i*1.7)*3+math.cos(i*.5)*2) for i in range(25)]
        line(p, points, CYAN, 1.3)
        text(p, 26, 191, "DÉMO" if self.readings is None else "CAPTEURS LOCAUX", 8, "#78aad0", False)
        phase=(time.monotonic()%7)/7
        for y,offset in ((5,0),(195,.48)):
            cx=24+((phase+offset)%1)*1516
            center=QPointF(cx,y)
            glow=QRadialGradient(center,11)
            glow.setColorAt(0,QColor(210,255,255,230))
            glow.setColorAt(.22,QColor(17,199,255,155))
            glow.setColorAt(1,QColor(0,40,255,0))
            p.setPen(Qt.PenStyle.NoPen);p.setBrush(glow);p.drawEllipse(center,11,9)
            line(p,[(cx-17,y),(cx-2,y)],"#42e5ff",1.4)

    def paint_slim(self,p):
        columns=6 if self.width()>=840 else 3
        rows=(6+columns-1)//columns
        width,height=self.width()/columns,self.height()/rows
        entries=[
            ("cpu","CPU",self.value("cpu_temperature_c",52)+" °C",self.value("cpu_percent",18)+"% · "+self.value("cpu_frequency_ghz",2.4,1)+" GHz","cpu_percent"),
            ("gpu","GPU",self.value("gpu_temperature_c",48)+" °C",self.gpu_ghz()+" GHz · "+self.value("gpu_percent",32)+"%","gpu_percent"),
            ("ram","RAM",self.value("ram_percent",44)+"%",self.used_free("ram","14.2 / 17.8 GB"),"ram_percent"),
            ("storage","SSD",self.value("disk_percent",62)+"%",self.used_free("disk","372 / 628 GB"),"disk_percent"),
            ("fans","FANS",str(self.fans()[0]["rpm"])+" RPM" if self.fans() else "—", "Ventilation",None),
            ("network","RÉSEAU","↓"+self.value("net_down_mbs",12.8,1),"↑"+self.value("net_up_mbs",1.6,1)+" MB/s",None)]
        entries.sort(key=lambda entry:self.slot_order.index(entry[0]))
        for index,(kind,label,value,detail,key) in enumerate(entries):
            bounds=self.module_rect(kind)
            x,y,width,height=bounds.x(),bounds.y(),bounds.width(),bounds.height()
            path=QPainterPath();path.addRoundedRect(QRectF(x+3,y+3,width-7,height-6),6,6)
            outline(p,path,module_background(self.module_opacity))
            # Specular streak, subtle energy trace and a stronger border on hover.
            # Paint stays inside the responsive module rectangle and never stretches text.
            p.save()
            p.setClipPath(path,Qt.ClipOperation.IntersectClip)
            shine=QLinearGradient(x,y+3,x,y+min(30,height))
            shine.setColorAt(0,QColor(170,238,255,50))
            shine.setColorAt(1,QColor(170,238,255,0))
            p.fillRect(QRectF(x+7,y+4,max(0,width-14),min(27,height/3)),QBrush(shine))
            phase=(time.monotonic()*.24+index*.13)%1
            track_width=max(0,width-30)
            tracer_x=x+15+track_width*phase
            p.setPen(QPen(QColor(95,245,255,185),2))
            p.drawLine(QPointF(tracer_x-10,y+4),QPointF(tracer_x+10,y+4))
            if self._hover_slot==kind:
                p.setBrush(Qt.BrushStyle.NoBrush)
                for stroke,alpha in ((7,46),(2,235)):
                    edge=QColor(69,230,255,alpha)
                    p.setPen(QPen(edge,stroke))
                    p.drawPath(path)
            p.restore()
            p.save();p.setClipPath(path,Qt.ClipOperation.IntersectClip)
            if height>=50:
                dial_size = min(height-14, width*.36, 92)
                has_dial = kind in ("cpu", "gpu", "ram", "storage") and width >= 120
                left = x+12
                if has_dial:
                    readings = self.readings or {}
                    dial_key = "cpu_frequency_ghz" if kind == "cpu" else "gpu_clock_mhz" if kind == "gpu" else key
                    dial_value = readings.get(dial_key)
                    if kind == "gpu" and dial_value is not None:
                        dial_value /= 1000
                    maximum = max(3.5, readings.get("cpu_frequency_max_ghz") or 0,
                                  dial_value or 0) if kind == "cpu" else max(3.5, dial_value or 0) if kind == "gpu" else 100
                    tachometer(p, QRectF(x+8,y+(height-dial_size)/2,dial_size,dial_size),
                               dial_value, maximum, "GHz" if kind in ("cpu","gpu") else "%")
                    left = x+12+dial_size
                available = x+width-left-10
                fitted_text(p,left,y+20,self.labels.get(kind,label),max(1,available-28),10)
                baseline=y+max(34,min(height*.6,80))
                fitted_text(p,left,baseline,value,available,18 if height<90 else 25)
                if height>=62:
                    fitted_text(p,left,y+height-12,detail,available,10,"#abdaed",False)
            else:
                fitted_text(p,x+10,y+12,label,max(0,width*.31-14),8)
                fitted_text(p,x+width*.36,y+height-8,value,width*.64-10,12)
            p.restore()
            if key:
                fraction=self.fraction(key,.44)
                line(p,[(x+11,y+height-6),(x+11+max(0,width-24)*fraction,y+height-6)],CYAN,1.3)

    def paint_compact(self, p):
        columns = 2 if self.width() < 520 else 3
        rows = math.ceil(6/columns)
        cell_w, cell_h = self.width()/columns, self.height()/rows
        entries = [("cpu", "CPU", self.value("cpu_temperature_c",52)+" °C / "+self.value("cpu_frequency_ghz",2.4,1)+" GHz"),
                   ("gpu", "GPU", self.value("gpu_temperature_c",48)+" °C / "+self.gpu_ghz()+" GHz"),
                   ("ram", "RAM", self.used_free("ram","14.2 / 17.8 GB")),
                   ("storage", "SSD", self.used_free("disk","372 / 628 GB")),
                   ("fans", "FANS", str(self.fans()[0]["rpm"])+" RPM" if self.fans() else "RPM —"),
                   ("network", "NETWORK", "↓"+self.value("net_down_mbs",12.8,1)+" ↑"+self.value("net_up_mbs",1.6,1)+" MB/s")]
        entries.sort(key=lambda item: self.slot_order.index(item[0]))
        for i, (kind, label, value) in enumerate(entries):
            x, y = (i % columns)*cell_w, (i // columns)*cell_h
            path = QPainterPath()
            path.addRoundedRect(QRectF(x+3, y+3, cell_w-7, cell_h-7), 8, 8)
            outline(p, path, module_background(self.module_opacity))
            icon(p, kind, x+12, y+10, 21)
            text(p, x+42, y+26, self.labels.get(kind, label)[:12], 12)
            text(p, x+12, y+cell_h-15, value, 12 if cell_w < 210 else 16)

    def paint_vertical(self, p):
        if self.width()<120:
            cell=self.height()/6
            for index,kind in enumerate(self.slot_order):
                y=index*cell
                path=QPainterPath();path.addRoundedRect(QRectF(3,y+3,self.width()-6,cell-6),6,6)
                outline(p,path,module_background(self.module_opacity))
                text(p,8,y+min(cell-10,49),{"storage":"SSD","network":"NET"}.get(kind,kind.upper()),10)
            return
        scale = self.width()/240
        p.scale(scale, scale)
        h = self.height()/scale
        entries = [("cpu", "CPU", self.value("cpu_temperature_c",52)+" °C / "+self.value("cpu_frequency_ghz",2.4,1)+" GHz"),
                   ("gpu", "GPU", self.value("gpu_temperature_c",48)+" °C / "+self.gpu_ghz()+" GHz"),
                   ("ram", "RAM", self.used_free("ram","14.2 / 17.8 GB")),
                   ("storage", "SSD NVMe", self.used_free("disk","372 / 628 GB")),
                   ("fans", "FANS", str(self.fans()[0]["rpm"])+" RPM" if self.fans() else "RPM —"),
                   ("network", "NETWORK", "↓"+self.value("net_down_mbs",12.8,1)+" ↑"+self.value("net_up_mbs",1.6,1)+" MB/s")]
        entries.sort(key=lambda item: self.slot_order.index(item[0]))
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
            text(p, 62, y+33, self.labels.get(kind, title)[:13], 18)
            text(p, 20, y+cell-29, value, 17)
            meter(p, 20, y+cell-22, 195, .44)
