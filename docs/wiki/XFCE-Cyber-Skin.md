# XFCE Cyber Skin — quatrième surface du HUD

L'habillage XFCE **ne remplace pas la barre système** : il conserve les fenêtres ouvertes, raccourcis d'applications, notifications, Wi-Fi, horloge et la liste de plugins du panneau d'origine. NovaBar fournit les trois panneaux habituels et une **quatrième couche graphique facultative**, appliquée au panneau natif.

## Déclenchement

Préférences NovaBar > **XFCE Cyber** > « Activer l'habillage CYBER NEXUS du panneau XFCE inférieur » ou menu de l'icône NovaBar dans la zone de notification > **Barre système XFCE**.

Cette fonction est désactivée par défaut. Elle nécessite une session **XFCE X11**, un panneau existant situé en bas de l'écran, `xfconf-query` et `xfce4-panel`.

La première activation :
1. Recherche le panneau du bas à partir de ses positions XFCE (sans supposer un numéro de panneau fixe).
2. Sauvegarde la propriété de rétractation originale dans la configuration utilisateur de NovaBar.
3. Demande le mode de masquage natif XFCE et insère dans `~/.config/gtk-3.0/gtk.css` un bloc GTK commenté, identifié « NOVABAR CYBER NEXUS PANEL SKIN ». Le reste du CSS utilisateur est laissé intact.
4. Relance uniquement `xfce4-panel` pour charger son style. **Les lanceurs et la taille existants ne sont jamais modifiés.**
5. Dessine, lorsqu'elle détecte le panneau visible, une couche Qt sans capture de souris : bordures, circuits, microcontacts et deux impulsions lumineuses circulant en sens inverse.

Le panneau XFCE gère lui-même l'apparition au survol du bord. Le délai demandé avant le repli est de **10 secondes** grâce à la propriété GTK `-XfcePanelWindow-popdown-delay` ; le résultat précis dépend de la version du panneau et du thème GTK.

## Apparence

- **Blue Neon** : cyan / bleu électrique.
- **Green Matrix** : vert phosphorescent.
- **Red Blood** : rouge/rose néon.
- Intensité de la couche animée : 0 à 100 % dans **Préférences > XFCE Cyber**.
- Le panneau conserve **strictement son épaisseur d'origine** : ni sa taille ni celle des icônes ne sont modifiées.
- Seules des bordures de quelques pixels accueillent les effets, sans recouvrir les icônes.

### Ajouter des icônes

Utiliser l'outil **Gérer les icônes et raccourcis…** dans le menu NovaBar (qui ouvre les préférences natives XFCE), ou clic droit sur le panneau > **Panneau** > **Ajouter de nouveaux éléments**. L'ordre et les raccourcis restent gérés par XFCE. NovaBar n'émule pas une seconde zone de notification.

## Restauration

Désactiver « Habillage CYBER NEXUS » depuis la zone de notification ou les préférences : NovaBar enlève **uniquement son bloc CSS**, remet la valeur de rétractation sauvegardée, supprime sa couche d'animation et relance le panneau pour recharger le style. Les modifications GTK antérieures de l'utilisateur restent en place.

**Limites connues :** le sélecteur GTK `.xfce4-panel.background` peut aussi teinter d'autres panneaux XFCE existants ; seule la préférence d'automasquage du panneau inférieur détecté est changée. Les effets par-dessus le panneau dépendent de la gestion des fenêtres X11/compositeur. **Wayland, Windows et macOS ne sont pas pris en charge pour cette couche XFCE.** Le panneau peut clignoter brièvement lors d'une activation/désactivation car son processus redémarre.

## Vérification avant diffusion

- Rétractation à 10 s, rappel au bord inférieur, pas d'interception du Wi-Fi/horloge.
- Test des trois couleurs et du réglage d'intensité sur Linux Mint XFCE X11.
- Test d'une session avec deux panneaux pour vérifier que le sélecteur GTK global reste acceptable.
- Après désactivation, vérifier les styles GTK préexistants et le retour de l'ancien comportement du panneau.
