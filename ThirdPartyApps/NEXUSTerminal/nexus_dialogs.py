"""NEXUS Terminal glass dialogs — Qt-only, safe configuration and SSH profiles."""
from __future__ import annotations
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from PySide6.QtCore import Qt, QProcess, QSettings, Signal, QPoint, QUrl
from PySide6.QtGui import QPainter, QPainterPath, QPen, QColor, QLinearGradient, QFont
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget,
    QLineEdit, QLabel, QPushButton, QComboBox, QCheckBox, QSpinBox,
    QSlider, QListWidget, QListWidgetItem, QFileDialog, QMessageBox,
    QDialogButtonBox, QFrame, QGraphicsDropShadowEffect, QInputDialog
)

CONFIG_DIR=Path.home()/".config"/"nexus-terminal"
PROFILES=CONFIG_DIR/"connections.json"
API_PROFILES=CONFIG_DIR/"api_profiles.json"
HOST_RE=re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,252}$")
USER_RE=re.compile(r"^[a-zA-Z_][a-zA-Z0-9_.-]{0,63}$")
ID_RE=re.compile(r"^[a-zA-Z0-9_. -]{1,64}$")
COLORS={"blue":("#00D8FF","#78EEFF"),"red":("#FF3153","#FF899C")}

def profiles_read():
    try:
        data=json.loads(PROFILES.read_text(encoding="utf-8"))
        if isinstance(data,list):
            return [p for p in data if isinstance(p,dict)][:100]
    except (ValueError,OSError):
        pass
    return []

def profiles_write(rows):
    CONFIG_DIR.mkdir(parents=True,exist_ok=True)
    try:os.chmod(CONFIG_DIR,0o700)
    except OSError:pass
    tmp=PROFILES.with_suffix(".tmp")
    tmp.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
    os.chmod(tmp,0o600)
    tmp.replace(PROFILES)

def safe_ssh(profile):
    host=str(profile.get("host","")).strip()
    username=str(profile.get("user","")).strip()
    port=int(profile.get("port",22))
    identity=str(profile.get("key_path","")).strip()
    if not HOST_RE.fullmatch(host) or not USER_RE.fullmatch(username):
        raise ValueError("Nom d'hôte ou utilisateur SSH incorrect.")
    if not 1<=port<=65535:
        raise ValueError("Port SSH invalide.")
    if not identity:
        raise ValueError("Sélectionner une clé SSH privée.")
    path=Path(identity).expanduser().resolve()
    if not path.is_file():
        raise ValueError("Clé SSH privée introuvable.")
    if path.stat().st_mode & 0o077:
        raise ValueError("Permissions de la clé trop ouvertes (chmod 600).")
    return ["ssh","-o","IdentitiesOnly=yes","-o","StrictHostKeyChecking=ask",
            "-i",str(path),"-p",str(port),"--",f"{username}@{host}"]

