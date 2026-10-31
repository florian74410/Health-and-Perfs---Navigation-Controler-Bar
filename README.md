<p align="center">
  <img src="docs/wiki/assets/banner.svg" alt="CYBER NEXUS HUD — NovaBar, cockpit néon" width="100%">
</p>

<h1 align="center">⚡ NovaBar — CYBER NEXUS HUD</h1>
<p align="center"><strong>Votre PC. Votre cockpit.</strong><br>Une barre de performances cyber-néon, compacte, transparente et extensible.</p>

<p align="center">
  <img alt="Version" src="https://img.shields.io/badge/version-0.4.0-00a8c8?style=for-the-badge">
  <img alt="Linux" src="https://img.shields.io/badge/Linux-Mint%20%2F%20Ubuntu-1f7fbc?style=for-the-badge&logo=linux&logoColor=white">
  <img alt="Windows" src="https://img.shields.io/badge/Windows-10%20%2F%2011-0879bd?style=for-the-badge&logo=windows&logoColor=white">
  <img alt="macOS" src="https://img.shields.io/badge/macOS-Intel%20%26%20ARM-1f3455?style=for-the-badge&logo=apple&logoColor=white">
</p>

<p align="center">
  <a href="docs/wiki/Home.md"><strong>📚 WIKI COMPLET</strong></a> ·
  <a href="Executable/README.md"><strong>⬇️ INSTALLATEURS</strong></a> ·
  <a href="docs/wiki/Premiers-pas.md"><strong>🚀 DÉMARRAGE</strong></a> ·
  <a href="docs/wiki/Architecture.md"><strong>🏗️ ARCHITECTURE</strong></a>
</p>

---

## 🌌 Découvrez la NovaBar

<p align="center"><img src="docs/novabar-neon-preview.png" width="100%" alt="Aperçu de NovaBar généré par le logiciel, thème néon bleu"></p>
<sub>📸 Aperçu de l'application, avec données d'illustration : les valeurs affichées ne sont pas celles de votre machine.</sub>

NovaBar reste au bord de votre bureau pour exposer les informations pertinentes sans encombrer l'écran : contours PCB cyan, panneaux vitrés, reflets, halo au survol et transparence hors des modules. **72 px** par défaut, **50–150 px** réglables et **100 % de largeur** initialement.

### 🖥️ Les six modules

| 🌡️ CPU | 🎮 GPU | 🧠 RAM | 💾 Stockage | 🌀 Ventilation | 🌐 Réseau |
|:---:|:---:|:---:|:---:|:---:|:---:|
| Charge, °C, GHz | °C, VRAM, charge | Utilisée / libre | Capacité, E/S | Vitesse RPM | Débits montant / descendant |

Les informations proviennent des capteurs du système : une valeur **—** signifie « indisponible », sans simulation trompeuse.

## ✨ L'expérience NovaBar

- **🎨 Mode néon** — halos cyan, reflet de verre, opacité modulable, barre responsive et rétractable.
- **🧠 Holo CPU CORE MATRIX** — affichage détaillé du processeur via le plugin CPU Manager / Viewer.
- **🧩 Plugin Control Center 2-en-1** — onglets **Plugins / Sources**, ZIP versionnés, sources GitHub configurables et restauration.
- **📐 Barre ajustable** — haut, bas, gauche, droite ; 25–100 % de longueur ; 50–150 px d'épaisseur.
- **🔌 Monitoring local** — collecteur CPU/GPU/RAM/disques/ventilateurs/réseau en lecture seule.
- **📁 Profils préservés** — réglages et extensions indépendants des exécutables.
- **📖 Wiki intégré (0.3.6+)** — bouton **?** dans la barre, dans les préférences, le menu contextuel et la zone de notification.

<p align="center"><img src="docs/novabar-normal-holo-neon.svg" width="100%" alt="Comparatif illustré : barre normale et panneau CPU Holo"></p>
<sub>Illustration vectorielle Normal/Holo. Seule la vue native Holo CPU est disponible dans cette version ; Turbo/PWM ne contrôle pas encore le matériel.</sub>

## 📦 Télécharger & installer

