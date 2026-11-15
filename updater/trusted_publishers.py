"""Signing certificates the updater trusts. Built into SolitaireUpdater.exe.

Add the thumbprint (SHA-1 fingerprint, 40 hex characters) of the Solitaire+
code-signing certificate below; docs/CODE_SIGNING.md explains how to get it.

When the certificate is replaced, KEEP the old entry and add the new one,
release that update (signed with the old certificate), and only then start
signing with the new certificate. Remove the old entry a few releases later.

While this list is empty, every update shows the two "could not be verified"
warnings.
"""

PUBLISHERS = [
    # {"name": "Solitaire+ Developers", "thumbprint": "0123456789ABCDEF0123456789ABCDEF01234567"},
]
