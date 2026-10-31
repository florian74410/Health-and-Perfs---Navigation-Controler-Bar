from pathlib import Path
"""NOVA glass chassis v3: shared framed notification/dialog. No desktop takeover."""
from .theme_engine import validate_theme, get_default_theme

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
            from PySide6.QtSvg import QSvgRenderer
            asset=Path(__file__).resolve().parent.parent / "Assets/Overlays/nova_pcb_overlay.svg"
            self.overlay=G.QPixmap(640,360)
            self.overlay.fill(C.Qt.transparent)
            if asset.is_file():
                renderer=QSvgRenderer(str(asset))
                if renderer.isValid():
                    painter=G.QPainter(self.overlay)
                    renderer.render(painter)
                    painter.end()
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
            self.minbtn.setObjectName('novaMinimize')
            self.minbtn.setFixedSize(24,22)
            self.minbtn.clicked.connect(self.showMinimized)
            self.closebtn=W.QPushButton('×')
            self.closebtn.setObjectName('novaClose')
            self.closebtn.setFixedSize(24,22)
            self.closebtn.clicked.connect(self.reject if dialog else self.close)
            self.minbtn.setStyleSheet('QPushButton#novaMinimize{color:#FF526A;font:bold 17px Arial;border:1px solid #00CBF3;background:rgba(3,12,27,225);padding:0;} QPushButton#novaMinimize:hover{color:white;background:#B52D45;border-color:#FF526A;}')
            self.closebtn.setStyleSheet('QPushButton#novaClose{color:#FF526A;font:bold 18px Arial;border:1px solid #00CBF3;background:rgba(3,12,27,225);padding:0;} QPushButton#novaClose:hover{color:white;background:#B52D45;border-color:#FF526A;}')
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
            # Draw the transparent motherboard-routing asset beneath text.
            pcb=self.overlay.scaled(w,h,C.Qt.IgnoreAspectRatio,C.Qt.SmoothTransformation)
            p.save()
            p.setOpacity(min(.7,max(.1,t['effects']['pcb_visibility'])))
            p.drawPixmap(0,0,pcb)
            p.restore()
            if motion:
                # A white neon pulse is clipped to the PCB trace alpha channel.
                pulse=G.QPixmap(w,h)
                pulse.fill(C.Qt.transparent)
                pp=G.QPainter(pulse)
                for i in range(3):
                    cx=((self.phase+i/3)%1)*w
                    light=G.QLinearGradient(cx-55,0,cx+55,0)
                    light.setColorAt(0,G.QColor(255,255,255,0))
                    light.setColorAt(.5,G.QColor(255,255,255,230))
                    light.setColorAt(1,G.QColor(255,255,255,0))
                    pp.fillRect(C.QRectF(cx-55,0,110,h),light)
                pp.setCompositionMode(G.QPainter.CompositionMode_DestinationIn)
                pp.drawPixmap(0,0,pcb)
                pp.end()
                p.drawPixmap(0,0,pulse)
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
