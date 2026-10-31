"""Isolated real X11/XFCE integration, run inside xvfb-run + dbus-run-session."""
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from Xlib import X
from healthbar.config import Settings
from healthbar.desktop_backend import DesktopBackend
from healthbar.bottom_dock import BottomDock


def wait_for(check,app,timeout=12):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        app.processEvents()
        value=check()
        if value:return value
        time.sleep(.1)
    raise AssertionError('Timed out waiting for isolated XFCE session')


def main():
    processes=[]
    with tempfile.TemporaryDirectory(prefix='novabar-xfce-') as temp:
        os.environ.update(XDG_CONFIG_HOME=temp+'/config',HEALTHBAR_DATA_DIR=temp+'/data',QT_QPA_PLATFORM='xcb')
        Path(os.environ['XDG_CONFIG_HOME']).mkdir()
        def setting(path,kind,value,array=False):
            command=['xfconf-query','-c','xfce4-panel','-p',path,'-n','-t',kind,'-s',str(value)]
            if array:command.append('-a')
            subprocess.run(command,check=True,timeout=15)
        setting('/panels','int',1,True)
        setting('/panels/panel-1/position','string','p=10;x=640;y=700')
        setting('/panels/panel-1/size','uint',48)
        setting('/panels/panel-1/length','uint',100)
        setting('/panels/panel-1/position-locked','bool','true')
        setting('/panels/panel-1/plugin-ids','int',1,True)
        setting('/plugins/plugin-1','string','applicationsmenu')
        app=QApplication([]);app.setQuitOnLastWindowClosed(False)
        backend=DesktopBackend();dock=None;hud=None;terminal=None
        try:
            processes.append(subprocess.Popen(['xfwm4','--compositor=off'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
            processes.append(subprocess.Popen(['xfce4-panel','--disable-wm-check'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
            bounds=app.primaryScreen().geometry()
            panels=wait_for(lambda:backend.native_bottom_panels(bounds),app)
            dock=BottomDock(Settings(configured=True,dock_app_paths=[]))
            wait_for(lambda:dock.native.rows,app)
            con=backend._connect()
            assert all(con.create_resource_object('window',r['id']).get_attributes().map_state==X.IsUnmapped for r in panels)
            code="from PySide6.QtWidgets import QApplication,QWidget; a=QApplication([]); w=QWidget(); w.setWindowTitle('NovaBar QA task'); w.resize(300,200); w.show(); a.exec()"
            processes.append(subprocess.Popen([sys.executable,'-c',code],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
            row=wait_for(lambda:next((r for r in backend.snapshot()[0] if r['name']=='NovaBar QA task'),None),app)
            assert backend.action(row['id'])
            wait_for(lambda:backend.snapshot()[1]==row['id'],app)
            assert backend.action(row['id'],minimize=True)
            wait_for(lambda:con.create_resource_object('window',row['id']).get_attributes().map_state==X.IsUnmapped,app)
            assert backend.action(row['id'])
            wait_for(lambda:con.create_resource_object('window',row['id']).get_attributes().map_state==X.IsViewable,app)
            assert backend.toggle_desktop()
            wait_for(backend.showing_desktop,app)
            wait_for(lambda:con.create_resource_object('window',row['id']).get_attributes().map_state==X.IsUnmapped,app)
            assert dock.isVisible()
            assert con.create_resource_object('window',int(dock.winId())).get_attributes().map_state==X.IsViewable
            assert backend.toggle_desktop()
            wait_for(lambda:not backend.showing_desktop(),app)
            from healthbar.nova_components import open_explorer,_windows
            assert open_explorer(temp)
            wait_for(lambda:any(r['name']=='NOVA Explorer' for r in backend.snapshot()[0]),app)
            for window in list(_windows):window.close()
            # An already-maximized external application must track the visible HUD edge.
            from healthbar.app import Bar
            from Xlib import protocol
            hud=Bar(Settings(configured=True,thickness=70,auto_hide=False,retract_mode='manual',
                dock_left_enabled=False,dock_right_enabled=False,bottom_dock_enabled=False))
            hud.animation.setDuration(0);hud.show()
            root=con.screen().root
            def work_top():return int(backend.prop(con,root,'_NET_WORKAREA',[0,0,0,0])[1])
            def outer_top(xid):
                window=con.create_resource_object('window',xid)
                extent=backend.prop(con,window,'_NET_FRAME_EXTENTS',[0,0,0,0])
                return root.translate_coords(window,0,0).y-int(extent[2])
            wait_for(lambda:work_top()==70,app)
            root.send_event(protocol.event.ClientMessage(window=con.create_resource_object('window',row['id']),
                client_type=con.intern_atom('_NET_WM_STATE'),data=(32,[1,
                con.intern_atom('_NET_WM_STATE_MAXIMIZED_VERT'),con.intern_atom('_NET_WM_STATE_MAXIMIZED_HORZ'),1,0])),
                event_mask=X.SubstructureRedirectMask|X.SubstructureNotifyMask);con.flush()
            wait_for(lambda:outer_top(row['id'])==70,app)
            hud.retract(manual=True)
            wait_for(lambda:work_top()==10 and outer_top(row['id'])==10,app)
            assert hud.height()==10
            hud.reveal();wait_for(lambda:work_top()==70 and outer_top(row['id'])==70,app)
            hud.settings.thickness=90;hud.apply_settings()
            wait_for(lambda:work_top()==90 and outer_top(row['id'])==90,app)
            # NOVA's split-layout maximize obeys the same reservation as external apps.
            from nova_nexus.terminal_manager import open_manager
            terminal=open_manager(start=False);terminal.set_format('grid')
            wait_for(lambda:terminal.window.isMaximized() and outer_top(int(terminal.window.winId()))==90,app)
            for button in (terminal.window.minbtn,terminal.window.closebtn):
                assert button.mapTo(terminal.window,button.rect().topLeft()).y()>=6
                assert button.mapTo(terminal.window,button.rect().bottomRight()).y()<=45
            terminal.window.close();terminal=None
            hud.settings.hud_enabled=False;hud.hide()
            wait_for(lambda:work_top()==0 and outer_top(row['id'])==0,app)
            hud.settings.hud_enabled=True;hud.show();wait_for(lambda:work_top()==90,app)
            hud.close();hud=None;wait_for(lambda:work_top()==0,app)
            print('PASS: dynamic HUD workarea 70/10/90/0; already-maximized external app; NOVA terminal titlebar and maximize')
            dock.collapse();assert not dock.isVisible()
            dock.expand();assert dock.isVisible()
            dock.close()
            wait_for(lambda:all(con.create_resource_object('window',r['id']).get_attributes().map_state==X.IsViewable for r in panels),app)
            assert not dock.native.path.exists()
            # Kill a separate NovaBar surface without closeEvent: its watchdog must recover XFCE.
            crash_code="from PySide6.QtWidgets import QApplication; from PySide6.QtCore import QTimer; from healthbar.bottom_dock import BottomDock; from healthbar.config import Settings; import os; a=QApplication([]); d=BottomDock(Settings(configured=True,dock_app_paths=[])); from healthbar.app import Bar; h=Bar(Settings(configured=True,thickness=70,auto_hide=False,retract_mode='manual',dock_left_enabled=False,dock_right_enabled=False,bottom_dock_enabled=False)); h.show(); QTimer.singleShot(3000,lambda:os._exit(9)); a.exec()"
            crashed=subprocess.Popen([sys.executable,'-c',crash_code],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            processes.append(crashed)
            wait_for(lambda:all(con.create_resource_object('window',r['id']).get_attributes().map_state==X.IsUnmapped for r in panels),app)
            wait_for(lambda:work_top()==70,app)
            assert crashed.wait(timeout=8)==9
            wait_for(lambda:work_top()==0,app)
            wait_for(lambda:all(con.create_resource_object('window',r['id']).get_attributes().map_state==X.IsViewable for r in panels),app)
            assert not dock.native.path.exists()
            con.close()
            print('PASS: XFCE close/crash restoration; task activation; show desktop; NOVA Explorer task; cockpit')
        finally:
            if terminal:terminal.window.close()
            if hud:hud.close()
            if dock:dock.close()
            for process in reversed(processes):
                process.terminate()
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:process.kill()

if __name__=='__main__':main()