class GlassDialog(QDialog):
    """Central transparent acrylic effect; Qt widgets stay native and sharp."""
    def __init__(self,title,parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground,True)
        self.setMinimumWidth(500)
        self._offset=None
        outer=QVBoxLayout(self)
        outer.setContentsMargins(17,17,17,17)
        outer.setSpacing(10)
        header=QHBoxLayout()
        self.heading=QLabel("⬡  "+title)
        self.heading.setObjectName("dialogHeading")
        header.addWidget(self.heading,1)
        close=QPushButton("×")
        close.setFixedSize(31,30)
        close.clicked.connect(self.reject)
        header.addWidget(close)
        outer.addLayout(header)
        self.body=QVBoxLayout()
        self.body.setSpacing(12)
        outer.addLayout(self.body)
        self.setStyleSheet("""
          QDialog{background:transparent;color:#DFF7FF;}
          QLabel{color:#CBEFFF;font-size:12px;}
          QLabel#dialogHeading{font-size:17px;font-weight:bold;color:white;}
          QPushButton{background:rgba(4,34,54,225);color:#E1F9FF;border:1px solid #2383A8;
                      border-radius:5px;padding:6px 10px;min-height:22px;}
          QPushButton:hover{border:1px solid #5AE5FF;background:rgba(18,82,116,235);}
          QLineEdit,QComboBox,QSpinBox,QListWidget{
            background:rgba(4,24,40,225);color:#DDF7FF;border:1px solid #276583;
            border-radius:4px;padding:6px;selection-background-color:#155A80;}
          QCheckBox{color:#D7F5FF;spacing:9px;}
          QTabWidget::pane{border:1px solid #246380;background:rgba(4,24,40,160);}
          QTabBar::tab{background:#09283B;color:#C7E7FF;padding:9px 16px;}
          QTabBar::tab:selected{background:#135174;border-bottom:2px solid #39DFFF;}
        """)
    def paintEvent(self,event):
        p=QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        box=self.rect().adjusted(5,5,-5,-5)
        x,y,w,h=box.x(),box.y(),box.width(),box.height()
        cut=15
        path=QPainterPath()
        path.moveTo(x+cut,y)
        path.lineTo(x+w-cut,y)
        path.lineTo(x+w,y+cut)
        path.lineTo(x+w,y+h-cut)
        path.lineTo(x+w-cut,y+h)
        path.lineTo(x+cut,y+h)
        path.lineTo(x,y+h-cut)
        path.lineTo(x,y+cut)
        path.closeSubpath()
        grad=QLinearGradient(x,y,x+w,y+h)
        grad.setColorAt(0,QColor(9,39,60,240))
        grad.setColorAt(.6,QColor(3,18,34,235))
        grad.setColorAt(1,QColor(7,33,53,243))
        p.fillPath(path,grad)
        for thickness,alpha in ((9,22),(4,48),(1.4,225)):
            p.setPen(QPen(QColor(0,211,255,alpha),thickness))
            p.drawPath(path)
        p.setPen(QPen(QColor(104,234,255,160),1))
        for i in range(3):
            yy=y+12+7*i
            a=x+w*.52+i*12
            p.drawLine(int(a),int(yy),int(a+37),int(yy))
            p.drawLine(int(a+37),int(yy),int(a+48),int(yy+11))
            p.drawLine(int(a+48),int(yy+11),int(a+95),int(yy+11))
        p.end()
    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton and event.position().y()<65:
            self._offset=event.globalPosition().toPoint()-self.pos()
            event.accept()
        else:super().mousePressEvent(event)
    def mouseMoveEvent(self,event):
        if self._offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint()-self._offset)
            event.accept()
        else:super().mouseMoveEvent(event)
    def mouseReleaseEvent(self,event):
        self._offset=None
        super().mouseReleaseEvent(event)

class SettingsDialog(GlassDialog):
    changed=Signal(dict)
    def __init__(self,parent=None):
        super().__init__("NEXUS / PARAMÈTRES",parent)
        settings=QSettings("NOVA","NEXUSTerminal")
        form=QFormLayout()
        self.font=QSpinBox()
        self.font.setRange(8,18)
        self.font.setValue(int(settings.value("font_size",10)))
        form.addRow("Police du terminal",self.font)
        self.opacity=QSlider(Qt.Orientation.Horizontal)
        self.opacity.setRange(55,95)
        self.opacity.setValue(int(settings.value("glass_opacity",82)))
        form.addRow("Opacité des panneaux (%)",self.opacity)
        self.glow=QCheckBox("Activer les animations lumineuses")
        self.glow.setChecked(str(settings.value("animations","true")).lower()=="true")
        form.addRow("Effets",self.glow)
        self.autosave=QCheckBox("Restaurer la disposition au lancement")
        self.autosave.setChecked(str(settings.value("restore_layout","true")).lower()=="true")
        form.addRow("Bureau",self.autosave)
        self.layout=QComboBox()
        self.layout.addItems(["2×2","2+1+1","1+1+2"])
        self.layout.setCurrentText(str(settings.value("layout","2×2")))
        form.addRow("Disposition",self.layout)
        self.body.addLayout(form)
        self.body.addWidget(QLabel("Les proportions originales des assets seront conservées."))
        actions=QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        actions.accepted.connect(self.save)
        actions.rejected.connect(self.reject)
        self.body.addWidget(actions)
    def save(self):
        opts={"font_size":self.font.value(),"glass_opacity":self.opacity.value(),
              "animations":self.glow.isChecked(),"restore_layout":self.autosave.isChecked(),
              "layout":self.layout.currentText()}
        settings=QSettings("NOVA","NEXUSTerminal")
        for key,value in opts.items():settings.setValue(key,value)
        settings.sync()
        self.changed.emit(opts)
        self.accept()

