"""NOVA Terminal: shared glass chassis and a real Linux PTY with VT emulation."""
from __future__ import annotations
import html
import os
from pathlib import Path
import signal
import struct
import subprocess
import sys
import threading
from PySide6 import QtCore as C, QtGui as G, QtWidgets as W
import pyte
from healthbar.system_env import native_env
from .chrome_v3 import make_window


def pty_child(fd, shell):
    """Fresh helper process: acquire a controlling TTY before exec, outside Qt threads."""
    if not sys.platform.startswith('linux'):
        return 2
    if hasattr(os, 'login_tty'):
        os.login_tty(fd)
    else:
        import fcntl, termios
        os.setsid()
        fcntl.ioctl(fd, termios.TIOCSCTTY, 0)
        for standard in range(3):os.dup2(fd, standard)
        if fd > 2:os.close(fd)
    env=native_env()
    env.update(TERM='linux',COLORTERM='truecolor')
    os.execve(shell,[shell,'-i'],env)


class TerminalSession(C.QObject):
    changed=C.Signal()
    finished=C.Signal(int)
    def __init__(self, parent=None, *, shell=None, cwd=None):
        super().__init__(parent)
        self.fd=None;self.process=None;self.notifier=None;self.pending=bytearray()
        self.screen=pyte.HistoryScreen(100,28,history=2000)
        self.stream=pyte.ByteStream(self.screen)
        self.screen.write_process_input=lambda text:self.write(text.encode())
        self.shell=shell or os.environ.get('SHELL') or '/bin/bash'
        self.cwd=Path(cwd or Path.home())
        self.poll=C.QTimer(self);self.poll.setInterval(100);self.poll.timeout.connect(self.check_exit)
        self.flush_timer=C.QTimer(self);self.flush_timer.setInterval(10);self.flush_timer.timeout.connect(self.flush)

    def start(self):
        if not sys.platform.startswith('linux'):
            raise OSError('NOVA Terminal nécessite Linux dans cette version')
        if not Path(self.shell).is_file() or not os.access(self.shell,os.X_OK):
            raise OSError('Shell introuvable : '+self.shell)
        import pty
        master,slave=pty.openpty()
        self.fd=master
        try:
            command=([sys.executable] if getattr(sys,'frozen',False) else [sys.executable,'-m','healthbar'])
            command+=['--nova-pty-child',str(slave),'--nova-shell',self.shell]
            environment=dict(native_env(),PYINSTALLER_RESET_ENVIRONMENT='1')
            if not getattr(sys,'frozen',False):
                environment['PYTHONPATH']=str(Path(__file__).resolve().parents[1])+os.pathsep+environment.get('PYTHONPATH','')
            self.process=subprocess.Popen(command,pass_fds=(slave,),cwd=self.cwd,
                env=environment,
                stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        except Exception:
            os.close(master);self.fd=None
            raise
        finally:os.close(slave)
        os.set_blocking(master,False)
        self.notifier=C.QSocketNotifier(master,C.QSocketNotifier.Read,self)
        self.notifier.activated.connect(self.read)
        self.resize(self.screen.columns,self.screen.lines)
        self.poll.start()

    def resize(self,columns,lines):
        columns=max(20,min(400,columns));lines=max(5,min(160,lines))
        self.screen.resize(lines=lines,columns=columns)
        if self.fd is not None:
            import fcntl,termios
            fcntl.ioctl(self.fd,termios.TIOCSWINSZ,struct.pack('HHHH',lines,columns,0,0))
        self.changed.emit()

    def write(self,data):
        if self.fd is None:return
        # Bound paste buffering; keep order across short nonblocking writes.
        if len(self.pending)+len(data)>1024*1024:return
        self.pending.extend(data);self.flush()

    def flush(self):
        if self.fd is None:
            self.flush_timer.stop();return
        try:
            if self.pending:
                count=os.write(self.fd,self.pending)
                del self.pending[:count]
        except BlockingIOError:pass
        except OSError:self.pending.clear()
        if self.pending:self.flush_timer.start()
        else:self.flush_timer.stop()

    def read(self,*_):
        if self.fd is None:return
        # Bound each event callback so continuous output cannot starve the UI.
        try:
            for _ in range(16):
                data=os.read(self.fd,65536)
                if not data:
                    self.notifier.setEnabled(False);break
                self.stream.feed(data)
        except BlockingIOError:pass
        except OSError:
            self.notifier.setEnabled(False)
        self.changed.emit()

    def check_exit(self):
        if self.process is not None and self.process.poll() is not None:
            code=self.process.returncode
            self.read();self.close();self.finished.emit(code)

    def close(self):
        self.poll.stop();self.flush_timer.stop()
        if self.notifier:self.notifier.setEnabled(False)
        if self.fd is not None:
            # Closing a controlling PTY sends SIGHUP to its foreground job.
            os.close(self.fd);self.fd=None
        process=self.process
        self.process=None
        if process is not None:
            def reap():
                try:process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    try:process.wait(timeout=2)
                    except subprocess.TimeoutExpired:process.kill();process.wait()
            threading.Thread(target=reap,daemon=True).start()


ANSI={'default':'#E9F6FF','black':'#172A39','red':'#FF647C','green':'#53D6AE',
      'brown':'#E9BA69','blue':'#6BAEFF','magenta':'#CF94EF','cyan':'#59DFEC','white':'#E9F6FF',
      'brightblack':'#718B9D','brightred':'#FF8BA0','brightgreen':'#82F0C9',
      'brightbrown':'#FFE09C','brightblue':'#A1D1FF','brightmagenta':'#E5BCFF',
      'brightcyan':'#A2F4FF','brightwhite':'#FFFFFF'}


def ansi_color(value,default):
    if value=='default':return default
    return ANSI.get(value,'#'+value if len(value)==6 and all(c in '0123456789abcdefABCDEF' for c in value) else default)


class TerminalView(W.QTextEdit):
    def __init__(self,session,parent=None):
        super().__init__(parent);self.session=session
        self.setReadOnly(True);self.setAcceptRichText(False)
        self.setLineWrapMode(W.QTextEdit.NoWrap)
        self.setVerticalScrollBarPolicy(C.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(C.Qt.ScrollBarAlwaysOff)
        self.document().setDocumentMargin(0)
        self.setFont(G.QFont('DejaVu Sans Mono',11))
        self.setStyleSheet('QTextEdit{background:rgba(4,16,27,220);color:#E9F6FF;border:1px solid #22657F;padding:8px;selection-background-color:#22586F;}')
        self.setFocusPolicy(C.Qt.StrongFocus)
        self.render_timer=C.QTimer(self);self.render_timer.setSingleShot(True);self.render_timer.setInterval(25)
        self.render_timer.timeout.connect(self.render_screen)
        session.changed.connect(self.request_render)

    def request_render(self):
        if not self.render_timer.isActive():self.render_timer.start()

    def render_screen(self):
        screen=self.session.screen;lines=[]
        for y in range(screen.lines):
            spans=[];group='';previous=None
            for x in range(screen.columns):
                char=screen.buffer[y][x]
                fg=ansi_color(char.fg,getattr(self,'foreground','#E9F6FF'));bg=ansi_color(char.bg,'transparent')
                if char.reverse:fg,bg=('#071523' if bg=='transparent' else bg),fg
                cursor=(not screen.cursor.hidden and x==screen.cursor.x and y==screen.cursor.y)
                style=(fg,'#285E73' if cursor else bg,char.bold,char.italics,char.underscore)
                if style!=previous and group:
                    spans.append(self.span(previous,group));group=''
                previous=style;group+=char.data
            if group:spans.append(self.span(previous,group))
            lines.append(''.join(spans))
        family=html.escape(self.font().family().replace("'", ""),quote=True)
        self.setHtml('<pre style="margin:0;font-family:\'%s\';font-size:%dpt;">' %
                     (family,self.font().pointSize())+'\n'.join(lines)+'</pre>')

    @staticmethod
    def span(style,text):
        fg,bg,bold,italic,underline=style
        return '<span style="color:%s;background-color:%s;font-weight:%s;font-style:%s;text-decoration:%s">%s</span>' % (fg,bg,'bold' if bold else 'normal','italic' if italic else 'normal','underline' if underline else 'none',html.escape(text))

    def resizeEvent(self,event):
        super().resizeEvent(event)
        self.sync_size()

    def sync_size(self):
        metrics=G.QFontMetricsF(self.font())
        self.session.resize(int((self.viewport().width()-16)/metrics.horizontalAdvance('M')),
                            int((self.viewport().height()-16)/metrics.height()))

    def paste_text(self):
        text=W.QApplication.clipboard().text().replace('\r\n','\n').replace('\r','\n')
        if 2004<<5 in self.session.screen.mode:text='\x1b[200~'+text+'\x1b[201~'
        self.session.write(text.encode('utf-8'))

    def keyPressEvent(self,event):
        control=bool(event.modifiers()&C.Qt.ControlModifier)
        shift=bool(event.modifiers()&C.Qt.ShiftModifier)
        if control and shift and event.key()==C.Qt.Key_C:
            self.copy();return
        if control and shift and event.key()==C.Qt.Key_V:
            self.paste_text();return
        if shift and event.key() in (C.Qt.Key_PageUp,C.Qt.Key_PageDown):
            (self.session.screen.prev_page if event.key()==C.Qt.Key_PageUp else self.session.screen.next_page)()
            self.request_render();return
        keys={C.Qt.Key_Return:b'\r',C.Qt.Key_Enter:b'\r',C.Qt.Key_Backspace:b'\x7f',
              C.Qt.Key_Tab:b'\t',C.Qt.Key_Backtab:b'\x1b[Z',C.Qt.Key_Escape:b'\x1b',
              C.Qt.Key_Up:b'\x1b[A',C.Qt.Key_Down:b'\x1b[B',C.Qt.Key_Right:b'\x1b[C',C.Qt.Key_Left:b'\x1b[D',
              C.Qt.Key_Home:b'\x1b[H',C.Qt.Key_End:b'\x1b[F',C.Qt.Key_Delete:b'\x1b[3~',
              C.Qt.Key_Insert:b'\x1b[2~',C.Qt.Key_PageUp:b'\x1b[5~',C.Qt.Key_PageDown:b'\x1b[6~'}
        if control and C.Qt.Key_A<=event.key()<=C.Qt.Key_Z:
            data=bytes([event.key()-C.Qt.Key_A+1])
        else:data=keys.get(event.key(),event.text().encode('utf-8'))
        if event.modifiers()&C.Qt.AltModifier and event.text():data=b'\x1b'+data
        self.session.write(data)

    def contextMenuEvent(self,event):
        menu=W.QMenu(self)
        menu.addAction('Copier · Ctrl+Maj+C',self.copy)
        menu.addAction('Coller · Ctrl+Maj+V',self.paste_text)
        menu.exec(event.globalPos())


_windows=[]


def open_terminal(*,start=True,cwd=None):
    if start and not sys.platform.startswith('linux'):
        raise OSError('NOVA Terminal interactif est disponible sous Linux')
    content=W.QWidget();layout=W.QVBoxLayout(content);layout.setContentsMargins(0,0,0,0)
    session=TerminalSession(content,cwd=cwd)
    view=TerminalView(session);layout.addWidget(view,1)
    status=W.QLabel('SHELL INTERACTIF  /  Ctrl+Maj+C copier · Ctrl+Maj+V coller · Maj+Page ↑↓ historique')
    status.setStyleSheet('color:#A6BFCD;font:10px Arial;');layout.addWidget(status)
    window=make_window('NOVA / TERMINAL',content)
    window.setMinimumSize(640,380);window.resize(1024,640)
    window.session=session;window.terminal_view=view
    session.finished.connect(lambda code:status.setText('SESSION TERMINÉE · code '+str(code)))
    class CloseFilter(C.QObject):
        def eventFilter(self,watched,event):
            if event.type()==C.QEvent.Close:session.close()
            return False
    window.close_filter=CloseFilter(window);window.installEventFilter(window.close_filter)
    window.setAttribute(C.Qt.WA_DeleteOnClose)
    _windows.append(window)
    window.destroyed.connect(lambda *_:_windows.remove(window) if window in _windows else None)
    window.show();view.setFocus()
    if start:
        try:session.start()
        except Exception:
            window.close();raise
    return window


def run():
    app=W.QApplication.instance() or W.QApplication(sys.argv[:1])
    open_terminal()
    return app.exec()


if __name__=='__main__':
    from .terminal_manager import run
    raise SystemExit(run())
