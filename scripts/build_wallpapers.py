"""Render palette/aspect variants of the existing approved PCB vector asset."""
import json
from pathlib import Path
import zipfile
from PySide6.QtCore import QRectF
from PySide6.QtGui import QImage,QPainter,QGuiApplication
from PySide6.QtSvg import QSvgRenderer
from nova_nexus.theme_engine import PALETTES,preset


def build(destination='dist/wallpapers'):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    root=Path(__file__).resolve().parents[1]
    template=(root/'src/nova_nexus/assets/nova-electric-blue-pcb.svg').read_text()
    paths=[]
    for name,(primary,secondary) in PALETTES.items():
        slug=name.lower().replace(' ','-')
        content=template.replace('#00CBF3',primary).replace('#277FEA',secondary)
        for width,height in ((2560,1440),(3440,1440),(1920,1440)):
            image=QImage(width,height,QImage.Format_ARGB32);image.fill(0xff09111b)
            renderer=QSvgRenderer(content.encode());painter=QPainter(image)
            renderer.render(painter,QRectF(0,0,width,height));painter.end()
            path=destination/f'NOVA-{slug}-{width}x{height}.png'
            assert image.save(str(path));paths.append(path)
        path=destination/f'{slug}-theme.json';path.write_text(json.dumps(preset(name),indent=2));paths.append(path)
    archive=destination.parent/'NOVA-NEXUS-HD-Wallpapers.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as out:
        for path in paths:out.write(path,path.name)
    return archive


if __name__=='__main__':
    app=QGuiApplication([])
    print(build())
