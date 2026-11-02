# NOVA NEXUS HD 1.1 Linux — journal de stabilité

## 2026-11-02 — P0 XFCE

### Point de départ vérifié

- Référence: branche `release/nova-nexus-hd-v1.1.0`, commit `7d1aada088a4f7fd7319ca110e8ce68c3f476a5a`.
- Le run Actions #172 échoue sur Ubuntu dans `scripts/test_xfce_session.py`, à l'attente du panneau XFCE après arrêt brutal du processus NovaBar.
- Le journal du job montre que les contrôles précédents (workarea, fenêtre externe maximisée, terminal) passent avant l'expiration de l'attente de restauration.
- L'échec prouve que le panneau n'est pas observé comme visible dans le délai du test. Il ne démontre pas encore, à lui seul, une cause racine unique.

### Défaut confirmé dans le code

Le chemin de récupération au démarrage et `NativePanelGuard.restore()` effaçaient le journal après un retour positif de `set_panel_visible()`. Ce résultat confirme uniquement que les requêtes X11 ont été émises; il ne confirme pas que XFCE a effectivement remappé ses panneaux. Le watchdog avait aussi une vérification de repli trop large après redémarrage: une seule fenêtre XFCE visible pouvait valider plusieurs panneaux sauvegardés.

### Changement appliqué

- Ajout d'une vérification d'état effectif des panneaux visibles.
- Sauvegarde de leur géométrie globale en plus de l'ID X11 et du PID; une géométrie sauvegardée permet de retrouver un panneau dont le XID a changé lors d'un redémarrage.
- Conservation du journal tant que tous les panneaux sauvegardés ne sont pas retrouvés visibles.
- Ajout de deux tests unitaires distinguant la réussite de la requête X11 de la visibilité effective.

### Compléments P1 et diagnostic

- Les quatre cases d'activation indépendantes étaient déjà présentes dans Paramètres; `Settings.validate()` empêchait toutefois de les désactiver toutes. Cette restriction est supprimée et un test valide le scénario bureau natif seul.
- Une trace JSONL persistante note maintenant détection, sauvegarde, demande de masquage, arrêt du propriétaire, redémarrage, vérification de visibilité et conservation/suppression du journal.
- Si le test XFCE échoue, il imprime la trace ainsi que le journal de récupération avant de quitter, pour distinguer panne de watchdog, de remappage et de détection.

### Validation en cours

La PR brouillon #24 ajoute une exécution Linux dédiée. Le workflow historique est ignoré uniquement pour la branche de travail afin qu'aucun job Windows ou macOS ne soit lancé pour cette mission. L'intégration XFCE réelle, les tests unitaires et le build Linux doivent encore confirmer le correctif.

### Suite P0

1. Lire les résultats du workflow Linux dédié.
2. Si la session XFCE échoue encore, instrumenter les étapes de détection, journalisation, masquage, crash, reprise et visibilité avec un état conservé jusqu'à la fin du test.
3. Ne pas déclarer la restauration réparée avant un passage du scénario X11 réel.
