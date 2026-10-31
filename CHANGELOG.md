# NovaBar 0.5.1

- Compte-tours circulaires dans la barre compacte : CPU/GPU en GHz, RAM/SSD en pourcentage. Les cadrans restent proportionnels de 50 à 150 px ; en espace réduit, les valeurs restent prioritaires.
- Holo CPU réduit à 460 × 330 px, autres Holo à 380 × 280 px ; tableaux défilants.
- Surfaces des Holo entièrement transparentes, y compris les zones de défilement ; seuls textes, cadres et circuits néon sont dessinés.
- Réseau : état, vitesse de lien et débits par interface ; valeurs initiales ou indisponibles signalées par un tiret.
- Détails GPU/CPU : puissance mesurée si disponible. Capacité RAM/VRAM/volume système et I/O disque clairement identifiés.
- 68 tests locaux réussis. Rendu Qt inspecté avec des données de démonstration.

# Changelog

## 0.5.0 — Update 2

- Service `cpu_mode_controller`, backend sysfs Linux Intel/AMD et fallback explicite Windows/macOS.
- Turbo Off / Turbo On / Auto 85 °C ; hystérésis 5 °C, coupure demandée en cas de sonde absente.
- Aucun changement CPU au lancement ; état effectif vérifié, erreurs de permissions visibles.
- Downloader séparé des paquets hors ligne, formats natifs et vérification SHA-256 avant exécution.
- Configuration initiale des thèmes, position, épaisseur, repli, priorité et Holo.
- Packaging Windows contenant le runtime, manifestes de release natifs et bootstrap multi-OS.
- Plugins CPU 2.1.0 et autres modules 1.1.0 ; kit Holo partagé, données indisponibles affichées « — ».
- Première installation : plugins officiels intégrés ; versions et activations existantes préservées.
- Demande X11 ABOVE / Windows TOPMOST sans voler le focus ; limites Wayland/macOS documentées.

## 0.4.0 — Update 1

- Kit Holo partagé, trois thèmes et traces PCB bord à bord.
- Logo puce partagé avec l’installateur.
- Logos de plugins en haut à droite : clic uniquement pour ouvrir/fermer le Holo.
- Panneaux GPU, RAM, SSD, FANS, NETWORK en complément de CPU CORE MATRIX.
- Flèche de minimisation et trois politiques de rétractation.
- Onglet Wiki et migration des préférences existantes.
