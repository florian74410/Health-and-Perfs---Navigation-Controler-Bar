# À faire — NovaBar 0.8.3 BlueNeon

**Statut : conception seulement, aucune fonctionnalité livrée.** Base de développement visée : **0.8.2, commit restant à identifier**. Ne pas présumer de fonctionnalités non vérifiées. Conserver le code, les images et l'organisation existants.

## Références graphiques EXISTANTES dans le dépôt
- `Assets/Previews/nova-v075-terminal-scrollback.png` — **référence principale de NEXUS Terminal**, inspectée : titre NOVA NEXUS / TERMINAL MANAGER, chrome bleu sombre, boutons minimiser/maximiser/fermer à symboles rouges, menus Fichier/Édition/Affichage/Aide, onglets, panneaux terminal séparables, scrollbar bleu électrique, trames PCB en fond.
- `Assets/Previews/novabar-v0611-nexus.png` — palette et cadre NEXUS / APPLICATIONS inspectés.
- Visuel utilisateur de notification « NOVA / NOTIFICATION — Electric Blue PCB » — référence pour fenêtres flottantes, popups et Paramètres.
- **Ne pas remplacer les visuels existants par des images conceptuelles générées** : reproduire les éléments UI en Qt natif. Une capture conceptuelle n'est pas une capture produit.

## 1. UI BlueNeon / correctif Paramètres
- [ ] Corriger le fond cyan saturé, le mauvais contraste et les défauts d'alpha/transparence de la 0.8.0 ; valider sur Linux Mint XFCE/X11.
- [ ] Aligner Paramètres, notifications et popups sur le même design NEXUS sombre : contours biseautés, PCB fin, quelques reflets néon animés, texte contrasté.
- [ ] Animation périphérique légère, pouvant être désactivée ; éviter opacité / couleurs incorrectes aux coins sur bureaux clairs.
- [ ] Préserver disposition, contenus, plugins et réglages actuels ; réduire les marges et paddings inutiles. Les décors ne doivent jamais masquer les widgets.

## 2. HUD : bouton Macros & Scripts
- [ ] À la place du bouton Plugin Manager du HUD, un bouton déroulant « Macros » (gestionnaire de plugins conservé dans Paramètres).
- [ ] Quatre propositions d'icône : fichier script </>, algorithme, .EXE avec engrenage, terminal >_ avec engrenage ; choix utilisateur.
- [ ] Menu listant les scripts .sh enregistrés : nom lisible, exécuter, « Ajouter » et « Gérer ».

## 3. Macro = fichier .sh, rien de plus
- [ ] Dossier unique de scripts sous la configuration utilisateur NovaBar : `~/.config/novabar/macros/` (à ajuster après inspection de l'arborescence réelle).
- [ ] Chaque macro est **un fichier .sh** ; son nom affiché vient du nom de fichier (ou première ligne commentaire si besoin, sans base de données).
- [ ] Paramètres > Macros : ListView des .sh du dossier, boutons Créer / Modifier / Supprimer et éditeur popup BlueNeon (nom + contenu du script).
- [ ] Exécution simple et sûre : `subprocess.Popen(["bash", chemin_absolu_du_script], cwd=dossier_macros, ...)` (équivalent de `bash ./xxxx.sh` depuis le dossier). **Ne jamais concaténer une entrée dans `shell=True`**.
- [ ] Option chmod +x possible uniquement sur le fichier choisi dans le dossier macros ; **non requis** pour `bash script.sh`.
- [ ] Scripts exemple, facultatifs : VPS Connect via `ssh` (clé/agent SSH existant, aucun mot de passe stocké), ouvrir terminal, ouvrir FileZilla/SFTP. Ne pas intégrer d'adresse/identifiant sensible fictif.
- [ ] Refuser chemins hors dossier, liens symboliques non autorisés et noms à traversal ; confirmations pour création, édition, suppression et lancement de scripts sensibles.
- [ ] Aucune couche service, JSON, SQLite, moteur de workflow, ordonnanceur, télémétrie ou autre complexité pour ce module.

## 4. NEXUS Terminal : base Qt, rendu ancien conservé
**Décision : PySide6 + QTermWidget natif, sous réserve de validation d'intégration/packaging. Pas de comparaison xterm.js/WebEngine tant que Qt fonctionne correctement.**

- [ ] Garder la fenêtre et les habillages de la capture `nova-v075-terminal-scrollback.png` : chrome, menus, onglets, PCB, titres/boutons. Ne changer que la zone d'émulation interne si nécessaire.
- [ ] Vérifier la compatibilité exacte des bindings QTermWidget/PySide6, des bibliothèques natives et de l'installateur .deb avant implémentation. Si indisponible, choisir une alternative Qt éprouvée, pas un émulateur terminal fait maison.
- [ ] Un QTermWidget par session et un QSplitter pour les dispositions : 1, vertical, horizontal, 2×2, 2+1 et colonne +2 ; séparateurs manipulables.
- [ ] Terminal interactif réel : PTY intégré à QTermWidget, ANSI/UTF-8, ssh, sudo, vim, nano, top, htop ; resize correct sans tronquer le texte.
- [ ] Raccourcis : Ctrl+Shift+C copier, Ctrl+Shift+V coller, Ctrl+C interruption, Ctrl+Shift+T nouvel onglet ; Ctrl+Alt+T optionnel pour ouverture du NEXUS Terminal.
- [ ] Scrollback >= 2 000 lignes, molette, Maj+Page haut/bas, scrollbar visible, historique pendant production de sortie.
- [ ] UI compacte et responsive : barre de titre et menus fins, marge autour de la zone terminal idéalement 4–8 px, pas de grands paddings ou bandeaux vides. Les panneaux doivent exploiter presque tout l'espace disponible.
- [ ] Conserver les boutons fermer/minimiser/maximiser, double clic titre, déplacement, mode plein écran et focus clavier correct.
- [ ] Contrôler mémoire, fluidité, fermeture de sessions et processus orphelins ; animations limitées au chrome, jamais au rendu terminal.
- [ ] Ne pas ajouter de serveur, WebSocket, WebEngine ni couche de synchronisation.

## 5. Tests avant ajout de nouvelles fonctions
- [ ] Comparer la nouvelle interface aux deux captures Assets réelles, vérifier les angles et la transparence sur fond de bureau clair et sombre.
- [ ] Installer et lancer sur Mint XFCE/X11 ; vérifier raccourcis/clavier FR, coller multi-lignes, application SSH interactive, vim/nano et scrollback.
- [ ] Tester disposition 1/2/2×2/2+1, redimensionnement rapide, 100k lignes, plusieurs sessions et fermeture propre.
- [ ] Vérifier création, lancement, modification et suppression d'un .sh, et qu'aucune macro n'est exécutée automatiquement.
- [ ] Tests de non-régression : HUD, Paramètres, plugins, panneaux et profils existants.
- [ ] Après obtention d'une **base saine et stable**, seulement alors **proposer** des améliorations facultatives avant de les ajouter. Aucun ajout fonctionnel non demandé.

## Notes de mise en œuvre
- Le projet actuel est à comparer au **commit exact 0.8.2** avant tout chantier.
- Les exemples visuels « Macros » sont des maquettes, pas des fonctions déjà disponibles.
