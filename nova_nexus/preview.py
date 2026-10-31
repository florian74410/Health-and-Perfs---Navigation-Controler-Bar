"""NOVA visual preview, without altering XFCE settings or installed NovaBar."""
from __future__ import annotations

import sys


def main() -> int:
    try:
        from PySide6 import QtCore, QtWidgets
    except ImportError:
        print("PySide6 is required for the NOVA preview", file=sys.stderr)
        return 2

    from .theme_engine import get_default_theme
    from .widgets import make_dialog, make_notification

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    theme = get_default_theme()
    toast = make_notification("NOVA / NOTIFICATION", "Notification frontale — Electric Blue PCB", theme)
    toast.setWindowTitle("NOVA Notification Preview")
    toast.setWindowFlag(QtCore.Qt.Window, True)
    toast.show()
    dialog = make_dialog("NOVA Dialog Preview", "Voulez-vous confirmer cette opération de démonstration ?", theme)
    dialog.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
