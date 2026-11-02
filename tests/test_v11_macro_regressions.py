"""Regression checks for NOVA NEXUS HD 1.1 on XFCE and the terminal."""
from pathlib import Path
import ast
import unittest

ROOT = Path(__file__).resolve().parents[1]
def source(path):
    content=(ROOT / path).read_text(encoding="utf-8")
    ast.parse(content)
    return content

def test_compact_hud_default_and_validation():
    config=source("src/healthbar/config.py")
    app=source("src/healthbar/app.py")
    dialogs=source("src/healthbar/dialogs.py")
    assert "retracted_hud_height: int = 30" in config
    assert "20 <= self.retracted_hud_height <= 50" in config
    assert "edge = self.settings.retracted_hud_height" in app
    assert 'form.addRow("Hauteur HUD rétracté", self.retracted_hud_height)' in dialogs
    assert "retracted_hud_height=self.retracted_hud_height.value()" in dialogs

def test_xfce_panel_guard_lifecycle():
    app=source("src/healthbar/app.py")
    desktop=source("src/healthbar/desktop_backend.py")
    assert "self.native_panel_guard.hide(self.bottom_dock.full_rect)" in app
    assert "self.native_panel_guard.restore()" in app
    assert "NativePanelGuard" in desktop
    assert "--restore-xfce-after-pid" in desktop

def test_terminal_clipboard_and_interrupt_semantics():
    terminal=source("src/nova_nexus/terminal.py")
    manager=source("src/nova_nexus/terminal_manager.py")
    assert "if control and event.key()==C.Qt.Key_C:" in terminal
    assert "shift or self.textCursor().hasSelection()" in terminal
    assert "if control and event.key()==C.Qt.Key_V:" in terminal
    assert "self.session.write(data)" in terminal
    assert "self.action(edit,'Copier',lambda:self.active_view().copy())" in manager
    assert "self.action(edit,'Coller',lambda:self.active_view().paste_text())" in manager

def test_scrollback_selection_snapshot():
    terminal=source("src/nova_nexus/terminal.py")
    assert "def begin_history_selection(self):" in terminal
    assert "def end_history_selection(self):" in terminal
    assert "self.setPlainText(text)" in terminal
    assert "self.setVerticalScrollBarPolicy(C.Qt.ScrollBarAlwaysOn)" in terminal
    assert "def mousePressEvent(self,event):" in terminal
    assert "super().wheelEvent(event)" in terminal
    assert "def copy_full_history(self):" in terminal


def load_tests(loader, tests, pattern):
    """Include these source regression checks in unittest discovery."""
    return unittest.TestSuite(unittest.FunctionTestCase(test) for name, test in
                              sorted(globals().items()) if name.startswith("test_")
                              and callable(test))
