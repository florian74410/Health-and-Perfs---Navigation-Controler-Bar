"""Generate native XFWM4 XPM pixmaps and themerc for a NOVA window theme.

Exports files to a selected directory; never activates xfconf or changes system
settings. XPM is supported by XFWM4 and can be generated without image libraries.
"""
from __future__ import annotations
from pathlib import Path
from .theme_engine import get_default_theme, validate_theme


def _xpm(path, pixels, colors):
    height = len(pixels)
    width = len(pixels[0])
    if any(len(row) != width for row in pixels):
        raise ValueError("Non-rectangular XPM")
    lines = ['/* XPM */', 'static char * icon[] = {',
             f'"{width} {height} {len(colors)} 1",']
    for key, color in colors.items():
        lines.append(f'"{key} c {color}",')
    lines.extend(f'"{row}"' + (',' if i + 1 < height else '') for i, row in enumerate(pixels))
    lines.append('};')
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def _button(symbol, active):
    # 24x24 chunky, square PCB buttons: border + hard bevel + visible symbol.
    p = [['.' for _ in range(24)] for _ in range(24)]
    for y in range(3, 21):
        for x in range(3, 21):
            if (x+y >= 10 and (23-x)+y >= 10 and x+(23-y) >= 10 and (23-x)+(23-y) >= 10):
                p[y][x] = 'b' if active else 'd'
    for y in range(5, 19):
        for x in range(5, 19):
            if p[y][x] != '.':
                p[y][x] = 'f'
    for x in range(7, 17):
        p[21][x] = 'r'
    if symbol == "close":
        for i in range(8, 16):
            p[i][i] = 's'
            p[i][23-i] = 's'
    elif symbol == "restore":
        for left, top in ((10, 7), (7, 10)):
            for x in range(left, left + 7):
                p[top][x] = p[top + 6][x] = "s"
            for y in range(top, top + 7):
                p[y][left] = p[y][left + 6] = "s"
    elif symbol == "maximize":
        for x in range(8, 16):
            p[8][x] = 's'
            p[15][x] = 's'
        for y in range(8, 16):
            p[y][8] = p[y][15] = 's'
    elif symbol == "hide":
        for x in range(8, 16):
            p[15][x] = 's'
    elif symbol == "menu":
        for x in range(8, 16):
            p[10][x] = p[13][x] = 's'
    elif symbol == "shade":
        for x in range(8, 16):
            p[10][x] = 's'
    elif symbol == "stick":
        for i in range(8, 16):
            p[11][i] = 's'
    return [''.join(row) for row in p]


def export_xfwm4_theme(destination, theme=None):
    """Write an XFWM4 pixmap candidate for visual testing and manual opt-in."""
    t = validate_theme(theme or get_default_theme())
    c = t["colors"]
    target = Path(destination).expanduser() / "xfwm4"
    target.mkdir(parents=True, exist_ok=True)
    colors = {".": "None", "b": c["primary"], "d": c["text_muted"],
              "f": c["surface"], "s": c["danger"], "r": c["secondary"]}
    for state in ("active", "inactive", "pressed", "prelight"):
        palette = dict(colors)
        if state in ("pressed", "prelight"):
            palette["f"] = c["secondary"]
        for name in ("close", "maximize", "hide", "menu", "shade", "stick"):
            _xpm(target / f"{name}-{state}.xpm", _button(name, True), palette)
            if name in ("maximize", "shade", "stick"):
                symbol = "restore" if name == "maximize" else name
                _xpm(target / f"{name}-toggled-{state}.xpm", _button(symbol, True), palette)
    # Edges and title strip: actual XFWM4 theme parts, not perspective illustrations.
    for state in ("active", "inactive"):
        border = "b" if state == "active" else "d"
        # XFWM assembles five separate title segments. Missing parts can leave
        # an empty/invalid title rail even though individual button pixmaps exist.
        for number in range(1, 6):
            pixels = [border * 32] + ["f" * 32 for _ in range(28)] + [border * 32]
            _xpm(target / f"title-{number}-{state}.xpm", pixels, colors)
            _xpm(target / f"top-{number}-{state}.xpm", [border * 32], colors)
        _xpm(target / f"top-left-{state}.xpm", [border * 4 for _ in range(30)], colors)
        _xpm(target / f"top-right-{state}.xpm", [border * 4 for _ in range(30)], colors)
        _xpm(target / f"left-{state}.xpm", [border * 3 for _ in range(8)], colors)
        _xpm(target / f"right-{state}.xpm", [border * 3 for _ in range(8)], colors)
        _xpm(target / f"bottom-{state}.xpm", [border * 24 for _ in range(3)], colors)
        _xpm(target / f"bottom-left-{state}.xpm", [border * 4 for _ in range(4)], colors)
        _xpm(target / f"bottom-right-{state}.xpm", [border * 4 for _ in range(4)], colors)
    (target / "themerc").write_text(
        "button_offset=3\nbutton_spacing=4\nbutton_layout=O|HMC\n"
        "maximized_offset=0\n"
        "title_vertical_offset_active=2\n"
        "title_vertical_offset_inactive=2\n"
        "title_horizontal_offset=8\n"
        "show_app_icon=true\n"
        "full_width_title=true\n"
        f"active_text_color={c['text']}\n"
        f"inactive_text_color={c['text_muted']}\n"
        "shadow_delta_x=1\nshadow_delta_y=2\n"
        "shadow_delta_width=0\nshadow_delta_height=0\n",
        encoding="utf-8")
    return target
