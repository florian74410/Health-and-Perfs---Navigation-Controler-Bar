"""BlackRed hardware/PCB surfaces; original geometry, not a blue hue filter.

All painting is clipped to the same beveled silhouette; no opaque rectangles
or imagery can bleed into transparent corners on light XFCE backgrounds.
"""
from __future__ import annotations
from functools import lru_cache
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainterPath, QPen
from PySide6.QtSvg import QSvgRenderer
from .theme_packs import asset_path

RED = "#FF2945"
HOT = "#FF6374"
DEEP = "#080609"
MID = "#1B0910"
STEEL = "#464147"

def is_blackred(theme=None):
    if theme is None:
        from .ui_kit import active_theme
        theme = active_theme()
    return isinstance(theme, str) and theme.startswith("blackred-")

def beveled(rect, cut=16):
    c = min(float(cut), rect.width()/7, rect.height()/4)
    path = QPainterPath(QPointF(rect.left()+c, rect.top()))
    for x,y in (
        (rect.right()-c,rect.top()), (rect.right(),rect.top()+c),
        (rect.right(),rect.bottom()-c), (rect.right()-c,rect.bottom()),
        (rect.left()+c,rect.bottom()), (rect.left(),rect.bottom()-c),
        (rect.left(),rect.top()+c)):
        path.lineTo(x,y)
    path.closeSubpath()
    return path

def _line(p, points, color, width=1.0, alpha=255):
    path=QPainterPath(QPointF(*points[0]))
    for pair in points[1:]:
        path.lineTo(QPointF(*pair))
    ink=QColor(color); ink.setAlpha(alpha)
    p.setPen(QPen(ink,width)); p.setBrush(Qt.BrushStyle.NoBrush);p.drawPath(path)

def _stroke(p, path, color, width=1.4):
    for spread,alpha in ((7,16),(4,42),(1,140),(0,250)):
        ink=QColor(color); ink.setAlpha(alpha)
        p.setPen(QPen(ink,width+spread));p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

@lru_cache(maxsize=12)
def _svg(filename):
    return QSvgRenderer(filename)

def _texture(p,theme,role,rect,opacity):
    file=asset_path(theme,role)
    if not file or file.suffix.lower()!=".svg":
        return
    renderer=_svg(str(file))
    if renderer.isValid():
        p.save();p.setOpacity(opacity);renderer.render(p,rect);p.restore()

