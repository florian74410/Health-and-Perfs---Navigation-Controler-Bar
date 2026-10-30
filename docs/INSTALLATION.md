# Installation et exploitation

## Sources — lancement simple

Télécharger puis extraire le dépôt, lancer Install-Linux.sh / Install-Windows.cmd /
Install-macOS.command. Python 3.10+ et Internet sont nécessaires pour installer Qt dans un
environnement dédié. Sous Linux il faut un environnement graphique et le module venv de Python.
L’installateur ne touche pas aux autres applications ni aux privilèges administrateur.

Le premier assistant propose placement, écran, épaisseur, opacité, rétractation et autostart.
Annuler ferme la configuration sans enregistrer ces choix ; le runtime installé reste en place.
Une autre session utilisateur peut installer sa propre copie et ses propres préférences.

## Paquets autonomes

Le workflow Native installers peut être lancé manuellement, se déclenche pour les pull requests
concernées et les tags v*. Télécharger l’artefact correspondant dans l’onglet Actions, puis l’extraire.

- Linux : extraire le .tar.xz et lancer `sh Install.sh`. Ajoute un lanceur au menu utilisateur.
- Windows : lancer l’exécutable Setup. Inno Setup propose le dossier d’installation et ajoute
  un raccourci et une désinstallation. Les préférences de la barre s’ouvrent à la fin.
- macOS : ouvrir le DMG arm64, déplacer l’app vers Applications, puis l’ouvrir.
  La première ouverture configure le profil utilisateur. Paquet non signé/non notarisé à ce stade.

Le packaging Linux est produit sur Ubuntu 22.04, Windows sur Windows Server 2022,
macOS sur le runner macos-14 arm64. Ces cibles sont des builds, pas une certification de tous les OS.

## Autostart

Option désactivée par défaut, modifiable par la roue dentée.

| Plateforme | Mécanisme |
| --- | --- |
| Linux | Fichier XDG `~/.config/autostart/health-perfs-bar.desktop` |
| Windows | Valeur HealthPerfsBar dans HKCU / Software / Microsoft / Windows / CurrentVersion / Run |
| macOS | `~/Library/LaunchAgents/com.healthperfs.bar.plist`, RunAtLoad |

L’autostart s’applique à la prochaine ouverture de session ; il ne requiert ni service root
ni tâche système. Le chemin vise la copie installée, pas le dossier de téléchargement.
Sur macOS, configurer l’autostart après avoir déplacé l’app à son emplacement définitif.
Déplacer le programme ensuite impose de désactiver puis réactiver cette option.

## Désinstallation

Désactiver l’autostart dans les préférences puis quitter via le clic droit ou la zone de notification.
Windows : utiliser la désinstallation créée par Setup, qui supprime aussi la valeur de démarrage.
macOS : retirer l’app ; pour la version source, retirer également le sous-dossier runtime.
Linux : retirer le dossier installé (`~/.local/share/health-perfs-bar`) et le lanceur
`~/.local/share/applications/health-perfs-bar.desktop` (ou le chemin XDG personnalisé).
Les préférences et extensions restent conservées dans le dossier documenté dans ARCHITECTURE.md.

## Compatibilité en cours

- Linux Mint XFCE/X11 : cible prioritaire ; nécessite les bibliothèques système Qt/XCB et un compositeur pour la transparence.
- Linux Wayland / Bazzite : fenêtre portable, mais ancrage et premier plan dépendent du compositeur.
  Le protocole layer-shell n’est pas implémenté. Une session X11 ou XWayland est à évaluer sur la machine.
- Windows 10/11 x64 : chaîne de packaging prévue, vérification sur machine réelle encore nécessaire.
- Windows 7 : non pris en charge par cette base Qt 6 ; nécessitera une branche legacy distincte.
- macOS récent : build arm64 ; Intel à ajouter séparément. Aucun test natif macOS effectué ici.

La barre est un overlay ; elle ne réserve pas encore une zone de travail système (strut/appbar).
Les applications en plein écran et les politiques du gestionnaire de fenêtres peuvent la recouvrir.
