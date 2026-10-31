"""Per-user preferences, atomically persisted outside the installation."""
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


def data_dir():
    override = os.getenv("HEALTHBAR_DATA_DIR")
    if override:
        return Path(override)
    if sys.platform == "win32":
        return Path(os.getenv("APPDATA", str(Path.home()))) / "HealthPerfsBar"
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/HealthPerfsBar"
    return Path(os.getenv("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "health-perfs-bar"


@dataclass
class Settings:
    position: str = "top"
    thickness: int = 200
    opacity: int = 88
    auto_hide: bool = True
    hide_seconds: int = 15
    autostart: bool = False
    configured: bool = False
    screen: int = 0
    length_percent: int = 100
    alignment: str = "center"
    refresh_seconds: int = 2
    shell_dir: str = ""
    theme: str = "cyber-futuriste"

    def validate(self):
        if self.position not in ("top", "bottom", "right") or self.alignment not in ("left", "center", "right"):
            raise ValueError("Position invalide")
        for name, lo, hi in (("thickness", 120, 360), ("opacity", 0, 100),
                             ("hide_seconds", 3, 120), ("screen", 0, 64),
                             ("length_percent", 25, 100), ("refresh_seconds", 1, 30)):
            value = getattr(self, name)
            if type(value) is not int or not lo <= value <= hi:
                raise ValueError(f"Préférence invalide : {name}")
        for name in ("autostart", "configured", "auto_hide"):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"Préférence invalide : {name}")
        if not isinstance(self.shell_dir, str) or len(self.shell_dir) > 1024 or "\x00" in self.shell_dir:
            raise ValueError("Dossier des scripts invalide")
        if self.theme != "cyber-futuriste":
            raise ValueError("Thème non reconnu")
        return self

    @classmethod
    def load(cls):
        try:
            raw = json.loads((data_dir() / "settings.json").read_text(encoding="utf-8"))
            return cls(**{k: v for k, v in raw.items() if k in cls.__dataclass_fields__}).validate()
        except (OSError, ValueError, TypeError, AttributeError):
            return cls()

    def save(self):
        self.validate()
        root = data_dir()
        root.mkdir(parents=True, exist_ok=True)
        tmp = root / "settings.tmp"
        tmp.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        tmp.replace(root / "settings.json")
