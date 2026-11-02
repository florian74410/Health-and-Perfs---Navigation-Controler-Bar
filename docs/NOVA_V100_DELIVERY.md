# Livraison NOVA NEXUS HD 1.0.0-rc.149

Projet développeur : **Cyber-Neon Interactif – THEME 1.0**. Application : **NovaBar**. Crédits conservés : **0verF1ow & La Puce**.

Préversion publiée : [v1.0.0-rc.149](https://github.com/florian74410/Health-and-Perfs---Navigation-Controler-Bar/releases/tag/v1.0.0-rc.149). Aucun tag stable v1.0.0 n'est publié par ce chantier. La PR reste en brouillon.

## Sources et validation

- Branche : `release/nova-nexus-hd-v1.0.0` ; [PR #20](https://github.com/florian74410/Health-and-Perfs---Navigation-Controler-Bar/pull/20).
- Commit logiciel compilé : `cd8462b45c34839326cb97f8461648a67cc42d93`.
- [CI finale réussie : quatre plateformes et publication](https://github.com/florian74410/Health-and-Perfs---Navigation-Controler-Bar/actions/runs/41431250546).
- 164 tests locaux réussis. Tests natifs sur Windows, macOS Intel, macOS Apple Silicon et Ubuntu 22.04 ; tests XFCE/XFWM, terminal et D-Bus isolés ; tests des runtimes compilés et des paquets en CI.
- DEB également construit, extrait et exécuté en auto-test local avec vérification de la version 1.0.0. Le helper Turbo et la politique Polkit sont présents, détenus par root, avec permissions 755/644.

## Téléchargements réellement publiés

| Plateforme | Installateur |
| --- | --- |
| Linux Mint/Ubuntu x86_64 | [NovaBar_1.0.0_amd64.deb](https://github.com/florian74410/Health-and-Perfs---Navigation-Controler-Bar/releases/download/v1.0.0-rc.149/NovaBar_1.0.0_amd64.deb) |
| Linux x86_64 autonome | [.run](https://github.com/florian74410/Health-and-Perfs---Navigation-Controler-Bar/releases/download/v1.0.0-rc.149/CyberNexusHUD-Linux-x86_64.run) |
| Windows x64 | [.exe](https://github.com/florian74410/Health-and-Perfs---Navigation-Controler-Bar/releases/download/v1.0.0-rc.149/CyberNexusHUD-Setup-Windows.exe) |
| macOS Intel | [.dmg](https://github.com/florian74410/Health-and-Perfs---Navigation-Controler-Bar/releases/download/v1.0.0-rc.149/CyberNexusHUD-macOS-x86_64.dmg) |
| macOS Apple Silicon | [.dmg](https://github.com/florian74410/Health-and-Perfs---Navigation-Controler-Bar/releases/download/v1.0.0-rc.149/CyberNexusHUD-macOS-arm64.dmg) |

[SHA256SUMS](https://github.com/florian74410/Health-and-Perfs---Navigation-Controler-Bar/releases/download/v1.0.0-rc.149/SHA256SUMS) · [Descripteur du patch](https://github.com/florian74410/Health-and-Perfs---Navigation-Controler-Bar/releases/download/v1.0.0-rc.149/nova-patch-to-v1.0.0-manifest.json) · [Archive du descripteur et instructions](https://github.com/florian74410/Health-and-Perfs---Navigation-Controler-Bar/releases/download/v1.0.0-rc.149/NOVA-Patch-to-v1.0.0.zip) · [Pack de fonds et palettes](https://github.com/florian74410/Health-and-Perfs---Navigation-Controler-Bar/releases/download/v1.0.0-rc.149/NOVA-NEXUS-HD-Wallpapers.zip).

L'archive de patch contient les métadonnées ; les quatre véritables runtimes sont téléchargés séparément par Upgrade. Le dossier `Patch/to-v1.0.0/` référence leurs URL, tailles et SHA-256 réels. Les sous-dossiers de `Builds/v1.0.0/` indexent les installateurs de cette release. Les anciens installateurs restent conservés.

## Changements principaux

Scrollbars indépendantes dans les consoles ; Turbo Linux avec authentification administrateur graphique ; rétraction des deux docks 2 secondes après sortie du curseur. Mesures et historique de batterie, cinq palettes persistantes, onglets/favoris/fil d'Ariane Explorer, ajout aux docks, notifications et récupération Upgrade. Le détail et les fonctionnalités préservées figurent dans [l'état technique](NOVA_V100_RELEASE_STATUS.md).

## Installation et mise à jour

Pour Mint XFCE, utiliser le DEB pour disposer du helper Turbo. Fermer l'ancienne instance avant de lancer `/usr/bin/novabar`. Vérifier `/usr/bin/novabar --version` : 1.0.0. Si un ancien raccourci ou démarrage automatique pointe vers un runtime 0.7.x, utiliser le lanceur système et vérifier sa cible avant réouverture de session.

Le contrôle Turbo demande le mot de passe administrateur dans l'invite Polkit système ; NovaBar ne reçoit pas ce mot de passe. Après annulation, recliquer sur ON/OFF pour réessayer.

Sur un client disposant du nouveau gestionnaire : **Paramètres → Upgrade → Inclure les préversions → Vérifier → Installer → Redémarrer NovaBar**. Le premier passage depuis un client 0.7.x nécessite l'installateur complet pour bénéficier de la nouvelle sauvegarde ; son ancien gestionnaire n'inclut pas ces améliorations et peut avoir supprimé l'ancien runtime. Une reconnexion est utile pour vérifier les préférences de session ; ne pas désinstaller les données utilisateur.

## Limites avant stable

Le login/lock facultatif n'est pas finalisé. Les essais sur matériel réel, l'invite Turbo sur le PC de Flo, les cycles complets de mise à jour/restauration sur chaque OS et les vérifications multi-écrans restent nécessaires. Les fonctions système XFWM/Polkit sont propres à Linux ; les capteurs dépendent du matériel. Les menus tiers hors NOVA Explorer restent limités. La signature indépendante des manifestes, la signature Windows et la notarisation Apple ne sont pas configurées. High Sierra n'est pas pris en charge.
