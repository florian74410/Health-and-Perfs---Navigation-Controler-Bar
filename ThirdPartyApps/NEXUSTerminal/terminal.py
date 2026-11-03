#!/usr/bin/env python3
"""NEXUS Terminal — independent compact Qt terminal, not a NovaBar plugin."""
import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMenu, QMessageBox, QSplitter,
    QTabWidget, QToolBar, QVBoxLayout, QWidget,
)
from pyside6_qtermwidget import QTermWidget

VERSION = "0.1.0-dev"
STYLE = """
QMainWindow, QWidget#central { background: #061320; color: #e0f3fc; }
QToolBar { background: #092436; border-bottom: 1px solid #00b6e8; spacing: 3px; padding: 2px; }
QToolButton { color: #e0f3fc; background: #0b3042; border: 1px solid #146e8a; padding: 3px 7px; }
QToolButton:hover { background: #14506a; border-color: #13e4ff; }
QTabWidget::pane { background: #071522; border: 1px solid #14728e; }
QTabBar::tab { color: #b2eafa; background: #09283c; border: 1px solid #16526b; padding: 4px 10px; }
QTabBar::tab:selected { color: white; background: #0a4358; border-bottom: 2px solid #09d7ff; }
QSplitter::handle { background: #126781; }
QMenu { background: #081e2d; color: #ecf7fd; border: 1px solid #1487a3; }
QMenu::item:selected { background: #0a465c; }
"""

class Shell(QTermWidget):
    """One terminal backed by the upstream Qt PTY engine."""
    def __init__(self, parent=None):
        super().__init__(0, parent)
        self.setTerminalFont(QFont("DejaVu Sans Mono", 10))
        self.setHistorySize(4000)
        self.setTerminalSizeHint(False)
        self.setShellProgram("/bin/bash")
        self.setColorScheme("DarkPastels")
        self.startShellProgram()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_menu)
        self._shortcuts = []
        for combo, callback in (
            ("Ctrl+Shift+C", self.copyClipboard),
            ("Ctrl+Shift+V", self.pasteClipboard),
        ):
            shortcut = QShortcut(QKeySequence(combo), self)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(callback)
            self._shortcuts.append(shortcut)

    def open_menu(self, point):
        menu = QMenu(self)
        menu.addAction("Copier", self.copyClipboard)
        menu.addAction("Coller", self.pasteClipboard)
        menu.exec(self.mapToGlobal(point))


def panes(mode):
    """Compact responsive nested QSplitters, one PTY per leaf."""
    def split(orientation, children):
        widget = QSplitter(orientation)
        widget.setChildrenCollapsible(False)
        widget.setHandleWidth(3)
        for child in children:
            widget.addWidget(child)
        widget.setSizes([100] * len(children))
        return widget

    h, v = Qt.Orientation.Horizontal, Qt.Orientation.Vertical
    if mode == "one": return Shell()
    if mode == "two-columns": return split(h, [Shell(), Shell()])
    if mode == "two-rows": return split(v, [Shell(), Shell()])
    if mode == "grid":
        return split(v, [split(h, [Shell(), Shell()]), split(h, [Shell(), Shell()])])
    if mode == "two-plus-one":
        return split(h, [split(v, [Shell(), Shell()]), Shell()])
    if mode == "one-plus-two":
        return split(h, [Shell(), split(v, [Shell(), Shell()])])
    raise ValueError("Unsupported layout")


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"NOVA NEXUS / TERMINAL — {VERSION}")
        self.resize(1050, 650)
        self.setMinimumSize(540, 320)
        self.setStyleSheet(STYLE)
        central = QWidget()
        central.setObjectName("central")
        box = QVBoxLayout(central)
        box.setContentsMargins(4, 4, 4, 4)
        box.setSpacing(2)
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        box.addWidget(self.tabs)
        self.setCentralWidget(central)
        toolbar = QToolBar("Disposition")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        self.action(toolbar, "+ Onglet", self.new_tab, "Ctrl+Shift+T")
        for label, mode in (
            ("1", "one"), ("2 │", "two-columns"), ("2 ─", "two-rows"),
            ("2×2", "grid"), ("2+1", "two-plus-one"), ("1+2", "one-plus-two"),
        ):
            self.action(toolbar, label, lambda checked=False, m=mode: self.change_layout(m))
        self.new_tab()

    def action(self, toolbar, label, fn, shortcut=None):
        act = QAction(label, self)
        act.triggered.connect(fn)
        if shortcut:
            act.setShortcut(QKeySequence(shortcut))
            self.addAction(act)
        toolbar.addAction(act)

    def new_tab(self):
        index = self.tabs.addTab(panes("one"), f"Terminal {self.tabs.count()+1}")
        self.tabs.setCurrentIndex(index)

    def change_layout(self, mode):
        index = self.tabs.currentIndex()
        if index < 0:
            return
        answer = QMessageBox.question(
            self, "Changer de disposition",
            "Changer de format ferme les sessions de cet onglet. Continuer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        old = self.tabs.widget(index)
        label = self.tabs.tabText(index)
        new = panes(mode)
        self.tabs.removeTab(index)
        old.deleteLater()
        self.tabs.insertTab(index, new, label)
        self.tabs.setCurrentIndex(index)

    def close_tab(self, index):
        if self.tabs.count() == 1:
            self.close()
            return
        old = self.tabs.widget(index)
        self.tabs.removeTab(index)
        old.deleteLater()

    def closeEvent(self, event):
        answer = QMessageBox.question(
            self, "Quitter NEXUS Terminal", "Fermer toutes les sessions terminal ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("NEXUS Terminal")
    window = Window()
    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
