"""Blue Neon Dark Night 0.8.3 — optional paint-only layer.

Widget ownership, telemetry and hitboxes remain unchanged. Optional GIF frames
are loaded exclusively from the local per-user theme directory.
"""
from functools import lru_cache
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QColor, QPainterPath, QPen, QLinearGradient, QPixmap

THEME="blue-night-083"
BLUE="#078AFF"
CYAN="#2CE3FF"
GRAPHITE="#080D14"

def active(theme=None):
    if theme is None:
        from .ui_kit import active_theme
        theme=active_theme()
    return theme==THEME

def color(value,alpha=255):
    c=QColor(value);c.setAlpha(max(0,min(255,round(alpha))));return c

def cut_path(rect,cut=15):
    x,y,w,h=rect.x(),rect.y(),rect.width(),rect.height()
    c=max(2,min(c,h*.28,w*.15))
    coords=[(x+c,y),(x+w-c,y),(x+w,y+c),(x+w,y+h-c),
            (x+w-c,y+h),(x+c,y+h),(x,y+h-c),(x,y+c)]
    p=QPainterPath(QPointF(*coords[0]))
    for point in coords[1:]:p.lineTo(QPointF(*point))
    p.closeSubpath();return p

@lru_cache(maxsize=48)
def asset_frames(name):
    allowed={"pcb_signal","glass_shimmer","focus_corners","scanline",
             "nodes_flow","holo_radar","neon_underline","hud_reticle"}
    if name not in allowed:return ()
    from .config import data_dir
    root=data_dir()/"Themes"/THEME/"animations"/name
    manifest=root/"frames.txt"
    if not manifest.is_file():return ()
    try:
        frames=[]
        for filename in manifest.read_text(encoding="utf-8").splitlines()[:24]:
            if not filename.startswith("frame_") or not filename.endswith(".png"):return ()
            path=root/filename
            if not path.is_file() or path.stat().st_size>1024*1024:return ()
            px=QPixmap(str(path))
            if px.isNull() or px.width()>1024 or px.height()>512:return ()
            frames.append(px)
        return tuple(frames)
    except (OSError,ValueError):
        return ()

def paint_animation(p,rect,name,phase=0,opacity=.15):
    frames=asset_frames(name)
    if not frames:return False
    p.save();p.setOpacity(max(0,min(1,opacity)))
    p.drawPixmap(QRectF(rect).toRect(),frames[int((phase%1)*len(frames))])
    p.restore();return True

def paint_surface(p,rect,kind="panel",phase=0,selected=False,opacity=.87):
    r=QRectF(rect)
    if r.width()<30 or r.height()<20:return
    p.save();p.setRenderHint(p.RenderHint.Antialiasing,True)
    path=cut_path(r,7 if r.height()<90 else 17)
    p.fillPath(path,color(GRAPHITE,255*max(.42,min(1,opacity))))
    p.setClipPath(path)
    x,y,w,h=r.x(),r.y(),r.width(),r.height()
    shine=QLinearGradient(x,y,x,y+min(h*.30,65))
    shine.setColorAt(0,color("#56BFFF",55))
    shine.setColorAt(.36,color("#246CA5",18))
    shine.setColorAt(1,color("#08101B",0))
    p.fillRect(QRectF(x+3,y+3,w-6,min(h*.30,65)),shine)
    # Carbon is limited to very narrow edge trims.
    p.fillRect(QRectF(x+20,y+3,max(0,w-40),2),color("#1A2029",155))
    p.fillRect(QRectF(x+20,y+h-5,max(0,w-40),2),color("#1A2029",125))
    if w>110 and h>64:
        from .blue_graphite_fx import paint_edge_fx
        paint_edge_fx(p,r,phase,.60 if not selected else .95)
        if kind in ("holo","settings","dialog","notification"):
            paint_animation(p,QRectF(x+20,y+5,min(w-40,200),16),
                            "neon_underline",phase,.13)
        if kind=="holo":
            paint_animation(p,QRectF(x+w-100,y+19,82,30),"holo_radar",phase,.09)
    p.setClipping(False)
    p.setBrush(Qt.BrushStyle.NoBrush)
    for thickness,alpha,shade in ((6,12,BLUE),(2.5,58,BLUE),(1.1,190,CYAN),(.5,160,"#D9FBFF")):
        p.setPen(QPen(color(shade,alpha if not selected else min(255,alpha*1.2)),thickness))
        p.drawPath(path)
    p.restore()

