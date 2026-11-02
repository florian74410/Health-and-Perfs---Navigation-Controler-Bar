# Mise à niveau vers NOVA NEXUS HD / NovaBar 1.0.0

Projet : **Cyber-Neon Interactif – THEME 1.0**. Les pseudonymes de crédit existants sont conservés : **0verF1ow & La Puce**.

Le patch est une mise à jour complète du runtime natif qui conserve les données utilisateur. Les ZIP runtime des GitHub Releases sont les vrais paquets installables par **Paramètres → Upgrade**. L'archive `NOVA-Patch-to-v1.0.0.zip` contient le manifeste et les instructions ; elle n'est pas un exécutable et ne doit pas être lancée.

Le manifeste distribuable `nova-patch-to-v1.0.0-manifest.json` est généré après compilation par `scripts/package_upgrade.py`. Il comporte les URL de fichiers réellement produits, les architectures, tailles et SHA-256. Le manifeste compatible avec les clients 0.7.x reste `novabar-update-manifest.json`. Les URL définitives sont celles de la release obtenue : aucun manifeste avec URL fictive n'est placé dans les sources.

Les préversions demandent l'activation volontaire du canal préversion dans Upgrade. Les installations stables ne les reçoivent pas automatiquement. Une stable 1.0.0 ne doit être publiée qu'après validation système et graphique complète.

Le client sauvegarde les profils, réglages et plugins avant activation, teste le nouveau runtime et conserve le précédent. **Restaurer la version précédente** vérifie l'ancien exécutable avant de rétablir son activation et les données sauvegardées. Un ancien runtime déjà supprimé par une version historique ne peut pas être recréé par cette fonction.

Confiance : téléchargement HTTPS depuis les releases du dépôt officiel, vérification SHA-256 ; aucune clé indépendante de signature de manifeste n'est configurée. Les systèmes signés/notariés ne sont pas annoncés tant que leurs certificats ne sont pas disponibles.
