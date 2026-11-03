# NEXUS Terminal — Panels Settings, Sessions, Web Inspector

## Target/source distinction
The source branch here is based on *NEXUS Terminal v0.2* from GitHub. The user's screenshot is **v0.5** / a later packaged v0.5.3; its exact source was not present on this branch. Therefore these modules are standalone Qt widgets and should be merged into the real v0.5 source before replacing a local installation. **Do not overwrite an existing working v0.5 with this older application entrypoint.**

## Implemented in this branch
- `nexus_dialogs.py`: frameless translucent QPainter NEXUS dialog; adjustable font, panel opacity preferences, toggle animations and layout preference saved using QSettings; SSH profiles and Ed25519 key generation through local ssh-keygen; API HTTPS profiles with optional OS keyring secret storage and async GET connection test.
- `web_inspector.py`: opens URL in default browser via QDesktopServices; optionally opens in Qt WebEngine with URL-request metadata inspection. Request log redacts query parameters, URL credentials and fragments; no cookies, response bodies or privileged proxy interception.
- `terminal.py` v0.2 entrypoint wires header/sidebar actions, starts a new QTermWidget shell tab and issues a safely shell-quoted ssh command upon connection.

## Future Web Inspector / Reverse Proxy
Qt WebEngine URL interception sees metadata for requests originating in its own profile, not a complete response-body capture. For genuine HTTP response inspection, application-level trace callbacks or an *opt-in* local mitmproxy process are separate, later adapter types. Never silently intercept unrelated apps or install TLS root certificates.

## Testing
```bash
python -m pip install PySide6 pytest pytest-qt
cd ThirdPartyApps/NEXUSTerminal
QT_QPA_PLATFORM=offscreen python -m pytest -q tests/test_nexus_dialogs.py
```

## Security
SSH host key verification remains enabled; key profiles store paths only, mode 0600. API tokens are not persisted in JSON. OS keyring integration is optional (requires the `keyring` Python package and working Secret Service backend). SSH key generation does not put a passphrase in process arguments. Follow secure key passphrase instructions inside the UI.
