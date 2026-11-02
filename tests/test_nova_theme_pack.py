import tempfile
import unittest
from pathlib import Path
from nova_nexus.theme_pack import desktop_entry

class TestThemePack(unittest.TestCase):
    def test_launcher_entry(self):
        result=desktop_entry("/usr/bin/python3",Path("/home/test/NOVA-DEV"))
        self.assertIn("Name=NOVA Explorer",result)
        self.assertIn('Exec="/usr/bin/python3" -m nova_nexus.explorer',result)
        self.assertNotIn("xdg-mime",result)

    def test_invalid_path(self):
        with self.assertRaises(ValueError):
            desktop_entry('/tmp/"bad',Path("/tmp"))
