"""Qt smoke/unit tests for connection dialogs without SSH/network side effects."""
import os
import json
from pathlib import Path
import pytest
from PySide6.QtCore import Qt
from nexus_dialogs import safe_ssh, profiles_write, profiles_read, GlassDialog, SettingsDialog, SessionsDialog
from web_inspector import display_url, WebInspector

def test_safe_ssh_arguments(tmp_path):
    key=tmp_path/"id_ed25519"
    key.write_text("not-a-real-key")
    key.chmod(0o600)
    profile={"name":"TEST","host":"example.org","user":"admin","port":22,"key_path":str(key)}
    args=safe_ssh(profile)
    assert args[0]=="ssh"
    assert "example.org" in args[-1]
    profile["host"]="evil;rm -rf /"
    with pytest.raises(ValueError):safe_ssh(profile)

def test_redact_sensitive_url():
    out=display_url("https://alice:password@example.org/api/v1?a=secret#fragment")
    assert out=="https://example.org/api/v1"

def test_glass_dialogs(qtbot,tmp_path,monkeypatch):
    import nexus_dialogs
    monkeypatch.setattr(nexus_dialogs,"PROFILES",tmp_path/"profiles.json")
    monkeypatch.setattr(nexus_dialogs,"API_PROFILES",tmp_path/"api.json")
    settings=SettingsDialog()
    qtbot.addWidget(settings)
    assert settings.windowFlags() & Qt.WindowType.FramelessWindowHint
    settings.font.setValue(12)
    sessions=SessionsDialog()
    qtbot.addWidget(sessions)
    assert sessions.identity.placeholderText()
    browser=WebInspector()
    qtbot.addWidget(browser)
    assert browser.table.columnCount()==3
    browser.append_record("GET","https://example.org","Document")
    assert browser.table.rowCount()==1
    sessions.close()
    settings.close()
    browser.close()
