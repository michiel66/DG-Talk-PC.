#define MyAppName "DG-Talk PC"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "DG-Talk"
#define MyAppExeName "DG-Talk-PC.exe"

[Setup]
AppId={{A82E973E-5634-4B72-A50F-D77F8A68A6A5}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\DG-Talk PC
DefaultGroupName=DG-Talk PC
DisableProgramGroupPage=yes
OutputDir=output
OutputBaseFilename=DG-Talk-PC-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\DG-Talk-PC.exe

[Files]
Source: "..\dist\DG-Talk-PC\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\DG-Talk PC"; Filename: "{app}\DG-Talk-PC.exe"
Name: "{autodesktop}\DG-Talk PC"; Filename: "{app}\DG-Talk-PC.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Bureaubladsnelkoppeling maken"; GroupDescription: "Extra snelkoppelingen:"

[Run]
Filename: "{app}\DG-Talk-PC.exe"; Description: "DG-Talk PC starten"; Flags: nowait postinstall skipifsilent
