# Code signing for Solitaire+

**Who this is for:** the person who holds the repository's GitHub secrets (today: the game's creator). Everyone
else, including AI assistants, only needs the box below.

> **In short:** releases are signed by GitHub, never by hand. The private key exists only as two GitHub secrets
> (and one offline backup). The updater trusts the certificate thumbprints listed in
> `updater/trusted_publishers.py`, and nothing else. Never put a `.pfx` file, a password or Base64 key text in
> the repository, a chat, an issue or a log.

## What signing does here

A release is signed in two ways, both with the same certificate:

| What is signed | How | Who checks it | What it gives |
|---|---|---|---|
| `SolitairePlus.exe`, `SolitaireNet.exe`, `SolitaireUpdater.exe`, the installer and its uninstaller | Authenticode (`signtool`) | Windows | "Verified publisher: Solitaire+ Developers" instead of "Unknown publisher", **if** the player trusts the certificate (the installer offers to) |
| `manifest.json` (the list of every file in the release with its SHA-256) | A detached signature, `manifest.json.p7s` | `SolitaireUpdater.exe` | Proof that an update came from you. Because the manifest lists every file's hash, this one signature covers every file in the update |

The updater compares the **thumbprint** (the certificate's SHA-1 fingerprint, 40 hex characters) with the list
built into it (`updater/trusted_publishers.py`). This works even if the player never trusted the certificate in
Windows. If the signature is missing, broken or from another certificate, the updater shows two warnings
("This update could not be verified", then "Are you sure?" with an "I understand the risk" box) before it will
install anything. It never installs an unverified update silently.

The certificate is **self-signed**: no company vouches for it, and it costs nothing. It can sign programs only:
it is not a certificate authority, so even on a PC that trusts it, it cannot vouch for websites or other
certificates.

## Part 1: one-time setup (about 20 minutes)

Do this once, on your own PC, before the first release that contains the updater (v0.0.7). The order matters:
players' updaters can only trust a certificate whose thumbprint was built into them, so the list must be filled
in **before** the first signed release goes out.

1. **Create the certificate.** In PowerShell, from the repository folder:

   ```powershell
   .\tools\new_signing_cert.ps1 -OutDir C:\SolitairePlusKeys
   ```

   Use a folder **outside** the repository (the script refuses one inside it). It asks for a password of at
   least 12 characters; store it in a password manager. It writes three files and prints the thumbprint:

   | File | What it is | Where it goes |
   |---|---|---|
   | `solitaireplus-signing.pfx` | **Secret.** Certificate and private key, protected by the password | Your offline backup only (password manager attachment, or a USB stick kept somewhere safe) |
   | `solitaireplus-signing.pfx.txt` | **Secret.** The same file as Base64 text | Pasted into a GitHub secret in step 2, then deleted |
   | `SolitairePlus-Publisher.cer` | Public certificate (no key) | Nowhere; CI exports its own copy from the secret. Keep it for reference |

   The script never touches the Windows certificate stores and never uploads anything.

2. **Add the two GitHub secrets.** On GitHub: the repository → **Settings** → **Secrets and variables** →
   **Actions** → **New repository secret**. Add both:

   | Name | Value |
   |---|---|
   | `SIGNING_CERT_PFX_BASE64` | The whole content of `solitaireplus-signing.pfx.txt` (one long line) |
   | `SIGNING_CERT_PASSWORD` | The password you chose |

   Then delete `solitaireplus-signing.pfx.txt`. GitHub never shows a secret again once saved, and it hides
   secrets in logs.

3. **Publish the thumbprint.** Copy the thumbprint the script printed (40 characters, for example
   `0DCF2758C471C0587B824E58A66E6D99B2893A63`) into two places, in one pull request:
   - `updater/trusted_publishers.py`:

     ```python
     PUBLISHERS = [
         {"name": "Solitaire+ Developers", "thumbprint": "PASTE-THE-40-CHARACTERS-HERE"},
     ]
     ```

   - `README.md`, the "Publisher certificate" line, so players can compare it with what Windows shows when the
     installer asks them to trust the certificate.

   Merge the pull request. The next release (made with `tools/release.ps1`, see [RELEASING.md](RELEASING.md))
   is signed automatically.

4. **Check the first signed release.** When the release has been published:
   - right-click the downloaded `SolitairePlus-Setup-<version>.exe` → **Properties** → **Digital Signatures**:
     the signer is "Solitaire+ Developers";
   - the release lists `manifest.json.p7s` and `SolitairePlus-Publisher.cer`;
   - the release's `SolitairePlus-Publisher.cer`, opened with a double-click → **Details** → **Thumbprint**,
     shows the thumbprint in the README.

## How the GitHub workflow signs (for reference)

Only builds of a version tag (`vX.Y.Z`, made by `tools/release.ps1`) are signed. Pull request and `main`
builds are unsigned test builds, kept as downloadable artifacts for 14 days.

In `.github/workflows/release-windows.yml`, a tag build:

1. writes the `.pfx` from `SIGNING_CERT_PFX_BASE64` into the runner's temporary folder (it **stops the release**
   if the secret is missing: a release is never published unsigned);
