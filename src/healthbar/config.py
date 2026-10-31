"""Per-user preferences, atomically persisted outside the installation."""
import json
import os
import getpass
import re
import sys
from dataclasses import asdict, dataclass, field
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
    slot_order: list = None
    shortcuts: list = field(default_factory=lambda: [{"action": "toggle", "sequence": "Ctrl+B"}])

    def validate(self):
        if self.position not in ("top", "bottom", "right", "left") or self.alignment not in ("left", "center", "right"):
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
        expected = ["cpu", "gpu", "ram", "storage", "fans", "network"]
        if self.slot_order is None:
            self.slot_order = expected.copy()
        if not isinstance(self.slot_order, list) or len(self.slot_order) != 6 or sorted(self.slot_order) != sorted(expected):
            raise ValueError("Disposition des modules invalide")
        if not isinstance(self.shortcuts, list) or len(self.shortcuts) > 20:
            raise ValueError("Liste de raccourcis invalide")
        seen = set()
        for binding in self.shortcuts:
            if not isinstance(binding, dict) or binding.get("action") not in ("toggle", "expand", "preferences"):
                raise ValueError("Action de raccourci invalide")
            sequence = binding.get("sequence", "")
            if not isinstance(sequence, str) or not 1 <= len(sequence) <= 80 or "," in sequence:
                raise ValueError("Combinaison de raccourci invalide")
            if sequence.casefold() in seen:
                raise ValueError("Raccourci en double")
            seen.add(sequence.casefold())
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
        username = re.sub(r"[^A-Za-z0-9_-]+", "_", getpass.getuser())[:48] or "Default"
        profile = root / "App" / "Profils" / username
        profile.mkdir(parents=True, exist_ok=True)
        details = [
            "# NovaBar Profile.md",
            "",
            f"- Position: {self.position}",
            f"- Screen: {self.screen}",
            f"- Longueur: {self.length_percent}%",
            f"- Épaisseur: {self.thickness}px",
            f"- Alignement: {self.alignment}",
            f"- Opacité: {self.opacity}%",
            f"- Délai de rétractation: {self.hide_seconds}s",
            f"- Démarrage automatique: {self.autostart}",
            f"- Thème: {self.theme}",
            f"- Modules: {', '.join(self.slot_order)}",
            "",
            "Le fichier settings.json est la source des préférences actives.",
        ]
        (profile / "Profile.md").write_text("\n".join(details) + "\n", encoding="utf-8")
        from .profiles import mirror_preferences
        mirror_preferences(asdict(self))
