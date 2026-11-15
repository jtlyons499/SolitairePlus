"""Single source of truth for the Solitaire+ version.

Change this ONLY through tools/release.ps1, which also updates CHANGELOG.md,
commits, and creates the matching git tag (v + this value). CI refuses to
publish a release whose tag does not match this string.

Format: Semantic Versioning, MAJOR.MINOR.PATCH, with an optional pre-release
suffix such as "0.0.7-beta.1". Do not use letter suffixes like "0.0.6b";
the updater cannot compare those.
"""

__version__ = "0.0.7"
