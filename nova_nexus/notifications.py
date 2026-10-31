"""Local NOVA notification previews — FRONT-FACING and opt-in, no D-Bus takeover."""
from __future__ import annotations
from .theme_engine import get_default_theme
from .widgets import make_notification


def show_notification(title: str, body: str, app, theme=None):
    """Show a front-facing popup. Caller owns Qt event loop."""
    from PySide6 import QtCore, QtGui
    palette = theme or get_default_theme()
    widget = make_notification(title, body, palette)
    widget.setWindowFlags(QtCore.Qt.Tool | QtCore.Qt.FramelessWindowHint |
                          QtCore.Qt.WindowStaysOnTopHint)
    screen = app.primaryScreen().availableGeometry()
    widget.adjustSize()
    widget.move(screen.right() - widget.width() - 20, screen.top() + 20)
    widget.show()
    milliseconds = palette["notifications"]["duration_ms"]
    QtCore.QTimer.singleShot(milliseconds, widget.close)
    return widget
