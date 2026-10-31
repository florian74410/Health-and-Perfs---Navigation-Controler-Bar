# NOVA NEXUS HD — release gate

**The development branch is not the production NovaBar auto-update channel.**

## Automated validation

The `nova-foundation-tests.yml` workflow compiles all source files and runs
`tests/test_nova_*.py`. The `nova-preview.yml` workflow creates a user-space
preview archive after these checks. Check actual Actions status and download
the artifact; an uploaded archive is not itself proof of successful XFCE UI tests.

## Visual acceptance checklist (Linux Mint XFCE X11)

- [ ] GTK buttons, menu hover and keyboard focus remain readable at 100% and 150%.
- [ ] XFWM4 button controls are visible and function with the current window manager;
      all required title/frame/button pixmap names are present.
- [ ] Window decoration applies correctly to active/inactive windows and can be restored.
- [ ] NOVA Explorer handles file/folder opens, absent paths, symlinks, permissions,
      renaming, trash failures and a directory with thousands of entries.
- [ ] Explorer animations work and are disabled with reduce-motion.
- [ ] Notification previews are frontal, not rotated, and stay within each screen.
- [ ] No other daemon is displaced from org.freedesktop.Notifications without opt-in.
- [ ] Wallpaper renders on each workspace/monitor and restores correctly.
- [ ] Login, wrong password, lock, sleep/resume, unlock and reboot pass in a VM.
- [ ] NovaBar 0.6.11 settings, profiles and plugin upgrade still work.
- [ ] A previous .deb version restores the working UI.

## Release blockers

A theme prototype is NOT a fully supported replacement for login, lock screen,
notification daemon or file manager. Do not merge the source-only preview into
the stable updater until native integration, comprehensive tests, packaging,
checksums and rollback have been reviewed.

## Useful commands (development environment only)

```bash
python3 -m unittest discover -s tests -p 'test_nova_*.py' -v
python3 -m nova_nexus.preview
python3 -m nova_nexus.explorer
python3 -m nova_nexus.install_theme        # exports only
python3 -m nova_nexus.install_theme --apply   # changes user's theme
python3 -m nova_nexus.install_theme --restore # revert if previous state saved
python3 -m nova_nexus.wallpapers           # copies wallpaper only
python3 -m nova_nexus.wallpapers --apply
python3 -m nova_nexus.wallpapers --restore
```