def paint_holo(p,widget):
    """PCB armored Holo frame + separate solid central readout cavity."""
    w,h=widget.width(),widget.height()
    if w<130 or h<110:return
    outer=QRectF(8,8,w-16,h-16)
    body=beveled(outer,19)
    p.save()
    p.setRenderHint(p.RenderHint.Antialiasing,True)
    p.setCompositionMode(p.CompositionMode.CompositionMode_Clear)
    p.fillRect(widget.rect(),Qt.GlobalColor.transparent)
    p.setCompositionMode(p.CompositionMode.CompositionMode_SourceOver)
    shell=QLinearGradient(0,outer.top(),0,outer.bottom())
    for t,color in ((0,"#494146"),(.07,"#12060B"),(.16,"#08070A"),(.86,"#0B080B"),(.94,"#301017"),(1,"#534049")):
        shell.setColorAt(t,QColor(color))
    p.fillPath(body,shell)
    p.save();p.setClipPath(body)
    header=QRectF(outer.left()+5,outer.top()+4,outer.width()-10,40)
    accent=QLinearGradient(header.left(),header.top(),header.right(),header.bottom())
    accent.setColorAt(0,QColor(75,5,18,240))
    accent.setColorAt(.45,QColor(20,3,8,245))
    accent.setColorAt(1,QColor(54,5,15,240))
    p.fillRect(header,accent)
    cavity=QRectF(outer.left()+12,outer.top()+53,outer.width()-24,outer.height()-68)
    p.fillPath(beveled(cavity,10),QColor(6,5,8,252))
    p.setPen(QPen(QColor(98,18,30,205),1.1));p.drawPath(beveled(cavity,10))
    # Beveled metal shoulder and glints never extend beyond the body.
    _line(p,[(outer.left()+20,outer.top()+46),(outer.right()-20,outer.top()+46)],RED,1,200)
    _line(p,[(outer.left()+23,outer.bottom()-10),(outer.right()-34,outer.bottom()-10)],"#B01A30",1,180)
    theme=None
    from .ui_kit import active_theme
    theme=active_theme()
    _texture(p,theme,"pcb",QRectF(outer),.10)
    # Curated PCB routes run through rails only; do not cover data rows.
    L,T,R,B=outer.left(),outer.top(),outer.right(),outer.bottom()
    traces=(
      [(L+7,T+72),(L+17,T+72),(L+25,T+64),(L+42,T+64)],
      [(R-7,T+79),(R-18,T+79),(R-31,T+66),(R-61,T+66)],
      [(L+8,B-66),(L+17,B-66),(L+32,B-51),(L+51,B-51)],
      [(R-8,B-61),(R-20,B-61),(R-36,B-45),(R-56,B-45)]
    )
    for i,route in enumerate(traces):
        _line(p,route,RED,1.15,120 if i%2 else 190)
        pos=QPointF(*route[-1]);p.setPen(QPen(QColor(255,79,101,190),1))
        p.setBrush(QColor(255,42,62,190));p.drawEllipse(pos,2.5,2.5)
    # Printed micro-dashes above right header / below footer.
    for i in range(4):
        x=R-70+i*9
        _line(p,[(x,T+11),(x+5,T+11)],HOT,2,240)
    p.restore()
    _stroke(p,body,RED,1.25)
    inner=beveled(outer.adjusted(5,5,-5,-5),15)
    p.setPen(QPen(QColor("#6F2632"),.8));p.drawPath(inner)
    # Real chrome corner joints / red electric light wells.
    for cx,cy in ((outer.left()+22,outer.top()+2),(outer.right()-28,outer.bottom()-2)):
        p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor(255,32,57,240))
        p.drawRoundedRect(QRectF(cx,cy-1,23,3),1,1)
    p.restore()

def paint_cockpit(p,widget):
    """Distinct BlackRed mechanical casing, with hard-edged metallic panels."""
    w,h=widget.width(),widget.height()
    if w<45 or h<25:return
    rect=QRectF(2,2,w-4,h-4)
    outline=beveled(rect,min(18,h*.19))
    p.save();p.setRenderHint(p.RenderHint.Antialiasing,True)
    p.setCompositionMode(p.CompositionMode.CompositionMode_Clear)
    p.fillRect(widget.rect(),Qt.GlobalColor.transparent)
    p.setCompositionMode(p.CompositionMode.CompositionMode_SourceOver)
    metal=QLinearGradient(0,rect.top(),0,rect.bottom())
    for t,c in ((0,"#6B5960"),(.06,"#11070B"),(.32,"#1E0A12"),(.68,"#070507"),(.94,"#350B17"),(1,"#4C4146")):
        metal.setColorAt(t,QColor(c))
    p.fillPath(outline,metal)
    p.save();p.setClipPath(outline)
    fill=beveled(rect.adjusted(8,8,-8,-8),max(3,min(11,h*.12)))
    p.fillPath(fill,QColor(4,4,7,max(215,min(250,round(255*max(.75,widget.glass_opacity/100))))))
    p.setPen(QPen(QColor(107,24,38,170),1));p.drawPath(fill)
    from .ui_kit import active_theme
    _texture(p,active_theme(),"frame",rect,.14)
    edge=rect.top()+6
    for i,x in enumerate(range(30,max(31,w-42),96)):
        top=edge+1
        _line(p,[(x,top),(x+15,top),(x+26,top+5),(x+62,top+5)], RED,.9,150)
        _line(p,[(x,rect.bottom()-7),(x+25,rect.bottom()-7),(x+32,rect.bottom()-12),(x+74,rect.bottom()-12)],"#C01530",.8,145)
    p.restore()
    _stroke(p,outline,RED,1.0)
    p.setPen(QPen(QColor(247,138,146,130),.7))
    p.drawPath(beveled(rect.adjusted(5,5,-5,-5),10))
    p.restore()

