; beboputer_tk_setup.iss — Inno Setup installer script for the tkinter build
; ─────────────────────────────────────────────────────────────────────────────
; Mirrors bin/beboputer_v7/beboputer_setup.iss exactly -- see that file's
; own header if you're comparing the two. Prerequisites:
;   1. Build the app first:  pyinstaller bin\beboputer_tk\beboputer_tk.spec
;      (output lands in  dist\Beboputer\)
;   2. Install Inno Setup 6:  https://jrsoftware.org/isinfo.php
;   3. Open this file in Inno Setup and click Build -> Compile
;      (or run from command line:  iscc beboputer_tk_setup.iss)
;
; Output: dist\BeboputerSetup.exe
; ─────────────────────────────────────────────────────────────────────────────
#define AppName      "PY-DIYCALCULATOR"
#define AppExeName   "Beboputer.exe"
; Version is the single source of truth in bin/beboputer_v7/__init__.py
; (__version__ -- beboputer_tk re-exports the exact same constant, see
; bin/beboputer_tk/__init__.py, so there's only ever one version number
; for the whole app regardless of which UI build you're packaging).
; build_installer.bat sets the BEBOPUTER_VERSION environment variable
; before invoking iscc.exe so this always tracks the app's real version
; automatically -- nothing to edit here. Falls back to a clearly-fake
; placeholder if compiled directly (e.g. by opening this file in the
; Inno Setup IDE) without going through build_installer.bat first.
#define AppVersion   GetEnv("BEBOPUTER_VERSION")
#if AppVersion == ""
  #define AppVersion "0.0.0-dev"
#endif
#define AppPublisher "Alvin Brown & Clive Maxfield"
#define AppURL       "https://www.clivemaxfield.com/diycalculator/downloads.shtml"
; SourcePath = folder containing this .iss file (bin\beboputer_tk\).
; ProjectRoot is two levels up, so this works regardless of where the repo lives.
#define ProjectRoot  SourcePath + "..\..\"
#define BuildDir     ProjectRoot + "dist\Beboputer"

[Setup]
; Deliberately a DIFFERENT AppId than beboputer_v7's installer (that
; one ends ...67890) -- these install to the same default folder name
; (PY-DIYCALCULATOR) and .exe name (Beboputer.exe), and Inno Setup
; uses AppId (not the name) to recognise "is this an upgrade of an
; already-installed app or a separate one" during install/uninstall.
; Sharing the Qt build's AppId would make installing this over/after
; it behave like an in-place upgrade (silently replacing files from a
; different codebase) instead of a clean, independent install.
AppId={{B2C3D4E5-F6A7-8901-BCDE-F12345678901}
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
SetupIconFile={#SourcePath}..\beboputer_v7\beboputer.ico
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
