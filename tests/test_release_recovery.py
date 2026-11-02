import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from healthbar.config import Settings
from healthbar.profiles import write_json
from healthbar.update_recovery import backup_user_data, rollback
from healthbar.install_engine import cleanup_obsolete_runtimes


class RecoveryTests(unittest.TestCase):
    def test_backup_keeps_plugins_and_rollback_restores_previous_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);root=base/'runtime';config=base/'data'
            with patch.dict(os.environ,HEALTHBAR_DATA_DIR=str(config),HEALTHBAR_INSTALL_ROOT=str(root)):
                Settings(opacity=77).save()
                plugins=config/'plugins';plugins.mkdir();(plugins/'custom.json').write_text('custom')
                binary=root/'versions/0.7.5/HealthPerfsBar'/('HealthPerfsBar.exe' if os.name=='nt' else 'HealthPerfsBar')
                binary.parent.mkdir(parents=True);binary.write_text('test fixture')
                old={'version':'0.7.5','executable':str(binary)}
                write_json(root/'installation.json',old)
                backup=backup_user_data(root)
                Settings(opacity=88).save();(plugins/'custom.json').write_text('new')
                write_json(root/'installation.json',{'version':'1.0.0','previous':old,'recovery_backup':str(backup)})
                cleanup_obsolete_runtimes(root,'1.0.0')
                self.assertTrue(binary.exists())
                with patch('healthbar.update_recovery.self_test'),patch('healthbar.install_engine.activate',return_value=dict(old)),patch('healthbar.autostart.set_enabled'):
                    state=rollback(root)
                self.assertTrue(state['rollback_requested'])
                self.assertEqual(Settings.load().opacity,77)
                self.assertEqual((plugins/'custom.json').read_text(),'custom')
                self.assertEqual(json.loads((root/'installation.json').read_text())['version'],'0.7.5')