def paint_button(p,widget):
    """Hex-machined action key, with inset face and micro-circuit indicator."""
    w,h=widget.width(),widget.height()
    if w<15 or h<15:return
    rect=QRectF(1.4,1.4,w-2.8,h-2.8)
    outer=beveled(rect,min(11,h*.27))
    hover=widget.underMouse()
    pressed=widget.isDown()
    p.save();p.setRenderHint(p.RenderHint.Antialiasing,True)
    p.setCompositionMode(p.CompositionMode.CompositionMode_Clear)
    p.fillRect(widget.rect(),Qt.GlobalColor.transparent)
    p.setCompositionMode(p.CompositionMode.CompositionMode_SourceOver)
    gradient=QLinearGradient(0,0,0,h)
    gradient.setColorAt(0,QColor("#5D0C1A" if hover or pressed else "#3B2027"))
    gradient.setColorAt(.25,QColor("#1D080E"))
    gradient.setColorAt(.75,QColor("#080508"))
    gradient.setColorAt(1,QColor("#3B0A16"))
    p.fillPath(outer,gradient)
    _stroke(p,outer,HOT if hover else RED,1.0)
    p.save();p.setClipPath(outer)
    _line(p,[(rect.left()+12,rect.top()+5),(rect.right()-14,rect.top()+5)],"#F86A75",.8,110)
    _line(p,[(rect.right()-19,rect.bottom()-5),(rect.right()-8,rect.bottom()-5)],RED,2,230)
    p.restore();p.restore()

def holo_stylesheet():
    """BlackRed Holo widgets are distinct physical components, not recolored QSS."""
    return """
    QWidget#cpuHolo {background:transparent; border:0;}
    QLabel {color:#F1E8E9;background:transparent;border:0;font-family:Sans;}
    QLabel#holoTitle {color:#FF4B61;font-weight:900;font-size:15px;letter-spacing:1px;}
    QLabel#holoSubtitle {color:#C4A6AC;font-size:11px;font-weight:600;}
    QLabel#holoHeading {color:#E8CED2;font-size:12px;font-weight:700;padding:4px 3px;}
    QLabel#holoValue {color:#FFFFFF;font-size:12px;font-weight:800;padding:4px 3px;}
    QLabel#holoGroup {background:#340A15;color:#FF6374;font-size:12px;
      font-weight:900;padding:6px 8px;border-left:3px solid #FF2945;}
    QLabel#holoFoot {color:#B29BA1;font-size:10px;padding:2px;}
    QPushButton {background:#19090E;color:#FFC8D0;border:1px solid #BD1735;
      padding:4px 8px;font-weight:800;}
    QPushButton:hover {background:#5E0C20;color:#FFFFFF;border:1px solid #FF6374;}
    QPushButton:checked {background:#650F25;border:1px solid #FF344E;}
    QPushButton#novaClose {background:#4F0917;color:#FFD5DA;border:1px solid #FF2945;}
    QPushButton#novaClose:hover {background:#A10D2A;color:white;}
    QScrollArea#novaDataScroll {background:#070507;border:1px solid #791728;
      border-radius:1px;}
    QScrollArea#novaDataScroll QWidget {background:transparent;border:0;}
    QScrollArea#novaDataScroll QWidget#novaDataWidget {background:transparent;border:0;}
    QScrollArea#novaDataScroll QScrollBar:vertical {background:#17070B;width:8px;}
    QScrollArea#novaDataScroll QScrollBar::handle:vertical {background:#A91831;
      border:1px solid #F34258;min-height:25px;}
    QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {height:0px;}
    """
