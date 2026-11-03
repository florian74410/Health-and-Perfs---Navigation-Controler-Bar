# NOVA REDBLACK R1 — Real asset layer

Branche de travail: `work/novabar-redblack-r1-asset-refactor`

## Contrat: conserver le fonctionnement 0.8.2.2

Cette branche ne change pas les moteurs matériels, le chargement des plugins,
les actions des boutons, les paramètres, les options de disposition, les
menus, la gestion des Holo ni les raccourcis. Le terminal restera une
application tierce indépendante ; il n'est pas remplacé par la démo
Terminal de la fondation NOVA CONTROL CENTER v0.1.

## Nouveau moteur d'apparence

`redblack_r1_assets.py` charge le pack utilisateur extrait à partir de
`Assets Themes.tar.gz` fourni par le propriétaire. Le code ne contient
aucun asset tiers acheté ou filigrané. Les ressources PNG conservent leur
alpha et sont mises à l'échelle par neuf zones pour préserver les coins
biseautés. Les textes, clics et états des vrais widgets Qt restent natifs.

La fonction `redblack_shell.paint_surface` utilise désormais les planches
de l'utilisateur pour les éléments `settings`, `holo`, `notification`,
`dock`, `catalog`, `hud`, `task` et `button`. Le châssis SVG
programmatique existant reste un fallback fiable si le pack est absent.

## Installation d'assets, sans privilèges root

Le fichier `NOVA_REDBLACK_R1_ASSETS.zip` créé depuis les planches utilisateur
contient un script `install.sh`, neuf PNG et un manifest JSON.

```bash
mkdir -p ~/NOVA-REDBLACK-R1
unzip -o ~/Téléchargements/NOVA_REDBLACK_R1_ASSETS.zip -d ~/NOVA-REDBLACK-R1
bash ~/NOVA-REDBLACK-R1/install.sh
```

Le script installe les ressources dans :
`~/.config/health-perfs-bar/Themes/redblack-r1`.
Ce pack nécessite **une compilation de cette branche**, pas le paquet 0.8.2.2
précédent. Aucun droit root requis pour le pack.

## Vérifications

Les tests `tests/test_redblack_r1_assets.py` protègent la transparence
des angles et le redimensionnement ; le workflow Linux exécute aussi la
suite de régression 0.8.2.2 et construit un paquet test.
Vérification XFCE réelle avant publication stable obligatoire.
