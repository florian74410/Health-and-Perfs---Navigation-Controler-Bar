"""Best-effort window priority, without stealing focus or bypassing the compositor."""
import os
import sys

def apply_priority(widget, enabled):
    if sys.platform=='win32':
        import ctypes
        from ctypes import wintypes
        set_position=ctypes.windll.user32.SetWindowPos
        set_position.argtypes=[wintypes.HWND,wintypes.HWND,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,wintypes.UINT]
        set_position.restype=wintypes.BOOL
        if not set_position(int(widget.winId()),-1 if enabled else -2,0,0,0,0,0x0013):
            return 'Windows : priorité refusée par le système.'
        return 'Windows : TOPMOST, sans activation. Plein écran exclusif non garanti.'
    if sys.platform.startswith('linux'):
        from PySide6.QtWidgets import QApplication
        if QApplication.platformName()!='xcb' or not os.getenv('DISPLAY'):
            return 'Wayland : placement et priorité dépendent du compositeur. Overlay global non garanti.'
        try:
            from Xlib import X, display, protocol
            connection=display.Display()
            try:
                window=connection.create_resource_object('window',int(widget.winId()))
                message=protocol.event.ClientMessage(window=window,client_type=connection.intern_atom('_NET_WM_STATE'),data=(32,[1 if enabled else 0,connection.intern_atom('_NET_WM_STATE_ABOVE'),0,1,0]))
                connection.screen().root.send_event(message,event_mask=X.SubstructureRedirectMask|X.SubstructureNotifyMask)
                connection.flush()
            finally:connection.close()
            return 'X11 : ABOVE demandé au gestionnaire de fenêtres ; plein écran non garanti.'
        except Exception as error:
            return 'X11 : priorité Qt uniquement ('+str(error)+').'
    return 'macOS : priorité Qt ; Spaces et plein écran contrôlés par macOS.'


def apply_all_workspaces(widget):
    """Best-effort EWMH sticky window for all virtual desktops on X11/XFCE.

    No workspace API is uniformly portable to Wayland, Windows Virtual Desktops
    or macOS Spaces; do not claim success on those platforms.
    """
    if not sys.platform.startswith("linux"):
        return False
    from PySide6.QtWidgets import QApplication
    if QApplication.platformName() != "xcb" or not os.getenv("DISPLAY"):
        return False
    try:
        from Xlib import X, Xatom, display, protocol
        connection = display.Display()
        try:
            window = connection.create_resource_object("window", int(widget.winId()))
            all_desktops = 0xFFFFFFFF
            atom = connection.intern_atom("_NET_WM_DESKTOP")
            window.change_property(atom, Xatom.CARDINAL, 32, [all_desktops])
            root = connection.screen().root
            message = protocol.event.ClientMessage(
                window=window, client_type=atom, data=(32, [all_desktops, 1, 0, 0, 0]))
            root.send_event(message, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
            sticky = connection.intern_atom("_NET_WM_STATE_STICKY")
            state = protocol.event.ClientMessage(
                window=window, client_type=connection.intern_atom("_NET_WM_STATE"),
                data=(32, [1, sticky, 0, 1, 0]))
            root.send_event(state, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
            connection.flush()
        finally:
            connection.close()
        return True
    except (OSError, ImportError, ValueError):
        return False
