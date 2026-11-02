"""Reusable PySide6 NOVA widgets — opt-in; does not change desktop defaults.

Run a visual preview with:
  python3 -m nova_nexus.preview
"""
from __future__ import annotations

from .theme_engine import get_default_theme, qt_stylesheet, validate_theme


def _qt():
    try:
        from PySide6 import QtCore, QtGui, QtWidgets
    except ImportError as exc:
        raise RuntimeError("PySide6 is required for NOVA widgets") from exc
    return QtCore, QtGui, QtWidgets


def make_dialog(title: str, message: str, theme=None, *, dangerous=False):
    """Modal dialog using exactly the same glass/PCB surface as notifications."""
    QtCore, QtGui, QtWidgets = _qt()
    t = validate_theme(theme if theme is not None else get_default_theme())

    class NovaGlassDialog(QtWidgets.QDialog):
        def __init__(self):
            super().__init__()
            self.setWindowTitle(title)
            self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint)
            self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
            self.setMinimumWidth(500)
            self.setModal(True)
            layout = QtWidgets.QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            actions = [
                ("ANNULER", self.reject),
                ("CONFIRMER" if dangerous else "VALIDER", self.accept),
            ]
            self.panel = make_notification(
                "NOVA / " + ("SECURE ACTION" if dangerous else "SYSTEM PROMPT"),
                message, t, actions=actions,
            )
            self.panel.setMinimumHeight(205)
            self.panel.setFixedWidth(500)
            layout.addWidget(self.panel)

        def keyPressEvent(self, event):
            if event.key() == QtCore.Qt.Key_Escape:
                self.reject()
            else:
                super().keyPressEvent(event)

    return NovaGlassDialog()


