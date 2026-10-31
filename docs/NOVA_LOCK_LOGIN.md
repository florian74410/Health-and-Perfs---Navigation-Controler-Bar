# NOVA Login / Lock Screen — safe integration spec

The NOVA wallpaper and GTK theme can eventually be reused by the login greeter,
but authentication must continue to be owned by the operating system.

## LightDM Slick Greeter (Linux Mint)

Slick Greeter supports [Greeter] background, background-color, draw-grid and
other options in `/etc/lightdm/slick-greeter.conf`. This is separate from GTK
Greeter's [greeter] configuration. Identify the active greeter before editing.

A future, optional system install should place a readable wallpaper under
`/usr/share/backgrounds/`, back up existing config, explicitly ask permission,
and apply only supported appearance settings. Root privileges and rollback are
required; the feature is NOT enabled in this branch.

## Locking

Determine which actual locker implements `xflock4` on the target Mint XFCE
session (xfce4-screensaver, light-locker or other). Theme that specific locker.
Do not simulate a lockscreen with a Qt overlay; it would not secure the session.

## Acceptance

Verify user switching, suspend/resume, wrong password, keyboard layouts,
multi-monitor, emergency recovery and login after reboot in a disposable VM.
Never alter PAM or auto-login as part of NOVA cosmetic updates.
