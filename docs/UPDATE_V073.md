# NovaBar 0.7.3 — ouvrir NOVA Terminal dans le thème

Le Terminal Manager NOVA était déjà inclus, mais le bouton du HUD ouvrait le menu des scripts et certains raccourcis épinglés lançaient encore le terminal XFCE.

## Raccourcis corrigés

- Le bouton Terminal du HUD ouvre NOVA Terminal, dans le dossier des scripts configuré s’il existe, sinon dans le dossier personnel.
- Les raccourcis simples XFCE et `exo-open --launch TerminalEmulator` utilisés dans les panneaux NOVA ouvrent le gestionnaire NOVA directement.
- Les favoris de la barre inférieure privilégient le lanceur NOVA possédé par le pack, sans modifier les chemins enregistrés dans les préférences.
- NEXUS présente une seule entrée NOVA Terminal lorsque son lanceur est disponible.
- Les lanceurs personnalisés avec une commande explicite, par exemple `xfce4-terminal -e htop`, conservent cette commande.
- Le menu des scripts reste accessible par clic droit sur le HUD → **Scripts locaux**.

Le terminal utilise son châssis NOVA, ses néons, ses pistes PCB et les préférences de texte du gestionnaire ; l’ouverture ne dépend pas de l’apparence du terminal XFCE.

## Stabilité du HUD

Le HUD est déclaré comme panneau X11 avant son premier affichage. Sa réservation est réappliquée après le placement initial par XFCE et les propriétés identiques ne sont plus réécrites à chaque synchronisation.

## Ouvrir le terminal

Depuis le HUD, la barre inférieure ou **NEXUS → NOVA Terminal**. Pour les versions 0.7.1 et 0.7.2 déjà installées, l’application NOVA existe aussi et peut être ouverte avec :

```bash
novabar --nova-terminal
```

Le nouveau paquet 0.7.3 relaie les commandes publiques de son lanceur vers un runtime utilisateur activé plus récent. Les commandes internes de vérification, de récupération et de PTY ne sont pas redirigées.

**Paramètres → Upgrade** installe le correctif. Fermer les anciennes fenêtres de terminal puis ouvrir NOVA Terminal depuis les nouveaux raccourcis. Le gestionnaire de terminaux préféré et les raccourcis clavier globaux de XFCE ne sont pas modifiés par cette correction des lanceurs NOVA.

[Paquet DEB 0.7.3](https://github.com/florian74410/Health-and-Perfs---Navigation-Controler-Bar/releases/download/v0.7.3/NovaBar_0.7.3_amd64.deb)
