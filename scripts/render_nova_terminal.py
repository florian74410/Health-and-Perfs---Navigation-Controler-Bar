"""Render actual Qt manager with labelled demonstration content, without executing commands."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import tempfile
from pathlib import Path
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from nova_nexus.terminal_manager import open_manager
app=QApplication([])
output=Path('Assets/Previews');output.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,HEALTHBAR_DATA_DIR=temp):
    manager=open_manager(start=False)
    manager.window.resize(1360,840)
    workspace=manager.workspace();workspace.set_format('grid')
    app.processEvents()
    demos=[
        ('SYSTÈME / LOCAL', '\x1b[36mNOVA NEXUS HD\x1b[0m  /  TERMINAL MANAGER\r\n\r\n\x1b[32mnova@desktop\x1b[0m:~$ uname -sr\r\nLinux · XFCE\r\n\r\n\x1b[32mnova@desktop\x1b[0m:~$ ls\r\n\x1b[34mDocuments   Images   Projets   Téléchargements\x1b[0m\r\n\r\n\x1b[36m▸ Un vrai shell pour chaque panneau\x1b[0m\r\n\x1b[32mnova@desktop\x1b[0m:~$ '),
        ('PROJET / DÉVELOPPEMENT', '\x1b[32mnova@desktop\x1b[0m:~/NOVA$ git status -sb\r\n## feature/nova-nexus-hd\r\n\x1b[36m M terminal_manager.py\x1b[0m\r\n\r\n\x1b[32mnova@desktop\x1b[0m:~/NOVA$ printf "NOVA\\n"\r\nNOVA\r\n\r\n\x1b[36m▸ Onglets indépendants · sessions conservées\x1b[0m\r\n\x1b[32mnova@desktop\x1b[0m:~/NOVA$ '),
        ('SURVEILLANCE / COMMANDES', '\x1b[36mSESSION INTERACTIVE / APERÇU\x1b[0m\r\n\r\nCouleurs ANSI, historique et sélection\r\nCtrl+C : interrompre une commande\r\nCtrl+Maj+C : copier la sélection\r\nCtrl+Maj+V : coller\r\n\r\n\x1b[33mÉDITION → TEXTE\x1b[0m\r\nPolice · couleur · taille · fond teinté\r\n\r\n\x1b[32mnova@desktop\x1b[0m:~$ '),
        ('ESPACE / LIBRE', '\x1b[36mCHOISIR SON ESPACE DE TRAVAIL\x1b[0m\r\n\r\n\x1b[33mÉDITION → FORMATS\x1b[0m\r\n  Terminal unique · 2 colonnes · 2 lignes\r\n  2 + 2 · 2 en haut + 1 en bas\r\n  Colonne gauche + 2 à droite\r\n\r\nF11 : agrandir / fenêtre\r\nLes séparateurs se redimensionnent à la souris.\r\n\r\n\x1b[32mnova@desktop\x1b[0m:~$ '),
    ]
    for pane,(title,content) in zip(workspace.panes,demos):
        pane.title.setText('◈  '+title);pane.session.stream.feed(content.encode());pane.view.render_screen()
    manager.tabs.setTabText(0,'◈  ESPACE PRINCIPAL')
    manager.status.setText('APERÇU VISUEL · CONTENU DE DÉMONSTRATION  /  FORMAT 2 + 2  /  ÉDITION → FORMATS · TEXTE')
    app.processEvents()
    manager.window.grab().save(str(output/'nova-v074-terminal-manager.png'))
    workspace.set_format('left_column');app.processEvents()
    for pane,(title,content) in zip(workspace.panes,demos):pane.session.stream.feed(b'\x1b[2J\x1b[H'+content.encode());pane.view.render_screen()
    manager.status.setText('APERÇU VISUEL · CONTENU DE DÉMONSTRATION  /  COLONNE GAUCHE + 2 À DROITE')
    app.processEvents();manager.window.grab().save(str(output/'nova-v074-terminal-column.png'))
    manager.window.close();app.processEvents()
print(output/'nova-v074-terminal-manager.png')
