# À faire — NovaBar 0.8.3 BlueNeon

**Statut :** feuille de route / conception, aucune fonctionnalité déclarée livrée.  
**Base cible :** code source NovaBar 0.8.2 **à identifier et vérifier** (commit/branche/artefact GitHub Actions).  
**Dépôt :** florian74410/Health-and-Perfs---Navigation-Controler-Bar.  
**Identité :** NOVA NEXUS HD / Cyber-Neon, fond bleu nuit, néon bleu électrique, cadres métalliques à angles coupés, traces PCB, animations discrètes.

## 0. Préparation / garde-fous
- [ ] Identifier le SHA exact de la version 0.8.2 et comparer son contenu à la branche de développement avant tout portage.
- [ ] Préserver images, assets, disposition générale des panneaux, plugins, paramètres et profils ; ne pas remplacer le thème par un aplat cyan.
- [ ] Réaliser les changements fonctionnels sur une branche de développement séparée ; préserver le runtime 0.8.2 et les chemins de retour à l'ancienne version.
- [ ] Captures comparatives sur fond clair et sombre : pixels réellement transparents aux quatre coins, zéro halo noir ou blanc intempestif.

## 1. Identité visuelle BlueNeon
- [ ] Unifier les fenêtres Paramètres, Notifications, Macros, NEXUS Terminal et fenêtres flottantes autour du visuel de référence « NOVA / NOTIFICATION » : verre bleu nuit, contour biseauté métallique, PCB animé, reflets contrôlés.
- [ ] Réparer la régression de l'interface Paramètres observée dans la 0.8.0 : fond cyan saturé, titre illisible, contraste et espacement.
- [ ] Utiliser de véritables zones alpha/transparence sur X11 ; contrôler les bordures avec et sans composition XFCE.
- [ ] Animation configurable et économe en CPU/GPU ; respect du paramètre « réduire les animations ».
- [ ] Contrastes de texte et tailles des boutons cohérents ; paddings/margins compacts et adaptatifs.

## 2. HUD Bar : raccourci Macros & Scripts
- [ ] Remplacer l'emplacement du bouton Plugin Manager dans le HUD par un bouton ouvrant « Macros & Scripts » ; le gestionnaire de plugins reste accessible depuis Paramètres et éventuellement un autre emplacement.
- [ ] Choix final parmi 4 icônes : fichier Script </>, algorithme/organigramme, .EXE + engrenage, terminal >_ + éclair/rouage. Icône paramétrable.
- [ ] Menu déroulant compact listant les macros activées : nom, icône, type, éventuellement raccourci clavier ; entrée « Ajouter une macro » et « Gérer les macros ».
- [ ] Exemples non préremplis avec identifiants inventés : « VPS Connect (IA-TB) », « Ouvrir NEXUS Terminal », « Connexion SFTP », « Script de synchronisation ».
- [ ] Un clic lance l'action autorisée, avec compte rendu dans NOVA Notifications (succès/échec) ; aucun shell distant ne doit être connecté sans configuration SSH existante.

## 3. Paramètres > Macros
- [ ] Ajouter un onglet « Macros & Scripts » à la navigation existante, sans casser les sections actuelles.
- [ ] ListView/table scrollable avec colonnes Nom, Type, Commande (résumé), Autorisations, État et actions.
- [ ] Boutons Créer, Modifier, Supprimer avec confirmation, activation/désactivation et tri.
- [ ] Popup de création/édition conforme au visuel « NOVA / NOTIFICATION » : nom, description facultative, type, commande/chemin de script, répertoire de travail, terminal à utiliser, environnement autorisé, options d'exécution.
- [ ] Options explicites : lancer dans NEXUS Terminal, laisser la fenêtre ouverte, exécuter en arrière-plan (si adapté), fichier exécutable, permission chmod +x **seulement sur un chemin utilisateur validé**.
- [ ] Sauvegarde persistante atomique (JSON versionné ou SQLite), sauvegarde préalable lors des migrations, export/import optionnel, contrôle de duplication et schéma de validation.
- [ ] Les macros à risque exigent confirmation ; aucune commande privilégiée ou destructrice automatique. Ne jamais enregistrer de mots de passe dans les profils.

## 4. Réintégrer NEXUS Terminal — étude technique
**Objectif :** restaurer le rendu NOVA Terminal / fenêtre gris anthracite, coins biseautés et PCB bleu électrique, tout en remplaçant l'émulation terminal artisanale par un moteur éprouvé.

