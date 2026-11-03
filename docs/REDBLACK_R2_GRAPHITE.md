# REDBLACK R2 — Graphite 75 / Rouge 25

Base: `work/novabar-redblack-r1-asset-refactor` (R1 real PNG nine-slice assets).
Correction branch: `work/novabar-redblack-r2-graphite-layout`.

## Design
- 75 % noir graphite pour les châssis, le fond opaque des Holo, les
  panneaux et tous les contrôles passifs
- 25 % rouge pour les pistes PCB, indicateurs, contours très fins et
  actions sélectionnées
- Un filet blanc froid dans l'animation du courant et les reflets
- L'ensemble des neuf assets R1 reste disponible dans le pack utilisateur,
  mais l'opacité des planches volumineuses est réduite pour conserver le
  dominant graphite

## Correction fonctionnelle : placement
Le style R1 de l'application appliquait `min-height`, `padding` et
bordures globaux aux `QToolButton`. Le dock inférieur, les plugins et
les boutons du HUD possèdent une géométrie explicite, imposée par les
options de la page Paramètres.

- Styles `control_stylesheet("dock")` et `("hud")` désormais
  compacts : aucune marge ni taille minimale ajoutée
- `control_stylesheet("window")` conserve les formes et composants
  complets pour Paramètres, NEXUS et fenêtres
- Contrat des géométries `HudCanvas.module_rect` /
  `HudCanvas.module_icon_rect` inchangé, ainsi que les déclencheurs
  Holo et les données du gestionnaire de plugins
- Titres recadrés pour laisser la place aux icônes de plugins

## Déploiement
Le numéro Debian historique demeure `0.8.2.2` dans cette branche
expérimentale. L'archive CI `NovaBar-0.8.2.2-REDBLACK-LINUX-QA`
doit provenir de la dernière exécution **de la branche R2**, et non des
runs R1/REDBLACK précédents. Installer le pack graphique
`NOVA_REDBLACK_R1_ASSETS.zip` une seule fois suffit.

Avant l'installation, fermer NOVA normalement : signal SIGTERM plutôt que
SIGKILL pour permettre la restauration du panneau XFCE.

## Validation
La CI vérifie le runtime, les transparences et le paquet Debian.
La dernière validation de la disposition sur un vrai bureau Linux Mint
XFCE avec des résolutions et profils variés est encore nécessaire.
