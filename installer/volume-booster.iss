; Inno Setup script for Volume Booster PC.
;
; Build it with build-installer.ps1, which passes the version:
;   ISCC.exe /DAppVersion=1.0.1 installer\volume-booster.iss
;
; The install is per-user (PrivilegesRequired=lowest), so it never shows a UAC
; prompt and lands in %LOCALAPPDATA%\Programs. Start-at-login is deliberately
; NOT registered here: the app owns that setting through its own toggle, and two
; sources of truth would fight each other.

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

#define AppName "Volume Booster"
#define AppExeName "VolumeBooster.exe"
#define AppPublisher "LeGaliza85"
#define AppUrl "https://github.com/LeGaliza85/volume-booster-pc"

[Setup]
AppId={{6F1B0C7A-3B4E-4F2A-9D31-8C57A2E4D910}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppUrl}
AppSupportURL={#AppUrl}/issues
AppUpdatesURL={#AppUrl}/releases
VersionInfoVersion={#AppVersion}.0
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=VolumeBoosterSetup
SetupIconFile=..\assets\volume-amplifier.ico
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
LicenseFile=..\LICENSE
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
