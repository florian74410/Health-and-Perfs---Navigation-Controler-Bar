"""Autonomous CYBER NEXUS taskbar: it exists even when no XFCE panel is detected."""
import os
import shutil
import subprocess
import time
from pathlib import Path
from PySide6.QtCore import Qt,QTimer,QRect,QSize,QDateTime,Signal
from PySide6.QtGui import QCursor,QIcon
from PySide6.QtWidgets import (QWidget,QHBoxLayout,QToolButton,QPushButton,QLabel,QMenu,
                               QScrollArea,QLineEdit,QWidgetAction,QApplication,QLayout,QSizePolicy)
from .edge_docks import PCBDockFrame,launcher_metadata,launch_item,dock_stylesheet
from .desktop_backend import DesktopBackend,NativePanelGuard
from .overlay import apply_priority,schedule_all_workspaces
from .xfce_panel_skin import PALETTES
from .system_env import native_env


def bottom_height(settings):return min(80,max(40,round(28*settings.xfce_skin_scale_percent/100)))


def applications():
    roots=[Path.home()/'.local/share/applications',Path('/usr/local/share/applications'),
           Path('/usr/share/applications'),Path.home()/'.local/share/flatpak/exports/share/applications',
           Path('/var/lib/flatpak/exports/share/applications')]
    result={}
    for root in roots:
        for path in sorted(root.glob('*.desktop')):
            if path.name in result:continue
            info=launcher_metadata(path)
            if info:result[path.name]=(str(path),info[0],info[1])
    return sorted(result.values(),key=lambda r:r[1].casefold())


