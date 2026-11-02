# Builds natifs 1.0.0

Les sources restent dans `src/`, les scripts dans `scripts/`, et les ressources dans `Assets/` et les packages Python. Il n'existe qu'un pipeline de build : `.github/workflows/build.yml`.

Les installateurs et runtimes sont distribués dans les assets de chaque GitHub Release (préversion `v1.0.0-rc.N` tant que les contrôles critiques restent à compléter). `SHA256SUMS` et les manifestes accompagnent les paquets. Les anciens fichiers `Executable/` restent conservés pour l'historique ; leur nom générique ne signifie pas qu'ils correspondent à 1.0.0.

Cibles : Linux x86_64 `.deb` / `.run`, Windows x64 `.exe`, macOS Intel et Apple Silicon `.dmg`. macOS High Sierra n'est pas pris en charge par cette édition Qt 6.8.
