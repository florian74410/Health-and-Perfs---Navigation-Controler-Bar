"""Logical VT scrollback: real history, stable reading position and independent panes."""
import os
import tempfile
import unittest
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6 import QtCore as C, QtGui as G, QtWidgets as W
from nova_nexus.terminal import TerminalSession, TerminalView
from nova_nexus.terminal_manager import open_manager


class ScrollbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=W.QApplication.instance() or W.QApplication([])

    def make_view(self):
        session=TerminalSession();view=TerminalView(session)
        view.resize(800,400);view.show();self.app.processEvents()
        self.addCleanup(view.close);self.addCleanup(session.close)
        return session,view

    @staticmethod
    def feed(session,start,count):
        session.stream.feed(''.join(f'ROW_{i:05d}\r\n' for i in range(start,start+count)).encode())

    def test_scrollbar_reaches_real_history_without_mutating_live_screen(self):
        session,view=self.make_view();self.feed(session,0,300);view.render_screen()
        bar=view.history_scrollbar
        self.assertTrue(bar.isVisible());self.assertGreater(bar.maximum(),250)
        self.assertEqual(bar.value(),bar.maximum())
        live=list(session.screen.display)
        bar.setValue(0);view.render_screen()
        self.assertIn('ROW_00000',view.toPlainText())
        self.assertNotIn('ROW_00299',view.toPlainText())
        self.assertEqual(session.screen.display,live)
        bar.setValue(bar.maximum());view.render_screen()
        self.assertIn('ROW_00299',view.toPlainText())
        self.assertEqual(bar.mapTo(view,C.QPoint(0,0)).x()+bar.width(),view.width()-1)
        self.assertLessEqual(view.viewport().geometry().right(),bar.x())

    def test_scrolled_position_is_anchored_while_bounded_history_rotates(self):
        session,view=self.make_view();self.feed(session,0,2300);view.render_screen()
        bar=view.history_scrollbar;self.assertEqual(bar.maximum(),2000)
        bar.setValue(700);view.render_screen();first=view.toPlainText().splitlines()[0]
        self.feed(session,2300,150);view.render_screen()
        self.assertEqual(view.toPlainText().splitlines()[0],first)
        self.assertEqual(bar.value(),550)
        self.assertFalse(view.follow_output)
        self.assertLessEqual(view.document().blockCount(),session.screen.lines+1)
        self.feed(session,2450,2200);view.render_screen()
        self.assertEqual(bar.value(),0) # Requested lines expired from the bounded history.
        self.assertEqual(len(session.screen.history.top),2000)
        view.follow_live();view.render_screen();self.assertIn('ROW_04649',view.toPlainText())

    def test_wheel_page_keys_and_input_follow_live_output(self):
        session,view=self.make_view();self.feed(session,0,150);view.render_screen();bar=view.history_scrollbar
        maximum=bar.maximum()
        event=G.QWheelEvent(C.QPointF(20,20),C.QPointF(20,20),C.QPoint(),C.QPoint(0,120),C.Qt.NoButton,C.Qt.NoModifier,C.Qt.NoScrollPhase,False)
        view.wheelEvent(event);view.render_screen();self.assertEqual(bar.value(),maximum-3)
        self.app.sendEvent(view,G.QKeyEvent(C.QEvent.KeyPress,C.Qt.Key_PageUp,C.Qt.ShiftModifier))
        view.render_screen();self.assertEqual(bar.value(),maximum-3-bar.pageStep())
        with patch.object(session,'write') as write:
            self.app.sendEvent(view,G.QKeyEvent(C.QEvent.KeyPress,C.Qt.Key_X,C.Qt.NoModifier,'x'))
            view.render_screen();write.assert_called_once_with(b'x')
        self.assertTrue(view.follow_output);self.assertEqual(bar.value(),maximum)
        self.feed(session,150,10);view.render_screen();self.assertEqual(bar.value(),bar.maximum())

    def test_split_panes_scroll_independently_and_style_survives_text_preferences(self):
        with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,HEALTHBAR_DATA_DIR=temp):
            manager=open_manager(start=False)
            try:
                manager.workspace().set_format('columns');self.app.processEvents()
                a,b=manager.workspace().panes[:2]
                for pane in (a,b):self.feed(pane.session,0,150);pane.view.render_screen()
                a.view.history_scrollbar.setValue(0);a.view.render_screen()
                self.assertIn('ROW_00000',a.view.toPlainText())
                self.assertEqual(b.view.history_scrollbar.value(),b.view.history_scrollbar.maximum())
                manager.text['size']=14;manager.apply_text(a.view);self.app.processEvents();a.view.render_screen()
                self.assertTrue(a.view.history_scrollbar.isVisible())
                self.assertIn('#00CBF3',a.view.history_scrollbar.styleSheet())
                self.assertEqual(a.view.history_scrollbar.value(),0)
            finally:manager.window.close()