def control_stylesheet():
    return """
    QWidget {font-family:DejaVu Sans;color:#D7EFFF;}
    QDialog {background:#080D14;}
    QDialog#novaSettings {background:transparent;}
    QLabel {background:transparent;color:#D9EFFF;}
    QLabel#title,QLabel#launcherTitle {color:#3ADFFF;font-weight:800;font-size:22px;}
    QLabel#sectionHeader,QLabel#holoTitle {color:#36DFFF;font-weight:800;}
    QWidget#generalContent,QWidget#settingsPages {background:rgba(7,13,22,227);
      border:1px solid #1267B3;border-radius:9px;}
    QListWidget#settingsNavigation {background:rgba(7,14,23,225);
      color:#D5EDFF;border:1px solid #165E9B;padding:8px;outline:none;}
    QListWidget#settingsNavigation::item {height:35px;padding:7px 9px;}
    QListWidget#settingsNavigation::item:selected {background:rgba(8,99,172,170);
      color:#FFFFFF;border-left:3px solid #28DFFF;}
    QListWidget#settingsNavigation::item:hover {background:rgba(23,86,139,110);}
    QLineEdit,QComboBox,QSpinBox,QKeySequenceEdit {background:rgba(8,22,36,236);
      color:#E8F9FF;border:1px solid #2374B3;border-radius:5px;padding:6px 9px;min-height:23px;}
    QComboBox QAbstractItemView {background:#091421;color:#E8F9FF;
      selection-background-color:#125C9D;border:1px solid #2374B3;}
    QPushButton,QToolButton {background:rgba(7,29,50,220);color:#EAF8FF;
      border:1px solid #1C7EC2;border-radius:5px;padding:6px 10px;}
    QPushButton:hover,QToolButton:hover {background:rgba(10,68,119,230);
      border-color:#38E9FF;color:white;}
    QPushButton:pressed,QToolButton:pressed {background:#075994;}
    QPushButton:disabled {color:#667E90;background:#0D1822;border-color:#263A4C;}
    QListWidget,QTreeWidget,QTableWidget {background:rgba(6,16,27,235);
      color:#D7EFFF;border:1px solid #21679E;outline:none;selection-background-color:#155892;}
    QTabWidget::pane {background:rgba(8,16,26,205);border:1px solid #205A8B;}
    QTabBar::tab {background:#0B1B2B;color:#BCD8EE;border:1px solid #285980;padding:8px 13px;}
    QTabBar::tab:selected {background:#103D67;color:white;border-bottom:2px solid #34DFFF;}
    QCheckBox {spacing:8px;color:#E3F5FF;}
    QCheckBox::indicator {background:#081E2D;border:1px solid #2B8BC6;width:16px;height:16px;}
    QCheckBox::indicator:checked {background:#078CDB;border-color:#39EAFF;}
    QScrollArea,QScrollArea QWidget,QScrollArea::viewport {background:transparent;border:0;}
    QScrollBar:vertical {width:9px;background:#081625;}
    QScrollBar::handle:vertical {background:#176FA6;min-height:26px;border-radius:4px;}
    QScrollBar:horizontal {height:8px;background:#081625;}
    QScrollBar::handle:horizontal {background:#176FA6;border-radius:4px;}
    QSlider::groove:horizontal {background:#184060;height:5px;}
    QSlider::handle:horizontal {background:#32DDFF;width:14px;margin:-5px 0;}
    QMenu {background:#0A1422;color:#EBF7FF;border:1px solid #1673B3;padding:5px;}
    QMenu::item {padding:8px 15px;}
    QMenu::item:selected {background:#135B98;}
    QToolTip {background:#0B1A2A;color:white;border:1px solid #35CDFF;}
    """
