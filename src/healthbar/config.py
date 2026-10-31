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
    thickness: int = 72
    layout_revision: int = 1
    opacity: int = 88
    auto_hide: bool = True
    retract_mode: str = ""
    always_on_top: bool = True
    holo_enabled: bool = True
    # Any combination of the three panels may be enabled.
    hud_enabled: bool = True
    dock_left_enabled: bool = True
    dock_right_enabled: bool = True
    dock_left_kind: str = "folders"
    dock_right_kind: str = "apps"
    # None = auto-discover defaults, [] = intentionally empty dock.
    dock_folder_paths: list | None = None
    dock_app_paths: list | None = None
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
        for name, lo, hi in (("thickness", 50, 150), ("opacity", 0, 100), ("layout_revision", 1, 1),
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
        if not self.retract_mode:
            self.retract_mode = "auto" if self.auto_hide else "manual"
        if self.retract_mode not in ("always", "auto", "manual"):
            raise ValueError("Mode de rétractation invalide")
        self.auto_hide = self.retract_mode == "auto"
        if type(self.always_on_top) is not bool or type(self.holo_enabled) is not bool:
            raise ValueError("Option affichage invalide")
        for name in ("hud_enabled", "dock_left_enabled", "dock_right_enabled"):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"Activation de barre invalide : {name}")
        if not (self.hud_enabled or self.dock_left_enabled or self.dock_right_enabled):
            raise ValueError("Activer au moins une des trois barres NovaBar")
        if sorted((self.dock_left_kind, self.dock_right_kind)) != ["apps", "folders"]:
            raise ValueError("Un dock Dossiers et un dock Applications sont requis")
        for key in ("dock_folder_paths", "dock_app_paths"):
            values = getattr(self, key)
            if values is None:
                continue
            if not isinstance(values, list) or len(values) > 128 or any(
                    not isinstance(p, str) or len(p) > 2048 or "\\x00" in p for p in values):
                raise ValueError(f"Favoris de dock invalides : {key}")
        if self.theme not in ("cyber-futuriste", "blue-neon", "green-matrix", "red-blood"):
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
            if "layout_revision" not in raw and raw.get("thickness", 200) == 200:
                raw["thickness"] = 72
            if type(raw.get("thickness")) is int:
                raw["thickness"] = max(50,min(150,raw["thickness"]))
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
            f"- NovaBar en haut: {self.hud_enabled}",
            f"- Dock gauche: {self.dock_left_enabled} ({self.dock_left_kind})",
            f"- Dock droit: {self.dock_right_enabled} ({self.dock_right_kind})",
            f"- Thème: {self.theme}",
            f"- Modules: {', '.join(self.slot_order)}",
            "",
            "Le fichier settings.json est la source des préférences actives.",
        ]
        (profile / "Profile.md").write_text("\n".join(details) + "\n", encoding="utf-8")
        from .profiles import mirror_preferences
        mirror_preferences(asdict(self))
