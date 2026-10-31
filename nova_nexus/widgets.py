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
    """Return a modal NOVA QDialog. Caller executes it and checks Accepted."""
    QtCore, QtGui, QtWidgets = _qt()
    t = validate_theme(theme if theme is not None else get_default_theme())
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle(title)
    dialog.setMinimumSize(430, 210)
    dialog.setObjectName("novaDialog")
    dialog.setStyleSheet(qt_stylesheet(t))
    layout = QtWidgets.QVBoxLayout(dialog)
    layout.setContentsMargins(26, 20, 26, 20)
    layout.setSpacing(14)
    head = QtWidgets.QLabel("NOVA / " + ("SECURE ACTION" if dangerous else "SYSTEM PROMPT"))
    head.setStyleSheet("font-weight: 700; color: " + t["colors"]["primary"] + ";")
    text = QtWidgets.QLabel(message)
    text.setWordWrap(True)
    text.setTextFormat(QtCore.Qt.PlainText)
    buttons = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    if dangerous:
        ok = buttons.button(QtWidgets.QDialogButtonBox.Ok)
        ok.setText("CONFIRMER")
        ok.setStyleSheet("border: 1px solid " + t["colors"]["danger"] + ";")
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(head)
    layout.addWidget(text, 1)
    layout.addWidget(buttons)
    return dialog


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
            bg.setColorAt(0, QtGui.QColor(9, 28, 42, int(208 * t["effects"]["opacity"])))
            bg.setColorAt(.55, QtGui.QColor(5, 14, 25, int(223 * t["effects"]["opacity"])))
            bg.setColorAt(1, QtGui.QColor(8, 28, 41, int(198 * t["effects"]["opacity"])))
            painter.fillPath(path, bg)
            reflection = QtGui.QLinearGradient(w * .44, 0, w * .75, h)
            reflection.setColorAt(0, QtGui.QColor(237, 252, 255, 0))
            reflection.setColorAt(.44, QtGui.QColor(237, 252, 255, 35))
            reflection.setColorAt(.63, QtGui.QColor(237, 252, 255, 5))
            reflection.setColorAt(1, QtGui.QColor(237, 252, 255, 0))
            painter.fillPath(path, reflection)
            painter.setClipping(False)

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
            # Rectilinear PCB zig-zag traces stay near the frame.
            stroke([(27, 56), (49, 56), (64, 41), (125, 41), (136, 30)], dim, 1.4)
            stroke([(w-27, h-57), (w-51, h-57),
                    (w-65, h-43), (w-132, h-43), (w-145, h-30)], dim, 1.4)
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
            painter.end()

    return GlassNotification()