2. runs `tools/sign_release.ps1 -CheckTrusted`, which **stops the release** if the certificate's thumbprint is
   not in `updater/trusted_publishers.py` (otherwise every player would see the two warnings);
3. signs only the exes that were rebuilt (unchanged exes are reused, already signed, from the previous release),
   with a timestamp from `timestamp.digicert.com`, and exports `SolitairePlus-Publisher.cer`;
4. writes `manifest.json` and signs it (`manifest.json.p7s`);
5. builds the installer; Inno Setup calls `sign_release.ps1` to sign the setup and its uninstaller, and ships the
   `.cer` for the installer's "Trust the Solitaire+ publisher" option;
6. deletes the `.pfx` from the runner, even if a step failed.

To sign by hand (normally never needed), see the header of `tools/sign_release.ps1`.

## Why Windows may still warn

- **"Windows protected your PC" (SmartScreen)** on the downloaded installer: SmartScreen judges downloads by
  reputation, which a self-signed certificate does not build up. Players choose **More info** → **Run anyway**.
  Only a paid certificate (or Microsoft's signing service, below) builds reputation over time.
- **"Unknown publisher"** on the exes: the player did not tick "Trust the Solitaire+ publisher" in the installer
  (or said No to Windows' confirmation). The game and updates still work; the updater's own check does not need
  Windows' trust.

## Renewing the certificate (every 5 years) or replacing it

The certificate is valid for 5 years (`sign_release.ps1` warns 30 days before it expires). Signatures made
before the expiry date stay valid afterwards (they are timestamped), but new releases need a valid certificate.
Replace it well before it expires, in this order:

1. Create a new certificate (Part 1, step 1) in a **new** folder.
2. **Add** its thumbprint to `updater/trusted_publishers.py` **next to** the old one (keep the old entry), and
   update the README line. Release that version **still signed with the old certificate** (do not change the
   secrets yet). Players' current updaters trust the old certificate, so they install it, and their new updater
   trusts both.
3. Wait until most players have that version (a few weeks).
4. Replace the two GitHub secrets with the new `.pfx` (Part 1, step 2). Releases are now signed with the new
   certificate.
5. A few releases later, remove the old thumbprint from `updater/trusted_publishers.py`.

Players who trusted the old certificate in Windows can remove it by uninstalling and reinstalling (the
uninstaller offers to remove it), or see [INSTALLING.md](INSTALLING.md), "Removing the certificate".

## If the private key leaks

Signs: the `.pfx` or the Base64 text was committed, pasted somewhere, or the PC that held it was compromised.
Someone with the key and the password can make updates that players' updaters accept, but they would still need
to get players to download them (updates are only fetched from this repository's GitHub Releases).

1. **Right away:** create a new certificate (Part 1, step 1) and replace both GitHub secrets with it. Treat the
   old key as public from now on, even if you delete the file or rewrite history. Check who has write access to
   the repository and its secrets.
2. Make a release whose `updater/trusted_publishers.py` lists **only the new thumbprint**. It has to be signed
   with the new certificate, so players' current updaters show the two warnings for this one update: tell players
   in the release notes and wherever they talk to you that this is expected, and why.
3. Tell players to remove the old certificate from Windows ([INSTALLING.md](INSTALLING.md), "Removing the
   certificate"), and give them the new thumbprint.

## Forks

A fork has no access to these secrets, so its tag builds stop at "Prepare signing certificate" by design, and
its pull request builds are unsigned (which is fine). To publish signed releases from a fork, create your own
certificate (Part 1), put your thumbprint in your fork's `updater/trusted_publishers.py`, and point
`GITHUB_REPOSITORY` in `updater/config.py` at your fork, so your players' updaters fetch your releases.

## Alternative: Microsoft's signing service (paid)

Microsoft offers a cloud code-signing service (called **Azure Trusted Signing** when this was written). It costs
a monthly fee, requires identity verification (check Microsoft's current rules for who is eligible), and gives
certificates that Windows trusts without any player action, so "Unknown publisher" disappears and SmartScreen
reputation builds up over time. The private key never leaves Microsoft.

It is **not** a drop-in replacement here. Moving to it is a project of its own:

1. Create the Azure account, the signing account, identity validation and a certificate profile (Microsoft's
   quick-start guide covers this).
2. Give GitHub access with an Azure app registration and a federated (OpenID Connect) credential, instead of the
   two secrets.
3. In the workflow, sign the exes and the installer with Microsoft's signing action instead of
   `tools/sign_release.ps1`.
4. **Change the updater's trust check.** The service issues a fresh short-lived certificate every few days, so
   its thumbprint changes all the time and the thumbprint list in `updater/trusted_publishers.py` cannot work.
   `updater/signing.py` would have to check the certificate's subject and its Microsoft issuer chain instead,
   and the manifest signature (`manifest.json.p7s`) would need another signing method, because the service does
   not hand out the private key.
5. Release the new updater signed with the **current** certificate first (as in "Renewing", step 2), so
   players' updaters accept the switch.
