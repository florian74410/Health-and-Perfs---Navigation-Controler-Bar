"""NOVA glass chassis v3: shared framed notification/dialog. No desktop takeover."""
from .theme_engine import validate_theme, get_default_theme

def routes(w,h):
    """Twelve disjoint PCB traces, 45-degree bends and regular 12px spacing.

    Three parallel, unfilled traces live in each corner. The repeated step
    geometry resembles PCB meander routing; no intersections or triangles.
    """
    tracks=[]
    for offset in (0,12,24):
        y=52+offset
        left=[(30,y),(48,y),(57,y-9),(78,y-9),
              (87,y),(105,y),(114,y-9),(135,y-9),
              (144,y),(172,y)]
        tracks.extend([
            left,
            [(w-x,yy) for x,yy in left],
            [(x,h-yy) for x,yy in left],
            [(w-x,h-yy) for x,yy in left],
        ])
    return tracks


def _panel(title, message, theme=None, actions=None, dialog=False, dangerous=False):
    from PySide6 import QtCore as C, QtGui as G, QtWidgets as W
    t=validate_theme(theme if theme is not None else get_default_theme())
    accent=G.QColor(t['colors']['primary'])
    motion=t['motion']['enabled'] and not t['motion']['reduce_motion']
    class Chrome(W.QDialog if dialog else W.QWidget):
        def __init__(self):
            super().__init__()
            self.setWindowFlags((C.Qt.Dialog if dialog else C.Qt.Tool)|C.Qt.FramelessWindowHint)
            self.setAttribute(C.Qt.WA_TranslucentBackground,True)
            self.setWindowTitle(title)
            self.setMinimumSize(500 if dialog else 460,235 if dialog else 195)
            self.resize(520 if dialog else 480,240 if dialog else 200)
            self.phase=0.0
            self.drag_origin=None
            self.timer=C.QTimer(self)
            self.timer.setInterval(33)
            self.timer.timeout.connect(self.advance)
            self.setStyleSheet('QLabel{background:transparent;border:none;color:%s;font:12px Arial;}'
                'QPushButton{background:rgba(3,21,35,220);color:%s;border:1px solid %s;'
                'border-radius:0px;padding:5px 11px;font:bold 11px Arial;}'
                'QPushButton:hover{background:%s;color:#03121c;}' %
                (t['colors']['text'],t['colors']['text'],t['colors']['primary'],t['colors']['primary']))
            root=W.QVBoxLayout(self)
            root.setContentsMargins(23,14,23,20)
            root.setSpacing(5)
            self.bar=W.QWidget()
            self.bar.setFixedHeight(28)
            self.bar.setObjectName('novaTitleBar')
            self.bar.setStyleSheet('QWidget#novaTitleBar{background:rgba(3,12,27,220);}')
            top=W.QHBoxLayout(self.bar)
            top.setContentsMargins(10,1,3,1)
            top.setSpacing(4)
            self.caption=W.QLabel(title)
            self.caption.setStyleSheet('color:%s;font:bold 11px Arial;' % t['colors']['primary'])
            top.addWidget(self.caption,1)
            self.minbtn=W.QPushButton('−')
            self.minbtn.setFixedSize(24,22)
            self.minbtn.clicked.connect(self.showMinimized)
            self.closebtn=W.QPushButton('×')
            self.closebtn.setFixedSize(24,22)
            self.closebtn.clicked.connect(self.reject if dialog else self.close)
            top.addWidget(self.minbtn)
            top.addWidget(self.closebtn)
            root.addWidget(self.bar)
            root.addStretch()
            body=W.QLabel(message)
            body.setTextFormat(C.Qt.PlainText)
            body.setAlignment(C.Qt.AlignCenter)
            body.setWordWrap(True)
            root.addWidget(body,2)
            row=W.QHBoxLayout()
            row.addStretch()
            for label, callback in (actions or []):
                btn=W.QPushButton(str(label))
                btn.clicked.connect(callback)
                row.addWidget(btn)
            row.addStretch()
            root.addLayout(row)
            root.addStretch()
            for area in (self.bar,self.caption):
                area.mousePressEvent=self.drag_start
                area.mouseMoveEvent=self.drag_move
                area.mouseReleaseEvent=self.drag_end
        def drag_start(self,event):
            if event.button()==C.Qt.LeftButton:
                self.drag_origin=event.globalPosition().toPoint()-self.frameGeometry().topLeft()
                event.accept()
        def drag_move(self,event):
            if self.drag_origin is not None and event.buttons() & C.Qt.LeftButton:
                self.move(event.globalPosition().toPoint()-self.drag_origin)
                event.accept()
        def drag_end(self,event):
            self.drag_origin=None
            event.accept()
        def advance(self):
            self.phase=(self.phase+.008)%1
            self.update()
        def showEvent(self,event):
            super().showEvent(event)
            if motion:self.timer.start()
        def hideEvent(self,event):
            self.timer.stop()
            super().hideEvent(event)
        def keyPressEvent(self,event):
            if event.key()==C.Qt.Key_Escape:
                self.reject() if dialog else self.close()
            else:super().keyPressEvent(event)
        def paintEvent(self,event):
            p=G.QPainter(self)
            p.setRenderHint(G.QPainter.Antialiasing)
            w,h=self.width(),self.height()
            cut=t['effects']['bevel_size']+9
            corners=[(6+cut,6),(w-6-cut,6),(w-6,6+cut),(w-6,h-6-cut),
                     (w-6-cut,h-6),(6+cut,h-6),(6,h-6-cut),(6,6+cut)]
            path=G.QPainterPath()
            path.addPolygon(G.QPolygonF([C.QPointF(*a) for a in corners]))
            path.closeSubpath()
            p.setClipPath(path)
            bg=G.QLinearGradient(0,0,w,h)
            for at,rgb in [(0,(12,40,58,215)),(.55,(5,19,31,238)),(1,(12,40,58,215))]:
                r,g,b,a=rgb
                bg.setColorAt(at,G.QColor(r,g,b,int(a*t['effects']['opacity'])))
            p.fillPath(path,bg)
            x=w*self.phase
            shine=G.QLinearGradient(x-100,0,x+110,h)
            shine.setColorAt(0,G.QColor(240,250,255,0))
            shine.setColorAt(.5,G.QColor(220,250,255,65 if motion else 30))
            shine.setColorAt(1,G.QColor(240,250,255,0))
            p.fillPath(path,shine)
            p.setClipping(False)
            intensity=t['effects']['glow']
            for width,alpha in ((17,20),(10,45),(6,85),(2.4,245)):
                color=G.QColor(accent)
                color.setAlpha(int(alpha*intensity))
                p.setPen(G.QPen(color,width,C.Qt.SolidLine,C.Qt.RoundCap,C.Qt.RoundJoin))
                p.setBrush(C.Qt.NoBrush)
                p.drawPath(path)
            for n,vertices in enumerate(routes(w,h)):
                trace=G.QPainterPath(C.QPointF(*vertices[0]))
                for vertex in vertices[1:]:trace.lineTo(C.QPointF(*vertex))
                dim=G.QColor(accent)
                dim.setAlpha(int(105+140*t['effects']['pcb_visibility']))
                p.setPen(G.QPen(dim,1.7,C.Qt.SolidLine,C.Qt.RoundCap,C.Qt.RoundJoin))
                p.drawPath(trace)
                for point in (vertices[0],vertices[-1]):
                    center=C.QPointF(*point)
                    p.setPen(G.QPen(dim,1))
                    p.setBrush(G.QColor(4,25,40,230))
                    p.drawEllipse(center,3.7,3.7)
                    p.setPen(C.Qt.NoPen)
                    p.setBrush(accent)
                    p.drawEllipse(center,1.4,1.4)
                if motion:
                    pos=trace.pointAtPercent((self.phase+n*.127)%1)
                    for radius,alpha in ((5,16),(3,70),(1.5,230)):
                        color=G.QColor(accent)
                        color.setAlpha(int(alpha*intensity))
                        p.setPen(C.Qt.NoPen)
                        p.setBrush(color)
                        p.drawEllipse(pos,radius,radius)
            p.end()
    panel=Chrome()
    if dialog:
        # Insert buttons before final stretch; real Qt dialog result (accepted/rejected).
        row=panel.layout().itemAt(panel.layout().count()-2).layout()
        for label,action in [('ANNULER',panel.reject),
                             ('CONFIRMER' if dangerous else 'VALIDER',panel.accept)]:
            btn=W.QPushButton(label)
            btn.clicked.connect(action)
            row.insertWidget(row.count()-1,btn)
    return panel

def make_notification(title,message,theme=None,*,actions=None):
    return _panel(title,message,theme,actions=actions,dialog=False)

def make_dialog(title,message,theme=None,*,dangerous=False):
    return _panel(title,message,theme,dialog=True,dangerous=dangerous)
