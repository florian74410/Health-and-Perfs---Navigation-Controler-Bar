# NOVA Blue Neon / Graphite FX

Branch: `work/novabar-blue-neon-graphite-fx`

**Functional base**: `work/novabar-v0.8.1-linux-polish-shortcuts`
(commit `fc23161708229cbd593ea4efd2e44f17d8670e70`).
No REDBLACK code is included; 0.8.2 was not found as a separate Blue Neon
source branch in the inspected repository.

Design balance (user-selected): 75% graphite, 20% electric blue, 5%
polished steel reflections. The neutral areas are #11151B / #090D12.

A focused first implementation:
- Graphite metal housing and glass cavity for Blue Neon cockpit frames,
  preserving all mouse targets and native icons
- Animated fine electron rail in the cockpit, using its existing timer
- Graphite-tinted Holo glass while maintaining accessibility and transparency
- Subtle moving highlight in Settings, only while the dialog is visible
- Strict clipping of settings reflection inside bevels
- Additional tests for alpha and animation primitive

Settings, functional modules, plugin discovery, native XFCE panels and window
geometry are unchanged. This branch is **not** production until manual
Linux Mint XFCE visual approval.
