#!/usr/bin/env python3
"""NEXUS Terminal 0.2 — native Qt terminal, standalone or embedded.

The terminal engine is QTermWidget/PTTY. UI chrome never intercepts the PTY
output or pretends to know a shell command's return code.
"""
from __future__ import annotations

import os
import sys
import shlex
from pathlib import Path

from PySide6.QtCore import Qt, QProcess, QTimer, Signal
from PySide6.QtGui import QAction, QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMenu, QMessageBox, QPushButton, QScrollArea,
    QSizePolicy, QSplitter, QTabWidget, QToolButton, QVBoxLayout, QWidget,
)
from pyside6_qtermwidget import QTermWidget
from nexus_dialogs import SettingsDialog, SessionsDialog
from web_inspector import WebInspector

VERSION = "0.2.0-dev"
APP_DIR = Path(__file__).resolve().parent
MACRO_DIR = Path.home() / ".config" / "nexus-terminal" / "macros"
MODES = {
    "one": ("1 panneau", 1),
    "two-columns": ("2 colonnes", 2),
    "two-rows": ("2 lignes", 2),
    "grid": ("Grille 2×2", 4),
    "two-plus-one": ("2 + 1", 3),
    "one-plus-two": ("1 + 2", 3),
}
STYLE = """
* { font-family: "DejaVu Sans", sans-serif; font-size: 11px; color: #d8f3fd; }
QWidget#nexusRoot, QMainWindow { background: #040d17; }
QFrame#header { background: #071c2b; border: 1px solid #13b4df;
                border-top: 2px solid #4de4ff; border-radius: 5px; }
QLabel#brand { font-size: 17px; font-weight: bold; color: #f2fcff; }
QLabel#subtle { color: #78a6bb; }
QLabel#section { color: #5edfff; font-weight: bold; padding: 5px 2px; }
QFrame#side, QFrame#footer { background: #061824; border: 1px solid #15738c;
                            border-radius: 5px; }
QFrame#pane { background: #03131f; border: 1px solid #1598ba;
              border-radius: 5px; }
QFrame#paneHeader { background: #092236; border: 0;
                    border-bottom: 1px solid #20b8dc; }
QPushButton, QToolButton, QComboBox {
    background: #0a293b; border: 1px solid #146a83;
    border-radius: 4px; padding: 6px 9px; color: #d8f3fd;
}
QPushButton:hover, QToolButton:hover, QComboBox:hover {
    background: #124055; border-color: #42dfff;
}
QPushButton:pressed, QToolButton:pressed { background: #17627b; }
QPushButton#primary { background: #0b5368; border-color: #36d9f9; }
QPushButton#danger { border-color: #a93a4a; color: #ffcbd0; }
QTabWidget::pane { background: #03111b; border: 1px solid #126e88; }
QTabBar::tab { background: #09283a; border: 1px solid #126784;
                color: #b9dfec; padding: 8px 15px; margin-right: 2px; }
QTabBar::tab:selected { background: #0c4056; color: white;
                        border-bottom: 2px solid #4be3ff; }
QSplitter::handle { background: #125b71; }
QSplitter::handle:hover { background: #39d8f6; }
QMenu { background: #061b2a; border: 1px solid #21b6dd; }
QMenu::item { padding: 6px 16px; }
QMenu::item:selected { background: #15516b; }
QLineEdit { background: #061c2a; border: 1px solid #2386a1;
            border-radius: 4px; padding: 7px; }
QScrollArea { border: 0; background: transparent; }
QLabel#toastSuccess { background: #072b26; color: #a9ffe4;
                      border: 1px solid #20c98f; border-radius: 5px; padding: 10px; }
QLabel#toastError { background: #30121f; color: #ffe0e4;
                    border: 1px solid #e54e68; border-radius: 5px; padding: 10px; }
QLabel#toastInfo { background: #082b40; color: #b6efff;
                   border: 1px solid #33c6ee; border-radius: 5px; padding: 10px; }
"""

