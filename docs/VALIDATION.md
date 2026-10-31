# Validation v0.1.0

Vérifications locales sur Linux, Qt 6.8.3, rendu offscreen :

- Tests de stockage des préférences, refus des valeurs invalides et récupération d’un fichier corrompu.
- Ajout de paquet déclaratif, activation, mise à jour, préservation de l’état et restauration.
- Rejet des chemins interdits, code exécutable, mauvais identifiants/API et paquet modifié.
- Simulation d’une erreur disque au remplacement : l’installation précédente reste disponible.
- Génération/retrait de l’autostart Linux et échappement des chemins à espaces et caractères réservés.
- Création et rendu de la coque en haut, en bas, à droite ; boutons de navigation visibles.
- Rendus aux largeurs 800, 1024, 1366 et 2048 ; disposition compacte ou détaillée.
- Rétractation/retour et conservation des dimensions ; préférences enregistrées/annulées.
- Inspection visuelle de docs/preview.png à 2048 × 205.
- Build PyInstaller Linux réussi ; lancement du binaire autonome avec --preview vérifié.

Le premier pipeline GitHub a également passé les 10 tests sur Windows Server 2022
et fabriqué le Setup Windows. Cela ne remplace pas une ouverture manuelle sur Windows 10/11.

Les tests utilisent des profils temporaires et ne modifient pas l’autostart de la session de travail.
Les avertissements Qt « propagateSizeHints / raise » sont propres au plugin de rendu offscreen.

Restent à vérifier sur machines réelles : composition transparente, multiécran avec DPI différents,
interaction avec les bureaux/panneaux, autostart à la reconnexion, installateurs Windows/macOS,
Bazzite/Wayland et plein écran. Le pipeline de builds n’équivaut pas à ces tests manuels.

Correction de transparence : test pixel alpha du fond général à 0 et des fonds de modules/boutons
à 0 %, 35 % et 100 %, avec maintien des textes opaques. 11 tests locaux passent.


## Exécution vérifiée pour V0.2 — 31/10/2026

CI : https://github.com/florian74410/Health-and-Perfs---Navigation-Controler-Bar/actions/runs/41149562691

- Ubuntu 22.04 : **SUCCESS** (tests + binaire + archive Linux).
- Windows Server 2022 : **SUCCESS** (tests + compilation + installeur Inno Setup).
- macOS 15 Apple Silicon : **SUCCESS** (tests + compilation + DMG arm64).
- Suite : 13 tests Python (11 fondation + 2 plugins/télémétrie), avec paquets ZIP v2 créés en test.

Cette validation en environnement CI n'est pas un essai matériel sur Windows 7,
Bazzite/Wayland ou Mac Intel anciens. Les contrôles PWM/Turbo restent absents.

## CYBER NEXUS HUD / NovaBar 0.3

25 tests locaux après vérification des migrations et des liens internes de bundles : acceptation des conditions, profil local,
préservation de l’e-mail lors d’un changement de préférences, refus d’une autre famille d’OS ou
High Sierra, raccourcis en double, conservation d’une version existante, absence d’activation
si le binaire échoue, manifeste officiel et versions, refus des chemins ZIP et des liens externes, refus d’envoi
SMTP sans confirmation, et conservation de l’état actif en cas de mauvais SHA-256.
Aperçus des deux pages inspectés. Les tests utilisent des répertoires temporaires.

Validation native locale 0.3 : runtime et lanceur PyInstaller construits ; lanceur autonome
ouvert en aperçu ; installation du vrai runtime dans un dossier temporaire, test de l’exécutable
staged avec version 0.3.0 attendue, création du profil et activation testées sans enregistrer
l’autostart ni créer de raccourci sur la machine de travail. Archive runtime créée, extraite
avec l’extracteur de l’updater, puis vrai binaire extrait exécuté en self-test : succès.
Les deux pages ont été inspectées à partir des captures du lanceur.

Le chemin source a également été exécuté en entier : venv privé, téléchargement des dépendances,
compilation PyInstaller sur l’hôte Linux, self-test du binaire produit et activation temporaire : succès.
