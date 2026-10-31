[Setup]
AppId=CyberNexusHUD
AppName=CYBER NEXUS HUD
AppVersion=0.3.4
CloseApplications=yes
RestartApplications=no
UsePreviousAppDir=yes
DefaultDirName={localappdata}\Programs\CyberNexusHUD
DefaultGroupName=CYBER NEXUS HUD
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=CyberNexusHUD-Setup-Windows
Compression=lzma2/fast
SolidCompression=yes
UninstallDisplayIcon={app}\CyberNexusInstaller.exe

[InstallDelete]
; Remove names used by older launchers; Inno upgrades the standard same-AppId
; CyberNexusInstaller.exe in place. Do not touch user data or NovaBar runtimes.
Type: files; Name: "{app}\\NovaBarInstaller.exe"
Type: files; Name: "{app}\\CyberNexusInstaller-old.exe"

[Files]
Source: "..\dist\CyberNexusInstaller\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Installer ou reconfigurer NovaBar"; Filename: "{app}\CyberNexusInstaller.exe"
Name: "{group}\Désinstaller le lanceur"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\CyberNexusInstaller.exe"; Description: "Configurer et installer NovaBar"; Flags: nowait postinstall skipifsilent
