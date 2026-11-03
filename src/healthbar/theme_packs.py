"""Validated, interchangeable NovaBar skin packs (stdlib-only, no Qt dependency).

Builtin skins ship with NovaBar; user packs live in
<config>/Themes/<id>/manifest.json and survive application upgrades.
A skin never executes code, changes plugins, or modifies XFCE settings.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ID = re.compile(r"^[a-z][a-z0-9_-]{2,47}$")
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
BASE = Path(__file__).resolve().parent / "assets" / "skins"
ASSET_KEYS = frozenset({"pcb", "frame", "notification", "button", "wallpaper"})
MAX_MANIFEST_BYTES = 32 * 1024
MAX_ASSET_BYTES = 12 * 1024 * 1024


def user_root() -> Path:
    from .config import data_dir
    return data_dir() / "Themes"


def _safe_asset(folder: Path, filename: str) -> Path | None:
    if not isinstance(filename, str) or not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9_.-]{0,100}\.(?:svg|png|webp)", filename):
        return None
    candidate = folder / filename
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(folder.resolve(strict=True))
        if not resolved.is_file() or resolved.stat().st_size > MAX_ASSET_BYTES:
            return None
        return resolved
    except (OSError, ValueError, RuntimeError):
        return None


def _read(folder: Path) -> dict | None:
    try:
        path = folder / "manifest.json"
        if path.is_symlink() or path.stat().st_size > MAX_MANIFEST_BYTES:
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("id") != folder.name or not ID.fullmatch(folder.name):
            return None
        label = data.get("name")
        if not isinstance(label, str) or not 1 <= len(label) <= 70 or any(ord(c)<32 for c in label):
            return None
        palette = data.get("palette")
        if not isinstance(palette, dict) or not all(
            isinstance(palette.get(key), str) and HEX.fullmatch(palette[key])
            for key in ("primary", "secondary", "background", "surface", "text")):
            return None
        assets = data.get("assets", {})
        if not isinstance(assets, dict) or set(assets) - ASSET_KEYS:
            return None
        if any(_safe_asset(folder, filename) is None for filename in assets.values()):
            return None
        return {"id": folder.name, "name": label, "palette": dict(palette),
                "assets": dict(assets), "version": str(data.get("version", "1"))[:32],
                "root": str(folder)}
    except (OSError, ValueError, TypeError, UnicodeError):
        return None


def get_pack(theme: str) -> dict | None:
    if not isinstance(theme, str) or not ID.fullmatch(theme):
        return None
    # System builtin skins cannot be shadowed by a user's external pack.
    folder = BASE / theme
    if folder.is_dir():
        return _read(folder)
    folder = user_root() / theme
    if folder.is_dir() and not folder.is_symlink():
        return _read(folder)
    return None


def list_packs() -> dict[str, str]:
    result = {}
    for root in (BASE, user_root()):
        if not root.is_dir():
            continue
        for folder in sorted(root.iterdir()):
            if folder.is_dir() and not folder.is_symlink() and folder.name not in result:
                pack = _read(folder)
                if pack:
                    result[pack["id"]] = pack["name"]
    return result


def known_theme(theme: str) -> bool:
    return theme in ("cyber-futuriste", "blue-neon", "green-matrix", "red-blood") or get_pack(theme) is not None


def asset_path(theme: str, role: str) -> Path | None:
    pack = get_pack(theme)
    if not pack or role not in ASSET_KEYS:
        return None
    name = pack["assets"].get(role)
    return _safe_asset(Path(pack["root"]), name) if name else None

def recolor_qss(source: str, theme: str) -> str:
    """Retint old blue QSS RGB/RGBA surfaces without altering white text or warnings."""
    pack = get_pack(theme)
    if not pack:
        return source
    import colorsys
    hue = int(pack["palette"]["primary"][1:3], 16) / 255
    green = int(pack["palette"]["primary"][3:5], 16) / 255
    blue = int(pack["palette"]["primary"][5:7], 16) / 255
    target_hue = colorsys.rgb_to_hsv(hue, green, blue)[0]

    def rgb_match(match):
        channel = [int(match.group(i)) for i in (2, 3, 4)]
        old_h, sat, val = colorsys.rgb_to_hsv(*(c/255 for c in channel))
        # Only decorative blue shades. Keep warning red, success green,
        # white typography and true neutral blacks entirely unchanged.
        if not (.46 <= old_h <= .72 and sat > .12):
            return match.group(0)
        new_rgb = [round(255*c) for c in colorsys.hsv_to_rgb(target_hue,sat,val)]
        return match.group(1) + ",".join(str(c) for c in new_rgb) + match.group(5) + ")"

    return re.sub(
        r"(rgba?\(\s*)(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})(\s*(?:,\s*(?:[0-9.]+|[0-9]+%)\s*)?)\)",
        rgb_match, source, flags=re.IGNORECASE)
