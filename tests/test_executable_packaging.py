import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

spec=importlib.util.spec_from_file_location('nexus_executable_packaging',Path(__file__).resolve().parents[1]/'scripts/package_executables.py')
packager=importlib.util.module_from_spec(spec);spec.loader.exec_module(packager)


class ExecutablePackagingTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform.startswith('linux'),'The single-file launcher targets GNU/Linux')
    def test_single_file_integrity_check_and_corruption_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);archive=root/'runtime.zip'
            with zipfile.ZipFile(archive,'w') as package:
                item=zipfile.ZipInfo('HealthPerfsBar/HealthPerfsBar');item.external_attr=0o100755<<16
                package.writestr(item,b'test-runtime')
            output=packager.linux_run(archive,root/'installer.run','1.2.3')
            self.assertEqual(subprocess.run(['sh',str(output),'--check'],capture_output=True).returncode,0)
            self.assertEqual(subprocess.check_output(['sh',str(output),'--version']).strip(),b'1.2.3')
            data=output.read_bytes();output.write_bytes(data[:-1]+bytes([data[-1]^1]))
            self.assertNotEqual(subprocess.run(['sh',str(output),'--check'],capture_output=True).returncode,0)

    def test_unsafe_archive_paths_are_rejected_before_packaging(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);archive=root/'bad.zip'
            with zipfile.ZipFile(archive,'w') as package:package.writestr('../outside','bad')
            with self.assertRaises(ValueError):packager.linux_run(archive,root/'installer.run','1.2.3')
