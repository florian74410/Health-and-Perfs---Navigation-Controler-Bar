"""API v1: declarative packages only. No downloaded Python/JS is executed."""
import hashlib
import json
import re
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from .config import data_dir

API_VERSION = 1
MAX_PACKAGE = 2 * 1024 * 1024
SLOTS = ("cpu", "gpu", "ram", "storage", "fans", "network")


def validate_manifest(raw):
    if not isinstance(raw, dict):
        raise ValueError("Le manifeste doit être un objet JSON")
    if type(raw.get("api_version")) is not int or raw["api_version"] != API_VERSION:
        raise ValueError("API de plugin incompatible")
    if not re.fullmatch(r"[a-z][a-z0-9-]{2,63}", str(raw.get("id", ""))):
        raise ValueError("Identifiant de plugin invalide")
    if not re.fullmatch(r"\d{1,6}\.\d{1,6}\.\d{1,6}", str(raw.get("version", ""))):
        raise ValueError("Version attendue : majeur.mineur.correctif")
    if raw.get("slot") not in SLOTS:
        raise ValueError("Emplacement inconnu")
    if not isinstance(raw.get("name"), str) or not 1 <= len(raw["name"]) <= 60:
        raise ValueError("Nom du plugin invalide")
    if raw.get("kind") != "declarative":
        raise ValueError("Cette version accepte seulement les extensions déclaratives")
    if set(raw) - {"id", "version", "name", "api_version", "slot", "kind", "description"}:
        raise ValueError("Champs de manifeste non pris en charge")
    if not isinstance(raw.get("description", ""), str) or len(raw.get("description", "")) > 400:
        raise ValueError("Description invalide")
    return raw


def version_tuple(value):
    return tuple(map(int, value.split(".")))


class PluginRegistry:
    def __init__(self, root=None):
        self.root = Path(root) if root else data_dir() / "plugins"

    def installed(self):
        if not self.root.exists():
            return []
        items = []
        for directory in sorted(self.root.iterdir()):
            if not directory.is_dir() or directory.name.startswith("."):
                continue
            try:
                manifest = validate_manifest(json.loads((directory / "manifest.json").read_text(encoding="utf-8")))
                state = json.loads((directory / "state.json").read_text(encoding="utf-8"))
                if manifest["id"] != directory.name:
                    continue
                items.append({**manifest, "enabled": state.get("enabled") is True})
            except (OSError, ValueError, TypeError, AttributeError):
                continue
        return items

    def inspect(self, archive):
        archive = Path(archive)
        if archive.stat().st_size > MAX_PACKAGE:
            raise ValueError("Paquet trop volumineux (2 Mio maximum)")
        with zipfile.ZipFile(archive) as package:
            members = package.infolist()
            names = [item.filename for item in members]
            for item in members:
                path = PurePosixPath(item.filename)
                if path.is_absolute() or ".." in path.parts or "\\" in item.filename:
                    raise ValueError("Chemin de paquet interdit")
            # v1 has exactly one declarative manifest. No executable assets.
            if names != ["manifest.json"] or members[0].file_size > 16384:
                raise ValueError("Le paquet v1 doit contenir uniquement manifest.json (16 Kio max.)")
            manifest = validate_manifest(json.loads(package.read("manifest.json")))
        return manifest, hashlib.sha256(archive.read_bytes()).hexdigest()

    def install(self, archive, expected_digest):
        manifest, digest = self.inspect(archive)
        if digest != expected_digest:
            raise ValueError("Le paquet a changé depuis sa vérification")
        current = next((p for p in self.installed() if p["id"] == manifest["id"]), None)
        if current and version_tuple(manifest["version"]) <= version_tuple(current["version"]):
            raise ValueError("La mise à jour doit avoir une version supérieure")
        self.root.mkdir(parents=True, exist_ok=True)
        target = self.root / manifest["id"]
        backup = self.root / ("." + manifest["id"] + ".previous")
        if backup.exists():
            shutil.rmtree(backup)
        with tempfile.TemporaryDirectory(dir=self.root, prefix=".stage-") as staging:
            stage = Path(staging) / manifest["id"]
            stage.mkdir()
            (stage / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            # Updating preserves the user's activation choice. New packages start disabled.
            (stage / "state.json").write_text(json.dumps({"enabled": bool(current and current["enabled"]),
                                                          "sha256": digest}), encoding="utf-8")
            if target.exists():
                target.rename(backup)
            try:
                stage.rename(target)
            except OSError:
                if backup.exists():
                    backup.rename(target)
                raise
        return manifest

    def set_enabled(self, plugin_id, enabled):
        item = next((p for p in self.installed() if p["id"] == plugin_id), None)
        if item is None:
            raise ValueError("Plugin introuvable")
        target = self.root / plugin_id / "state.json"
        state = json.loads(target.read_text(encoding="utf-8"))
        state["enabled"] = bool(enabled)
        temp = target.with_suffix(".tmp")
        temp.write_text(json.dumps(state), encoding="utf-8")
        temp.replace(target)

    def rollback(self, plugin_id):
        if not re.fullmatch(r"[a-z][a-z0-9-]{2,63}", plugin_id):
            raise ValueError("Identifiant invalide")
        target = self.root / plugin_id
        previous = self.root / ("." + plugin_id + ".previous")
        if not previous.is_dir():
            raise ValueError("Aucune version précédente")
        with tempfile.TemporaryDirectory(dir=self.root, prefix=".rollback-") as tmp:
            displaced = Path(tmp) / plugin_id
            target.rename(displaced)
            try:
                previous.rename(target)
            except OSError:
                displaced.rename(target)
                raise
