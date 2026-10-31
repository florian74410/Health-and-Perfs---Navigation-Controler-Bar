"""CYBER NEXUS cockpit taskbar with large app icons, categorized launcher and live tray."""
import os
import shutil
import subprocess
import sys
from pathlib import Path
from PySide6.QtCore import Qt,QTimer,QRect,QRectF,QSize,QDateTime,QPoint,Signal
from PySide6.QtGui import QCursor,QIcon,QPainter,QColor,QLinearGradient,QPen
from PySide6.QtWidgets import (QWidget,QHBoxLayout,QToolButton,QPushButton,QLabel,QMenu,QScrollArea,
                               QApplication,QLayout,QSizePolicy,QSlider,QWidgetAction)
from .edge_docks import launcher_metadata,launch_item
from .desktop_backend import DesktopBackend,NativePanelGuard,x11_ready
from .overlay import apply_priority,schedule_all_workspaces
from .xfce_panel_skin import PALETTES
from .system_env import native_env
from .cockpit_style import CockpitFrame,app_icon,symbol_icon,cut_path,glow,lookup_icon
from .app_catalog import ApplicationLauncher,catalog
from .system_status import DesktopStatus
from .status_notifier import StatusNotifierHost,item_icon


def bottom_height(settings):return min(104,max(72,round(50*settings.xfce_skin_scale_percent/100)))


def applications():return [(a.path,a.name,a.icon) for a in catalog()]


