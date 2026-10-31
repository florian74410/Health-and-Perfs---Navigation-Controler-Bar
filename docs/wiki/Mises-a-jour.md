# 🔄 Mises à jour et sauvegardes

> La priorité est de ne pas détruire une installation saine ni les plugins locaux.

[🏠 Accueil](Home.md) · [🚀 Démarrage](Premiers-pas.md) · [📦 Installation](Installation.md) · [🎛️ Interface](Interface.md) · [🔌 Plugins](Plugins.md) · [🛠️ Dépannage](Depannage.md)

---

## 📦 Selon votre installateur

| Mode | Mise à jour | Nettoyage |
|---|---|---|
| **.deb** | Installer le nouveau `.deb` avec `apt` | Fichiers du paquet remplacés ; profil conservé |
| **Flatpak** | Installer un bundle plus récent | Le gestionnaire Flatpak garde son modèle de versions |
| **.run** | Télécharger le nouveau lanceur et l'exécuter | Le nouveau runtime est d'abord testé ; nettoyage des anciennes versions gérées |
| **Windows** | Nouveau setup portant le même AppId | Lanceur remplacé, runtime versionné |
| **macOS** | Nouveau DMG ou mise à jour intégrée disponible | Respecter le processus de l'OS |

Les paquets `.deb` et Flatpak **n'effacent pas** un ancien runtime géré par `.run` : désinstallez manuellement cette copie si vous migrez définitivement, après sauvegarde de votre profil.

## 🛡️ Installation transactionnelle du runtime autonome

```mermaid
flowchart TD
  A[Version actuellement installée] --> B[Préparer le nouveau runtime]
  B --> C{Autotest OK ?}
  C -->|Non| D[Conserver la version précédente]
  C -->|Oui| E[Activer la nouvelle version]
  E --> F[Mettre à jour les raccourcis et les métadonnées]
  F --> G[Nettoyer uniquement les anciennes versions gérées]
```

Une version encore utilisée et verrouillée peut rester en place. Le nettoyage ne doit jamais parcourir arbitrairement les dossiers utilisateur.

## 💾 Ce qui ne doit pas disparaître

- Les profils dans `Documents/NovaBar/App/Profiles` et `Profiles`.
- Le catalogue et la configuration des sources GitHub.
- Les ZIP/plugins dans `Documents/NovaBar/Plugins`.
- Les préférences locales du compte et les thèmes utilisateur.

## 🔎 Vérifier un téléchargement

Pour le fichier `.run` : `sh CyberNexusHUD-Linux-x86_64.run --check`. Pour les autres paquets, consultez `Executable/SHA256SUMS` et `Executable/manifest.json`. Une empreinte permet de constater une corruption, mais ne remplace **pas** une signature d'éditeur indépendante.

[📦 Ouvrir les téléchargements](../../Executable/README.md)

---

<sub>⚡ NovaBar • CYBER NEXUS HUD · Les illustrations sont documentaires, les fonctions non livrées sont signalées.</sub>
