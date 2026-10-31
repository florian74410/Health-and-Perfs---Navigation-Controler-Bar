# ⚡ CYBER NEXUS HUD — NovaBar 0.6.9

Les exécutables autonomes sont produits par le workflow GitHub Actions **Native installers** à partir du code de la version 0.6.9. La publication synchronise les binaires dans les sous-dossiers `Executable/` et dans les **assets de la release**, qui restent le moyen de téléchargement recommandé.

## 📦 Télécharger la dernière version

| Système | Installateur direct (release v0.6.9) | Dossier du dépôt |
| --- | --- | --- |
| Linux Mint XFCE / Ubuntu amd64 | [**NovaBar_0.6.9_amd64.deb**](https://github.com/florian74410/Health-and-Perfs---Navigation-Controler-Bar/releases/download/v0.6.9/NovaBar_0.6.9_amd64.deb) | [Executable/Linux](Linux/) |
| Linux Flatpak x86_64 | [NovaBar_0.6.9_x86_64.flatpak](https://github.com/florian74410/Health-and-Perfs---Navigation-Controler-Bar/releases/download/v0.6.9/NovaBar_0.6.9_x86_64.flatpak) | [Executable/Linux](Linux/) |
| Linux autonome | [CyberNexusHUD-Linux-x86_64.run](https://github.com/florian74410/Health-and-Perfs---Navigation-Controler-Bar/releases/download/v0.6.9/CyberNexusHUD-Linux-x86_64.run) | [Executable/Linux](Linux/) |
| Windows 10/11 | [CyberNexusHUD-Setup-Windows.exe](https://github.com/florian74410/Health-and-Perfs---Navigation-Controler-Bar/releases/download/v0.6.9/CyberNexusHUD-Setup-Windows.exe) | [Executable/Windows](Windows/) |
| macOS Apple Silicon | [CyberNexusHUD-macOS-arm64.dmg](https://github.com/florian74410/Health-and-Perfs---Navigation-Controler-Bar/releases/download/v0.6.9/CyberNexusHUD-macOS-arm64.dmg) | [Executable/MacOS](MacOS/) |
| macOS Intel | [CyberNexusHUD-macOS-x86_64.dmg](https://github.com/florian74410/Health-and-Perfs---Navigation-Controler-Bar/releases/download/v0.6.9/CyberNexusHUD-macOS-x86_64.dmg) | [Executable/MacOS](MacOS/) |

La page de release est [**v0.6.9**](https://github.com/florian74410/Health-and-Perfs---Navigation-Controler-Bar/releases/tag/v0.6.9). Les chemins ne sont utilisables qu'après confirmation du succès de la publication. Pour les builds non publiés, utiliser temporairement [les artifacts de GitHub Actions](https://github.com/florian74410/Health-and-Perfs---Navigation-Controler-Bar/actions).

## 🐧 Installer sur Linux Mint XFCE

```bash
cd "$(xdg-user-dir DOWNLOAD)"
sudo apt install ./NovaBar_0.6.9_amd64.deb
novabar
```

Inutile de supprimer NovaBar 0.6.0 ou tes préférences avant une mise à jour native. Le paquet fournit les exécutables et leurs dépendances : Python et PyInstaller ne sont pas nécessaires sur le poste utilisateur.

## Vérifier un fichier

Le workflow calcule `manifest.json` (version, commit, tailles, SHA-256) et `SHA256SUMS`. Une fois le paquet téléchargé et les sommes disponibles dans ce dossier :

```bash
sha256sum NovaBar_0.6.9_amd64.deb
```

Comparer la somme avec le manifeste généré par la **même publication**. Ne pas utiliser les empreintes d'une ancienne version.

## Comportement

La barre supérieure, les deux docks latéraux et l'habillage facultatif du panneau système XFCE sont réunis dans le même programme. Les raccourcis, applications ouvertes et icônes de notification existants restent gérés par XFCE. Le choix des éléments visibles dans le HUD se fait dans les préférences NovaBar.

**Limites :** applications non signées/non notarisées ; tester les workspaces et l'habillage sur une session XFCE X11 réelle. Pour les détails, lire [Mise à jour 0.6.9](../docs/UPDATE_V069.md) et [Installation](../docs/INSTALLATION.md).
