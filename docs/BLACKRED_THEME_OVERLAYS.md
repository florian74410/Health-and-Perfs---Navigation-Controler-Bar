# NOVA / BLACKRED CYBER NEON — thème superposé (0.8.1-BR.1)

Branche QA : `work/novabar-v0.8.1-blackred-theme-overlays`.
Base vérifiée : `work/novabar-v0.8.1-linux-polish-shortcuts` (0.8.1).
**Ce travail n'est pas une release 0.8.2 publiée.**

## Design

Noir graphite `#08090D`, surfaces verre fumé `#16080E`, néon rouge
`#FF233E`, bord secondaire `#A20C24`. Les polices conservent un blanc
lisible et les états métiers vert/rouge ne sont pas artificiellement modifiés.

Le pack intégré `blackred-neon` fournit cinq ressources SVG **sans fond
opaque dans les angles** : circuits, cadre, notification, bouton et fond
d'écran. Les fenêtres de préférences clipsent reflets et textures au tracé
biseauté. Aucun moteur web, vidéo ni minuterie supplémentaire n'est requis.

## Activation et retour en arrière

1. Installer une version de NovaBar **construite à partir de cette branche**.
   La version 0.8.1 déjà installée ne connaît pas les packs superposés :
   déposer les fichiers de thème seuls n'active rien dans l'ancien runtime.
2. Ouvrir NovaBar → Paramètres → Général → Thème actif.
3. Choisir « BlackRed / Cyber Neon », appliquer et relancer NovaBar si
   l'interface de lancement du NEXUS était déjà ouverte.
4. Pour revenir en arrière, sélectionner « Blue Neon » ou
   « Cyber-Futuriste » ; les profils, favoris et plugins ne changent pas.
5. L'habillage du panneau XFCE reste **facultatif** et réversible.
   La surcouche ne supprime ni le panneau Linux Mint ni ses plugins.

## Ajouter une autre surcouche

Placer un répertoire de skin validé dans le répertoire utilisateur :

- Linux : `~/.config/health-perfs-bar/Themes/<skin-id>/manifest.json`
- Windows : `%APPDATA%/HealthPerfsBar/Themes/<skin-id>/manifest.json`
- macOS : `~/Library/Application Support/HealthPerfsBar/Themes/<skin-id>/manifest.json`

Le manifest définit l'identifiant, le nom, la palette (les cinq couleurs
obligatoires `primary`, `secondary`, `background`, `surface`, `text`)
et jusqu'à cinq assets `pcb`, `frame`, `button`, `notification`,
`wallpaper` (SVG/PNG/WebP). Les chemins d'assets ne peuvent pas quitter
le répertoire de la surcouche, et aucun code n'est exécuté à partir du pack.

Redémarrer NovaBar après ajout de nouvelles surcouches ; elles apparaissent
alors dans la liste des thèmes et dans le menu de la zone de notification.

La version studio avec les photos de référence livrées séparément peut être
installée **sans privilèges root** dans ce répertoire utilisateur.

## Périmètre et limites

La surcouche retinte les éléments Qt du HUD, Holo, docks, NEXUS,
Plugin Control Center, paramètres, graphiques et icône NovaBar. Les icônes
des applications installées restent leurs véritables icônes. Les
notifications émises par le système d'exploitation ou par XFCE ne sont
pas remplacées de force par une notification Nova : elles conservent
leurs propriétés système. Les images `notification` et `button` sont
des ressources disponibles pour la future couche de dialogues NOVA.

Contrôles prévus sur XFCE/X11 : transparence aux quatre angles, clic et
double-clic du menu d'applications, Holo CPU/GPU/RAM/stockage/réseau,
boutons des fenêtres, panneau original après fermeture, et bascule
BlackRed ↔ Blue Neon après redémarrage.

**QA** : les tests automatisés couvrent validation des packs,
résistance aux chemins de fuite, sélecteur, sauvegarde et angles
transparents. Une validation sur un vrai bureau XFCE reste nécessaire
avant publication comme version stable.