def make_notification(title: str, message: str, theme=None, *, actions=None):
    """Frontal smoked-glass PCB notification; optional (label, callback) actions.

    Fully painted with QPainter: no white backing, no browser, no fake D-Bus.
    Title/body remain real selectable-accessible Qt labels. Action callbacks
    run only when clicked. A widget reference must be kept by its caller.
    """
    QtCore, QtGui, QtWidgets = _qt()
    t = validate_theme(theme if theme is not None else get_default_theme())
    c = t["colors"]
    actions = list(actions or [])[:2]

    class GlassNotification(QtWidgets.QFrame):
        def __init__(self):
            super().__init__()
            self.setObjectName("novaGlassNotification")
            self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
            self.setAutoFillBackground(False)
            self.setMinimumSize(400, 170 if actions else 143)
            self.setFixedWidth(460)
            self._phase = 0
            self._pulse_speed = max(1, round(190 / max(60, t["motion"]["duration_ms"])))
            self._motion = bool(t["motion"]["enabled"] and not t["motion"]["reduce_motion"])
            self._timer = QtCore.QTimer(self)
            self._timer.setInterval(40)
            self._timer.timeout.connect(self._animate)
            self.setStyleSheet("""
                QFrame#novaGlassNotification { background: transparent; border: none; }
                QLabel { background: transparent; border: none; }
                QPushButton { background: rgba(9, 28, 41, 195);
                  border: 1px solid %s; border-radius: 0px; color: %s;
                  font-family: Arial; font-weight: 700; padding: 7px 13px; }
                QPushButton:hover { background: %s; color: #06101A; }
                QPushButton:focus { border: 2px solid %s; }
            """ % (c["primary"], c["text"], c["primary"], c["text"]))
            layout = QtWidgets.QVBoxLayout(self)
            layout.setContentsMargins(32, 24, 32, 26)
            layout.setSpacing(12)
            heading = QtWidgets.QLabel(title)
            heading.setAlignment(QtCore.Qt.AlignCenter)
            heading.setFont(QtGui.QFont("Arial", 13, QtGui.QFont.Bold))
            heading.setStyleSheet("color: %s; letter-spacing: 1px;" % c["primary"])
            heading.setAccessibleName("Notification title")
            body = QtWidgets.QLabel(message)
            body.setTextFormat(QtCore.Qt.PlainText)
            body.setAlignment(QtCore.Qt.AlignCenter)
            body.setWordWrap(True)
            body.setFont(QtGui.QFont("Arial", 11))
            body.setStyleSheet("color: %s;" % c["text"])
            body.setAccessibleName("Notification message")
            layout.addWidget(heading)
            layout.addWidget(body, 1)
            if actions:
                action_row = QtWidgets.QHBoxLayout()
                action_row.addStretch()
                for label, callback in actions:
                    button = QtWidgets.QPushButton(str(label))
                    button.clicked.connect(callback)
                    action_row.addWidget(button)
                action_row.addStretch()
                layout.addLayout(action_row)
            if self._motion:
                self._timer.start()

        def _animate(self):
            self._phase = (self._phase + self._pulse_speed) % 150
            self.update()

        def hideEvent(self, event):
            self._timer.stop()
            super().hideEvent(event)

        def showEvent(self, event):
            super().showEvent(event)
            if self._motion:
                self._timer.start()

        def paintEvent(self, event):
            painter = QtGui.QPainter(self)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            w, h = self.width(), self.height()
            inset, cut = 5.0, float(t["effects"]["bevel_size"] + 8)
            path = QtGui.QPainterPath()
            path.moveTo(inset + cut, inset)
            path.lineTo(w - inset - cut, inset)
            path.lineTo(w - inset, inset + cut)
            path.lineTo(w - inset, h - inset - cut)
            path.lineTo(w - inset - cut, h - inset)
            path.lineTo(inset + cut, h - inset)
            path.lineTo(inset, h - inset - cut)
            path.lineTo(inset, inset + cut)
            path.closeSubpath()
            painter.setClipPath(path)

            # Transparent smoked glass, subtle gradient and optical reflection.
            bg = QtGui.QLinearGradient(0, 0, w, h)
            bg.setColorAt(0, QtGui.QColor(9, 28, 42, int(228 * t["effects"]["opacity"])))
            bg.setColorAt(.55, QtGui.QColor(5, 14, 25, int(239 * t["effects"]["opacity"])))
            bg.setColorAt(1, QtGui.QColor(8, 28, 41, int(224 * t["effects"]["opacity"])))
            painter.fillPath(path, bg)
            reflection = QtGui.QLinearGradient(w * .44, 0, w * .75, h)
            reflection.setColorAt(0, QtGui.QColor(237, 252, 255, 0))
            reflection.setColorAt(.44, QtGui.QColor(237, 252, 255, 76))
            reflection.setColorAt(.63, QtGui.QColor(237, 252, 255, 12))
            reflection.setColorAt(1, QtGui.QColor(237, 252, 255, 0))
            painter.fillPath(path, reflection)
            painter.setClipping(False)
            # Layered rim illumination: simulated neon bloom with several soft strokes.
            glow_power = float(t["effects"]["glow"])
            for width, alpha in ((16, 19), (11, 34), (7, 63), (3.0, 190)):
                halo = QtGui.QColor(c["primary"])
                halo.setAlpha(min(255, int(alpha * glow_power)))
                painter.setPen(QtGui.QPen(halo, width, QtCore.Qt.SolidLine,
                                        QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                painter.setBrush(QtCore.Qt.NoBrush)
                painter.drawPath(path)

            def stroke(points, color, width=1.0):
                painter.setPen(QtGui.QPen(color, width))
                for start, end in zip(points, points[1:]):
                    painter.drawLine(QtCore.QPointF(*start), QtCore.QPointF(*end))

            accent = QtGui.QColor(c["primary"])
            dim = QtGui.QColor(accent)
            dim.setAlpha(int(95 * t["effects"]["pcb_visibility"]))
            rim = QtGui.QPen(QtGui.QColor(125, 211, 236, 185), 2.0)
            painter.setPen(rim)
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawPath(path)
            for offset, alpha in ((9, 70), (13, 35)):
                painter.setPen(QtGui.QPen(QtGui.QColor(0, 203, 243, alpha), 1))
                painter.drawLine(offset + cut, offset, w - offset - cut, offset)
                painter.drawLine(offset + cut, h - offset, w - offset - cut, h - offset)
            # Four layered PCB tracks with animated energy nodes riding the routing.
            routes = [
                [(27, 56), (49, 56), (64, 41), (125, 41), (136, 30)],
                [(27, 70), (53, 70), (83, 49), (170, 49), (183, 35)],
                [(w-27, h-57), (w-51, h-57), (w-65, h-43), (w-132, h-43), (w-145, h-30)],
                [(w-27, h-70), (w-58, h-70), (w-85, h-51), (w-171, h-51), (w-185, h-37)],
                [(55, h-29), (128, h-29), (146, h-17), (w*.40, h-17)],
                [(w-55, 29), (w-128, 29), (w-146, 17), (w*.60, 17)],
            ]
            for n, points in enumerate(routes):
                trace = QtGui.QPainterPath(QtCore.QPointF(*points[0]))
                for point in points[1:]:
                    trace.lineTo(QtCore.QPointF(*point))
                base = QtGui.QColor(accent)
                base.setAlpha(int(90 + 110 * t["effects"]["pcb_visibility"]))
                painter.setPen(QtGui.QPen(base, 1.7))
                painter.drawPath(trace)
                if self._motion:
                    p = (self._phase / 150 + n * .19) % 1.
                    for width, alpha in ((10, 20), (6, 58), (3, 145)):
                        color = QtGui.QColor(accent)
                        color.setAlpha(int(alpha * glow_power))
                        painter.setBrush(color)
                        painter.setPen(QtCore.Qt.NoPen)
                        painter.drawEllipse(trace.pointAtPercent(p), width/2, width/2)
                    painter.setBrush(QtGui.QColor(180, 255, 255))
                    painter.drawEllipse(trace.pointAtPercent(p), 1.7, 1.7)
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(accent)
            for x, y in ((27, 56), (w-27, h-57)):
                painter.drawEllipse(QtCore.QPointF(x, y), 2.5, 2.5)
            glow = QtGui.QLinearGradient(w*.37, 0, w*.63, 0)
            glow.setColorAt(0, QtGui.QColor(0, 203, 243, 0))
            glow.setColorAt(.5, accent)
            glow.setColorAt(1, QtGui.QColor(0, 203, 243, 0))
            painter.fillRect(QtCore.QRectF(w*.37, 6, w*.26, 3), glow)
            painter.fillRect(QtCore.QRectF(w*.37, h-9, w*.26, 3), glow)
            # Moving electric pulse across the top rail and a moving glossy sweep.
            if self._motion:
                x = (self._phase / 149.0) * (w + 120) - 60
                pulse = QtGui.QRadialGradient(QtCore.QPointF(x, 7), 68)
                pulse.setColorAt(0, QtGui.QColor(105, 245, 255, int(180 * glow_power)))
                pulse.setColorAt(1, QtGui.QColor(0, 203, 243, 0))
                painter.fillRect(QtCore.QRectF(max(5, x - 68), 5, 136, 7), pulse)
                painter.setClipPath(path)
                sweep = QtGui.QLinearGradient(x - 75, 0, x + 75, 0)
                sweep.setColorAt(0, QtGui.QColor(255, 255, 255, 0))
                sweep.setColorAt(.5, QtGui.QColor(180, 244, 255, 52))
                sweep.setColorAt(1, QtGui.QColor(255, 255, 255, 0))
                painter.fillRect(QtCore.QRectF(x-75, 0, 150, h), sweep)
                painter.setClipping(False)
            painter.end()

    return GlassNotification()

# NOVA v3: both public constructors use one shared glass chassis.
from .chrome_v3 import make_dialog, make_notification  # noqa: F811,E402