def row(*widgets, spacing=6):
    layout = QHBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(spacing)
    for widget in widgets:
        layout.addWidget(widget)
    return layout


def button(text, callback, name=None):
    b = QPushButton(text)
    if name:
        b.setObjectName(name)
    b.clicked.connect(callback)
    return b


class Shell(QTermWidget):
    """Each shell owns its real PTY and keeps it when moved between layouts."""

    def __init__(self, parent=None):
        super().__init__(0, parent)
        self.setTerminalFont(QFont("DejaVu Sans Mono", 10))
        self.setHistorySize(6000)
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


class TerminalPane(QFrame):
    def __init__(self, shell=None, title="Local Bash"):
        super().__init__()
        self.setObjectName("pane")
        self.shell = shell or Shell()
        v = QVBoxLayout(self)
        v.setContentsMargins(2, 2, 2, 2)
        v.setSpacing(1)
        bar = QFrame()
        bar.setObjectName("paneHeader")
        hdr = QHBoxLayout(bar)
        hdr.setContentsMargins(8, 2, 5, 2)
        label = QLabel("◉  " + title)
        label.setStyleSheet("color: #89ebff; font-weight: bold;")
        hdr.addWidget(label)
        hdr.addStretch()
        v.addWidget(bar)
        v.addWidget(self.shell, 1)


def make_split(orientation, children):
    s = QSplitter(orientation)
    s.setChildrenCollapsible(False)
    s.setHandleWidth(4)
    for w in children:
        s.addWidget(w)
    s.setSizes([100] * len(children))
    return s


def make_layout(mode, shells):
    h, v = Qt.Orientation.Horizontal, Qt.Orientation.Vertical
    panes = [TerminalPane(shell, f"Console {i + 1} — Bash") for i, shell in enumerate(shells)]
    if mode == "one":
        return panes[0]
    if mode == "two-columns":
        return make_split(h, panes)
    if mode == "two-rows":
        return make_split(v, panes)
    if mode == "grid":
        return make_split(v, [make_split(h, panes[:2]), make_split(h, panes[2:])])
    if mode == "two-plus-one":
        return make_split(h, [make_split(v, panes[:2]), panes[2]])
    if mode == "one-plus-two":
        return make_split(h, [panes[0], make_split(v, panes[1:])])
    raise ValueError("Unknown terminal layout: " + mode)


