import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from nova_nexus.theme_engine import preset, set_active_theme, get_active_theme


class ThemePersistenceTests(unittest.TestCase):
    def test_presets_persist_without_changing_default(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ,HEALTHBAR_DATA_DIR=tmp):
            for name in ('Matrix Green','Cyber Magenta','Tactical Amber','Stealth Dark'):
                theme=preset(name,'Off');set_active_theme(theme)
                self.assertEqual(get_active_theme(),theme)
                self.assertFalse(theme['motion']['enabled'])
                self.assertEqual(theme['effects']['pcb_visibility'],0)
            set_active_theme(preset())
            self.assertEqual(get_active_theme()['colors']['primary'],'#00CBF3')
