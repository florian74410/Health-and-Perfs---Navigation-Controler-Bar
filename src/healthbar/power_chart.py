"""Bounded history of measured/calculated battery discharge power."""
from PySide6 import QtCore as C, QtGui as G, QtWidgets as W


class PowerChart(W.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.samples = []
        self.setMinimumHeight(100)
        self.setAccessibleName('Historique de puissance batterie en watts')

    def record(self, data):
        self.samples = data.get('battery_power_history', [])[-120:]
        self.update()

    def paintEvent(self, event):
        p = G.QPainter(self)
        p.setRenderHint(G.QPainter.Antialiasing)
        area = self.rect().adjusted(40, 24, -12, -20)
        p.fillRect(self.rect(), G.QColor('#09111B'))
        values = [w for _, w in self.samples if w is not None]
        peak = max([1, *values])
        p.setPen(G.QColor('#A6BFCD'))
        p.drawText(8, 17, f'BATTERIE · W · maximum visible {peak:.1f}')
        p.setPen(G.QColor('#277FEA'))
        p.drawRect(area)
        if len(self.samples) > 1:
            start, end = self.samples[0][0], self.samples[-1][0]
            line = G.QPainterPath()
            connected = False
            for at, watts in self.samples:
                if watts is None:
                    connected = False
                    continue
                point = C.QPointF(area.left() + (at-start)/max(.001,end-start)*area.width(),
                                 area.bottom() - watts/peak*area.height())
                if connected: line.lineTo(point)
                else: line.moveTo(point)
                connected = True
            p.setPen(G.QPen(G.QColor('#00CBF3'), 2))
            p.drawPath(line)
        p.end()