class TerminalPage(QWidget):
    """An open tab: retains shell objects across layout changes."""

    def __init__(self):
        super().__init__()
        self.mode = "one"
        self.shells = [Shell()]
        self.root = None
        self.layout_box = QVBoxLayout(self)
        self.layout_box.setContentsMargins(3, 3, 3, 3)
        self.layout_box.setSpacing(0)
        self.rebuild()

    def rebuild(self):
        # Reparent shell widgets before deleting old decorative chrome.
        # A shell continues to run its PTY while its owning QSplitter changes.
        for shell in self.shells:
            shell.setParent(self)
        old = self.root
        if old:
            self.layout_box.removeWidget(old)
            old.hide()
        self.root = make_layout(self.mode, self.shells)
        self.layout_box.addWidget(self.root)
        if old:
            old.deleteLater()

    def change_mode(self, mode, parent):
        wanted = MODES[mode][1]
        current = len(self.shells)
        if wanted < current:
            answer = QMessageBox.question(
                parent, "Réduire les consoles",
                f"Cette disposition ferme {current - wanted} session(s) Bash. Continuer ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return False
            for shell in self.shells[wanted:]:
                shell.setParent(None)
                shell.close()
                shell.deleteLater()
            self.shells = self.shells[:wanted]
        elif wanted > current:
            self.shells.extend(Shell() for _ in range(wanted - current))
        self.mode = mode
        self.rebuild()
        return True


class SecretDialog(QDialog):
    """Only for NEXUS-managed operations; never captures arbitrary PTY passwords."""

    def __init__(self, description="Saisie confidentielle", parent=None):
        super().__init__(parent)
        self.setWindowTitle("NEXUS • Saisie sécurisée")
        self.setModal(True)
        self.setMinimumWidth(360)
        v = QVBoxLayout(self)
        v.addWidget(QLabel(description))
        self.edit = QLineEdit()
        self.edit.setEchoMode(QLineEdit.EchoMode.Password)
        v.addWidget(self.edit)
        reveal = QCheckBox("Afficher temporairement")
        reveal.toggled.connect(
            lambda yes: self.edit.setEchoMode(
                QLineEdit.EchoMode.Normal if yes else QLineEdit.EchoMode.Password
            )
        )
        v.addWidget(reveal)
        actions = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        actions.accepted.connect(self.accept)
        actions.rejected.connect(self.reject)
        v.addWidget(actions)

    @staticmethod
    def request(description, parent=None):
        dlg = SecretDialog(description, parent)
        return dlg.edit.text() if dlg.exec() == QDialog.DialogCode.Accepted else None


class NexusTerminalWidget(QWidget):
    """Embeddable component: no QApplication or QMainWindow is created here."""

    event = Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("nexusRoot")
        self.setStyleSheet(STYLE)
        self._jobs = set()
        self._toast_timer = QTimer(self)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(lambda: self.toast.hide())
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 7)
        outer.setSpacing(6)

        header = QFrame()
        header.setObjectName("header")
        h = QHBoxLayout(header)
        h.setContentsMargins(12, 7, 12, 7)
        logo = QLabel("⬡  NEXUS TERMINAL")
        logo.setObjectName("brand")
        h.addWidget(logo)
        h.addStretch()
        h.addWidget(QLabel("MULTI CONSOLE"))
        self.mode_picker = QComboBox()
        for key, (label, _) in MODES.items():
            self.mode_picker.addItem(label, key)
        self.mode_picker.currentIndexChanged.connect(self.layout_selected)
        h.addWidget(self.mode_picker)
        h.addWidget(button("◈ Sessions", self.open_sessions))
        h.addWidget(button("⚙ Paramètres", self.open_settings))
        h.addWidget(button("↗ Web Inspector", self.open_web))
        h.addWidget(button("+ Onglet", self.new_tab, "primary"))
        outer.addWidget(header)

        body = QSplitter(Qt.Orientation.Horizontal)
        body.setChildrenCollapsible(False)
        body.setHandleWidth(4)
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.sync_picker)
        body.addWidget(self.tabs)

        sidebar = QFrame()
        sidebar.setObjectName("side")
        sidebar.setMinimumWidth(175)
        sidebar.setMaximumWidth(265)
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(9, 9, 9, 9)
        sb.addWidget(self.section("◈  ACTIONS RAPIDES"))
        sb.addWidget(button("＋ Nouvelle console", self.new_tab))
        sb.addWidget(button("⌘  Scripts / Macros", self.choose_macro))
        sb.addWidget(button("◈  Sessions / SSH", self.open_sessions))
        sb.addWidget(button("↗  Web Inspector", self.open_web))
        sb.addWidget(button("⚙  Paramètres", self.open_settings))
        sb.addWidget(button("🔒  Saisie confidentielle", self.secret_demo))
        sb.addWidget(self.section("◈  DISPOSITIONS"))
        for mode, (label, _) in MODES.items():
            sb.addWidget(button(label, lambda checked=False, m=mode: self.set_layout(m)))
        sb.addStretch()
        sb.addWidget(self.section("NEXUS • ElectroBlueNEON"))
        body.addWidget(sidebar)
        body.setStretchFactor(0, 1)
        body.setSizes([850, 208])
        outer.addWidget(body, 1)

        self.toast = QLabel()
        self.toast.setObjectName("toastInfo")
        self.toast.setWordWrap(True)
        self.toast.hide()
        outer.addWidget(self.toast)
        footer = QFrame()
        footer.setObjectName("footer")
        foot = QHBoxLayout(footer)
        foot.setContentsMargins(10, 4, 10, 4)
        self.session_count = QLabel("●  Sessions : 0")
        foot.addWidget(self.session_count)
        foot.addStretch()
        foot.addWidget(QLabel("PTY natif • Bash • Qt6"))
        outer.addWidget(footer)
        self.new_tab()
        self._shortcuts = []
        shortcut = QShortcut(QKeySequence("Ctrl+Shift+T"), self)
        shortcut.activated.connect(self.new_tab)
        self._shortcuts.append(shortcut)

    @staticmethod
    def section(text):
        label = QLabel(text)
        label.setObjectName("section")
        return label

    def current_page(self):
        return self.tabs.currentWidget()

    def update_status(self):
        total = sum(len(self.tabs.widget(i).shells) for i in range(self.tabs.count()))
        self.session_count.setText(f"●  Sessions : {total}")

    def new_tab(self):
        page = TerminalPage()
        index = self.tabs.addTab(page, f"Terminal {self.tabs.count() + 1}")
        self.tabs.setCurrentIndex(index)
        self.update_status()
        self.event.emit("terminal.session.created", {"count": self.tabs.count()})

    def sync_picker(self, index):
        page = self.current_page()
        if page:
            pos = self.mode_picker.findData(page.mode)
            self.mode_picker.blockSignals(True)
            self.mode_picker.setCurrentIndex(pos)
            self.mode_picker.blockSignals(False)

    def layout_selected(self, index):
        mode = self.mode_picker.itemData(index)
        if mode:
            self.set_layout(mode)

    def set_layout(self, mode):
        page = self.current_page()
        if page and page.change_mode(mode, self):
            self.update_status()
            self.event.emit("terminal.layout.changed", {"mode": mode})
        self.sync_picker(self.tabs.currentIndex())

    def close_tab(self, index):
        page = self.tabs.widget(index)
        if not page:
            return
        answer = QMessageBox.question(
            self, "Fermer l'onglet", "Fermer les sessions Bash de cet onglet ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.tabs.removeTab(index)
        page.deleteLater()
        if self.tabs.count() == 0:
            self.new_tab()
        self.update_status()

    def notify(self, kind, message, duration=5500):
        kind = kind if kind in {"Success", "Error", "Info"} else "Info"
        symbols = {"Success": "✓", "Error": "⚠", "Info": "ⓘ"}
        self.toast.setObjectName("toast" + kind)
        self.toast.setText(symbols[kind] + "  " + str(message))
        self.toast.style().unpolish(self.toast)
        self.toast.style().polish(self.toast)
        self.toast.show()
        self._toast_timer.start(duration)
        self.event.emit("terminal.notification", {"kind": kind.lower(), "message": str(message)})

    def open_settings(self):
        dialog=SettingsDialog(self)
        dialog.changed.connect(self.apply_settings)
        dialog.exec()

    def apply_settings(self,options):
        font=QFont("DejaVu Sans Mono",int(options.get("font_size",10)))
        for i in range(self.tabs.count()):
            page=self.tabs.widget(i)
            if isinstance(page,TerminalPage):
                for shell in page.shells:
                    shell.setTerminalFont(font)
        self.notify("Success","Préférences enregistrées.")

    def open_sessions(self):
        dialog=SessionsDialog(self)
        dialog.connect_ssh.connect(self.start_ssh_session)
        dialog.exec()

    def start_ssh_session(self,args):
        """Run validated ssh argv as quoted interactive command in a new PTY."""
        if not args or args[0]!="ssh":
            self.notify("Error","Commande SSH refusée.")
            return
        self.new_tab()
        page=self.current_page()
        if page is None or not page.shells:
            self.notify("Error","Impossible de créer la session.")
            return
        # Quotes are essential: never concatenate raw profile fields into shell code.
        command=shlex.join(args)
        page.shells[0].sendText(command+"\\n")
        self.notify("Info","Connexion SSH démarrée dans un nouvel onglet.")

    def open_web(self):
        # Separate Qt window in this older source. The v0.5 host can dock the
        # same WebInspector(QWidget) into its own multi-pane layout.
        if not hasattr(self,"_web_inspectors"):
            self._web_inspectors=[]
        panel=WebInspector()
        panel.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose,True)
        panel.resize(860,620)
        panel.show()
        self._web_inspectors.append(panel)
        panel.destroyed.connect(lambda:self._web_inspectors.remove(panel)
                                if panel in self._web_inspectors else None)

    def choose_macro(self):
        MACRO_DIR.mkdir(parents=True, exist_ok=True)
        filename, _ = QFileDialog.getOpenFileName(
            self, "Choisir un script shell", str(MACRO_DIR),
            "Scripts Bash (*.sh);;Tous les fichiers (*)",
        )
        if filename:
            self.run_script(Path(filename))

    def run_script(self, path):
        """Run explicit script in QProcess, not within an arbitrary interactive PTY.

        Exit codes are reliable here, so success/error notifications are accurate.
        """
        path = Path(path).expanduser().resolve()
        if not path.is_file() or path.suffix != ".sh":
            self.notify("Error", "Seuls les fichiers .sh existants sont acceptés.")
            return
        answer = QMessageBox.question(
            self, "Exécuter un script", f"Exécuter ce script avec Bash ?\n{path}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        process = QProcess(self)
        process.setProgram("/bin/bash")
        process.setArguments([str(path)])
        process.setWorkingDirectory(str(path.parent))
        self._jobs.add(process)
        process.errorOccurred.connect(
            lambda error, p=process: self.notify("Error", f"Impossible de lancer : {p.errorString()}")
        )
        process.finished.connect(
            lambda code, status, p=process: self._finished_script(p, path.name, code, status)
        )
        process.start()
        self.notify("Info", f"Exécution : {path.name}", 2300)
        self.event.emit("terminal.script.started", {"name": path.name})

    def _finished_script(self, process, name, code, status):
        ok = code == 0 and status == QProcess.ExitStatus.NormalExit
        self.notify("Success" if ok else "Error",
                    f"{name} : {'terminé avec succès' if ok else 'échec'} (code {code})")
        self.event.emit("terminal.script.finished", {"name": name, "code": code, "success": ok})
        self._jobs.discard(process)
        process.deleteLater()

    def secret_demo(self):
        # This dialog is an example of a safe managed action. It does not
        # forward or save a password to the shell, clipboard or event bus.
        result = SecretDialog.request("Démonstration : saisir une donnée masquée", self)
        if result is not None:
            self.notify("Info", "Saisie confirmée (non enregistrée et non transmise).")

    def shutdown_confirmed(self):
        """Call only after the host has asked the user to close this component."""
        for process in list(self._jobs):
            process.terminate()
        self._jobs.clear()


class Window(QMainWindow):
    """Standalone wrapper. The same NexusTerminalWidget embeds in a host MDI."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"NEXUS Terminal — ElectroBlueNEON {VERSION}")
        self.resize(1200, 750)
        self.setMinimumSize(640, 420)
        self.terminal = NexusTerminalWidget(self)
        self.setCentralWidget(self.terminal)

    def closeEvent(self, event):
        answer = QMessageBox.question(
            self, "Quitter NEXUS Terminal", "Fermer toutes les sessions et scripts actifs ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.terminal.shutdown_confirmed()
            event.accept()
        else:
            event.ignore()


def create_widget(context=None, parent=None):
    """Host integration: create QWidget within the existing QApplication.

    If context has an event/publish API, bridge only structured NEXUS events.
    """
    widget = NexusTerminalWidget(parent)
    if context is not None and hasattr(context, "publish"):
        widget.event.connect(lambda name, payload: context.publish(name, payload))
    return widget


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("NEXUS Terminal")
    window = Window()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
