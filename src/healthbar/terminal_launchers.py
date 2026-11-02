"""Route plain desktop terminal shortcuts to NOVA without changing command launchers."""
import configparser
import os
from pathlib import Path
import shlex


def is_nova_terminal_shortcut(path):
    try:
        parser=configparser.ConfigParser(interpolation=None,strict=False)
        parser.read(path,encoding='utf-8');entry=parser['Desktop Entry']
        if entry.get('Type')!='Application':return False
        words=shlex.split(entry.get('Exec',''))
        if not words:return False
        if Path(path).name=='nova-nexus-terminal.desktop':
            return entry.getboolean('X-NOVA-Owned',False) and ('--nova-terminal' in words or 'nova_nexus.terminal' in words)
        executable=Path(words[0]).name
        args=[word for word in words[1:] if word not in ('%f','%F','%u','%U')]
        if executable in ('xfce4-terminal','x-terminal-emulator','sensible-terminal'):
            return not args
        return executable=='exo-open' and args==['--launch','TerminalEmulator']
    except (OSError,ValueError,KeyError,configparser.Error):return False


def preferred_terminal_launcher(path):
    if not is_nova_terminal_shortcut(path):return path
    roots=[Path(os.getenv('XDG_DATA_HOME',str(Path.home()/'.local/share'))),Path.home()/'.local/share']
    for root in roots:
        candidate=root/'applications/nova-nexus-terminal.desktop'
        if candidate.is_file() and is_nova_terminal_shortcut(candidate):return str(candidate)
    return path