### Candidats
- **QTermWidget + PySide6** : premier prototype, moteur Qt natif ; contrôler disponibilité des bindings pyside6-qtermwidget et des bibliothèques natives selon les cibles et PyInstaller, licences et stabilité.
- **xterm.js + Qt WebEngine + PTY local** : prototype comparatif, très personnalisable, FitAddon/clipboard/search/renderer ; coût mémoire et sécurisation du pont WebChannel à mesurer.
- **VTE (GTK)** : option de secours native, moins adaptée au cœur Qt/PySide6.

### Exigences obligatoires
- [ ] Véritable PTY (pseudo-terminal) par onglet/panneau ; UTF-8, ANSI/VT, prompts interactifs, sudo/ssh, nano/vim/top/htop et applications TUI.
- [ ] Copier : Ctrl+Shift+C ; coller : Ctrl+Shift+V ; sélection, menu contextuel, Ctrl+C transmis au processus pour interruption (pas copie) ; raccourcis configurables, gestion fiable des layouts clavier.
- [ ] Barre de défilement fonctionnelle, historique configurable (minimum 2 000 lignes), molette, Maj+Page haut/bas, recherche dans l'historique.
- [ ] Modes : simple, deux colonnes, deux lignes, grille 2×2, vue 2+1, colonne+2 ; séparation redimensionnable, onglets indépendants, taille de fenêtre responsive.
- [ ] Optimiser l'espace : marge interne du terminal 4–8 px (selon résolution et DPI), titres compacts, aucun padding décoratif qui rogne l'espace des caractères ; calcul dynamique lignes/colonnes (SIGWINCH/resize PTY).
- [ ] Lancement via bouton HUD, raccourci Ctrl+Alt+T optionnel et macros ; comportement non intrusif quand une autre application gère déjà le raccourci.
- [ ] Fenêtre flottante et maximisée : boutons Fermer/Maximiser/Minimiser intégrés au chrome NOVA ; déplacement et double clic titre ; focus correct.
- [ ] Persistance des profils, thèmes, disposition et connexions **sans enregistrer les secrets** ; processus fermés proprement à la fermeture d'un onglet.
- [ ] SSH vers VPS IA-TB via client OpenSSH et clés/agent SSH locaux existants ; confirmation des clés d'hôte et refus des désactivations de vérification d'hôte.
- [ ] Tests de performance (démarrage, RAM, débit 100k lignes, scroll, redimensionnement rapide), tests raccourcis, tests X11/XFCE et packaging .deb.

### Décision d'architecture (provisoire)
Prototyper **QTermWidget** en priorité dans un hôte PySide6 afin de limiter la complexité. Décider après tests concrets versus xterm.js intégré. Ne pas déclarer le choix final avant tests sur Linux Mint XFCE avec la pile Qt/PyInstaller réellement utilisée.

## 5. Conditions d'acceptation
- [ ] Aucun contrôle ni page de paramètres perdus par rapport à la 0.8.2 confirmée.
- [ ] HUD, Paramètres, Macros et Terminal visuellement fidèles à la référence NOVA Notification, visibles sur fonds de bureau clairs/sombres ; transparences et angles validés.
- [ ] Création, édition, suppression, activation et lancement de macros fonctionnels et persistants, avec erreurs et permissions gérées.
- [ ] Terminal interactif utilisable pour SSH, Vim/Nano, défilement, copier/coller, raccourcis et toutes les dispositions de panneaux demandées.
- [ ] Build .deb et tests end-to-end sur Linux Mint XFCE/X11, vérification du SHA et procédure de rollback.
- [ ] Documentation installateur, notes de version, captures réelles et distinction explicite entre fonctions existantes et nouveautés 0.8.3.

## Références
- Visuel utilisateur « NOVA / NOTIFICATION — Electric Blue PCB » fourni dans la conversation.
- Nouveau concept « NovaBar 0.8.3 BlueNeon — Macros & Scripts » : visuel de conception, valeurs et exemples fictifs.
- QTermWidget/PySide6 : https://pypi.org/project/pyside6-qtermwidget/
- xterm.js : https://xtermjs.org/ et https://xtermjs.org/docs/guides/using-addons/
- VTE : https://gnome.pages.gitlab.gnome.org/vte/gtk3/class.Terminal.html
