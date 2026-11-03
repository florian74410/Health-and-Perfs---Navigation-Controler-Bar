"""NEXUS Web Inspector — Qt-first request metadata inspection, external browser default.

Not a transparent HTTPS MITM proxy: response bodies and TLS traffic of other
applications are NOT intercepted. Use mitmproxy as an opt-in separate layer.
"""
from __future__ import annotations
from collections import deque
from urllib.parse import urlsplit, urlunsplit
from PySide6.QtCore import Qt, QUrl, Signal, QTimer
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QCheckBox, QMessageBox, QHeaderView
)

def display_url(raw):
    """Avoid revealing credentials, query tokens, and fragments in the log."""
    parts=urlsplit(raw)
    if parts.scheme not in ("http","https"):
        return "[unsupported URL]"
    host=parts.hostname or ""
    if not host:return "[invalid URL]"
    if ":" in host and not host.startswith("["):host="["+host+"]"
    if parts.port:host+=f":{parts.port}"
    return urlunsplit((parts.scheme,host,parts.path,"",""))

class WebInspector(QWidget):
    request_captured=Signal(str,str,str)
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowTitle("NEXUS / WEB INSPECTOR")
        self.records=deque(maxlen=500)
        self.view=None
        self.profile=None
        self.interceptor=None
        root=QVBoxLayout(self)
        root.setContentsMargins(9,9,9,9)
        self.heading=QLabel("◉ WEB INSPECTOR  /  HTTP REQUEST MONITOR")
        self.heading.setStyleSheet("color:#55E4FF;font-size:13px;font-weight:bold;")
        root.addWidget(self.heading)
        bar=QHBoxLayout()
        self.address=QLineEdit("https://example.org")
        self.address.setPlaceholderText("https://example.org")
        bar.addWidget(self.address,1)
        open_default=QPushButton("↗  Navigateur par défaut")
        open_default.clicked.connect(self.open_external)
        bar.addWidget(open_default)
        embedded=QPushButton("◈  Inspecter dans Qt")
        embedded.clicked.connect(self.open_embedded)
        bar.addWidget(embedded)
        root.addLayout(bar)
        note=QLabel("Seules les requêtes initiées dans la vue Qt intégrée sont inspectées. "
                    "En-têtes sensibles, cookies et paramètres de requête ne sont pas journalisés.")
        note.setWordWrap(True)
        note.setStyleSheet("color:#86B8D1;")
        root.addWidget(note)
        self.table=QTableWidget(0,3)
        self.table.setHorizontalHeaderLabels(["Méthode","Adresse sans paramètres","Type"])
        self.table.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        root.addWidget(self.table,1)
        self.embed_container=QVBoxLayout()
        root.addLayout(self.embed_container,2)
        clear=QPushButton("Effacer le journal")
        clear.clicked.connect(self.clear_records)
        root.addWidget(clear)
        self.request_captured.connect(self.append_record)
    def url(self):
        url=QUrl.fromUserInput(self.address.text().strip())
        if not url.isValid() or url.scheme() not in ("https","http") or not url.host():
            QMessageBox.warning(self,"WEB","URL HTTP(S) invalide.")
            return None
        return url
    def open_external(self):
        url=self.url()
        if url is not None:
            if not QDesktopServices.openUrl(url):
                QMessageBox.warning(self,"WEB","Impossible d'ouvrir le navigateur par défaut.")
    def open_embedded(self):
        url=self.url()
        if url is None:return
        try:
            from PySide6.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineProfile, QWebEnginePage
            from PySide6.QtWebEngineWidgets import QWebEngineView
        except ImportError:
            QMessageBox.information(self,"Qt WebEngine",
                "Qt WebEngine n'est pas installé.\n"
                "Installer PySide6-Addons / PySide6 QtWebEngine selon la distribution.")
            return
        if self.view is None:
            receiver=self.request_captured
            class Interceptor(QWebEngineUrlRequestInterceptor):
                def interceptRequest(self,info):
                    try:
                        # Do not block request thread with UI work or network calls.
                        method=bytes(info.requestMethod()).decode("ascii","replace")[:12]
                        url=display_url(info.requestUrl().toString())
                        kind=str(info.resourceType()).split(".")[-1]
                        receiver.emit(method,url,kind)
                    except Exception:
                        pass
            self.profile=QWebEngineProfile(self)
            self.interceptor=Interceptor(self.profile)
            self.profile.setUrlRequestInterceptor(self.interceptor)
            self.view=QWebEngineView(self)
            self.view.setPage(QWebEnginePage(self.profile,self.view))
            self.embed_container.addWidget(self.view)
        self.view.setUrl(url)
    def append_record(self,method,url,kind):
        self.records.append((method,url,kind))
        row=self.table.rowCount()
        if row>=500:
            self.table.removeRow(0)
            row=499
        self.table.insertRow(row)
        for i,item in enumerate((method,url,kind)):
            self.table.setItem(row,i,QTableWidgetItem(str(item)))
        self.table.scrollToBottom()
    def clear_records(self):
        self.records.clear()
        self.table.setRowCount(0)
