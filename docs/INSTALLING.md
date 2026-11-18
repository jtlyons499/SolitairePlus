# Installing and updating Solitaire+

**Who this is for:** players (Part I and Part II), and anyone helping a friend install the game. Windows 10 or
11, 64-bit. You do not need Python or administrator rights.

Your saves are never stored in the game folder. They live in your user folder:

| What | Where |
|---|---|
| Profiles, career, settings | `%LOCALAPPDATA%\SimpleSolitaire` (profiles in its `saves` folder) |
| Multiplayer name, avatar, options | `%LOCALAPPDATA%\SolitaireMultiplayer` |

(Paste either path into File Explorer's address bar to open it.) Installing, updating and uninstalling leave
these folders alone, unless you tell the uninstaller to delete them.

---

## Part I: new players

1. Open the [latest release](https://github.com/jtlyons499/SolitairePlus/releases/latest) and download
   `SolitairePlus-Setup-<version>.exe`.
2. Double-click it. If Windows shows **"Windows protected your PC"**, click **More info**, then **Run anyway**.
   (Windows shows this for programs that few people have downloaded yet; it is not a virus warning.)
3. Click through the installer:
   - **Shortcuts:** tick "Create a desktop shortcut" if you want one. The game is always in the Start Menu.
   - **Security: "Trust the Solitaire+ publisher (recommended)"** (official releases only). Leave it ticked.
     Near the end, Windows asks **"Do you want to install this certificate?"**. Before clicking **Yes**,
     check that the "Thumbprint (sha1)" in that window matches the **Publisher certificate** thumbprint in the
     project's [README](../README.md). Windows calls it a "certification authority" in that window, but this
     certificate can only mark Solitaire+ programs as coming from the developers: it cannot vouch for websites
     or anything else.
   - **Saves from an older copy:** leave the box unticked (see Part II if you played before October 2026).
4. Click **Install**, then **Finish** with "Play Solitaire+ now" ticked.

The game is installed for your Windows account only, in `%LOCALAPPDATA%\Programs\SolitairePlus`.

**If you said No to the certificate** (or the installer did not offer it), the game and its updates still work
and are still checked. Windows just shows "Unknown publisher" for the game's programs. You can trust the
certificate later, below.

### Trusting the certificate by hand (optional)

Only do this with the `SolitairePlus-Publisher.cer` file from the game folder
(`%LOCALAPPDATA%\Programs\SolitairePlus`) or from an official release page, and only if its thumbprint matches
the README.

**With the mouse:**

1. Double-click `SolitairePlus-Publisher.cer`. On the **Details** tab, check that **Thumbprint** matches the
   README.
2. On the **General** tab, click **Install Certificate…** → **Current User** → **Next**.
3. Choose **Place all certificates in the following store** → **Browse…** → **Trusted Root Certification
   Authorities** → **OK** → **Next** → **Finish**. Windows asks you to confirm: click **Yes**.
4. Repeat steps 2 and 3, choosing **Trusted Publishers** as the store.

**With PowerShell** (run in the game folder; Windows asks you to confirm the first one):

```powershell
Import-Certificate -FilePath .\SolitairePlus-Publisher.cer -CertStoreLocation Cert:\CurrentUser\Root
Import-Certificate -FilePath .\SolitairePlus-Publisher.cer -CertStoreLocation Cert:\CurrentUser\TrustedPublisher
```

### Removing the certificate

The uninstaller offers to remove it. To remove it yourself, press **Win+R**, type `certmgr.msc`, press Enter,
then delete **Solitaire+ Developers** from **Trusted Root Certification Authorities → Certificates** and from
**Trusted Publishers → Certificates**. Or in PowerShell:

```powershell
Get-ChildItem Cert:\CurrentUser\Root, Cert:\CurrentUser\TrustedPublisher |
    Where-Object Subject -like '*Solitaire+ Developers*' | Remove-Item
```

---

## Part II: players who already have the game

### You installed version 0.0.7 or later

The game updates itself. Nothing to download by hand.

- **Automatic:** when the game starts, it checks for a new version in the background. If there is one, the main
  menu shows an **Update to X.Y.Z** button. Click it: the game saves, closes, downloads only the files that
  changed, and opens again.
- **By hand:** **Options → Updates → Check now** (then **Update now**), or run **Solitaire+ Updater** from the
  Start Menu while the game is closed.
- **Turning the automatic check off:** **Options → Updates → Auto check: Off**. You can still check by hand.

Every update is checked for the developers' signature. If it cannot be verified, the updater shows **"This
update could not be verified"** and then **"Are you sure?"**. Click **Cancel** unless the game's creator told you
the certificate changed. If an update is interrupted (power cut, crash), the game undoes it automatically the
next time it starts.

### You play an unzipped copy of 0.0.6 or 0.0.6b

Your saves are already in `%LOCALAPPDATA%\SimpleSolitaire\saves`, outside the game folder.

1. **Back up first:** copy the folders `%LOCALAPPDATA%\SimpleSolitaire` and `%LOCALAPPDATA%\SolitaireMultiplayer`
   somewhere safe (for example your Desktop).
2. Install the game (Part I). Leave "Saves from an older copy" unticked.
3. Start the game and check that your profiles are there.
4. Delete the old unzipped game folder. From now on, use the Start Menu shortcut.

### You play a copy from before October 2026

Those versions kept saves inside the game folder (a `saves` folder next to the game).

1. **Back up first:** copy the whole old game folder somewhere safe.
2. Run the installer. On **"Saves from an older copy"**, tick **Import saves from an older Solitaire+ folder**,
   click **Next**, and choose the old game folder (or its `saves` folder). Saves that already exist in your
   user folder are never overwritten; the installer tells you how many it copied.
3. Start the game and check your profiles. Then you can delete the old folder.

**By hand instead:** copy the `profile_*.json` files from the old `saves` folder into
`%LOCALAPPDATA%\SimpleSolitaire\saves` (create the folder if it does not exist), with the game closed.

### The ZIP instead of the installer

Each release also has `Solitaire-Windows.zip`: extract it to a folder and run `SolitairePlus.exe`. It uses the
same saves and can update itself the same way, but it has no Start Menu entry, no uninstaller and no certificate
option. The installer is recommended.

---

## Uninstalling

**Settings → Apps → Installed apps → Solitaire+ → Uninstall.** The uninstaller then asks:

- **"Also delete your Solitaire+ saves and settings?"** The default is **No** (keep them). Choose Yes only if you
  will never play again.
- **"Remove the Solitaire+ publisher certificate from this PC?"** (official releases only) Yes, unless you will
  reinstall soon.

If Solitaire+ is not in the list but the folder `%LOCALAPPDATA%\Programs\SolitairePlus` exists (an early test
copy), run the installer once (it installs over it), then uninstall normally.

## When something goes wrong

| Problem | What to do |
|---|---|
| "Windows protected your PC" | **More info → Run anyway** (Part I, step 2). |
| An antivirus removes or blocks a file | Restore it from quarantine if you downloaded it from the official release page, or reinstall. Please report it on the project's Issues page. |
| An update failed or the game won't start after one | Start the game again: it undoes the interrupted update. If that does not help, run `SolitaireUpdater.exe --recover` from the game folder, or reinstall (saves are kept). |
| The update check says it could not check | You are offline, or GitHub is not reachable. Try **Check now** later. |
| You need the updater's log | `%LOCALAPPDATA%\SimpleSolitaire\logs\updater.log` |