class SessionsDialog(GlassDialog):
    connect_ssh=Signal(list)
    def __init__(self,parent=None):
        super().__init__("NEXUS / SESSIONS & CONNEXIONS",parent)
        self.setMinimumSize(660,480)
        tabs=QTabWidget()
        self.body.addWidget(tabs)
        ssh=QWidget()
        ssh_layout=QVBoxLayout(ssh)
        self.saved=QListWidget()
        ssh_layout.addWidget(QLabel("Profils SSH enregistrés (aucun mot de passe stocké)"))
        ssh_layout.addWidget(self.saved,1)
        form=QFormLayout()
        self.profile=QLineEdit()
        self.profile.setPlaceholderText("GEN-1")
        self.host=QLineEdit()
        self.host.setPlaceholderText("example.org")
        self.user=QLineEdit()
        self.user.setPlaceholderText("utilisateur")
        self.port=QSpinBox()
        self.port.setRange(1,65535)
        self.port.setValue(22)
        self.identity=QLineEdit()
        self.identity.setPlaceholderText("~/.ssh/id_ed25519")
        chooser=QHBoxLayout()
        chooser.addWidget(self.identity)
        pick=QPushButton("…")
        pick.clicked.connect(self.select_identity)
        chooser.addWidget(pick)
        form.addRow("Nom du profil",self.profile)
        form.addRow("Hôte",self.host)
        form.addRow("Utilisateur",self.user)
        form.addRow("Port",self.port)
        form.addRow("Clé privée",chooser)
        ssh_layout.addLayout(form)
        row=QHBoxLayout()
        for title,action in (("Générer une clé Ed25519",self.generate_key),
                             ("Enregistrer",self.store),("Connecter",self.connect)):
            b=QPushButton(title)
            b.clicked.connect(action)
            row.addWidget(b)
        ssh_layout.addLayout(row)
        tabs.addTab(ssh,"SSH / CLÉS")
        api=QWidget()
        apil=QVBoxLayout(api)
        apil.addWidget(QLabel("Connexion à une API HTTPS — profil local"))
        self.api_profiles=QComboBox()
        self.api_profiles.addItem("— Nouveau profil —",None)
        try:
            existing=json.loads(API_PROFILES.read_text(encoding="utf-8"))
            if isinstance(existing,list):
                for item in existing:
                    if isinstance(item,dict) and item.get("name") and item.get("url"):
                        self.api_profiles.addItem(item["name"],item)
        except (OSError,ValueError):
            pass
        self.api_profiles.currentIndexChanged.connect(self.load_api)
        apil.addWidget(self.api_profiles)
        api_form=QFormLayout()
        self.api_name=QLineEdit()
        self.api_name.setPlaceholderText("IA-TB GEN-1")
        self.api_url=QLineEdit()
        self.api_url.setPlaceholderText("https://example.org/api/health")
        self.api_token=QLineEdit()
        self.api_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_token.setPlaceholderText("Jeton Bearer (facultatif, jamais stocké dans JSON)")
        api_form.addRow("Profil",self.api_name)
        api_form.addRow("URL de test",self.api_url)
        api_form.addRow("Token API",self.api_token)
        apil.addLayout(api_form)
        self.api_result=QLabel("● Non connecté")
        self.api_result.setWordWrap(True)
        apil.addWidget(self.api_result)
        api_actions=QHBoxLayout()
        save_api=QPushButton("Enregistrer le profil")
        save_api.clicked.connect(self.save_api)
        api_actions.addWidget(save_api)
        test_api=QPushButton("Tester la connexion HTTPS")
        test_api.clicked.connect(self.test_api)
        api_actions.addWidget(test_api)
        apil.addLayout(api_actions)
        apil.addWidget(QLabel("Jetons conservés uniquement en mémoire, sauf si le trousseau système est disponible."))
        apil.addStretch()
        self.net=QNetworkAccessManager(self)
        self.api_reply=None
        tabs.addTab(api,"API / APPS")
        self.saved.itemSelectionChanged.connect(self.load_selection)
        self.refresh()
    def load_api(self,index):
        item=self.api_profiles.itemData(index)
        if not isinstance(item,dict):
            return
        self.api_name.setText(str(item.get("name","")))
        self.api_url.setText(str(item.get("url","")))
        self.api_token.clear()
        self.api_result.setText("Profil chargé. Token depuis le trousseau si disponible.")

    def save_api(self):
        name=self.api_name.text().strip()
        url=QUrl(self.api_url.text().strip())
        if not ID_RE.fullmatch(name) or not url.isValid() or url.scheme()!="https" or not url.host() or url.userName() or url.password() or url.hasQuery() or url.hasFragment():
            QMessageBox.warning(self,"API","Nom de profil ou URL HTTPS invalide.")
            return
        try:
            data=json.loads(API_PROFILES.read_text(encoding="utf-8")) if API_PROFILES.exists() else []
            if not isinstance(data,list):data=[]
        except (OSError,ValueError):
            data=[]
        data=[p for p in data if isinstance(p,dict) and p.get("name")!=name]
        data.append({"name":name,"url":url.toString(QUrl.UrlFormattingOption.RemovePassword)})
        CONFIG_DIR.mkdir(mode=0o700,parents=True,exist_ok=True)
        temp=API_PROFILES.with_suffix(".tmp")
        temp.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf-8")
        os.chmod(temp,0o600)
        temp.replace(API_PROFILES)
        found=self.api_profiles.findText(name)
        if found<0:self.api_profiles.addItem(name,{"name":name,"url":url.toString()})
        else:self.api_profiles.setItemData(found,{"name":name,"url":url.toString()})
        token=self.api_token.text()
        if token:
            try:
                import keyring
                keyring.set_password("NEXUS-Terminal/API",name,token)
                self.api_result.setText("✓ Profil enregistré, token conservé par le trousseau.")
            except Exception:
                self.api_result.setText("✓ Profil enregistré. Token non enregistré (trousseau indisponible).")
        else:
            self.api_result.setText("✓ Profil enregistré (sans token).")

    def test_api(self):
        if self.api_reply is not None:
            return
        url=QUrl(self.api_url.text().strip())
        if not url.isValid() or url.scheme()!="https" or not url.host() or url.userName() or url.password():
            QMessageBox.warning(self,"API","Utiliser une URL HTTPS valide.")
            return
        request=QNetworkRequest(url)
        request.setTransferTimeout(10000)
        request.setRawHeader(b"Accept",b"application/json")
        request.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute,
                             QNetworkRequest.RedirectPolicy.ManualRedirectPolicy)
        token=self.api_token.text()
        if not token:
            try:
                import keyring
                token=keyring.get_password("NEXUS-Terminal/API",self.api_name.text().strip()) or ""
            except Exception:
                token=""
        if token:
            request.setRawHeader(b"Authorization",b"Bearer "+token.encode("utf-8"))
        self.api_result.setText("◌ Vérification HTTPS en cours…")
        self.api_reply=self.net.get(request)
        self.api_reply.finished.connect(self.api_finished)

    def api_finished(self):
        reply=self.api_reply
        self.api_reply=None
        if reply is None:return
        status=reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if reply.error():
            self.api_result.setText("✕ Échec API : "+reply.errorString())
        else:
            self.api_result.setText(f"✓ Réponse HTTPS reçue : HTTP {status}")
        reply.deleteLater()

    def refresh(self):
        self.saved.clear()
        for p in profiles_read():
            item=QListWidgetItem(p.get("name",p.get("host","Profil")))
            item.setData(Qt.ItemDataRole.UserRole,p)
            self.saved.addItem(item)
    def load_selection(self):
        item=self.saved.currentItem()
        if not item:return
        obj=item.data(Qt.ItemDataRole.UserRole)
        self.profile.setText(str(obj.get("name","")))
        self.host.setText(str(obj.get("host","")))
        self.user.setText(str(obj.get("user","")))
        self.port.setValue(int(obj.get("port",22)))
        self.identity.setText(str(obj.get("key_path","")))
    def select_identity(self):
        name,_=QFileDialog.getOpenFileName(self,"Sélectionner une clé privée",str(Path.home()/".ssh"))
        if name:self.identity.setText(name)
    def current_profile(self):
        obj={"name":self.profile.text().strip(),"host":self.host.text().strip(),
             "user":self.user.text().strip(),"port":self.port.value(),
             "key_path":self.identity.text().strip()}
        if not ID_RE.fullmatch(obj["name"]):raise ValueError("Nom de profil invalide.")
        safe_ssh(obj)
        return obj
    def store(self):
        try:obj=self.current_profile()
        except (ValueError,OSError) as exc:
            QMessageBox.warning(self,"Profil SSH",str(exc));return
        values=[p for p in profiles_read() if p.get("name")!=obj["name"]]
        values.append(obj)
        profiles_write(values)
        self.refresh()
    def generate_key(self):
        if shutil.which("ssh-keygen") is None:
            QMessageBox.warning(self,"SSH","ssh-keygen est introuvable.");return
        folder=Path.home()/".ssh"
        folder.mkdir(mode=0o700,parents=True,exist_ok=True)
        nickname=self.profile.text().strip()
        if not ID_RE.fullmatch(nickname):
            QMessageBox.warning(self,"SSH","Choisir d'abord un nom de profil.");return
        safe=re.sub(r"[^A-Za-z0-9_-]","_",nickname)
        key=folder/("nexus_"+safe+"_ed25519")
        if key.exists() or key.with_suffix(".pub").exists():
            QMessageBox.warning(self,"SSH","La clé existe déjà : aucun écrasement.");return
        passphrase,ok=QInputDialog.getText(self,"Protection de la clé",
            "Phrase secrète (conseillée) :",QLineEdit.EchoMode.Password)
        if not ok:return
        # CLI arguments are never sent through a shell. Warning: passphrase may
        # briefly appear in process arguments; use ssh-keygen's interactive prompt
        # for stronger secrecy if required.
        if passphrase:
            QMessageBox.information(self,"SSH",
                "Pour protéger ta phrase secrète, génère la clé dans un terminal :\n"
                "ssh-keygen -t ed25519 -a 64\nPuis sélectionne-la ici.")
            return
        answer=QMessageBox.question(self,"Clé sans phrase secrète",
            "Créer une clé SSH non protégée par phrase secrète ?\\n"
            "Préférer une clé protégée pour tout serveur sensible.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if answer!=QMessageBox.StandardButton.Yes:return
        result=subprocess.run(["ssh-keygen","-q","-t","ed25519","-a","64",
                               "-N","","-f",str(key)],capture_output=True,text=True,timeout=30)
        if result.returncode:
            QMessageBox.warning(self,"SSH",result.stderr[-400:]);return
        os.chmod(key,0o600)
        self.identity.setText(str(key))
        QMessageBox.information(self,"Clé créée",
            "Clé publique disponible : "+str(key)+".pub\n"
            "Installe la clé publique sur le serveur avant de te connecter.")
    def connect(self):
        try:profile=self.current_profile()
        except (ValueError,OSError) as exc:
            QMessageBox.warning(self,"Connexion SSH",str(exc));return
        self.connect_ssh.emit(safe_ssh(profile))
        self.accept()
