#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/nexus-terminal"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$APP_DIR" "$BIN_DIR" "$DESKTOP_DIR"
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/python" -m pip install --only-binary=:all: -r "$HERE/requirements.txt"
install -m 644 "$HERE/terminal.py" "$APP_DIR/terminal.py"
cat > "$BIN_DIR/nexus-terminal" <<EOF
#!/usr/bin/env bash
exec "$APP_DIR/venv/bin/python" "$APP_DIR/terminal.py" "\$@"
EOF
chmod 755 "$BIN_DIR/nexus-terminal"
cat > "$DESKTOP_DIR/nexus-terminal.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=NEXUS Terminal
Comment=Terminal multi-panneaux BlueNeon
Exec=$BIN_DIR/nexus-terminal
Icon=utilities-terminal
Terminal=false
Categories=System;TerminalEmulator;
EOF
chmod 644 "$DESKTOP_DIR/nexus-terminal.desktop"
echo "Installé : $BIN_DIR/nexus-terminal"
