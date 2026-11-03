# NOVA REDBLACK R2 — Graphite 75 / Rouge 25

Base fonctionnelle: `work/novabar-redblack-r1-asset-refactor`.
Aucune reprise de la branche Blue Neon Graphite.

## Direction artistique
- Noir graphite `#0D1015`, panneaux `#151920` : ~75 %
- Rouge profond `#D42B43` et néon actif `#E75E71` : ~25 %
- Très fins reflets blancs ponctuels ; pas de surfaces rouge vif pleines
- Les 9 PNG d'assets REDBLACK R1 restent chargés. L'alpha de leurs
  calques est réduit sans supprimer les cadres ni la texture PCB.

## Réparations d'interface
- Cartes HUD lisibles même aux hauteurs de 50–80 px et en disposition
  verticale ; les titres récupèrent les libellés réels du registre plugins.
- Zones Holo conservées via `HudCanvas.module_rect`,
  `module_icon_rect` et `module_at`, aucune nouvelle couche cliquable
  au-dessus des boutons.
- Dock inférieur : marges adaptatives au lieu de 20 px fixes,
  tailles minimales contrôlées, icônes redimensionnées, boutons tâche
  lisibles aux valeurs 62–130 px.
- Compatibilité : mêmes paramètres, déclencheurs, raccourcis et données
  capteurs. Aucune réinitialisation du profil utilisateur.

## Validation
`tests/test_redblack_r2_layout.py` vérifie la géométrie pour six
résolutions/positions et les tailles des boutons. Les tests existants
et la compilation PyInstaller/.deb tournent en CI.

La conformité des menus du bureau XFCE et des plugins système externes
reste à confirmer sur un vrai bureau avant toute promotion en stable.
