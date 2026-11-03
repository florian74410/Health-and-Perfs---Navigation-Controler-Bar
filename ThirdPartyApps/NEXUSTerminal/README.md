# NEXUS Terminal — application tierce Qt

**Statut : 0.1.0-dev ; prototype autonome, non validé graphiquement sur Linux Mint XFCE.** Ce programme n'est pas un plugin NovaBar.

## Intégration légère

Le projet vit dans `ThirdPartyApps/NEXUSTerminal/` ; NovaBar/Cyber-Neon ne fera que référencer le lanceur `nexus-terminal` ou `nexus-terminal.desktop`. Aucun changement au runtime ni au Plugin Manager.

## Fonctionnalités

- PySide6 + QTermWidget, vrai terminal Bash/PTY par panneau.
- Onglets et six formats : 1, 2 colonnes, 2 lignes, 2×2, 2+1 et 1+2.
- Redimensionnement par QSplitter ; marges 4 px ; thème bleu nuit sobre.
- Copier Ctrl+Shift+C, coller Ctrl+Shift+V, nouvel onglet Ctrl+Shift+T.
- Historique 4 000 lignes et menu contextuel.
- Le changement de format détruit les sessions de l'onglet, **après confirmation**. La conservation des sessions est un travail ultérieur.

## Installation utilisateur, isolée

Sous Linux Mint XFCE/X11 (Python 3.11+), depuis ce dossier :

```bash
bash install-local.sh
~/.local/bin/nexus-terminal
```

Installe une venv dans `~/.local/share/nexus-terminal`, une commande dans `~/.local/bin` et une entrée XFCE `.desktop`. Aucun sudo, aucun remplacement du paquet NovaBar. Internet nécessaire pour télécharger les wheels PyPI. Si QTermWidget ne fournit pas une wheel compatible, l'installation échoue sans toucher aux paquets système.

## Validation nécessaire

- Sur machine réelle : Qt/QTermWidget, raccourcis clavier FR, Bash, ssh, vim/nano, scrollback, redimensionnement, fermeture des PTY et consommation mémoire.
- Conserver le décor XFCE standard pendant les tests, puis recréer le chrome BlueNeon inspiré de `Assets/Previews/nova-v075-terminal-scrollback.png`.
- Tester avant tout installateur .deb officiel ou intégration au thème.
- Référence NovaBar 1.0.0 souhaitée, **commit exact pas encore identifié**. Aucune modification ni suppression de l'ancien terminal sur le dépôt.

## Licence

Le binding `pyside6-qtermwidget` est GPL-3.0 ; vérifier les obligations de redistribution avant packaging public.
