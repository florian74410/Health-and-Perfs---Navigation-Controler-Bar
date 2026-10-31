"""Read-only transparent PCB/electron pulse overlay for the EXISTING Xfce panel.

It never receives mouse events, so every original launcher and systray icon
continues to work. The geometry follows the native panel on X11; the overlay
does not change the panel's original height.
"""
from __future__ import annotations

import math
import os
import sys
import time

from PySide6.QtCore import QPointF, Qt, QTimer, QRect, QRectF
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QApplication, QWidget

from .overlay import apply_all_workspaces, apply_priority
from .xfce_panel_skin import PALETTES


def panel_x11_bounds(screen_geometry):
    """Find a visible Xfce panel along the bottom screen edge (no guessed bounds)."""
    if not sys.platform.startswith("linux") or not os.environ.get("DISPLAY"):
        return None
    try:
        from Xlib import X, display, error
        connection = display.Display()
        try:
            root = connection.screen().root
            children = root.query_tree().children
            matching = []
            for window in children:
                try:
                    klass = " ".join(window.get_wm_class() or ()).lower()
                    title = (window.get_wm_name() or "").lower()
                    if "xfce4-panel" not in klass and "xfce4-panel" not in title:
                        continue
                    attrs = window.get_attributes()
                    if attrs.map_state != X.IsViewable:
                        continue
                    rect = window.get_geometry()
                    location = window.translate_coords(root, 0, 0)
                    x, y, w, h = location.x, location.y, rect.width, rect.height
                    # Hidden autohide stubs may have 1-3px; those get no overlay.
                    if w < 120 or h < 15 or h > 180:
                        continue
                    if abs((y+h) - (screen_geometry.y()+screen_geometry.height())) > 12:
                        continue
                    if x+w <= screen_geometry.left() or x >= screen_geometry.right():
                        continue
                    matching.append(QRect(x, y, w, h))
                except (error.XError, OSError, ValueError, TypeError):
                    continue
            return max(matching, key=lambda r:r.width()) if matching else None
        finally:
            connection.close()
    except (ImportError, OSError, ValueError, RuntimeError):
        return None


class XFCEPanelCircuitEffects(QWidget):
    """Click-through overlay: narrow cyber traces, pulses and microchip nodes."""
    def __init__(self, settings):
        super().__init__(None)
        self.settings = settings
        self._phase = 0.0
        self._native_bounds = None
        flags = (Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint |
                 Qt.WindowType.WindowStaysOnTopHint |
                 Qt.WindowType.WindowDoesNotAcceptFocus |
                 Qt.WindowType.WindowTransparentForInput)
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.poller = QTimer(self)
        self.poller.setInterval(900)
        self.poller.timeout.connect(self.locate_native_panel)
        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.tick)
        self.poller.start()
        self.locate_native_panel()

    def locate_native_panel(self):
        if not getattr(self.settings, "xfce_skin_enabled", False):
            self.hide()
            return
        screens = QApplication.screens()
        if not screens:
            self.hide()
            return
        screen = screens[min(self.settings.screen, len(screens)-1)]
        rect = panel_x11_bounds(screen.geometry())
        if rect is None:
            self.hide()
            return
        if self._native_bounds != rect:
            self._native_bounds = rect
            self.setGeometry(rect)
        if not self.isVisible():
            self.show()
            apply_priority(self, True)
            apply_all_workspaces(self)
        if not self.timer.isActive():
            self.timer.start()

    def tick(self):
        if self.isVisible():
            self._phase = time.monotonic() % 12 / 12
            self.update()
        else:
            self.timer.stop()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        width, height = self.width(), self.height()
        if width < 60 or height < 12:
            p.end()
            return
        theme = PALETTES.get(self.settings.theme, PALETTES["blue-neon"])
        accent = QColor(theme[0])
        soft = QColor(theme[1])
        strength = max(0.0, min(1.0, self.settings.xfce_skin_fx_intensity/100.0))
        if strength == 0:
            p.end()
            return
        alpha = round(170 * strength)
        accent.setAlpha(alpha)
        soft.setAlpha(round(125 * strength))

        # Microtraces only in the top/bottom 4px and at the endpoints:
        # they never paint over the native XFCE icons or tray hit targets.
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(soft, 1))
        p.drawLine(QPointF(0, 2), QPointF(width, 2))
        p.drawLine(QPointF(0, height-2), QPointF(width, height-2))
        for x in range(20, width-10, 52):
            p.setPen(QPen(soft, .7))
            p.drawLine(QPointF(x, 1.5), QPointF(x+9, 1.5))
            p.drawLine(QPointF(x+9, 1.5), QPointF(x+14, 4.5))
            p.drawLine(QPointF(x+14, 4.5), QPointF(x+32, 4.5))
            p.setPen(QPen(accent, 1))
            p.drawEllipse(QPointF(x+32, 4.5), 1.4, 1.4)
        # Subminiature silicon nodes are confined to the thin upper edge.
        # No added row: all existing launcher and systray hit zones remain native.
        for chip_x in range(108, width-35, 224):
            core = QColor(theme[0]); core.setAlpha(round(35*strength))
            p.setPen(QPen(soft, .7))
            p.setBrush(core)
            p.drawRoundedRect(QRectF(chip_x, .5, 18, 7), 1.2, 1.2)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRect(QRectF(chip_x+5, 2.3, 8, 3.1))
            for pin in (3, 8, 13):
                p.drawLine(QPointF(chip_x+pin, 0), QPointF(chip_x+pin, 1.5))
                p.drawLine(QPointF(chip_x+pin, 6.9), QPointF(chip_x+pin, 8.3))
        for x in (9, width-10):
            p.setPen(QPen(accent, 1))
            p.drawEllipse(QPointF(x, height-4), 2.4, 2.4)

        # Electron pulses travel in opposite directions around the PCB rails.
        for fraction, y, direction in ((self._phase, 2.5, 1),
                                        ((self._phase+.43)%1, height-2.5, -1)):
            cx = fraction*width if direction > 0 else (1-fraction)*width
            trail = QLinearGradient(cx-27*direction, y, cx+14*direction, y)
            bright = QColor(theme[0])
            bright.setAlpha(round(230 * strength))
            dark = QColor(theme[0]);dark.setAlpha(0)
            trail.setColorAt(0, dark)
            trail.setColorAt(.65, bright)
            trail.setColorAt(1, dark)
            p.setPen(QPen(QBrush(trail), 2.8))
            p.drawLine(QPointF(cx-27*direction, y), QPointF(cx+14*direction, y))
            p.setPen(QPen(bright, 1.4))
            p.drawEllipse(QPointF(cx, y), 2.1, 2.1)
        p.end()

    def closeEvent(self, event):
        self.poller.stop()
        self.timer.stop()
        super().closeEvent(event)
