"""User-owned notification history and stacked front-facing NOVA popups."""
from datetime import datetime, timezone
import json
from PySide6 import QtCore as C, QtWidgets as W
from healthbar.config import data_dir
from healthbar.profiles import write_json
from .theme_engine import get_active_theme,qt_stylesheet
from .chrome_v3 import make_notification


class NotificationCenter(C.QObject):
    changed=C.Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.path=data_dir()/'nova-notifications.json'
        try: state=json.loads(self.path.read_text())
        except (OSError,ValueError): state={}
        self.history=state.get('history', [])[-200:]
        self.quiet=bool(state.get('quiet',False))
        self.active={};self.next_id=1
        self.theme=get_active_theme()
        self.window=None

    def save(self):
        write_json(self.path, {'quiet':self.quiet,'history':self.history[-200:]})
        self.changed.emit()

    def notify(self,title,body,category='Info',*,actions=None,timeout=None,replace=0):
        category=category if category in ('Info','Success','Warning','Error') else 'Info'
        identifier=replace or self.next_id
        self.next_id=max(self.next_id,identifier+1)
        if replace in self.active:self.dismiss(replace)
        record={'id':identifier,'title':str(title)[:200],'body':str(body)[:4000],
                'category':category,'at':datetime.now(timezone.utc).isoformat()}
        self.history.append(record);self.history=self.history[-200:];self.save()
        if self.quiet:return identifier
        widget=make_notification(f'NOVA / {category.upper()} · {record["title"]}',record['body'],self.theme,actions=actions)
        widget.setWindowFlags(C.Qt.Tool|C.Qt.FramelessWindowHint|C.Qt.WindowStaysOnTopHint)
        widget.setAttribute(C.Qt.WA_DeleteOnClose)
        widget.destroyed.connect(lambda *_:self._removed(identifier,widget))
        self.active[identifier]=widget
        widget.show();self.reflow()
        if len(self.active)>4:self.dismiss(next(iter(self.active)))
        milliseconds=self.theme['notifications']['duration_ms'] if timeout is None or timeout<0 else timeout
        if milliseconds:
            C.QTimer.singleShot(min(30000,max(1000,int(milliseconds))),lambda:self.dismiss(identifier) if self.active.get(identifier) is widget else None)
        return identifier

    def _removed(self,identifier,widget):
        if self.active.get(identifier) is widget:self.active.pop(identifier,None)
        self.reflow()

    def dismiss(self,identifier):
        widget=self.active.pop(identifier,None)
        if widget:widget.close()
        self.reflow()

    def reflow(self):
        app=W.QApplication.instance()
        if not app or not app.primaryScreen():return
        area=app.primaryScreen().availableGeometry()
        position=self.theme['notifications']['position']
        top=position.startswith('top');right=position.endswith('right')
        y=area.top()+12 if top else area.bottom()-12
        for widget in self.active.values():
            widget.setMaximumWidth(max(220,area.width()-24))
            x=area.right()-widget.width()-12 if right else area.left()+12
            if not top:y-=widget.height()
            widget.move(x,y)
            y+=widget.height()+10 if top else -10

    def show_history(self):
        if self.window:
            self.window.show();self.window.raise_();return self.window
        window=W.QDialog();window.setWindowTitle('NOVA NEXUS HD · Notifications');window.resize(640,500)
        window.setStyleSheet(qt_stylesheet(self.theme))
        root=W.QVBoxLayout(window)
        quiet=W.QCheckBox('Mode silencieux');quiet.setChecked(self.quiet)
        quiet.toggled.connect(self.set_quiet);root.addWidget(quiet)
        position=W.QComboBox();position.addItems(['top-right','top-left','bottom-right','bottom-left'])
        position.setCurrentText(self.theme['notifications']['position'])
        position.currentTextChanged.connect(self.set_position);root.addWidget(position)
        duration=W.QSpinBox();duration.setRange(1000,30000);duration.setSuffix(' ms')
        duration.setValue(self.theme['notifications']['duration_ms'])
        duration.valueChanged.connect(self.set_duration);root.addWidget(duration)
        items=W.QListWidget();items.setWordWrap(True);root.addWidget(items,1)
        def refresh():
            items.clear()
            for entry in reversed(self.history):
                items.addItem(f'{entry["at"]} · {entry["category"]} · {entry["title"]}\n{entry["body"]}')
        self.changed.connect(refresh);refresh()
        preview=W.QPushButton('Tester une notification');preview.clicked.connect(lambda:self.notify('NOVA NEXUS HD','Centre de notifications actif.','Success'));root.addWidget(preview)
        clear=W.QPushButton('Effacer l’historique');clear.clicked.connect(self.clear);root.addWidget(clear)
        import sys
        if sys.platform.startswith('linux'):
            self.bus_status=W.QLabel('Service système actuel conservé')
            root.addWidget(self.bus_status)
            activate=W.QPushButton('Activer le service D-Bus NOVA (session)')
            deactivate=W.QPushButton('Arrêter le service D-Bus NOVA')
            from .notification_bus import NotificationBus
            self.bus=NotificationBus(self)
            self.bus.status.connect(self.bus_status.setText)
            activate.clicked.connect(self.bus.start);deactivate.clicked.connect(self.bus.stop)
            root.addWidget(activate);root.addWidget(deactivate)
            W.QApplication.instance().aboutToQuit.connect(self.bus.stop)
        self.window=window;window.show();return window

    def set_quiet(self,value):self.quiet=value;self.save()
    def clear(self):self.history=[];self.save()
    def set_position(self,value):
        self.theme['notifications']['position']=value;self.save_theme();self.reflow()
    def set_duration(self,value):
        self.theme['notifications']['duration_ms']=value;self.save_theme()
    def save_theme(self):
        from .theme_engine import set_active_theme
        set_active_theme(self.theme)


_center=None

def center():
    global _center
    if _center is None:_center=NotificationCenter(W.QApplication.instance())
    return _center
