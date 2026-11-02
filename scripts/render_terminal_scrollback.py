"""Capture the actual two-pane terminal UI with labelled demo scrollback."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
import tempfile
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from nova_nexus.terminal_manager import open_manager
app=QApplication([])
with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,HEALTHBAR_DATA_DIR=temp):
    manager=open_manager(start=False);manager.window.resize(1280,760)
    workspace=manager.workspace();workspace.set_format('columns');app.processEvents()
    for pane in workspace.panes:
        text=''.join(f'\x1b[36m[{i:03d}]\x1b[0m NOVA / ligne de démonstration\r\n' for i in range(220))
        pane.session.stream.feed(text.encode());pane.view.render_screen()
    left,right=workspace.panes[:2]
    left.title.setText('◈  HISTORIQUE / LECTURE EN COURS')
    right.title.setText('◈  SESSION / SORTIE EN DIRECT')
    left.view.history_scrollbar.setValue(left.view.history_scrollbar.maximum()-70)
    left.view.render_screen()
    manager.status.setText('APERÇU DE DÉMONSTRATION · BARRES INDÉPENDANTES · MOLETTE · MAJ + PAGE ↑↓ · 2 000 LIGNES')
    app.processEvents()
    path=Path('Assets/Previews/nova-v075-terminal-scrollback.png');path.parent.mkdir(parents=True,exist_ok=True)
    assert manager.window.grab().save(str(path))
    manager.window.close();app.processEvents()
print(path)
