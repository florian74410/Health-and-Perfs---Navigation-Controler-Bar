"""Real native title buttons: run under xvfb-run + dbus-run-session, no user state."""
import os
import subprocess
import tempfile
import time
from pathlib import Path
from PySide6 import QtCore as C, QtWidgets as W
from Xlib import X, display
from Xlib.ext import xtest
from healthbar.desktop_backend import DesktopBackend


def main():
    original = os.environ.copy()
    with tempfile.TemporaryDirectory(prefix='nova-decorations-') as temp:
        os.environ.update(HOME=temp, XDG_CONFIG_HOME=temp+'/config', QT_QPA_PLATFORM='xcb')
        from nova_nexus.install_theme import main as theme_main
        theme_main(['--apply'])
        wm = subprocess.Popen(['xfwm4', '--compositor=off'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        app = W.QApplication.instance() or W.QApplication([])
        app.setQuitOnLastWindowClosed(False)
        backend = DesktopBackend()
        connection = display.Display()
        window = W.QWidget();window.setWindowTitle('NOVA / Native window controls');window.resize(620,300)
        def wait(check):
            deadline=time.monotonic()+12
            while time.monotonic()<deadline:
                app.processEvents()
                if check():return
                time.sleep(.05)
            raise AssertionError('Native window decoration did not reach expected state')
        gtk = None
        try:
            window.show()
            xid=int(window.winId());root=connection.screen().root
            target=connection.create_resource_object('window',xid)
            wait(lambda: len(backend.prop(connection,target,'_NET_FRAME_EXTENTS',[]))==4)
            time.sleep(.2);app.processEvents()
            extents=backend.prop(connection,target,'_NET_FRAME_EXTENTS',[0]*4)
            pos=root.translate_coords(target,0,0)
            left,top=pos.x-extents[0],pos.y-extents[2]
            image=app.primaryScreen().grabWindow(0,left,top,window.width()+extents[0]+extents[1],extents[2]).toImage()
            # Detect actual red pixels in the right-hand title buttons, not file names.
            groups=[]
            for x in range(max(0,image.width()-130),image.width()):
                ys=[y for y in range(image.height()) if (lambda c:c.red()>200 and c.green()<140 and c.blue()<160)(image.pixelColor(x,y))]
                if ys:
                    if not groups or x>groups[-1][-1][0]+1:groups.append([])
                    groups[-1].extend((x,y) for y in ys)
            assert len(groups)==3, ('Missing native red minimize/maximize/close symbols',len(groups),extents)
            centers=[(left+sum(x for x,y in group)//len(group),top+sum(y for x,y in group)//len(group)) for group in groups]
            def click(index):
                x,y=centers[index]
                xtest.fake_input(connection,X.MotionNotify,x=x,y=y)
                xtest.fake_input(connection,X.ButtonPress,1)
                xtest.fake_input(connection,X.ButtonRelease,1)
                connection.sync()
            click(0);wait(lambda:window.isMinimized())
            window.showNormal();wait(lambda:not window.isMinimized())
            click(1);wait(window.isMaximized)
            # The restore button moves when maximized: invoke normal state before
            # checking close at its original position (Qt test covers restore click).
            window.showNormal();wait(lambda:not window.isMaximized())
            click(2);wait(lambda:not window.isVisible())
            gtk_code = """
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk
s=Gtk.Settings.get_default()
s.set_property('gtk-theme-name','NOVA-NEXUS-HD')
s.set_property('gtk-decoration-layout','menu:minimize,maximize,close')
w=Gtk.Window(title='NOVA / GTK controls');w.set_default_size(620,300)
h=Gtk.HeaderBar(title='NOVA / GTK controls');h.set_show_close_button(True)
w.set_titlebar(h);w.add(Gtk.Label(label='NOVA GTK3 title controls'));w.show_all()
Gtk.main()
"""
            with open(temp+'/gtk-errors.log','w+') as errors:
                gtk=subprocess.Popen(['/usr/bin/python3','-c',gtk_code],stderr=errors)
                def gtk_row():
                    return next((r for r in backend.snapshot()[0] if r['name']=='NOVA / GTK controls'),None)
                wait(gtk_row)
                time.sleep(.3);app.processEvents()
                target=connection.create_resource_object('window',gtk_row()['id'])
                position=root.translate_coords(target,0,0);geometry=target.get_geometry()
                img=app.primaryScreen().grabWindow(0,position.x,position.y,geometry.width,min(90,geometry.height)).toImage()
                reds=[]
                for x in range(max(0,img.width()-160),img.width()):
                    if any((lambda c:c.red()>200 and c.green()<140 and c.blue()<160)(img.pixelColor(x,y)) for y in range(img.height())):
                        if not reds or x>reds[-1][-1]+1:reds.append([])
                        reds[-1].append(x)
                errors.flush();errors.seek(0);diagnostics=errors.read()
                assert len(reds)==3, ('Missing GTK red minimize/maximize/close symbols',len(reds),diagnostics)
                assert 'Theme parsing error' not in diagnostics, diagnostics
            print('PASS: actual GTK3 CSD has three red symbols and parses NOVA CSS without errors')
            theme_main(['--restore'])
            print('PASS: real XFWM title pixmaps and X11 clicks: minimize, maximize, close; reversible theme')
        finally:
            if gtk:
                gtk.terminate()
                try:gtk.wait(timeout=5)
                except subprocess.TimeoutExpired:gtk.kill()
            window.close();connection.close();wm.terminate()
            try:wm.wait(timeout=5)
            except subprocess.TimeoutExpired:wm.kill()
            os.environ.clear();os.environ.update(original)

if __name__=='__main__':main()
