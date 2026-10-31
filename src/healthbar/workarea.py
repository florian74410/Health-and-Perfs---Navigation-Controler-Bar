"""Advertise the visible HUD edge to X11 window managers using EWMH struts."""
import os
import sys
from PySide6.QtCore import QRect


def top_strut(rect, root):
    """Native pixel coordinates; partial X span avoids reserving other monitors.

    EWMH struts originate at the root edge. Never cover a monitor above an
    internal edge in a vertically stacked arrangement.
    """
    visible=rect.intersected(root)
    values=[0]*12
    if visible.isEmpty() or rect.top()!=root.top():return values
    values[2]=visible.bottom()-root.top()+1
    values[8]=visible.left()-root.left()
    values[9]=visible.right()-root.left()
    return values


def reserve_top(widget, enabled):
    from PySide6.QtWidgets import QApplication
    if not sys.platform.startswith('linux') or not os.getenv('DISPLAY') or QApplication.platformName()!='xcb':
        return False
    connection=None
    try:
        from Xlib import Xatom,display
        connection=display.Display();root=connection.screen().root
        window=connection.create_resource_object('window',int(widget.winId()))
        partial=connection.intern_atom('_NET_WM_STRUT_PARTIAL')
        legacy=connection.intern_atom('_NET_WM_STRUT')
        if enabled:
            geometry=window.get_geometry();point=root.translate_coords(window,0,0)
            bounds=root.get_geometry()
            values=top_strut(QRect(point.x,point.y,geometry.width,geometry.height),QRect(0,0,bounds.width,bounds.height))
            if any(values):
                window.change_property(connection.intern_atom('_NET_WM_WINDOW_TYPE'),Xatom.ATOM,32,
                                       [connection.intern_atom('_NET_WM_WINDOW_TYPE_DOCK')])
                window.change_property(partial,Xatom.CARDINAL,32,values)
                window.change_property(legacy,Xatom.CARDINAL,32,values[:4])
            else:
                window.delete_property(partial);window.delete_property(legacy)
        else:
            window.delete_property(partial);window.delete_property(legacy)
        connection.flush()
        return True
    except Exception:
        # Overlay still works on compositors that do not expose these properties.
        return False
    finally:
        if connection:connection.close()
