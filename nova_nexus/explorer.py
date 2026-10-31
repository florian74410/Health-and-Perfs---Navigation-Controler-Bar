"""NOVA Explorer V2 — cyberpunk file manager for XFCE, opt-in preview.

Uses native Qt file models, XDG open and Gio trash. Does not replace Thunar.
"""
from __future__ import annotations
import os
import shutil
import subprocess
import sys
from pathlib import Path
from .theme_engine import get_default_theme, qt_stylesheet


def run(start=None):
    from PySide6 import QtCore as C, QtGui as G, QtWidgets as W
    from .chrome_v3 import make_dialog
    app = W.QApplication.instance() or W.QApplication(sys.argv)
    theme = get_default_theme()
    colors = theme["colors"]
    cyan = colors["primary"]

    class Explorer(W.QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("NOVA Explorer")
            self.setWindowFlags(C.Qt.Window | C.Qt.FramelessWindowHint)
            self.setAttribute(C.Qt.WA_TranslucentBackground, True)
            self.drag_start = None
            from PySide6.QtSvg import QSvgRenderer
            self.pcb = G.QPixmap(640, 360)
            self.pcb.fill(C.Qt.transparent)
            asset = Path(__file__).resolve().parent.parent / "Assets/Overlays/nova_pcb_overlay.svg"
            if asset.is_file():
                svg = QSvgRenderer(str(asset))
                if svg.isValid():
                    painter = G.QPainter(self.pcb)
                    svg.render(painter)
                    painter.end()
            self.resize(1180, 740)
            self.setMinimumSize(810, 510)
            self.setStyleSheet("""
                QMainWindow, QWidget#root {background:transparent;color:#F2F8FF;}
                QLabel {color:#E5F8FF;background:transparent;}
                QFrame#sidebar {background:rgba(14,39,54,205);border:1px solid #1E7E97;}
                QFrame#toolbar {background:rgba(18,48,66,210);border:1px solid #2490A8;}
                QPushButton {background:rgba(18,49,67,215);color:#E8FBFF;border:1px solid #2D8CA3;
                    padding:7px 11px;min-height:20px;border-radius:0;}
                QPushButton:hover {border:1px solid #3EEBFF;background:rgba(26,84,108,235);}
                QPushButton:pressed {background:rgba(11,101,126,235);}
                QLineEdit {background:rgba(6,24,36,232);color:#F4FCFF;border:1px solid #39B9D0;
                    padding:8px;border-radius:0;}
                QLineEdit:focus {background:rgba(9,31,46,238);border:1px solid #6EF2FF;}
                QListView, QTreeView {background:rgba(7,28,42,198);color:#E9F6FF;border:0;
                    selection-background-color:rgba(33,126,156,190);selection-color:#FFFFFF;
                    alternate-background-color:rgba(11,37,54,165);}
                QListView::item:hover,QTreeView::item:hover{background:#123A50;}
                QHeaderView::section {background:#102D3D;color:#8FE9F6;padding:6px;border:0;}
                QScrollBar:vertical {background:#081D2B;width:11px;}
                QScrollBar::handle:vertical {background:#16718B;min-height:25px;}
                QMenu {background:#0B2231;color:#EFFBFF;border:1px solid #00BBDD;}
                QMenu::item:selected {background:#12536B;}
                QStatusBar {background:#0B2837;color:#99EDF8;border-top:1px solid #117B91;}
            """)
            self.model = W.QFileSystemModel(self)
            self.model.setRootPath(str(Path.home()))
            self.model.setReadOnly(True)
            self.history = []
            self.cursor = -1
            self.clipboard_path = None
            self.cut_mode = False

            root = W.QWidget(objectName="root")
            outer = W.QVBoxLayout(root)
            outer.setContentsMargins(22, 18, 22, 18)
            outer.setSpacing(9)
            header = W.QHBoxLayout()
            mark = W.QLabel("◈  NOVA Explorer")
            mark.setStyleSheet("color:#00DFFF;font:bold 19px Arial;")
            header.addWidget(mark)
            header.addStretch()
            header.addWidget(W.QLabel("NOVA NEXUS HD  /  FILE SYSTEM"))
            mini = W.QPushButton("−")
            close = W.QPushButton("×")
            for btn in (mini, close):
                btn.setFixedSize(26, 24)
                btn.setStyleSheet("QPushButton{background:#253641;color:#FF526A;border:1px solid #00CBEF;padding:0;font:bold 18px Arial;} QPushButton:hover{background:#A92E43;color:white;}")
            mini.clicked.connect(self.showMinimized)
            close.clicked.connect(self.close)
            header.addWidget(mini)
            header.addWidget(close)
            mark.mousePressEvent = self.drag_press
            mark.mouseMoveEvent = self.drag_move
            mark.mouseReleaseEvent = self.drag_release
            outer.addLayout(header)

            navigation = W.QHBoxLayout()
            for text, handler in (("❮",self.back),("❯",self.forward),("↑",self.up),("⌂",lambda:self.navigate(Path.home()))):
                b = W.QPushButton(text)
                b.setFixedWidth(39)
                b.clicked.connect(handler)
                navigation.addWidget(b)
            self.address = W.QLineEdit()
            self.address.setAccessibleName("Chemin du dossier")
            self.address.returnPressed.connect(lambda:self.navigate(Path(self.address.text()).expanduser()))
            navigation.addWidget(self.address, 3)
            self.search = W.QLineEdit()
            self.search.setPlaceholderText("⌕  Rechercher dans le dossier…")
            self.search.textChanged.connect(self.filter_files)
            navigation.addWidget(self.search, 1)
            outer.addLayout(navigation)

            body = W.QHBoxLayout()
            body.setSpacing(10)
            sidebar = W.QFrame(objectName="sidebar")
            sidebar.setFixedWidth(205)
            nav = W.QVBoxLayout(sidebar)
            nav.setContentsMargins(8,12,8,10)
            for group, locations in (
                ("◆  ACCÈS RAPIDE",[("Bureau",Path.home()/"Bureau"),("Documents",Path.home()/"Documents"),
                   ("Téléchargements",Path.home()/"Téléchargements"),("Images",Path.home()/"Images"),
                   ("Vidéos",Path.home()/"Vidéos"),("Musique",Path.home()/"Musique")]),
                ("◆  EMPLACEMENTS",[("Dossier personnel",Path.home()),("Système /",Path("/")),
                   ("Stockage /media",Path("/media")),("Réseau (GVfs)",Path.home()/".gvfs")]),
            ):
                heading = W.QLabel(group)
                heading.setStyleSheet("color:#40DFFF;font:bold 11px Arial;padding:8px 3px;")
                nav.addWidget(heading)
                for label, destination in locations:
                    btn = W.QPushButton(label)
                    btn.setStyleSheet("text-align:left;padding:6px 9px;")
                    btn.clicked.connect(lambda checked=False,p=destination:self.navigate(p))
                    nav.addWidget(btn)
            nav.addStretch()
            body.addWidget(sidebar)

            right = W.QVBoxLayout()
            tools = W.QFrame(objectName="toolbar")
            actions = W.QHBoxLayout(tools)
            actions.setContentsMargins(6,6,6,6)
            actions.setSpacing(5)
            for name, fn in (
                ("＋ Nouveau",self.new_folder),("Couper",self.cut),("Copier",self.copy),
                ("Coller",self.paste),("Corbeille",self.trash),("Renommer",self.rename),
                ("Propriétés",self.properties),
            ):
                button = W.QPushButton(name)
                button.clicked.connect(fn)
                actions.addWidget(button)
            actions.addStretch()
            grid = W.QPushButton("▦")
            details = W.QPushButton("☷")
            grid.clicked.connect(lambda:self.change_view(True))
            details.clicked.connect(lambda:self.change_view(False))
            actions.addWidget(grid)
            actions.addWidget(details)
            right.addWidget(tools)

            self.views = W.QStackedWidget()
            self.tiles = W.QListView()
            self.tiles.setModel(self.model)
            self.tiles.setViewMode(W.QListView.IconMode)
            self.tiles.setResizeMode(W.QListView.Adjust)
            self.tiles.setMovement(W.QListView.Static)
            self.tiles.setIconSize(C.QSize(68,68))
            self.tiles.setStyleSheet("QListView{background:rgba(9,34,49,205);border:1px solid #25849B;} QListView::item:hover{background:rgba(0,190,230,55);} QListView::item:selected{background:rgba(0,160,210,95);border:1px solid #00E4FF;}")
            self.tiles.setGridSize(C.QSize(120,112))
            self.tiles.setWordWrap(True)
            self.tiles.setSpacing(8)
            self.tiles.doubleClicked.connect(self.open_index)
            self.tiles.setContextMenuPolicy(C.Qt.CustomContextMenu)
            self.tiles.customContextMenuRequested.connect(lambda pos:self.context_menu(self.tiles,pos))
            self.details = W.QTreeView()
            self.details.setModel(self.model)
            self.details.setAlternatingRowColors(True)
            self.details.setSortingEnabled(True)
            self.details.doubleClicked.connect(self.open_index)
            self.details.setContextMenuPolicy(C.Qt.CustomContextMenu)
            self.details.customContextMenuRequested.connect(lambda pos:self.context_menu(self.details,pos))
            self.views.addWidget(self.tiles)
            self.views.addWidget(self.details)
            right.addWidget(self.views,1)
            body.addLayout(right,1)
            outer.addLayout(body,1)
            self.setCentralWidget(root)
            self.statusBar().showMessage("NOVA Explorer prêt")
            self.effect = W.QGraphicsOpacityEffect(self.views)
            self.views.setGraphicsEffect(self.effect)
            self.fade = C.QPropertyAnimation(self.effect,b"opacity",self)
            self.fade.setDuration(190)
            self.navigate(Path(start).expanduser() if start else Path.home())

        def drag_press(self,event):
            if event.button()==C.Qt.LeftButton:
                self.drag_start=event.globalPosition().toPoint()-self.frameGeometry().topLeft()
                event.accept()
        def drag_move(self,event):
            if self.drag_start is not None and event.buttons() & C.Qt.LeftButton:
                self.move(event.globalPosition().toPoint()-self.drag_start)
                event.accept()
        def drag_release(self,event):
            self.drag_start=None
            event.accept()
        def paintEvent(self,event):
            p=G.QPainter(self)
            p.setRenderHint(G.QPainter.Antialiasing)
            w,h=self.width(),self.height()
            pts=[(26,6),(w-26,6),(w-6,26),(w-6,h-26),(w-26,h-6),(26,h-6),(6,h-26),(6,26)]
            outline=G.QPainterPath()
            outline.addPolygon(G.QPolygonF([C.QPointF(*a) for a in pts]))
            outline.closeSubpath()
            p.setClipPath(outline)
            bg=G.QLinearGradient(0,0,w,h)
            bg.setColorAt(0,G.QColor(18,52,70,220))
            bg.setColorAt(.5,G.QColor(7,24,38,226))
            bg.setColorAt(1,G.QColor(15,46,64,220))
            p.fillPath(outline,bg)
            p.setOpacity(.13)
            p.drawPixmap(C.QRect(0,0,w,h),self.pcb)
            p.setOpacity(1)
            p.setClipping(False)
            for width,alpha in ((14,20),(7,60),(2.5,215)):
                glow=G.QColor("#00CBF3")
                glow.setAlpha(alpha)
                p.setPen(G.QPen(glow,width))
                p.setBrush(C.Qt.NoBrush)
                p.drawPath(outline)
            p.end()

        def navigate(self, path, record=True):
            p = Path(path).expanduser()
            if not p.is_dir():
                W.QMessageBox.warning(self,"NOVA Explorer","Dossier inaccessible ou inexistant.")
                return
            p = p.resolve()
            self.address.setText(str(p))
            idx = self.model.index(str(p))
            self.tiles.setRootIndex(idx)
            self.details.setRootIndex(idx)
            if record:
                self.history=self.history[:self.cursor+1]+[p]
                self.cursor=len(self.history)-1
            if theme["motion"]["enabled"] and not theme["motion"]["reduce_motion"]:
                self.fade.stop()
                self.fade.setStartValue(.5)
                self.fade.setEndValue(1.0)
                self.fade.start()
            self.update_status()

        def update_status(self):
            p=Path(self.address.text())
            try:
                items=list(p.iterdir())
                folders=sum(x.is_dir() for x in items)
                self.statusBar().showMessage(f"{p.name or '/'}  —  {len(items)} éléments ({folders} dossiers, {len(items)-folders} fichiers)")
            except OSError:
                self.statusBar().showMessage(str(p)+"  —  accès limité")

        def back(self):
            if self.cursor>0:
                self.cursor-=1
                self.navigate(self.history[self.cursor],False)
        def forward(self):
            if self.cursor+1<len(self.history):
                self.cursor+=1
                self.navigate(self.history[self.cursor],False)
        def up(self):
            self.navigate(Path(self.address.text()).parent)
        def filter_files(self, text):
            # FilesystemModel name filters apply to both list and tree views.
            self.model.setNameFilters(["*"+text+"*"] if text else [])
            self.model.setNameFilterDisables(False)
        def change_view(self, icon_mode):
            self.views.setCurrentIndex(0 if icon_mode else 1)
        def selected(self):
            view=self.tiles if self.views.currentIndex()==0 else self.details
            idx=view.currentIndex()
            return Path(self.model.filePath(idx)) if idx.isValid() else None
        def open_index(self, idx):
            p=Path(self.model.filePath(idx))
            if p.is_dir():
                self.navigate(p)
            elif p.exists():
                subprocess.Popen(["xdg-open",str(p)],start_new_session=True)
        def context_menu(self,view,pos):
            idx=view.indexAt(pos)
            if not idx.isValid():
                return
            view.setCurrentIndex(idx)
            menu=W.QMenu(self)
            for title,fn in (("Ouvrir",lambda:self.open_index(idx)),("Copier",self.copy),
                             ("Couper",self.cut),("Renommer",self.rename),
                             ("Propriétés",self.properties),("Mettre à la corbeille",self.trash)):
                menu.addAction(title,fn)
            menu.exec(view.viewport().mapToGlobal(pos))
        def new_folder(self):
            name,ok=W.QInputDialog.getText(self,"NOVA / NOUVEAU DOSSIER","Nom du dossier")
            if not ok or not name or "/" in name or name in (".","..") or chr(0) in name:
                return
            try:(Path(self.address.text())/name).mkdir(exist_ok=False)
            except OSError as e:W.QMessageBox.warning(self,"NOVA",str(e))
            self.update_status()
        def rename(self):
            p=self.selected()
            if not p:return
            name,ok=W.QInputDialog.getText(self,"NOVA / RENOMMER","Nouveau nom",text=p.name)
            if not ok or not name or "/" in name or name in (".","..") or chr(0) in name:return
            dest=p.with_name(name)
            if dest.exists() or dest.is_symlink():
                W.QMessageBox.warning(self,"NOVA","La destination existe déjà.")
                return
            try:p.rename(dest)
            except OSError as e:W.QMessageBox.warning(self,"NOVA",str(e))
            self.update_status()
        def copy(self):
            p=self.selected()
            if p:self.clipboard_path=p;self.cut_mode=False
        def cut(self):
            p=self.selected()
            if p:self.clipboard_path=p;self.cut_mode=True
        def paste(self):
            source=self.clipboard_path
            if not source or not source.exists():return
            destination=Path(self.address.text())/source.name
            if destination.exists() or destination.is_symlink():
                W.QMessageBox.warning(self,"NOVA","La destination existe déjà.")
                return
            try:
                if self.cut_mode:
                    shutil.move(str(source),str(destination))
                    self.clipboard_path=None
                elif source.is_dir():
                    shutil.copytree(source,destination,symlinks=True)
                else:
                    shutil.copy2(source,destination,follow_symlinks=False)
            except (OSError,shutil.Error) as e:W.QMessageBox.warning(self,"NOVA",str(e))
            self.update_status()
        def trash(self):
            p=self.selected()
            if not p:return
            question=make_dialog("NOVA / CORBEILLE",f"Déplacer « {p.name} » vers la corbeille ?")
            if question.exec()!=W.QDialog.Accepted:return
            try:
                import gi
                gi.require_version("Gio","2.0")
                from gi.repository import Gio
                if not Gio.File.new_for_path(str(p)).trash(None):
                    raise OSError("Mise à la corbeille impossible")
            except Exception as e:W.QMessageBox.warning(self,"NOVA",str(e))
            self.update_status()
        def properties(self):
            p=self.selected()
            if not p:return
            try:
                st=p.stat()
                size=f"{st.st_size:,} octets" if p.is_file() else "Dossier"
                message=f"Nom : {p.name}\nEmplacement : {p.parent}\nTaille : {size}\nPermissions : {oct(st.st_mode & 0o777)}"
            except OSError as e:message=str(e)
            dialog=make_dialog("NOVA / PROPRIÉTÉS",message)
            dialog.exec()

    window=Explorer()
    window.show()
    return app.exec()


if __name__=="__main__":
    raise SystemExit(run(sys.argv[1] if len(sys.argv)>1 else None))
