#!/bin/sh
# Installed from the extracted Linux binary archive. No root, pip or Python needed.
set -eu
cd -- "$(dirname -- "$0")"
target="$HOME/.local/share/health-perfs-bar/native"
mkdir -p "$target" "${XDG_DATA_HOME:-$HOME/.local/share}/applications"
cp -R HealthPerfsBar/. "$target/"
chmod +x "$target/HealthPerfsBar"
# Desktop Entry Exec quoting includes %, $, backtick and backslash.
exec_path=$(printf '%s' "$target/HealthPerfsBar" | sed 's/\\/\\\\/g; s/"/\\"/g; s/`/\\`/g; s/\$/\\$/g; s/%/%%/g')
cat > "${XDG_DATA_HOME:-$HOME/.local/share}/applications/health-perfs-bar.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Health & Perfs Bar
Exec="$exec_path"
Terminal=false
Categories=System;Monitor;
DESKTOP
"$target/HealthPerfsBar" --setup &