def pinned_apps(settings):
    if settings.dock_app_paths is not None:return settings.dock_app_paths[:10]
    root=Path(os.getenv('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'xfce4/panel'
    paths=[str(p) for p in sorted(root.glob('launcher-*/*.desktop')) if launcher_metadata(p)]
    return list(dict.fromkeys(paths))[:10]


class BottomDock(QWidget):
    settings_requested=Signal();quit_requested=Signal()
    def __init__(self,settings,parent=None):
        super().__init__(None,Qt.WindowType.Tool|Qt.WindowType.FramelessWindowHint|Qt.WindowType.WindowStaysOnTopHint)
        self.settings=settings;self.backend=DesktopBackend();self.native=NativePanelGuard(self.backend)
        self.collapsed=False;self.full_rect=QRect();self._task_key=None;self._active=None
        self.setWindowTitle('NovaBar · CYBER NEXUS · Barre inférieure')
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        root=QHBoxLayout(self);root.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint);root.setContentsMargins(0,0,0,0)
        self.body=PCBDockFrame(settings);root.addWidget(self.body)
        self.row=QHBoxLayout(self.body);self.row.setContentsMargins(15,5,15,5);self.row.setSpacing(6)
        self.menu_button=QPushButton('◈ NEXUS');self.menu_button.clicked.connect(self.open_menu);self.row.addWidget(self.menu_button)
        for path in pinned_apps(settings):
            info=launcher_metadata(Path(path))
            if not info:continue
            button=QToolButton();button.setIcon(QIcon.fromTheme(info[1]));button.setIconSize(QSize(26,26));button.setToolTip(info[0])
            button.clicked.connect(lambda checked=False,p=path:launch_item(p,'apps'));self.row.addWidget(button)
        self.tasks_area=QScrollArea();self.tasks_area.setWidgetResizable(True);self.tasks_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self.tasks_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tasks_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tasks_body=QWidget();self.tasks=QHBoxLayout(self.tasks_body);self.tasks.setContentsMargins(0,0,0,0);self.tasks.setSpacing(4)
        self.tasks_area.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Ignored)
        self.tasks_area.setMinimumSize(0,0)
        self.tasks_area.setWidget(self.tasks_body);self.row.addWidget(self.tasks_area,1)
        self.status=QPushButton('▦ Système');self.status.clicked.connect(self.open_system);self.row.addWidget(self.status)
        self.clock=QLabel();self.row.addWidget(self.clock)
        self.preferences=QToolButton();self.preferences.setText('⚙');self.preferences.clicked.connect(self.settings_requested.emit);self.row.addWidget(self.preferences)
        self.hide_timer=QTimer(self);self.hide_timer.setSingleShot(True);self.hide_timer.timeout.connect(self.collapse)
        self.timer=QTimer(self);self.timer.setInterval(120);self.timer.timeout.connect(self.check_pointer);self.timer.start()
        self.tasks_timer=QTimer(self);self.tasks_timer.setInterval(1000);self.tasks_timer.timeout.connect(self.refresh);self.tasks_timer.start()
        self.apply_settings(settings);self.refresh()

    def apply_settings(self,settings):
        if getattr(self,"_screen",settings.screen)!=settings.screen:self.native.restore()
        self._screen=settings.screen
        self.settings=settings;self.body.settings=settings
        primary,secondary,_rgb=PALETTES.get(settings.theme,PALETTES["blue-neon"])
        self.body.setStyleSheet(dock_stylesheet(settings.theme)+'''
          QToolButton,QPushButton {color:#e8f2fc;background:rgba(5,20,34,210);border:1px solid #1765bc;padding:4px;}
          QToolButton:hover,QPushButton:hover {border-color:#18dfff;background:#143a52;}
          QScrollArea,QScrollArea QWidget {background:transparent;border:none;}
          QToolButton[active="true"] {border-bottom:3px solid #18dfff;background:#15384d;}
        '''.replace('#18dfff',primary).replace('#1765bc',secondary))
        screens=QApplication.screens()
        if not screens:return
        bounds=screens[min(settings.screen,len(screens)-1)].geometry();height=bottom_height(settings)
        self.full_rect=QRect(bounds.left(),bounds.bottom()-height+1,bounds.width(),height)
        self.setFixedHeight(height)
        for button in self.body.findChildren(QPushButton)+self.body.findChildren(QToolButton):button.setFixedHeight(height-12)
        self.setGeometry(self.full_rect);self.hide_timer.setInterval(settings.xfce_skin_delay_seconds*1000)
        if not self.collapsed:self.show()
        self.body.update()

    def expand(self):
        self.collapsed=False;self.setGeometry(self.full_rect);self.show();self.raise_();self.hide_timer.stop()

    def collapse(self):
        if QApplication.activePopupWidget() is not None:self.hide_timer.start();return
        self.collapsed=True;self.hide()

    def check_pointer(self):
        if not self.full_rect.isValid():return
        point=QCursor.pos()
        if self.collapsed:
            if QRect(self.full_rect.left(),self.full_rect.bottom()-9,self.full_rect.width(),10).contains(point):self.expand()
        elif self.geometry().contains(point) or QApplication.activePopupWidget() is not None:self.hide_timer.stop()
        elif not self.hide_timer.isActive():self.hide_timer.start()

    def refresh(self):
        self.clock.setText(QDateTime.currentDateTime().toString('HH:mm  dd/MM'))
        rows,active=self.backend.snapshot();self._active=active
        key=tuple((r['id'],r['name'],r['icon']) for r in rows)+(active,)
        if key!=self._task_key:
            self._task_key=key
            while self.tasks.count():
                item=self.tasks.takeAt(0)
                if item.widget():item.widget().deleteLater()
            for row in rows:
                button=QToolButton();ico=QIcon.fromTheme(row['icon'])
                if ico.isNull():ico=QIcon.fromTheme('application-x-executable')
                button.setIcon(ico)
                if ico.isNull():button.setText(row['name'][:2].upper())
                button.setIconSize(QSize(28,28));button.setToolTip(row['name']);button.setFixedSize(40,self.full_rect.height()-12)
                button.setProperty('active',row['id']==active)
                button.clicked.connect(lambda checked=False,x=row['id']:self.backend.action(x,minimize=x==self._active))
                button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                button.customContextMenuRequested.connect(lambda pos,b=button,r=row:self.task_menu(b,r))
                self.tasks.addWidget(button)
            self.tasks.addStretch()
        if self.isVisible() or self.collapsed:
            screens=QApplication.screens()
            if screens:self.native.hide(screens[min(self.settings.screen,len(screens)-1)].geometry())

    def task_menu(self,button,row):
        menu=QMenu(self);menu.addAction('Activer',lambda:self.backend.action(row['id']))
        menu.addAction('Fermer',lambda:self.backend.action(row['id'],close=True))
        menu.exec(button.mapToGlobal(button.rect().topLeft()))

    def open_menu(self):
        menu=QMenu(self);search=QLineEdit();search.setPlaceholderText('Rechercher une application…')
        widget=QWidgetAction(menu);widget.setDefaultWidget(search);menu.addAction(widget)
        actions=[]
        for path,name,icon in applications():
            action=menu.addAction(QIcon.fromTheme(icon),name,lambda checked=False,p=path:launch_item(p,'apps'));actions.append(action)
        search.textChanged.connect(lambda text:[a.setVisible(text.casefold() in a.text().casefold()) for a in actions])
        menu.addSeparator();menu.addAction('Préférences NovaBar',self.settings_requested.emit)
        menu.addAction('Quitter NovaBar et restaurer XFCE',self.quit_requested.emit)
        menu.exec(self.menu_button.mapToGlobal(self.menu_button.rect().topLeft()))

    def open_system(self):
        menu=QMenu(self)
        for label,commands in [('Réseau',[['nm-connection-editor']]),('Volume',[['pavucontrol'],['xfce4-mixer']]),
                               ('Bluetooth',[['blueman-manager']]),('Notifications',[['xfce4-notifyd-config']]),
                               ('Paramètres système',[['xfce4-settings-manager']]),('Verrouiller',[['xflock4']]),
                               ('Session / arrêt',[['xfce4-session-logout']])]:
            command=next((c for c in commands if shutil.which(c[0])),None)
            action=menu.addAction(label,lambda checked=False,c=command:self.run_command(c));action.setEnabled(command is not None)
        menu.addSeparator();menu.addAction('Afficher les icônes XFCE pendant 30 s',self.native.reveal)
        menu.exec(self.status.mapToGlobal(self.status.rect().topLeft()))

    def run_command(self,command):
        if command:
            try:subprocess.Popen(command,env=native_env(),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
            except OSError:pass

    def showEvent(self,event):
        super().showEvent(event);apply_priority(self,True);schedule_all_workspaces(self)

    def closeEvent(self,event):
        self.native.restore();self.hide_timer.stop();self.timer.stop();self.tasks_timer.stop();super().closeEvent(event)
