import subprocess
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch,Mock
from healthbar.cpu_backends import LinuxBoostBackend
from healthbar.cpu_mode_controller import CpuModeController


class BoostAuthorizationTests(unittest.TestCase):
    def backend(self):
        backend=LinuxBoostBackend('/missing-test-cpu')
        backend.system_root=True;backend.path=Mock();backend.inverted=True
        return backend
    def test_only_boolean_helper_request_and_verified_readback(self):
        backend=self.backend()
        with patch.object(backend,'read',side_effect=[False,True]),patch('healthbar.cpu_backends.os.access',return_value=False),patch.object(Path,'is_file',return_value=True),patch.object(Path,'stat',return_value=SimpleNamespace(st_uid=0,st_mode=0o100755)),patch('healthbar.cpu_backends.subprocess.run',return_value=SimpleNamespace(returncode=0)) as run:
            self.assertTrue(backend.write(True))
            self.assertEqual(run.call_args.args[0],['/usr/bin/pkexec','/usr/libexec/novabar-boost','1'])
            self.assertNotIn('input',run.call_args.kwargs)
            backend.path.write_text.assert_not_called()
    def test_cancel_does_not_reprompt_until_user_selects_again(self):
        backend=self.backend();controller=CpuModeController(backend);controller.select('on')
        with patch.object(backend,'read',return_value=False),patch('healthbar.cpu_backends.os.access',return_value=False),patch.object(Path,'is_file',return_value=True),patch.object(Path,'stat',return_value=SimpleNamespace(st_uid=0,st_mode=0o100755)),patch('healthbar.cpu_backends.subprocess.run',return_value=SimpleNamespace(returncode=126)) as run:
            self.assertIsNotNone(controller.sample(40)['error'])
            self.assertIsNotNone(controller.sample(40)['error'])
            self.assertEqual(run.call_count,1)
            controller.select('off');controller.select('on')
            controller.sample(40)
            self.assertEqual(run.call_count,2)
