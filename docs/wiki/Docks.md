# NovaBar 0.6.0 — Trois barres, un seul programme

NovaBar peut afficher indépendamment jusqu'à trois fenêtres dans le même exécutable :

- **HUD** : télémétrie CPU, GPU, RAM, SSD, ventilateurs et réseau (haut/bas/latéral selon les préférences historiques).
- **Dock Dossiers** : raccourcis de vos répertoires personnels, Documents, Téléchargements, Images, Musique, Vidéos, Bureau et Récents (selon disponibilité).
- **Dock Applications** : raccourcis présents sur votre Bureau.

Par défaut, Dossiers est à gauche, Applications à droite ; les deux docks ont leur propre languette de 9 px. Approcher le bord de l'écran ouvre immédiatement le dock correspondant. Le panneau se referme **3 secondes après la sortie du pointeur**. Tant qu'on le survole, il reste ouvert.

## Personnalisation

Dans **Préférences > Docks**, chaque fenêtre peut être activée ou désactivée individuellement ; il faut au moins une barre active. Choisir « Dossiers personnels » ou « Applications » pour le dock gauche attribue automatiquement l'autre rôle au dock droit.

La poignée ⠿ se glisse vers l'autre moitié de l'écran pour **échanger les docks** ou **déplacer le seul dock actif**. Le bouton ↔ produit le même résultat. Les données sont conservées.

Sur un dock ouvert :

- Cliquer un dossier lance le gestionnaire de fichiers défini par le système (Thunar sur beaucoup de sessions XFCE, Finder sur macOS).
- Cliquer un raccourci d'application lance l'entrée du Bureau ; sous Linux, les fichiers `.desktop` valides sont confiés à GIO (`gio launch`). Aucun chemin ne passe dans un shell.
- Faire glisser un dossier depuis Thunar vers le dock Dossiers, ou un fichier `.desktop` depuis le Bureau vers Applications.
- Réordonner les éléments par glisser-déposer.
- Clic droit : ajouter un élément via sélecteur ou le retirer. Retirer un raccourci ne supprime **jamais** le fichier cible.

Les dossiers viennent des chemins **XDG** : les noms localisés du compte sont respectés, sans supposer que votre dossier personnel s'appelle « overflow ». Le favori « Récents » utilise le schéma GIO `recent:///` ; son ouverture dépend de votre gestionnaire de fichiers et des services GIO installés.

## Espaces de travail

Sous **XFCE X11**, NovaBar demande au gestionnaire de fenêtres que chaque panneau soit présent sur **tous les bureaux virtuels**, via `_NET_WM_DESKTOP = 0xFFFFFFFF` et l'état EWMH sticky, sans créer une instance par espace de travail.

La présence sur tous les espaces n'est **pas garantie** sous Wayland, les bureaux virtuels Windows ou les Spaces macOS ; les politiques de plein écran exclusif restent contrôlées par le système.

## Installer une fois

Les trois panneaux sont dans le runtime Python/PySide6 compilé de NovaBar, donc :

- Linux Mint / XFCE : `NovaBar_0.6.0_amd64.deb` (après validation CI).
- Windows : exécutable natif dans le programme d'installation.
- macOS : application dans le DMG.

Aucune installation indépendante de dock ou de plugin n'est nécessaire. Les raccourcis sont persistés dans les préférences utilisateur `settings.json`, jamais dans les fichiers du paquet système.

**Statut :** branche de développement, vérification de l'intégration en cours ; valider sur un vrai bureau XFCE avant release stable.
