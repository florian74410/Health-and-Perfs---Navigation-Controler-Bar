# Cyber-Neon Interactif – THEME 1.0

**Marque : NOVA NEXUS HD · Application : NovaBar · Crédits existants : 0verF1ow & La Puce**

La branche `release/nova-nexus-hd-v1.0.0` intègre les sources 0.7.5/0.7.6 et l'historique de `main`. Les anciens paquets et documents sont conservés. Le numéro de runtime est 1.0.0 ; les distributions restent des **préversions `v1.0.0-rc.N`** jusqu'à validation complète. Aucun tag stable 1.0.0 ne doit être publié par ce chantier avant ces validations.

## Modifications livrées dans les sources

- Contrôles NOVA minimiser/maximiser/restaurer/fermer conservés dans les rails supérieurs ; décorations GTK/XFWM et restauration existantes intégrées.
- Historique terminal réel, scrollbar verticale bleu électrique par panneau, molette et Maj+Page Haut/Bas ; sessions indépendantes dans les dispositions fractionnées.
- Terminal : PTY POSIX Linux/macOS, ConPTY Windows via pywinpty. Un test exécute une commande dans le shell natif de chaque runner.
- HUD compact et calque PCB commun repris de la base 0.7.6.
- Barres gauche et droite : rétraction 2 secondes après sortie du curseur, annulation du délai au retour, contrôle de la position au moment de la rétraction. Un menu étranger à la barre ne bloque plus indéfiniment sa rétraction.
- Menu NEXUS : clic droit, double-clic et Maj+F10 pour ajouter aux applications ; lancement différé au simple clic pour distinguer le double-clic.
- Explorer : onglets, fil d'Ariane, favoris persistants, ajout de dossier au dock, protection contre la copie d'un dossier dans lui-même, corbeille native. L'activation du thème conserve le gestionnaire de fichiers choisi ; le remplacement exige un choix explicite.
- Thème : cinq palettes, modes Off/Eco/Standard/Ultra, couleurs, opacités, reflets, halo, biseaux, taille du texte et vitesse des effets persistants. Les nouvelles fenêtres utilisent les réglages ; les décorations système demandent une réapplication du bureau NOVA.
- POWER HOLO : données de batterie V/A/W/Ah/Wh, énergie restante, usure, source matérielle ou calculée, historique et intégration estimée de la décharge. Aucun total secteur ni puissance par cœur inventé. Un courant nul reste une mesure valide.
- Turbo ON/OFF Linux : helper `/usr/libexec/novabar-boost` fourni par le DEB, limité aux attributs kernel `no_turbo`/`boost`. Authentification administrateur graphique Polkit, état relu après action, aucun mot de passe détenu par NovaBar, aucune relance répétée après annulation sans nouvelle sélection utilisateur.
- Notifications : historique local borné, catégories, actions, durée, position, empilement et mode silencieux. Service D-Bus facultatif pour la session, qui refuse de remplacer un propriétaire existant. Le service XFCE reste actif tant que l'utilisateur ne le désactive pas lui-même.
- Upgrade : téléchargement officiel, contrôle SHA-256/taille si déclarée, test isolé du runtime, sauvegarde des profils/réglages/plugins et conservation du runtime précédent. Restauration explicite depuis Upgrade, vérification de l'ancien exécutable et réactivation. Les préversions exigent un choix volontaire.
- Pack de fonds : quinze PNG dérivés du vecteur PCB existant, cinq palettes et formats 2560×1440, 3440×1440, 1920×1440 ; profils JSON joints.

## Utilisation

**Thème** : Paramètres → Bureau NOVA → Personnaliser le thème NOVA. Sauvegarder, ouvrir une nouvelle fenêtre ; pour XFWM/GTK, appliquer de nouveau le bureau NOVA.

**Turbo** : installer le DEB, cliquer CPU Mode → Turbo On ou Turbo Off, puis saisir le mot de passe administrateur dans l'invite système. Le changement est confirmé par relecture du noyau. Si l'authentification est annulée, sélectionner de nouveau ON/OFF pour réessayer. La présence d'un agent Polkit de session et d'un contrôle Turbo exposé par le noyau est nécessaire. Ce n'est pas une invite dans le terminal et NovaBar ne lance pas de shell root.

**Consoles** : scrollbar à droite de chaque terminal ; molette ou Maj+Page ↑↓ ; saisir une commande revient à la sortie en direct. Le tampon conserve 2 000 lignes.

**Mise à jour** : Paramètres → Upgrade → Vérifier → Installer la mise à jour → Redémarrer NovaBar. Les préversions sont disponibles uniquement avec la case correspondante. Une version 0.7.x déjà distribuée ne possède pas cette nouvelle case : pour tester un candidat, installer son paquet natif complet. La mise à jour vers la future stable reste compatible avec le manifeste historique 0.7.x.

**Restauration** : Upgrade → Restaurer la version précédente → Redémarrer NovaBar. Elle exige que l'ancien runtime existe encore. Les versions historiques qui l'ont déjà supprimé ne peuvent pas être restaurées sans réinstallation de leur paquet.

## Validation et limites de la préversion

Les tests automatiques, les auto-tests de l'exécutable compilé, les tests XFCE/XFWM isolés et les quatre builds natifs sont exécutés en CI. Les contrôles D-Bus sont effectués sur un bus isolé ; l'environnement local ne permet pas d'ouvrir ce socket.

Les captures `Assets/Previews/nova-v100-*.png` montrent les widgets exécutés en rendu Qt hors écran. Le fichier `nova-v100-power-demo.png` utilise des données de démonstration explicitement identifiées ; ce n'est pas une mesure matérielle du MacBook Macro.

Restent indispensables avant une stable : essais sur bureaux réels Windows/macOS et plusieurs écrans/résolutions XFCE ; authentification Turbo sur le matériel de Flo ; cycle réel 0.7.x → 1.0.0 → restauration sur chaque OS ; vérification connexion/verrouillage/veille/reprise. Aucun remplacement de PAM, de l'authentification Windows/macOS ou du gestionnaire de connexion n'est réalisé. L'habillage login/lock facultatif n'est pas finalisé et ne doit pas être annoncé comme livré. Les intégrations de menus de gestionnaires de fichiers tiers, hors NOVA Explorer, restent limitées.

Aucune signature indépendante du manifeste, signature Windows ou notarisation Apple n'est configurée. macOS High Sierra n'est pas compatible avec Qt 6.8. Les effets complets du bureau et XFWM/Polkit restent propres à Linux ; la télémétrie dépend des capteurs réellement exposés par l'OS.

## Distribution et chemins

Sources : `src/healthbar`, `src/nova_nexus`. Ressources : `Assets/`, assets des packages Python. Installation système limitée : `packaging/linux/`. Build unique : `.github/workflows/build.yml`, `scripts/build.py` et scripts de packaging. Builds : assets des GitHub Releases, référencés par `Builds/v1.0.0/README.md`. Patch : `Patch/to-v1.0.0/README.md`, manifestes générés depuis les vrais runtimes par `scripts/package_upgrade.py`. Les URL et SHA-256 finaux doivent être lus dans la release produite, jamais inventés avant compilation.
