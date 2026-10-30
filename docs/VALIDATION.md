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

Les tests utilisent des profils temporaires et ne modifient pas l’autostart de la session de travail.
Les avertissements Qt « propagateSizeHints / raise » sont propres au plugin de rendu offscreen.

Restent à vérifier sur machines réelles : composition transparente, multiécran avec DPI différents,
interaction avec les bureaux/panneaux, autostart à la reconnexion, installateurs Windows/macOS,
Bazzite/Wayland et plein écran. Le pipeline de builds n’équivaut pas à ces tests manuels.
