import os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from healthbar.terminal_launchers import is_nova_terminal_shortcut,preferred_terminal_launcher
from healthbar.edge_docks import launch_item
from healthbar.app_catalog import catalog
from healthbar.bottom_dock import favorite_apps
from healthbar.config import Settings
from healthbar.app import Bar

class TerminalLaunchersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def entry(self,root,name,command,extra=''):
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text('[Desktop Entry]\nType=Application\nName='+name+'\nExec='+command+'\nIcon=utilities-terminal\n'+extra)
        return path
    def test_plain_shortcuts_only_not_user_commands(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for command in ('xfce4-terminal','/usr/bin/xfce4-terminal %U','exo-open --launch TerminalEmulator','x-terminal-emulator'):
                self.assertTrue(is_nova_terminal_shortcut(self.entry(root,'terminal.desktop',command)))
            for command in ('xfce4-terminal -e htop','xfce4-terminal --working-directory /tmp','exo-open --launch WebBrowser','x-terminal-emulator -e ssh host'):
                self.assertFalse(is_nova_terminal_shortcut(self.entry(root,'terminal.desktop',command)))
    @unittest.skipUnless(sys.platform.startswith("linux"),"Linux desktop launchers")
    def test_launch_route_opens_themed_manager_without_native_gio(self):
        with tempfile.TemporaryDirectory() as temp:
            path=self.entry(Path(temp),'terminal.desktop','xfce4-terminal')
            with patch('healthbar.nova_components.open_terminal') as nova,patch('healthbar.edge_docks.subprocess.Popen') as native:
                self.assertTrue(launch_item(str(path),'apps'));nova.assert_called_once_with();native.assert_not_called()
            custom=self.entry(Path(temp),'custom.desktop','xfce4-terminal -e htop')
            with patch('healthbar.nova_components.open_terminal') as nova,patch('healthbar.edge_docks.subprocess.Popen') as native:
                self.assertTrue(launch_item(str(custom),'apps'));nova.assert_not_called();native.assert_called_once()
    def test_pins_and_catalog_prefer_owned_nova_but_keep_custom_commands(self):
        with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,XDG_DATA_HOME=temp):
            root=Path(temp)/'applications'
            native=self.entry(root,'xfce.desktop','xfce4-terminal')
            custom=self.entry(root,'custom.desktop','xfce4-terminal -e htop')
            nova=self.entry(root,'nova-nexus-terminal.desktop','/old/runtime/HealthPerfsBar --nova-terminal','X-NOVA-Owned=true\n')
            self.assertEqual(preferred_terminal_launcher(str(native)),str(nova))
            settings=Settings(dock_app_paths=[str(native),str(custom)])
            self.assertEqual(favorite_apps(settings),[str(nova),str(custom)])
            self.assertEqual(settings.dock_app_paths,[str(native),str(custom)])
            self.assertEqual({app.path for app in catalog([root])},{str(nova),str(custom)})
    @unittest.skipUnless(sys.platform.startswith("linux"),"Linux NOVA Terminal")
    def test_hud_terminal_button_opens_nova_not_scripts(self):
        with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,HEALTHBAR_DATA_DIR=temp):
            bar=Bar(Settings(configured=True,shell_dir=temp,auto_hide=False,dock_left_enabled=False,dock_right_enabled=False,bottom_dock_enabled=False))
            try:
                button=next(b for b in bar.buttons.findChildren(__import__('healthbar.app',fromlist=['NeonButton']).NeonButton) if b.property('icon_kind')=='terminal')
                with patch('healthbar.nova_components.open_terminal') as nova,patch.object(bar,'console_info') as scripts:
                    button.click();nova.assert_called_once_with(Path(temp));scripts.assert_not_called()
            finally:bar.close()


class ActiveRuntimeTests(unittest.TestCase):
    def test_newer_activated_runtime_is_selected_but_internal_flags_are_not_forwarded(self):
        from healthbar.active_runtime import newer_active_executable
        from healthbar import __version__
        import json
        with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,HEALTHBAR_INSTALL_ROOT=temp),patch.object(sys,'frozen',True,create=True):
            root=Path(temp)
            executable=root/'versions/9.0.0'/('HealthPerfsBar.app/Contents/MacOS/HealthPerfsBar' if sys.platform=='darwin' else 'HealthPerfsBar/HealthPerfsBar.exe' if sys.platform=='win32' else 'HealthPerfsBar/HealthPerfsBar')
            executable.parent.mkdir(parents=True);executable.touch()
            (root/'installation.json').write_text(json.dumps({'version':'9.0.0','executable':str(executable)}))
            self.assertEqual(newer_active_executable(['--nova-terminal']),executable)
            self.assertEqual(newer_active_executable(['--version']),executable)
            for args in (['--self-test'],['--expect-version','0.7.2'],['--nova-pty-child','3'],['--restore-xfce-after-pid','10']):
                self.assertIsNone(newer_active_executable(args))
            (root/'installation.json').write_text(json.dumps({'version':__version__,'executable':str(executable)}))
            self.assertIsNone(newer_active_executable(['--nova-terminal']))
    def test_foreign_executable_is_not_selected(self):
        from healthbar.active_runtime import newer_active_executable
        import json
        with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,HEALTHBAR_INSTALL_ROOT=temp),patch.object(sys,'frozen',True,create=True):
            root=Path(temp);foreign=root/'foreign';foreign.touch()
            (root/'installation.json').write_text(json.dumps({'version':'9.0.0','executable':str(foreign)}))
            self.assertIsNone(newer_active_executable(['--nova-terminal']))
