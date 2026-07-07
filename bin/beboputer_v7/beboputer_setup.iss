; beboputer_setup.iss — Inno Setup installer script for PY-DIYCALCULATOR
; ─────────────────────────────────────────────────────────────────────────────
; Prerequisites
;   1. Build the app first:  pyinstaller beboputer.spec
;      (output lands in  dist\Beboputer\)
;   2. Install Inno Setup 6:  https://jrsoftware.org/isinfo.php
;   3. Open this file in Inno Setup and click Build → Compile
;      (or run from command line:  iscc beboputer_setup.iss)
;
; Output: dist\BeboputerSetup.exe
; ─────────────────────────────────────────────────────────────────────────────
#define AppName      "PY-DIYCALCULATOR"
#define AppExeName   "Beboputer.exe"
#define AppVersion   "7.0.0"
#define AppPublisher "Alvin Brown & Clive Maxfield"
#define AppURL       "https://www.clivemaxfield.com/diycalculator/downloads.shtml"
; SourcePath = folder containing this .iss file (bin\beboputer_v7\).
; ProjectRoot is two levels up, so this works regardless of where the repo lives.
#define ProjectRoot  SourcePath + "..\..\"
#define BuildDir     ProjectRoot + "dist\Beboputer"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
OutputDir={#ProjectRoot}dist
OutputBaseFilename=BeboputerSetup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
MinVersion=10.0
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
SetupIconFile={#SourcePath}beboputer.ico
UninstallDisplayIcon={app}\{#AppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";   Description: "Create a &desktop shortcut";   GroupDescription: "Additional icons:"; Flags: unchecked
Name: "startmenuicon"; Description: "Create a &Start Menu shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "{#BuildDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}";           Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}";     Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName} now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
