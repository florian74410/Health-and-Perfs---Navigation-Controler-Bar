# NOVA NEXUS HD — priority fixes after Macro visual tests

## 1. Window buttons (blocking)
An experimental XFWM4 theme is **not release-ready** until close, maximize,
minimize and focus work on Firefox, terminal, Thunar and other applications.

Inspect:
`xfconf-query -c xfwm4 -p /general/theme`
`xfconf-query -c xfwm4 -p /general/button_layout`
Usual XFCE button layout: `O|HMC` (menu, hide, maximize, close).
Use XFCE Window Manager settings to revert to a known-good decoration
if the experimental pixmap theme omits required assets; do not ship it by default.

## 2. Power Holo
Added `nova_nexus/power_monitor.py` telemetry groundwork (sysfs, read only).
It reports battery volts, amps, watts and Wh (when counter exists), a separate
**estimated** remaining energy from Ah * voltage, battery health where counters
exist, and an accumulated discharge Wh session. Unknown AC wall watts and CPU
package watts remain missing (not fabricated). A Full battery with current 0
is **not** a reading of 0 W computer power consumption.
Next: wire readings to the actual existing Power Holo widget (do not create
another disconnected power dashboard), add W/V/A/Wh plots and sensor state text.

## 3. NOVA Terminal
Identify the existing NovaBar terminal implementation and enable a vertical
scrollbar on its output widget; preserve scrollback, keyboard navigation and
resize behavior. Theme scrollbar with cyan hover and bezel, not hidden.
When theme NOVA is enabled, make NOVA Terminal the **user opt-in** preferred
terminal for NOVA actions only, with a saved prior preference. Changing the
system-wide x-terminal-emulator via root alternatives is NOT allowed as an
automatic cosmetic update. Respect user defaults outside NOVA.
If the UI requests system-wide default, offer a separate explicit setting
with reversible handling of preferred-app entries.

## 4. Turbo
Intel pstate `no_turbo=0` means turbo enabled. Implement explicit
polkit authorization for the exact sysfs write, validate 0/1, verify
read-back, and do not elevate the entire Qt GUI. No blanket sudoers rules.
UI should show availability, state and denial/error.

## Release gate
All above must be implemented in the **existing NovaBar runtime**, tested on
Macro X11, and packaged with a working rollback before any stable .deb or
automatic update is published.
