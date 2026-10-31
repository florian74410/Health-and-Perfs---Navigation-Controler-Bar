# Linux — Mint XFCE / Ubuntu / Bazzite Desktop

### Nouveau — formats natifs (.deb et .flatpak)
- `NovaBar_0.3.6_amd64.deb` : installation Mint/Ubuntu directement par gestionnaire de paquets.
  Double-cliquer le .deb ou `sudo apt install ./NovaBar_0.3.6_amd64.deb`.
  Lancer ensuite « NovaBar » depuis le menu, ou exécuter `novabar`.
- `NovaBar_0.3.6_x86_64.flatpak` : bundle Flatpak installable avec
  `flatpak install --user ./NovaBar_0.3.6_x86_64.flatpak`,
  puis `flatpak run io.github.florian74410.NovaBar`.
  Nécessite Flatpak et le runtime Freedesktop 25.08 (téléchargement séparé possible).

Les deux paquets contiennent directement NovaBar et ouvrent la configuration au
premier lancement. Ils remplacent leurs propres fichiers programme lors d'une
mise à niveau sans effacer les profils, thèmes et plugins. **Ils ne désinstallent
pas automatiquement un précédent runtime installé par l'ancien .run** :
fermer toute instance encore ouverte et éviter de lancer deux versions en parallèle.

Le Flatpak utilise un sandbox : certaines sondes CPU/GPU, nvidia-smi et le
démarrage automatique peuvent être limités. Pour un monitoring matériel
complet sur Linux Mint XFCE, privilégier le .deb.

### Installateur autonome historique (.run)

Télécharger `CyberNexusHUD-Linux-x86_64.run` puis exécuter :

```sh
sh CyberNexusHUD-Linux-x86_64.run
```

Le fichier contient l’installateur graphique, NovaBar et ses dépendances.
Bazzite Desktop reste expérimental. Pas de mode Gaming.
