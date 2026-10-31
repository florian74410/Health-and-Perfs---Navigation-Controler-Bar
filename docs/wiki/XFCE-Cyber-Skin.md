# XFCE Cyber Skin — quatrième surface du HUD

L'habillage XFCE **ne remplace pas la barre système** : il conserve les fenêtres ouvertes, raccourcis d'applications, notifications, Wi-Fi, horloge et la liste de plugins du panneau d'origine. NovaBar fournit les trois panneaux habituels et une **quatrième couche graphique facultative**, appliquée au panneau natif.

## Déclenchement

Préférences NovaBar > **XFCE Cyber** > « Activer l'habillage CYBER NEXUS du panneau XFCE inférieur » ou menu de l'icône NovaBar dans la zone de notification > **Barre système XFCE**.

Cette fonction est désactivée par défaut. Elle nécessite une session **XFCE X11**, un panneau existant situé en bas de l'écran, `xfconf-query` et `xfce4-panel`.

La première activation :
1. Recherche le panneau du bas à partir de ses positions XFCE (sans supposer un numéro de panneau fixe).
2. Sauvegarde les propriétés de rétractation **et d'épaisseur** originales dans la configuration utilisateur de NovaBar.
3. Demande le mode de masquage natif XFCE et insère dans `~/.config/gtk-3.0/gtk.css` un bloc GTK commenté, identifié « NOVABAR CYBER NEXUS PANEL SKIN ». Le reste du CSS utilisateur est laissé intact.
4. Relance uniquement `xfce4-panel` pour charger son style. **Les lanceurs, les fenêtres ouvertes et les icônes de notification ne sont jamais modifiés.** L'épaisseur du panneau est ajustée en fonction de l'originale et restaurable.
5. Dessine, lorsqu'elle détecte le panneau visible, une couche Qt sans capture de souris : bordures, circuits, microcontacts et deux impulsions lumineuses circulant en sens inverse.

Le panneau XFCE gère lui-même l'apparition au survol du bord. Le délai avant le repli est **réglable de 1 à 120 secondes** (10 s par défaut), via la propriété GTK `-XfcePanelWindow-popdown-delay`. Le style demande une **zone de rappel de 1 pixel**, nécessaire au survol : le corps du panneau disparaît entièrement, mais il ne s'agit pas d'un masquage mathématique à 0 px. Le résultat précis dépend de la version du panneau et du thème GTK.

## Apparence

- **Blue Neon** : cyan / bleu électrique.
- **Green Matrix** : vert phosphorescent.
- **Red Blood** : rouge/rose néon.
- Intensité de la couche animée : 0 à 100 % dans **Préférences > XFCE Cyber**.
- Épaisseur native réglable de **100 à 200 %** de la hauteur d'origine (175 % par défaut), sans jamais dépasser le double ; réglage sauvegardé et réversible. Les icônes et applications d'origine sont préservées.
- Seules des bordures de quelques pixels accueillent les effets, sans recouvrir les icônes.

### Ajouter des icônes

Utiliser l'outil **Gérer les icônes et raccourcis…** dans le menu NovaBar (qui ouvre les préférences natives XFCE), ou clic droit sur le panneau > **Panneau** > **Ajouter de nouveaux éléments**. L'ordre et les raccourcis restent gérés par XFCE. NovaBar n'émule pas une seconde zone de notification.

## Restauration

Désactiver « Habillage CYBER NEXUS » depuis la zone de notification ou les préférences : NovaBar enlève **uniquement son bloc CSS**, remet les valeurs de rétractation et d'épaisseur sauvegardées, supprime sa couche d'animation et relance le panneau pour recharger le style. Les modifications GTK antérieures de l'utilisateur restent en place.

**Limites connues :** le sélecteur GTK `.xfce4-panel.background` peut aussi teinter d'autres panneaux XFCE existants ; seule la préférence d'automasquage du panneau inférieur détecté est changée. Les effets par-dessus le panneau dépendent de la gestion des fenêtres X11/compositeur. **Wayland, Windows et macOS ne sont pas pris en charge pour cette couche XFCE.** Le panneau peut clignoter brièvement lors d'une activation/désactivation car son processus redémarre.

## Vérification avant diffusion

- Rétractation réglable (1–120 s), rappel au bord inférieur via zone native de 1 px, pas d'interception du Wi-Fi/horloge.
- Test des trois couleurs, de l'épaisseur 100–200 %, et du réglage d'intensité sur Linux Mint XFCE X11.
- Test d'une session avec deux panneaux pour vérifier que le sélecteur GTK global reste acceptable.
- Après désactivation, vérifier les styles GTK préexistants et le retour de l'ancien comportement du panneau.
