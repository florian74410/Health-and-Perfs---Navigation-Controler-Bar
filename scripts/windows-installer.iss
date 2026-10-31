[Setup]
AppId=CyberNexusHUD
AppName=CYBER NEXUS HUD
AppVersion=0.3.3
DefaultDirName={localappdata}\Programs\CyberNexusHUD
DefaultGroupName=CYBER NEXUS HUD
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=CyberNexusHUD-Setup-Windows
Compression=lzma2/fast
SolidCompression=yes
UninstallDisplayIcon={app}\CyberNexusInstaller.exe

[Files]
Source: "..\dist\CyberNexusInstaller\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Installer ou reconfigurer NovaBar"; Filename: "{app}\CyberNexusInstaller.exe"
Name: "{group}\Désinstaller le lanceur"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\CyberNexusInstaller.exe"; Description: "Configurer et installer NovaBar"; Flags: nowait postinstall skipifsilent
