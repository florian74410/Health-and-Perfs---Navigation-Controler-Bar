# 🎛️ Interface et contrôles

> Une barre ultra-fine sur le bureau, transparente en dehors des modules et responsive.

[🏠 Accueil](Home.md) · [🚀 Démarrage](Premiers-pas.md) · [📦 Installation](Installation.md) · [🎛️ Interface](Interface.md) · [🔌 Plugins](Plugins.md) · [🛠️ Dépannage](Depannage.md)

---

![Repères de l'interface](assets/interface.svg)

## 📐 Géométrie du HUD

| Élément | Valeurs acceptées | Valeur initiale |
|---|---|---|
| Épaisseur | **50–150 px** | 72 px |
| Longueur | 25–100 % du bord | 100 % |
| Position | Haut / Bas / Gauche / Droite | Haut |
| Alignement | Gauche / Centre / Droite | Centre |
| Opacité des fonds | 0–100 % | 88 % |
| Rétractation | Activée ou désactivée, délai 3–120 s | 15 s |
| Actualisation des capteurs | 1–30 s | 2 s |

Les modules conservent leur géométrie proportionnelle : à faible largeur, la disposition s'adapte. Le fond hors panneaux est transparent. L'application ne réserve pas actuellement d'espace de travail comme une barre de tâches : les fenêtres plein écran et certains compositeurs peuvent la recouvrir.

## 🧭 Boutons

**TURBO⌄** : emplacement de contrôle non encore fonctionnel ; n'effectue aucun overclocking. **Console** : menu de scripts locaux du dossier choisi ; confirmation nécessaire avant exécution. **Dossier** : configuration ; **Extensions** : Plugin Control Center ; **Préférences** : réglages ; **? Wiki** : documentation GitHub dans le navigateur (v0.3.6+) ; **⤢** : hauteur ; **✕** : quitter.

Un menu contextuel et l'icône système proposent les actions importantes. Les modules peuvent être réordonnés par glisser-déposer. Le clic sur le module CPU peut ouvrir sa vue Holo si le plugin correspondant est actif.

## ⌨️ Raccourcis

- **Ctrl+B** : afficher / masquer (raccourci par défaut).
- **Ctrl+Q** : quitter.
- Les raccourcis personnalisables comprennent l'affichage, les préférences et l'agrandissement. Leur capture globale dépend des permissions X11 / Windows / macOS ; sur Wayland, une variante locale peut être utilisée.

![Aperçu réel des effets néon](../novabar-neon-preview.png)

---

<sub>NovaBar • CYBER NEXUS HUD • Documentation maintenue dans le dépôt. Les illustrations utilisent des valeurs d'exemple ; les sondes réelles dépendent du système et du matériel.</sub>

## NovaBar 0.4 · Holo et thèmes

Trois thèmes partagent le même kit UI : Blue Neon, Green Matrix, Red Blood.
Les traces PCB parcourent toute la fenêtre et la puce NovaBar occupe l’espace des actions.
Chaque **logo en haut à droite du plugin** est le seul déclencheur du Holo.
Un clic ouvre les détails du plugin activé, un second clic ferme. Aucun survol ni clic sur les valeurs ne l’ouvre.
CPU, GPU, RAM, SSD, FANS et NETWORK ont un panneau ; les données manquantes restent « — ».
La flèche vers le haut minimise manuellement. Le bord de l’écran et la zone de notification révèlent la barre.
Paramètres propose Always visible, Auto retract et Manual retract only, ainsi qu’un onglet Wiki.
Always visible désactive le repli temporisé ; la flèche reste une commande manuelle explicite.
