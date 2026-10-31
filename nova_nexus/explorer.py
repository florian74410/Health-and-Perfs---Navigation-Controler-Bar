"""NOVA Explorer — animated Qt file manager, user-space and opt-in.

Run: python3 -m nova_nexus.explorer [path]
Deletion moves to trash via Gio's GFile.trash; no permanent-delete shortcut.
"""
from __future__ import annotations
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .theme_engine import get_default_theme, qt_stylesheet


def run(path=None):
    from PySide6 import QtCore, QtGui, QtWidgets

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    class Explorer(QtWidgets.QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("NOVA / EXPLORER")
            self.resize(1040, 680)
            self.theme = get_default_theme()
            self.setStyleSheet(qt_stylesheet(self.theme))
            self.model = QtWidgets.QFileSystemModel(self)
            self.model.setRootPath(str(Path.home()))
            self.model.setReadOnly(False)
            self.view = QtWidgets.QTreeView()
            self.view.setModel(self.model)
            self.view.setAnimated(True)
            self.view.setAlternatingRowColors(True)
            self.view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
            self.view.doubleClicked.connect(self.open_item)
            self.view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            self.view.customContextMenuRequested.connect(self.context_menu)
            self.path = QtWidgets.QLineEdit()
            self.path.returnPressed.connect(lambda: self.go(self.path.text()))
            self.path.setAccessibleName("Current directory")
            up = QtWidgets.QPushButton("↑")
            up.clicked.connect(lambda: self.go(str(Path(self.path.text()).parent)))
            home = QtWidgets.QPushButton("⌂")
            home.clicked.connect(lambda: self.go(str(Path.home())))
            refresh = QtWidgets.QPushButton("⟳")
            refresh.clicked.connect(lambda: self.go(self.path.text()))
            toolbar = QtWidgets.QHBoxLayout()
            for item in (home, up, self.path, refresh):
                toolbar.addWidget(item)
            central = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout(central)
            caption = QtWidgets.QLabel("NOVA NEXUS  /  FILE SYSTEM")
            caption.setStyleSheet("font-weight:bold;color:#00CBF3;")
            layout.addWidget(caption)
            layout.addLayout(toolbar)
            layout.addWidget(self.view)
            self.setCentralWidget(central)
            self.statusBar().showMessage("Double-click to open · Right-click for actions")
            self.opacity_effect = QtWidgets.QGraphicsOpacityEffect(self.view.viewport())
            self.view.viewport().setGraphicsEffect(self.opacity_effect)
            self.animation = QtCore.QPropertyAnimation(self.opacity_effect, b"opacity", self)
            self.animation.setDuration(190)
            self.go(path or str(Path.home()))

        def go(self, folder):
            target = Path(folder).expanduser()
            if not target.is_dir():
                QtWidgets.QMessageBox.warning(self, "NOVA", "Folder not found or inaccessible")
                return
            target = target.resolve()
            self.path.setText(str(target))
            self.view.setRootIndex(self.model.index(str(target)))
            self.animation.stop()
            self.animation.setStartValue(0.45)
            self.animation.setEndValue(1.0)
            self.animation.start()

        def selected(self):
            idx = self.view.currentIndex()
            return Path(self.model.filePath(idx)) if idx.isValid() else None

        def open_item(self, idx):
            file = Path(self.model.filePath(idx))
            if file.is_dir():
                self.go(file)
            elif file.exists():
                subprocess.Popen(["xdg-open", str(file)], start_new_session=True)

        def context_menu(self, pos):
            file = self.selected()
            if file is None:
                return
            menu = QtWidgets.QMenu(self)
            menu.addAction("Open", lambda: self.open_item(self.model.index(str(file))))
            menu.addAction("Rename", lambda: self.rename(file))
            menu.addAction("Move to Trash", lambda: self.trash(file))
            menu.exec(self.view.viewport().mapToGlobal(pos))

        def rename(self, file):
            name, ok = QtWidgets.QInputDialog.getText(self, "NOVA / RENAME", "New name", text=file.name)
            if not ok or not name or name in (".", "..") or "/" in name or "\\x00" in name:
                return
            destination = file.with_name(name)
            if destination.exists():
                QtWidgets.QMessageBox.warning(self, "NOVA", "Destination already exists")
                return
            try:
                file.rename(destination)
            except OSError as err:
                QtWidgets.QMessageBox.warning(self, "NOVA", str(err))

        def trash(self, file):
            reply = QtWidgets.QMessageBox.question(self, "NOVA / TRASH", f"Move {file.name} to trash?")
            if reply != QtWidgets.QMessageBox.Yes:
                return
            try:
                # GTK/Gio integrates with the user's desktop trash; avoids unsafe deletion.
                import gi
                gi.require_version("Gio", "2.0")
                from gi.repository import Gio
                if not Gio.File.new_for_path(str(file)).trash(None):
                    raise OSError("Unable to move item to trash")
            except Exception as err:
                QtWidgets.QMessageBox.warning(self, "NOVA", f"Trash operation failed: {err}")

    window = Explorer()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1] if len(sys.argv) > 1 else None))