def favorite_apps(settings):
    if settings.dock_app_paths is not None:return settings.dock_app_paths
    root=Path(os.getenv('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'xfce4/panel'
    paths=[str(p) for p in sorted(root.glob('launcher-*/*.desktop')) if launcher_metadata(p)]
    if not paths:
        entries=catalog()
        for wanted in ('firefox','thunar','terminal','xed'):
            found=next((a.path for a in entries if wanted in (a.name+' '+a.icon).lower()),None)
            if found:paths.append(found)
    unique=[];seen=set()
    for path in paths:
        info=launcher_metadata(Path(path))
        if info and info[0] not in seen:unique.append(path);seen.add(info[0])
    return unique


def pinned_apps(settings):return favorite_apps(settings)[:4]


class TaskButton(QToolButton):
    def __init__(self,row,icon,theme,parent=None):
        super().__init__(parent);self.row=row;self.icon=icon;self.theme=theme
        self.setToolTip(row['name']);self.setAccessibleName(row['name']);self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(128);self.setMaximumWidth(480)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        primary,secondary,_=PALETTES.get(self.theme,PALETTES['blue-neon']);active=bool(self.property('active'))
        shape=cut_path(QRectF(2,2,self.width()-4,self.height()-4),9)
        g=QLinearGradient(0,0,0,self.height());g.setColorAt(0,QColor('#226080' if active else '#122d40'));g.setColorAt(.48,QColor('#113f5b' if active else '#061723'));g.setColorAt(1,QColor('#092031'))
        p.fillPath(shape,g);p.setBrush(Qt.BrushStyle.NoBrush);glow(p,shape,primary if active or self.underMouse() else secondary,1.3)
        size=min(38,self.height()-14);self.icon.paint(p,QRect(10,(self.height()-size)//2,size,size))
        p.setPen(QColor('#f0f8ff' if active else '#c6d6e4'));font=p.font();font.setPixelSize(12);font.setBold(active);p.setFont(font)
        text=p.fontMetrics().elidedText(self.row['name'],Qt.TextElideMode.ElideRight,max(0,self.width()-size-32))
        p.drawText(QRect(20+size,0,self.width()-size-30,self.height()),Qt.AlignmentFlag.AlignVCenter,text)
        if active:p.setPen(QPen(QColor(primary),2));p.drawLine(18,self.height()-5,self.width()-18,self.height()-5)
        p.end()


class BottomDock(QWidget):
    settings_requested=Signal();quit_requested=Signal()
    def __init__(self,settings,parent=None):
        super().__init__(None,Qt.WindowType.Tool|Qt.WindowType.FramelessWindowHint|Qt.WindowType.WindowStaysOnTopHint)
        self.settings=settings;self.backend=DesktopBackend();self.native=NativePanelGuard(self.backend)
        self.collapsed=False;self.full_rect=QRect();self._task_key=None;self._active=None;self.launcher=None
        self._icon_cache={};self._pin_key=None;self._sni_rows=[];self._sni_key=None;self._closing=False
        self.status_reader=DesktopStatus();self.live_status=x11_ready();self.desktop_state=self.status_reader.value
        self.setWindowTitle('NovaBar · CYBER NEXUS · Cockpit inférieur')
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground);self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        root=QHBoxLayout(self);root.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint);root.setContentsMargins(0,0,0,0)
        self.body=CockpitFrame(settings.theme);root.addWidget(self.body)
        self.row=QHBoxLayout(self.body);self.row.setContentsMargins(23,20,23,20);self.row.setSpacing(8)
        self.launchers=QWidget();self.pins=QHBoxLayout(self.launchers);self.pins.setContentsMargins(0,0,0,0);self.pins.setSpacing(4)
        self.menu_button=QToolButton();self.menu_button.setObjectName('nexus');self.menu_button.setIcon(lookup_icon('linuxmint-logo') if not lookup_icon('linuxmint-logo').isNull() else symbol_icon('apps','#3ee5ff'));self.menu_button.setToolTip('NEXUS · Applications et favoris');self.menu_button.setAccessibleName('NEXUS · Applications')
        self.menu_button.clicked.connect(self.open_menu);self.pins.addWidget(self.menu_button);self.row.addWidget(self.launchers)
        self.tasks_area=QScrollArea();self.tasks_area.setWidgetResizable(True);self.tasks_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self.tasks_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded);self.tasks_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tasks_area.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Ignored);self.tasks_area.setMinimumSize(0,0)
        self.tasks_body=QWidget();self.tasks=QHBoxLayout(self.tasks_body);self.tasks.setContentsMargins(3,0,3,0);self.tasks.setSpacing(8);self.tasks.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.tasks_area.setWidget(self.tasks_body);self.row.addWidget(self.tasks_area,1)
        self.tray_widget=QWidget();self.tray_row=QHBoxLayout(self.tray_widget);self.tray_row.setContentsMargins(0,0,0,0);self.tray_row.setSpacing(3);self.row.addWidget(self.tray_widget)
        self.indicators={}
        for kind,tip,handler in [('network','Réseau',self.network_menu),('volume','Volume',self.volume_menu),('bluetooth','Bluetooth',lambda:self.run_first([['blueman-manager']])),
                                  ('notifications','Notifications',lambda:self.run_first([['xfce4-notifyd-config']])),('battery','Alimentation',lambda:self.run_first([['xfce4-power-manager-settings']])),
                                  ('lock','Verrouiller la session',lambda:self.run_first([['xflock4']]))]:
            button=QToolButton();button.setToolTip(tip);button.setAccessibleName(tip);button.setIcon(symbol_icon({'network':'wifi','notifications':'bell','lock':'shield'}.get(kind,kind)));button.clicked.connect(handler);self.indicators[kind]=button;self.row.addWidget(button)
        self.clock=QToolButton();self.clock.setObjectName('cockpitClock');self.clock.clicked.connect(self.open_system);self.row.addWidget(self.clock)
        self.status=self.clock  # Retain system-menu access for existing integrations.
        self.preferences=QToolButton();self.preferences.setIcon(symbol_icon('settings'));self.preferences.setToolTip('Préférences NovaBar');self.preferences.clicked.connect(self.settings_requested.emit);self.row.addWidget(self.preferences)
        self.tray=StatusNotifierHost(self);self.tray.items_changed.connect(self.update_tray);self.tray.menu_ready.connect(self.tray_menu)
        if self.live_status and os.getenv('DBUS_SESSION_BUS_ADDRESS'):self.tray.start()
        self.hide_timer=QTimer(self);self.hide_timer.setSingleShot(True);self.hide_timer.timeout.connect(self.collapse)
        self.timer=QTimer(self);self.timer.setInterval(120);self.timer.timeout.connect(self.check_pointer);self.timer.start()
        self.tasks_timer=QTimer(self);self.tasks_timer.setInterval(1000);self.tasks_timer.timeout.connect(self.refresh);self.tasks_timer.start()
        self.fx_timer=QTimer(self);self.fx_timer.setInterval(160);self.fx_timer.timeout.connect(self.animate);self.fx_timer.start()
        self.body.regions=self.housing_regions
        self.apply_settings(settings);self.refresh()
        QTimer.singleShot(0,self.refresh)

    def housing_regions(self):
        regions=[self.launchers.geometry().adjusted(-7,-7,7,7)]
        widgets=[w for w in [self.tray_widget,*self.indicators.values(),self.clock,self.preferences] if w.isVisible() and w.width()>0]
        if widgets:
            left=min(w.geometry().left() for w in widgets);right=max(w.geometry().right() for w in widgets)
            regions.append(QRect(left-7,13,right-left+15,self.height()-26))
        return regions

    def animate(self):
        if self.isVisible():self.body.phase+=.2;self.body.update()

    def apply_settings(self,settings):
        if getattr(self,'_screen',settings.screen)!=settings.screen:self.native.restore()
        self._screen=settings.screen;self.settings=settings;self.body.theme=settings.theme
        primary,secondary,_=PALETTES.get(settings.theme,PALETTES['blue-neon'])
        self.body.setStyleSheet(f'''QToolButton {{color:#e6f1fa;background:transparent;border:1px solid transparent;border-radius:6px;padding:2px;}}
            QToolButton:hover {{background:rgba(28,93,123,130);border-color:{primary};}}
            QToolButton#nexus {{background:rgba(15,44,60,180);border-color:{secondary};}}
            QToolButton#cockpitClock {{font-size:17px;color:#ecf7ff;}}
            QScrollArea,QScrollArea QWidget {{background:transparent;border:none;}}
            QScrollBar:horizontal {{background:transparent;height:4px;}} QScrollBar::handle:horizontal {{background:{secondary};min-width:25px;}}''')
        screens=QApplication.screens()
        if not screens:return
        bounds=screens[min(settings.screen,len(screens)-1)].geometry();height=bottom_height(settings)
        self.full_rect=QRect(bounds.left(),bounds.bottom()-height+1,bounds.width(),height);self.setFixedHeight(height);self.setGeometry(self.full_rect)
        key=tuple(pinned_apps(settings))
        if key!=self._pin_key:
            self._pin_key=key
            while self.pins.count()>1:
                item=self.pins.takeAt(1)
                if item.widget():item.widget().hide();item.widget().deleteLater()
            for path in key:
                info=launcher_metadata(Path(path))
                if not info:continue
                button=QToolButton();button.setIcon(app_icon(info[1]));button.setToolTip(info[0]);button.setAccessibleName(info[0]);button.clicked.connect(lambda checked=False,p=path:launch_item(p,'apps'));self.pins.addWidget(button)
        self._task_key=None
        for button in self.launchers.findChildren(QToolButton):button.setFixedSize(height-36,height-40);button.setIconSize(QSize(min(42,height-48),min(42,height-48)))
        for button in self.indicators.values():button.setFixedSize(34,height-40);button.setIconSize(QSize(27,27))
        self.preferences.setFixedSize(30,height-40);self.preferences.setIconSize(QSize(23,23));self.clock.setFixedSize(76,height-40)
        self.hide_timer.setInterval(settings.xfce_skin_delay_seconds*1000)
        if not self.collapsed:self.show()
        self.body.update()

    def expand(self):
        self.collapsed=False;self.setGeometry(self.full_rect);self.show();self.raise_();self.hide_timer.stop()
    def collapse(self):
        if QApplication.activePopupWidget() is not None or any(r.get('_menu_open') for r in self._sni_rows):self.hide_timer.start();return
        self.collapsed=True;self.hide();self.fx_timer.stop()
    def check_pointer(self):
        if not self.full_rect.isValid():return
        point=QCursor.pos()
        if self.collapsed:
            if QRect(self.full_rect.left(),self.full_rect.bottom()-9,self.full_rect.width(),10).contains(point):self.expand();self.fx_timer.start()
        elif self.geometry().contains(point) or QApplication.activePopupWidget() is not None or any(r.get('_menu_open') for r in self._sni_rows):self.hide_timer.stop()
        elif not self.hide_timer.isActive():self.hide_timer.start()

    def refresh(self):
        self.clock.setText(QDateTime.currentDateTime().toString('HH:mm'));self.clock.setToolTip(QDateTime.currentDateTime().toString('dddd dd MMMM yyyy')+'\nCliquer : système et session')
        rows,active=self.backend.snapshot();self._active=active
        key=tuple((r['id'],r['name'],r['icon']) for r in rows)+(active,self.settings.theme,self.tasks_area.viewport().width())
        if key!=self._task_key:
            self._task_key=key
            while self.tasks.count():
                item=self.tasks.takeAt(0)
                if item.widget():item.widget().hide();item.widget().deleteLater()
            live_ids={r['id'] for r in rows};self._icon_cache={k:v for k,v in self._icon_cache.items() if k in live_ids}
            for row in rows:
                if row['id'] not in self._icon_cache:
                    icon=QIcon.fromTheme(row['icon'])
                    if icon.isNull():icon=self.backend.window_icon(row['id'])
                    self._icon_cache[row['id']]=icon if not icon.isNull() else app_icon(row['icon'])
                button=TaskButton(row,self._icon_cache[row['id']],self.settings.theme);button.setFixedHeight(self.full_rect.height()-42);button.setProperty('active',row['id']==active)
                button.setFixedWidth(min(480,max(128,(self.tasks_area.viewport().width()-14)//max(1,len(rows))-8)))
                button.clicked.connect(lambda checked=False,x=row['id']:self.backend.action(x,minimize=x==self._active))
                button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu);button.customContextMenuRequested.connect(lambda pos,b=button,r=row:self.task_menu(b,r));self.tasks.addWidget(button)
            self.tasks.addStretch()
        if self.live_status:self.apply_status(self.status_reader.poll())
        else:self.apply_status(self.desktop_state)
        if self.isVisible() or self.collapsed:
            screens=QApplication.screens()
            if screens:self.native.hide(screens[min(self.settings.screen,len(screens)-1)].geometry())

    def apply_status(self,state):
        self.desktop_state=state;network=state.get('network');primary=PALETTES.get(self.settings.theme,PALETTES['blue-neon'])[0]
        network_icon='ethernet' if network and network['kind']=='ethernet' else 'wifi'
        self.indicators['network'].setIcon(symbol_icon(network_icon,'#edf7ff' if network and network['kind']!='disconnected' else '#718595'))
        self.indicators['network'].setToolTip(('Réseau · '+network['name']) if network else 'Réseau · état indisponible')
        volume=state.get('volume');muted=state.get('muted')
        self.indicators['volume'].setIcon(symbol_icon('muted' if muted else 'volume','#edf7ff' if volume is not None else '#718595'))
        self.indicators['volume'].setToolTip(f'Volume · {volume} %'+(' · muet' if muted else '') if volume is not None else 'Volume · état indisponible')
        bt=state.get('bluetooth');self.indicators['bluetooth'].setIcon(symbol_icon('bluetooth','#40aaff' if bt else '#718595'));self.indicators['bluetooth'].setToolTip('Bluetooth · '+('activé' if bt else 'désactivé' if bt is False else 'indisponible'))
        self.indicators['bluetooth'].setVisible(bt is not None or bool(shutil.which('blueman-manager')))
        battery=state.get('battery');self.indicators['battery'].setIcon(symbol_icon('battery' if battery else 'power','#f5b35b' if battery and battery['percent']<20 else '#edf7ff'))
        self.indicators['battery'].setToolTip((f"Batterie · {battery['percent']} %"+(' · secteur' if battery['plugged'] else '')) if battery else 'Alimentation secteur · aucune batterie détectée')
        # Real applets take precedence over duplicated built-in indicators.
        ids=' '.join(str(r.get('Id',''))+' '+str(r.get('Title','')) for r in self._sni_rows).lower()
        for role,markers in {'network':('nm-applet','networkmanager'),'volume':('volume','pulseaudio'),'bluetooth':('blueman',),'battery':('power-manager',)}.items():
            if any(marker in ids for marker in markers):self.indicators[role].hide()
            elif role!='bluetooth':self.indicators[role].show()
        visibility=tuple(b.isHidden() for b in self.indicators.values())
        if visibility!=getattr(self,'_visibility_key',None):
            self._visibility_key=visibility;QTimer.singleShot(0,self.refresh)

    def update_tray(self,rows):
        self._sni_rows=[r for r in rows if str(r.get('Id','')).lower() not in ('healthperfsbar','novabar')]
        while self.tray_row.count():
            item=self.tray_row.takeAt(0)
            if item.widget():item.widget().hide();item.widget().deleteLater()
        # Keep the task area readable; overflow applets remain available in an icon menu.
        for record in self._sni_rows[:4]:
            button=QToolButton();button.setIcon(item_icon(record));button.setIconSize(QSize(28,28));button.setFixedSize(34,self.full_rect.height()-40);button.setToolTip(str(record.get('Title') or record.get('Id') or 'Application'))
            button.clicked.connect(lambda checked=False,k=record['key'],b=button:self.activate_tray(k,b,False));button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu);button.customContextMenuRequested.connect(lambda pos,k=record['key'],b=button:self.activate_tray(k,b,True));self.tray_row.addWidget(button)
        if len(self._sni_rows)>4:
            more=QToolButton();more.setText('⌃');more.setFixedWidth(26);more.setToolTip('Autres icônes de notification');more.clicked.connect(self.tray_overflow);self.tray_row.addWidget(more)
        self.apply_status(self.desktop_state)
        QTimer.singleShot(0,self.refresh)

    def activate_tray(self,key,button,context):
        point=button.mapToGlobal(button.rect().center());self.tray.activate(key,point.x(),point.y(),context)
    def tray_overflow(self):
        menu=self.themed_menu()
        for r in self._sni_rows[4:]:
            menu.addAction(item_icon(r),str(r.get('Title') or r.get('Id') or 'Application'),lambda checked=False,k=r['key']:self.tray.activate(k,QCursor.pos().x(),QCursor.pos().y(),False))
        menu.exec(QCursor.pos())
    def tray_menu(self,key,layout,x,y):
        menu=self.themed_menu()
        def populate(parent,node):
            if not isinstance(node,(list,tuple)) or len(node)!=3:return
            for child in node[2]:
                if not isinstance(child,(list,tuple)) or len(child)!=3:continue
                item_id,props,children=child
                if not props.get('visible',True):continue
                if props.get('type')=='separator':parent.addSeparator();continue
                label=str(props.get('label','')).replace('_','&')
                if children:sub=parent.addMenu(label);populate(sub,child)
                else:
                    action=parent.addAction(label,lambda checked=False,i=item_id:self.tray.menu_event(key,i));action.setEnabled(props.get('enabled',True))
                    if props.get('toggle-type'):action.setCheckable(True);action.setChecked(props.get('toggle-state')==1)
                    if props.get('icon-name'):action.setIcon(app_icon(props['icon-name']))
        populate(menu,layout);self._applet_menu=menu;menu.popup(QPoint(x,y))

    def themed_menu(self):
        menu=QMenu(self);primary,secondary,_=PALETTES.get(self.settings.theme,PALETTES['blue-neon']);menu.setStyleSheet(f'QMenu {{background:#071725;color:#e9f2fa;border:1px solid {primary};padding:7px;}} QMenu::item {{padding:8px 16px;}} QMenu::item:selected {{background:#15445e;}} QMenu::item:disabled {{color:#7892a5;}}');return menu
    def task_menu(self,button,row):
        menu=self.themed_menu();menu.addAction('Activer',lambda:self.backend.action(row['id']));menu.addAction('Fermer',lambda:self.backend.action(row['id'],close=True));menu.exec(button.mapToGlobal(button.rect().topLeft()))
    def open_menu(self):
        if self.launcher:self.launcher.close();self.launcher.deleteLater()
        self.launcher=ApplicationLauncher(self.settings.theme,favorite_apps(self.settings),parent=self);self.launcher.settings_requested.connect(self.settings_requested.emit);self.launcher.quit_requested.connect(self.quit_requested.emit);self.launcher.show_above(self.menu_button)
    def network_menu(self):
        menu=self.themed_menu();state=self.desktop_state.get('network');menu.addAction(state['name'] if state else 'État réseau indisponible').setEnabled(False)
        if state:menu.addAction('Interface : '+state.get('device','—')).setEnabled(False)
        if self.desktop_state.get('vpn'):menu.addAction('Tunnel VPN actif').setEnabled(False)
        menu.addSeparator();menu.addAction('Réseaux et connexions…',lambda:self.run_first([['nm-connection-editor'],['xfce4-settings-manager']]))
        menu.exec(self.indicators['network'].mapToGlobal(QPoint(0,0)))
    def volume_menu(self):
        menu=self.themed_menu();volume=self.desktop_state.get('volume');menu.addAction(f'Volume : {volume} %' if volume is not None else 'Volume indisponible').setEnabled(False)
        slider=QSlider(Qt.Orientation.Horizontal);slider.setRange(0,100);slider.setValue(min(volume or 0,100));slider.setFixedWidth(210);slider.setEnabled(volume is not None)
        slider.sliderReleased.connect(lambda:self.run_command(['pactl','set-sink-volume','@DEFAULT_SINK@',str(slider.value())+'%']))
        widget=QWidgetAction(menu);widget.setDefaultWidget(slider);menu.addAction(widget)
        mute=menu.addAction('Réactiver le son' if self.desktop_state.get('muted') else 'Couper le son',lambda:self.run_command(['pactl','set-sink-mute','@DEFAULT_SINK@','toggle']));mute.setEnabled(volume is not None)
        menu.addSeparator();menu.addAction('Paramètres audio…',lambda:self.run_first([['pavucontrol'],['xfce4-mixer']]))
        menu.exec(self.indicators['volume'].mapToGlobal(QPoint(0,0)))
    def open_system(self):
        menu=self.themed_menu()
        for label,commands in [('Réseau',[['nm-connection-editor']]),('Volume',[['pavucontrol'],['xfce4-mixer']]),('Bluetooth',[['blueman-manager']]),('Notifications',[['xfce4-notifyd-config']]),('Alimentation',[['xfce4-power-manager-settings']]),('Paramètres système',[['xfce4-settings-manager']]),('Verrouiller',[['xflock4']]),('Session / arrêt',[['xfce4-session-logout']])]:
            command=next((c for c in commands if shutil.which(c[0])),None);action=menu.addAction(label,lambda checked=False,c=command:self.run_command(c));action.setEnabled(command is not None)
        menu.addSeparator();menu.addAction('Icônes XFCE anciennes pendant 30 s',self.native.reveal);menu.exec(self.clock.mapToGlobal(QPoint(0,0)))
    def run_first(self,commands):self.run_command(next((c for c in commands if shutil.which(c[0])),None))
    def run_command(self,command):
        if command:
            try:subprocess.Popen(command,env=native_env(),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
            except OSError:pass
    def showEvent(self,event):super().showEvent(event);apply_priority(self,True);schedule_all_workspaces(self)
    def closeEvent(self,event):
        if not self._closing:
            self._closing=True
            if self.launcher:self.launcher.close()
            self.native.restore();self.tray.stop();self.status_reader.close()
            for timer in (self.hide_timer,self.timer,self.tasks_timer,self.fx_timer):timer.stop()
        super().closeEvent(event)
