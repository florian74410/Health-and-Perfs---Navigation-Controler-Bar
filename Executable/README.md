# CYBER NEXUS HUD — installateurs autonomes de NovaBar

Les exécutables sont déposés ici par le pipeline après validation des builds natifs.
Ils **contiennent NovaBar et ses dépendances** : aucun clone du dépôt, Python ou compilateur n’est nécessaire.

| Système | Téléchargement | Lancement |
| --- | --- | --- |
| Linux Mint XFCE / Ubuntu x64 | [NovaBar_0.3.6_amd64.deb](Linux/NovaBar_0.3.6_amd64.deb) | Double-clic ou `sudo apt install ./NovaBar_0.3.6_amd64.deb` |
| Linux x64 avec Flatpak | [NovaBar_0.3.6_x86_64.flatpak](Linux/NovaBar_0.3.6_x86_64.flatpak) | `flatpak install --user ./NovaBar_0.3.6_x86_64.flatpak` |
| Linux x64 autonome | [CyberNexusHUD-Linux-x86_64.run](Linux/CyberNexusHUD-Linux-x86_64.run) | `sh CyberNexusHUD-Linux-x86_64.run` |
| Windows 10/11 x64 | [CyberNexusHUD-Setup-Windows.exe](Windows/CyberNexusHUD-Setup-Windows.exe) | Double-cliquer |
| macOS 12+ Apple Silicon | [CyberNexusHUD-macOS-arm64.dmg](MacOS/CyberNexusHUD-macOS-arm64.dmg) | Ouvrir le DMG puis CyberNexusInstaller.app |
| macOS 12+ Intel | [CyberNexusHUD-macOS-x86_64.dmg](MacOS/CyberNexusHUD-macOS-x86_64.dmg) | Ouvrir le DMG puis CyberNexusInstaller.app |

Sur la page d’un fichier GitHub, choisir **Download raw file** pour télécharger le fichier réel.
Le paquet Linux est aussi destiné aux essais Bazzite Desktop ; cette cible reste expérimentale.
High Sierra 10.13 n’est pas pris en charge par ces DMG. Les paquets ne sont pas signés/notarisés.

## Mint XFCE

Télécharger le fichier `.run`, ouvrir un terminal dans le dossier de téléchargement, puis :

```sh
sh CyberNexusHUD-Linux-x86_64.run
```

L’assistant s’ouvre, installe la barre dans le compte utilisateur, enregistre les préférences
et propose le démarrage automatique. Le fichier peut être vérifié sans installation :

```sh
sh CyberNexusHUD-Linux-x86_64.run --check
sh CyberNexusHUD-Linux-x86_64.run --verify
```

Le mode `--verify` utilise un dossier temporaire et teste le binaire hors écran, sans
modifier le profil ou le démarrage automatique. Le `.run` ne nécessite que les outils
usuels du système (sh, tail, gzip, tar, sha256sum, mktemp) pour se décompacter.

`manifest.json` indique version, commit source, tailles et empreintes ; `SHA256SUMS`
permet de contrôler les téléchargements Windows/macOS. Ces empreintes ne remplacent
pas une signature indépendante de l’éditeur.

Le code source complet est sur la branche
[feature/cyber-nexus-installer-v03](https://github.com/florian74410/Health-and-Perfs---Navigation-Controler-Bar/tree/feature/cyber-nexus-installer-v03).
Le dossier Executable est également publié sur main pour être accessible depuis la page principale.