| Système | Installateur | Usage |
|---|---|---|
| 🐧 **Linux Mint XFCE / Ubuntu** | [NovaBar 0.3.6 (.deb)](Executable/Linux/NovaBar_0.3.6_amd64.deb) | Paquet natif recommandé |
| 🧊 **Linux avec Flatpak** | [NovaBar 0.3.6 (.flatpak)](Executable/Linux/NovaBar_0.3.6_x86_64.flatpak) | Bundle isolé |
| 🐧 **Linux autonome** | [CyberNexusHUD (.run)](Executable/Linux/CyberNexusHUD-Linux-x86_64.run) | Installeur autonome historique |
| 🪟 **Windows 10/11** | [Setup (.exe)](Executable/Windows/CyberNexusHUD-Setup-Windows.exe) | Assistant graphique |
| 🍎 **macOS Intel** | [DMG x86_64](Executable/MacOS/CyberNexusHUD-macOS-x86_64.dmg) | macOS 12+ |
| 🍏 **macOS Apple Silicon** | [DMG arm64](Executable/MacOS/CyberNexusHUD-macOS-arm64.dmg) | macOS 12+ |

> ⚠️ Le pipeline GitHub Actions publie les exécutables après les tests multi-OS. **Vérifiez la version dans [Executable/manifest.json](Executable/manifest.json)** : la documentation peut être mise à jour avant les binaires. Les paquets ne sont pas signés/notarisés.

**Installation sur Linux Mint :**

```bash
cd "$(xdg-user-dir DOWNLOAD)"
sudo apt install ./NovaBar_0.3.6_amd64.deb
novabar
```

[📦 Procédure complète et désinstallation](docs/wiki/Installation.md) · [🔄 Mise à jour sans effacer les profils](docs/wiki/Mises-a-jour.md)

## 🧩 Plugin Manager

<p align="center"><img src="docs/wiki/assets/plugins.svg" width="100%" alt="Source GitHub, catalogue ZIP, validation puis activation"></p>

Le gestionnaire détecte les **versions installées et disponibles**. Il peut synchroniser plusieurs sources GitHub publiques, installer des ZIP compatibles sans reconstruire le lanceur, activer un module et restaurer la version précédente. Un changement de contrat de capteur/API demande néanmoins une mise à jour du programme.

[🧩 Tout comprendre sur les plugins](docs/wiki/Plugins.md)

## 🏗️ Architecture

<p align="center"><img src="docs/wiki/assets/architecture.svg" width="100%" alt="Flux système vers sondes, collecteur puis interface Qt"></p>

**Python 3.10+ · PySide6 / Qt · psutil · collecteur de sondes · PyInstaller**. Le travail de collecte est dissocié des animations. Les données sont stockées localement, et les extensions utilisent des manifestes inspectés avant installation.

[🏗️ Étudier l'architecture](docs/wiki/Architecture.md) · [📊 Comprendre les capteurs](docs/wiki/Capteurs.md)

## 📚 Wiki et assistance

**La documentation NovaBar complète est hébergée dans [`docs/wiki/`](docs/wiki/Home.md)**, avec un index, des pages détaillées, des illustrations SVG et des guides pratiques. La barre ouvre ces pages GitHub dans votre navigateur (une connexion Internet est nécessaire). Il ne s'agit pas encore du dépôt Git séparé du Wiki natif GitHub.

[🚀 Premiers pas](docs/wiki/Premiers-pas.md) · [🎛️ Interface](docs/wiki/Interface.md) · [🧠 Holo CPU](docs/wiki/Holo-CPU.md) · [⚙️ Configuration](docs/wiki/Configuration.md) · [🛠️ Dépannage](docs/wiki/Depannage.md) · [❓ FAQ](docs/wiki/FAQ.md) · [🤝 Contribuer](docs/wiki/Contribuer.md)

## 🚦 Statut

Projet en développement. La compatibilité des overlays Wayland/Bazzite et le comportement exact des sondes doivent être validés sur les machines réelles. **Pas de contrôle Turbo/PWM actif**, pas de fenêtres Holo dédiées pour tous les modules, ni de garantie d'accès à toutes les sondes GPU. Les builds CI vérifient des systèmes de compilation, pas toutes les configurations matérielles.

---

<p align="center"><strong>⚡ CYBER NEXUS HUD / NOVABAR</strong><br><em>Un cockpit discret. Une lecture instantanée.</em></p>

## Nouvelle génération 0.4

Voir [CHANGELOG](CHANGELOG.md). Les sources de développement et les exécutables publiés peuvent avoir des versions différentes ; le manifeste des exécutables reste la référence pour les téléchargements.
