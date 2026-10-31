# 🧠 Holo CPU — CORE MATRIX

> Une fenêtre holographique pour détailler les mesures par cœur, sans altérer la barre principale.

[🏠 Accueil](Home.md) · [🚀 Démarrage](Premiers-pas.md) · [📦 Installation](Installation.md) · [🎛️ Interface](Interface.md) · [🔌 Plugins](Plugins.md) · [🛠️ Dépannage](Depannage.md)

---

![Diagramme du panneau Holo CPU](assets/holo-cpu.svg)

## Comment l'ouvrir ?

1. Allez dans **Extensions → Plugins**.
2. Installez le plugin **CPU Manager / Viewer** (`cpu-manager-viewer`) depuis le catalogue officiel ou un ZIP valide.
3. Activez ce plugin, puis cliquez sur le **logo CPU en haut à droite** du module. Le survol et le clic sur les valeurs ne déclenchent rien. Un second clic sur ce logo ferme le panneau.
4. Fermez la fenêtre Holo avec **✕** ou utilisez **Épingler** pour maintenir son affichage.

La fenêtre Holo peut s'ancrer près du module CPU et se repositionner lorsque la barre change d'écran ou de taille. Elle ne constitue pas une transformation de tous les modules.

## Données affichées

- Identité du processeur, nombre de cœurs physiques et threads si disponibles.
- Température, fréquence, charge et puissance CPU **si la sonde fournit ces mesures**.
- Fréquences et températures détaillées par cœur lorsque la topologie et les mesures du système le permettent.
- **—** en cas de fréquence, de température ou de puissance individuelle inconnue.

**Important :** Intel RAPL fournit une puissance totale de package, et le logiciel ne calcule **pas** de watts fictifs pour chaque cœur. La topologie physique peut être inconnue sur certains systèmes.

## Panneaux compacts et transparents — 0.5.1

![CPU et réseau transparents](../../Assets/Previews/novabar-v051-transparent-holo.png)

*Rendu réel Qt avec données de démonstration. La grille montre le bureau à travers les panneaux ; elle ne fait pas partie du logiciel.*

Le CPU s’ouvre à **460 × 330 px**. Les panneaux GPU, RAM, stockage, ventilateurs et réseau s’ouvrent à **380 × 280 px**. Les lignes défilent dans le panneau ; aucun tableau ni zone de défilement n’a de fond gris ou blanc. Les textes, contours et circuits néon suivent le thème actif.

## Détails des autres Holo

| Plugin | Mesures affichées si disponibles |
|---|---|
| GPU | Charge, température, fréquence, VRAM utilisée/totale et puissance |
| RAM | Utilisée, disponible, totale et pourcentage |
| Stockage | Capacité et espace libre du volume système ; lecture/écriture agrégées de tous les disques |
| Ventilateurs | Nom de la sonde et RPM |
| Réseau | Réception/envoi globaux et par interface, état et vitesse de lien |

Le logo en haut à droite de **chaque plugin actif** ouvre son Holo. Les débits par interface sont calculés entre deux relevés ; ils restent « — » au premier échantillon. La vitesse du lien en Mbit/s est différente du débit mesuré en MB/s.

[Notes de version et installation 0.5.1](../UPDATE_V051.md)

---

<sub>NovaBar • CYBER NEXUS HUD • Documentation maintenue dans le dépôt. Les illustrations utilisent des valeurs d'exemple ; les sondes réelles dépendent du système et du matériel.</sub>
