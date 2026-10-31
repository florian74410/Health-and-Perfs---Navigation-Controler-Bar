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


def make_notification(title: str, message: str, theme=None):
    """Return a front-facing, screen-aligned QWidget; caller controls its lifetime.

    Not a D-Bus notification daemon. Use as an internal preview/component.
    """
    QtCore, QtGui, QtWidgets = _qt()
    t = validate_theme(theme if theme is not None else get_default_theme())
    toast = QtWidgets.QFrame()
    toast.setObjectName("novaNotification")
    toast.setFixedWidth(360)
    toast.setMinimumHeight(108)
    toast.setStyleSheet(qt_stylesheet(t))
    layout = QtWidgets.QVBoxLayout(toast)
    layout.setContentsMargins(18, 14, 18, 14)
    header = QtWidgets.QLabel(title)
    header.setStyleSheet("font-weight: 700; color: " + t["colors"]["primary"] + ";")
    body = QtWidgets.QLabel(message)
    body.setTextFormat(QtCore.Qt.PlainText)
    body.setWordWrap(True)
    layout.addWidget(header)
    layout.addWidget(body)
    return toast
