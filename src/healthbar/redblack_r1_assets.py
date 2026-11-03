"""NOVA REDBLACK R1 asset compositor.

The assets are genuine alpha PNG slices extracted from the user's theme boards.
Only presentation changes: controls remain real Qt widgets wired to NovaBar.

No filesystem access except the sandboxed per-user Themes/redblack-r1 directory.
No timers are introduced: pre-existing repaint cycles drive light motion.
"""
from __future__ import annotations
from functools import lru_cache
import json
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPixmap

PACK_ID = "redblack-r1"
ROLES = {
    "settings": "window-chrome.png",
    "holo": "window-chrome.png",
    "notification": "panel-chrome.png",
    "dock": "panel-chrome.png",
    "catalog": "panel-chrome.png",
    "hud": "card-chrome.png",
    "task": "tile-chrome.png",
    "button": "button-chrome.png",
}
LIMIT = 4 * 1024 * 1024
EXPECTED = {
    "window-chrome.png": (45, 35, 45, 35),
    "panel-chrome.png": (40, 34, 40, 34),
    "button-chrome.png": (32, 24, 32, 24),
    "button-secondary.png": (32, 24, 32, 24),
    "card-chrome.png": (25, 22, 25, 22),
    "card-metal.png": (25, 22, 25, 22),
    "tile-chrome.png": (25, 22, 25, 22),
    "toggle-frame.png": (20, 12, 20, 12),
}

def asset_root():
    from .config import data_dir
    return data_dir() / "Themes" / PACK_ID

@lru_cache(maxsize=1)
def _manifest():
    root=asset_root()
    path=root/"manifest.json"
    try:
        if root.is_symlink() or path.is_symlink() or path.stat().st_size>4096:
            return None
        data=json.loads(path.read_text(encoding="utf-8"))
        if data.get("id") != PACK_ID or not isinstance(data.get("slices"),dict):
            return None
        return data
    except (OSError, ValueError, TypeError, UnicodeError):
        return None

@lru_cache(maxsize=16)
def _image(name):
    if name not in EXPECTED or _manifest() is None:
        return QPixmap()
    path=asset_root()/name
    try:
        path.resolve(strict=True).relative_to(asset_root().resolve(strict=True))
        if path.is_symlink() or path.stat().st_size>LIMIT:
            return QPixmap()
    except (OSError,ValueError):
        return QPixmap()
    image=QPixmap(str(path))
    if image.isNull() or not image.hasAlphaChannel():
        return QPixmap()
    return image

def installed():
    return _manifest() is not None and not _image("window-chrome.png").isNull()

def reset_cache():
    _manifest.cache_clear()
    _image.cache_clear()

def _sections(length,lo,hi):
    """Source or destination coordinates with corners never exceeding bounds."""
    scale=min(1.,length/max(1.,lo+hi))
    near=lo*scale
    far=hi*scale
    return (0.,near,max(near,length-far),float(length))

def paint_nine_slice(painter,filename,dest):
    """Nine-slice drawing retains crisp beveled corners at any UI size."""
    if filename not in EXPECTED or dest.width()<=0 or dest.height()<=0:
        return False
    image=_image(filename)
    if image.isNull():
        return False
    left,top,right,bottom=EXPECTED[filename]
    sw,sh=image.width(),image.height()
    if sw<=left+right or sh<=top+bottom:
        return False
    source_x=(0,left,sw-right,sw)
    source_y=(0,top,sh-bottom,sh)
    dest_x=_sections(dest.width(),left,right)
    dest_y=_sections(dest.height(),top,bottom)
    painter.save()
    painter.setRenderHint(painter.RenderHint.SmoothPixmapTransform,True)
    for y in range(3):
        for x in range(3):
            src=QRectF(source_x[x],source_y[y],
                       source_x[x+1]-source_x[x],source_y[y+1]-source_y[y])
            target=QRectF(dest.x()+dest_x[x],dest.y()+dest_y[y],
                          dest_x[x+1]-dest_x[x],dest_y[y+1]-dest_y[y])
            if target.width()>0 and target.height()>0:
                painter.drawPixmap(target,image,src)
    painter.restore()
    return True

def paint_asset_layer(painter,kind,rect,phase=0,selected=False):
    """Draw actual artwork and a low-cost moving light over its upper rail."""
    filename=ROLES.get(kind)
    if not filename or not paint_nine_slice(painter,filename,rect):
        return False
    painter.save()
    if selected and kind in ("hud","task","button"):
        from PySide6.QtGui import QColor, QPen
        painter.setPen(QPen(QColor(255,87,113,180),1.5))
        painter.drawLine(rect.left()+24,rect.top()+3,rect.right()-24,rect.top()+3)
    # Light effect uses parent widgets' existing animation phases.
    if rect.width()>100 and phase:
        from PySide6.QtGui import QColor, QLinearGradient
        pos=rect.left()+18+(rect.width()-36)*(phase%1)
        light=QLinearGradient(pos-25,rect.top()+5,pos+25,rect.top()+5)
        light.setColorAt(0,QColor(255,38,64,0))
        light.setColorAt(.5,QColor(255,230,232,200))
        light.setColorAt(1,QColor(255,38,64,0))
        painter.fillRect(QRectF(pos-25,rect.top()+4,50,2),light)
    painter.restore()
    return True
