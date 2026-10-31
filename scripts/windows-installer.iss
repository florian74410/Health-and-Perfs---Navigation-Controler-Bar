[Setup]
AppId=HealthPerfsBar
AppName=Health & Perfs Bar
AppVersion=0.1.0
DefaultDirName={localappdata}\Programs\HealthPerfsBar
DefaultGroupName=Health & Perfs Bar
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=HealthPerfsBar-Setup-Windows
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={app}\HealthPerfsBar.exe

[Files]
Source: "..\dist\HealthPerfsBar\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Health & Perfs Bar"; Filename: "{app}\HealthPerfsBar.exe"
Name: "{group}\Désinstaller"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\HealthPerfsBar.exe"; Parameters: "--setup"; Description: "Configurer et ouvrir la barre"; Flags: nowait postinstall skipifsilent

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: none; ValueName: "HealthPerfsBar"; Flags: uninsdeletevalue
