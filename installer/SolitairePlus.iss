; Solitaire+ installer (Inno Setup 6, https://jrsoftware.org/isinfo.php)
;
; Built by the GitHub workflow and by build_release.ps1 -Installer. By hand:
;   ISCC.exe /DAppVersion=0.0.7 /DSourceDir=..\dist\SolitairePlus installer\SolitairePlus.iss
; Optional:
;   /DPublisherCer=path\SolitairePlus-Publisher.cer /DPublisherThumbprint=ABC...  adds the
;        "Trust the Solitaire+ publisher" step (and lets the uninstaller remove that certificate)
;   /DUseSigning /Ssolsign=...                        signs the setup and the uninstaller (CI does this)
;
; What it does:
; * Installs for the current user only into %LOCALAPPDATA%\Programs\SolitairePlus: no admin
;   prompt, and the in-game updater can update it without admin rights later.
; * Never touches saves (%LOCALAPPDATA%\SimpleSolitaire, %LOCALAPPDATA%\SolitaireMultiplayer)
;   unless the player asks the uninstaller to delete them.
; * Installing over an existing copy (same AppId) upgrades it in place.

#ifndef AppVersion
  #error Pass the version: ISCC /DAppVersion=0.0.7
#endif
#ifndef FileVersion
  ; Windows version fields must be numbers only: 0.0.8-beta.1 -> pass /DFileVersion=0.0.8
  #define FileVersion AppVersion
#endif
#ifndef SourceDir
  #define SourceDir "..\dist\SolitairePlus"
#endif

#define AppName "Solitaire+"
#define GameExe "SolitairePlus.exe"
#define UpdaterExe "SolitaireUpdater.exe"

[Setup]
; Never change AppId: Windows uses it to recognise an existing installation.
AppId={{6B0E4C5A-3D7F-4B0E-9A61-2F7C1D9E5A42}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=Solitaire+ Developers
AppPublisherURL=https://github.com/jtlyons499/SolitairePlus
AppSupportURL=https://github.com/jtlyons499/SolitairePlus/issues
AppUpdatesURL=https://github.com/jtlyons499/SolitairePlus/releases
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=
DefaultDirName={autopf}\SolitairePlus
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#GameExe}
UninstallDisplayName={#AppName}
SetupIconFile=..\assets\app_icon.ico
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
OutputDir=..\release
OutputBaseFilename=SolitairePlus-Setup-{#AppVersion}
CloseApplications=yes
RestartApplications=no
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
VersionInfoVersion={#FileVersion}
#ifdef UseSigning
SignTool=solsign
SignedUninstaller=yes
#endif

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Shortcuts:"
#ifdef PublisherCer
Name: "trustcert"; Description: "Trust the Solitaire+ publisher (recommended). Windows will ask you to confirm."; GroupDescription: "Security:"
#endif

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
#ifdef PublisherCer
Source: "{#PublisherCer}"; DestDir: "{app}"; DestName: "SolitairePlus-Publisher.cer"; Flags: ignoreversion
#endif

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#GameExe}"
Name: "{autoprograms}\{#AppName} Updater"; Filename: "{app}\{#UpdaterExe}"; Comment: "Check for and install Solitaire+ updates"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#GameExe}"; Tasks: desktopicon

[Run]
#ifdef PublisherCer
; certutil is built into Windows. Adding to the current user's Root store makes Windows show
; its own confirmation dialog with the certificate's thumbprint; it cannot be skipped without
; admin rights, and that is intended. TrustedPublisher makes Windows show "Verified publisher".
Filename: "{sys}\certutil.exe"; Parameters: "-user -f -addstore Root ""{app}\SolitairePlus-Publisher.cer"""; StatusMsg: "Trusting the Solitaire+ publisher..."; Flags: runminimized waituntilterminated; Tasks: trustcert
Filename: "{sys}\certutil.exe"; Parameters: "-user -f -addstore TrustedPublisher ""{app}\SolitairePlus-Publisher.cer"""; Flags: runhidden waituntilterminated; Tasks: trustcert
#endif
Filename: "{app}\{#GameExe}"; Description: "Play {#AppName} now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Files the in-game updater added after installation are not in Inno's list, so remove the
; whole program folder content. Saves live elsewhere and are NOT touched here.
Type: filesandordirs; Name: "{app}\SolitairePlus_Data"
Type: filesandordirs; Name: "{app}\.update"
Type: files; Name: "{app}\*.updating-old"
Type: files; Name: "{app}\pending-delete.txt"
Type: files; Name: "{app}\manifest.json"
Type: dirifempty; Name: "{app}"

[Code]
const
  SavesSubdir = 'SimpleSolitaire\saves';

var
  ImportChoicePage: TInputOptionWizardPage;
  ImportPage: TInputDirWizardPage;

{ ----- Optional pages: bring saves over from an old "unzipped" copy of the game ----- }

procedure InitializeWizard;
begin
  ImportChoicePage := CreateInputOptionPage(wpSelectTasks,
    'Saves from an older copy',
    'Only needed if you played a version from before October 2026.',
    'Since October 2026 your saves are kept in your user folder automatically, so most players can skip this. ' +
    'If you played an older ZIP version, tick the box to copy its profiles over. Existing saves are never overwritten.',
    False, False);
  ImportChoicePage.Add('Import saves from an older Solitaire+ folder');
  ImportChoicePage.Values[0] := False;

  ImportPage := CreateInputDirPage(ImportChoicePage.ID,
    'Import saves from an older copy',
    'Choose the old game folder.',
    'Pick the folder that contains the old game (or its "saves" folder), then click Next.',
    False, '');
  ImportPage.Add('Old game folder:');
  ImportPage.Values[0] := ExpandConstant('{userdesktop}');
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := (PageID = ImportPage.ID) and not ImportChoicePage.Values[0];
end;

function ImportOldSaves(const Folder: String): Integer;
var
  Source, Target: String;
  Found: TFindRec;
begin
  Result := 0;
  Source := AddBackslash(Folder);
  if DirExists(Source + 'saves') then
    Source := Source + 'saves\';
  Target := ExpandConstant('{localappdata}\') + SavesSubdir + '\';
  ForceDirectories(Target);
  if FindFirst(Source + 'profile_*.json', Found) then
  try
    repeat
      if not FileExists(Target + Found.Name) then
        if FileCopy(Source + Found.Name, Target + Found.Name, True) then
          Result := Result + 1;
    until not FindNext(Found);
  finally
    FindClose(Found);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Copied: Integer;
begin
  if (CurStep = ssPostInstall) and ImportChoicePage.Values[0] and (Trim(ImportPage.Values[0]) <> '') then
  begin
    Copied := ImportOldSaves(Trim(ImportPage.Values[0]));
    if not WizardSilent then
      MsgBox(IntToStr(Copied) + ' save file(s) imported. Saves that already existed were left unchanged.',
             mbInformation, MB_OK);
  end;
end;

{ ----- Uninstall: saves and the certificate are kept unless the player says otherwise ----- }

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if CurUninstallStep <> usPostUninstall then
    exit;
  if UninstallSilent then
    exit;
  if MsgBox('Also delete your Solitaire+ saves and settings?' + #13#10#13#10 +
            'Choose No to keep them (recommended if you might play again).',
            mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
  begin
    DelTree(ExpandConstant('{localappdata}\SimpleSolitaire'), True, True, True);
    DelTree(ExpandConstant('{localappdata}\SolitaireMultiplayer'), True, True, True);
  end;
#ifdef PublisherThumbprint
  if MsgBox('Remove the Solitaire+ publisher certificate from this PC?' + #13#10#13#10 +
            'Choose Yes unless you plan to reinstall Solitaire+ soon.',
            mbConfirmation, MB_YESNO) = IDYES then
  begin
    { Removing from Root shows Windows' own confirmation dialog. }
    Exec(ExpandConstant('{sys}\certutil.exe'), '-user -delstore TrustedPublisher {#PublisherThumbprint}', '',
         SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Exec(ExpandConstant('{sys}\certutil.exe'), '-user -delstore Root {#PublisherThumbprint}', '',
         SW_SHOWMINNOACTIVE, ewWaitUntilTerminated, ResultCode);
  end;
#endif
end;
