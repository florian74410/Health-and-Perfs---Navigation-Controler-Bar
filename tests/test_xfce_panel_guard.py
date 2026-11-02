"""Regression tests for verified XFCE panel restoration."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from healthbar.desktop_backend import NativePanelGuard


class _Backend:
    def __init__(self, effectively_visible):
        self.effectively_visible = effectively_visible
        self.map_calls = 0

    def set_panel_visible(self, rows, visible):
        self.map_calls += 1
        return True

    def panels_effectively_visible(self, rows):
        return self.effectively_visible


class NativePanelGuardTests(unittest.TestCase):
    def test_keeps_recovery_journal_when_x11_map_is_not_effective(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(
                os.environ, {"HEALTHBAR_DATA_DIR": temp, "DISPLAY": ":99"}):
            backend = _Backend(effectively_visible=False)
            guard = NativePanelGuard(backend)
            guard.rows = [{"id": 123, "pid": 456}]
            guard.path.parent.mkdir(parents=True, exist_ok=True)
            guard.path.write_text(json.dumps({"panels": guard.rows}), encoding="utf-8")

            self.assertFalse(guard.restore())
            self.assertTrue(guard.path.exists())
            self.assertEqual(backend.map_calls, 1)

    def test_removes_recovery_journal_only_after_effective_visibility(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(
                os.environ, {"HEALTHBAR_DATA_DIR": temp, "DISPLAY": ":99"}):
            backend = _Backend(effectively_visible=True)
            guard = NativePanelGuard(backend)
            guard.rows = [{"id": 123, "pid": 456}]
            guard.path.parent.mkdir(parents=True, exist_ok=True)
            guard.path.write_text(json.dumps({"panels": guard.rows}), encoding="utf-8")

            self.assertTrue(guard.restore())
            self.assertFalse(guard.path.exists())


if __name__ == "__main__":
    unittest.main()
