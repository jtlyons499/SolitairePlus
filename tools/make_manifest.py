"""Release packaging: keep unchanged exes byte-identical, list every file, build the delta.

Run after PyInstaller has built dist/SolitairePlus/ (CI does this; see docs/RELEASING.md).

    # 1. Tag builds only: put back the previous release's copy of any part whose
    #    source did not change, so players do not re-download identical code.
    python tools/make_manifest.py reuse --dist dist/SolitairePlus \
        --previous-manifest prev/manifest.json --previous-dir prev/files

    # 2. Describe the install folder (and, given the previous manifest, build the
    #    "delta" zip holding only the files that changed).
    python tools/make_manifest.py manifest --dist dist/SolitairePlus --out release/manifest.json \
        [--previous-manifest prev/manifest.json --delta-dir release]

Why "reuse" exists: rebuilding an exe from the same source does not give
byte-identical output (timestamps, and later the signature timestamp). If the
updater compared fresh builds, every release would re-download every exe.
Each part of the install has a "source hash": a fingerprint of the files it
is built from plus the Python/PyInstaller versions. When that fingerprint
matches the previous release, the previous release's file is reused unchanged.

Parts ("components") of the install folder:
    game     SolitairePlus.exe         built from main.py and solitaireplus/
    net      SolitaireNet.exe          built from netservice/
    updater  SolitaireUpdater.exe      built from updater/
    runtime  SolitairePlus_Data/*      Python, pygame and other libraries (DLLs, .pyd, base_library.zip)
    content  SolitairePlus_Data/assets, data, multiplayer, version.py   copied straight from the repo
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import platform
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = "SolitairePlus_Data"
FULL_ASSET = "Solitaire-Windows.zip"
MANIFEST_NAMES = {"manifest.json", "manifest.json.p7s"}
SCHEMA = 1

EXES = {"SolitairePlus.exe": "game", "SolitaireNet.exe": "net", "SolitaireUpdater.exe": "updater"}
CONTENT_PREFIXES = tuple(f"{DATA_DIR}/{folder}/" for folder in ("assets", "data", "multiplayer"))
CONTENT_FILES = {f"{DATA_DIR}/version.py"}

# What each built component is made from. Over-including only causes an extra
# rebuild; under-including could ship a stale exe, so when in doubt, add it.
BUILD_TOOLING = ["SolitairePlus.spec", "requirements-build.txt", "tools/write_version_info.py", "assets/app_icon.ico"]
COMPONENT_INPUTS = {
    # version.py is excluded on purpose: it ships as a loose file, so a version bump alone
    # does not need a new game exe.
    "game": (["main.py", "solitaireplus/**/*.py", "requirements.txt", *BUILD_TOOLING], {"version.py"}),
    "net": (["netservice/**/*.py", *BUILD_TOOLING], set()),
    "updater": (["updater/**/*.py", *BUILD_TOOLING], set()),
    "runtime": (["SolitairePlus.spec", "requirements.txt", "requirements-build.txt"], set()),
}
REUSABLE = set(COMPONENT_INPUTS)  # "content" is always taken fresh from the repo


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def component_of(relpath: str) -> str:
    if relpath in EXES:
        return EXES[relpath]
    if relpath in CONTENT_FILES or relpath.startswith(CONTENT_PREFIXES):
        return "content"
    if relpath.startswith(DATA_DIR + "/"):
        return "runtime"
    return "other"


def toolchain() -> str:
    try:
        from importlib.metadata import version
        pyinstaller = version("pyinstaller")
    except Exception:
        pyinstaller = "unknown"
    return f"python {platform.python_version()} {platform.machine()}; pyinstaller {pyinstaller}"


def source_hash(component: str, root: Path = ROOT, tools: str | None = None) -> str:
    patterns, excluded = COMPONENT_INPUTS[component]
    files = set()
    for pattern in patterns:
        for path in root.glob(pattern):
            relpath = path.relative_to(root).as_posix()
            if path.is_file() and relpath not in excluded and "__pycache__" not in path.parts:
                files.add(relpath)
    digest = hashlib.sha256((tools or toolchain()).encode())
    for relpath in sorted(files):
        digest.update(f"\n{relpath}\n".encode())
        # Normalise line endings so a Windows (CRLF) and a CI (LF) checkout agree.
        digest.update((root / relpath).read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()


def scan(dist: Path) -> dict[str, dict]:
    files = {}
    for path in sorted(dist.rglob("*")):
        if not path.is_file():
            continue
        relpath = path.relative_to(dist).as_posix()
        if relpath in MANIFEST_NAMES:
            continue
        files[relpath] = {"sha256": sha256_file(path), "size": path.stat().st_size,
                          "component": component_of(relpath)}
    return files


def load_manifest(path: Path | None) -> dict | None:
    if path is None or not path.is_file():
        return None
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema") != SCHEMA:
        print(f"Previous manifest {path} has schema {manifest.get('schema')}; ignoring it.")
        return None
    return manifest


# ----------------------------------------------------------------------------- commands

def cmd_reuse(dist: Path, previous_manifest: Path, previous_dir: Path, rebuilt_out: Path | None) -> None:
    previous = load_manifest(previous_manifest)
    if previous is None:
        print("No usable previous release manifest: every part is new this time.")
        reused_components: set[str] = set()
    else:
        reused_components = {
            name for name in REUSABLE
            if previous.get("components", {}).get(name, {}).get("source_hash") == source_hash(name)
        }
    copied = 0
    for relpath, info in scan(dist).items():
        component = info["component"]
        if component not in reused_components:
            continue
        old = previous["files"].get(relpath)
        old_path = previous_dir / relpath
        if old and old["sha256"] != info["sha256"] and old_path.is_file() and sha256_file(old_path) == old["sha256"]:
            shutil.copy2(old_path, dist / relpath)
            copied += 1
    for name in sorted(REUSABLE):
        state = "unchanged -> reusing previous release's files" if name in reused_components else "changed -> fresh build"
        print(f"  {name:<8} {state}")
    print(f"Restored {copied} file(s) from the previous release.")
    rebuilt = [exe for exe, component in EXES.items() if component not in reused_components and (dist / exe).is_file()]
    if rebuilt_out:
        rebuilt_out.parent.mkdir(parents=True, exist_ok=True)
        rebuilt_out.write_text("\n".join(rebuilt) + ("\n" if rebuilt else ""), encoding="utf-8")
        print(f"Freshly built exes (these need signing): {', '.join(rebuilt) or 'none'} -> {rebuilt_out}")


def cmd_manifest(dist: Path, out: Path, version: str, previous_manifest: Path | None, delta_dir: Path | None) -> dict:
    files = scan(dist)
    missing = [exe for exe in EXES if exe not in files]
    if missing:
        raise SystemExit(f"Build output is missing {', '.join(missing)}")
    tools = toolchain()
    manifest = {
        "schema": SCHEMA,
        "version": version,
        "created": _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat(),
        "toolchain": tools,
        "full_asset": FULL_ASSET,
        "delta": None,
        "components": {name: {"source_hash": source_hash(name, tools=tools)} for name in sorted(COMPONENT_INPUTS)},
        "files": files,
    }
    previous = load_manifest(previous_manifest)
    if previous is not None and previous.get("version") != version:
        old_files = previous.get("files", {})
        changed = [p for p, info in files.items() if old_files.get(p, {}).get("sha256") != info["sha256"]]
        removed = sorted(set(old_files) - set(files))
        summarize(changed, removed, files, previous["version"], version)
        if delta_dir is not None:
            name = f"SolitairePlus-{version}-delta-from-{previous['version']}.zip"
            delta_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(delta_dir / name, "w", zipfile.ZIP_DEFLATED) as archive:
                for relpath in changed:
                    archive.write(dist / relpath, relpath)
            manifest["delta"] = {"from": previous["version"], "asset": name, "files": len(changed), "paths": changed}
            print(f"Wrote {delta_dir / name} ({len(changed)} file(s))")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=1, sort_keys=False) + "\n", encoding="utf-8")
    print(f"Wrote {out}: version {version}, {len(files)} files")
    return manifest


def summarize(changed: list[str], removed: list[str], files: dict, old_version: str, new_version: str) -> None:
    print(f"\nChanges from {old_version} to {new_version}:")
    by_component: dict[str, list[str]] = {}
    for relpath in changed:
        by_component.setdefault(files[relpath]["component"], []).append(relpath)
    for component in ("game", "net", "updater", "runtime", "content", "other"):
        items = by_component.get(component, [])
        if items:
            shown = ", ".join(items[:8]) + (" ..." if len(items) > 8 else "")
            print(f"  {component:<8} {len(items):>4} changed: {shown}")
    if removed:
        print(f"  removed  {len(removed):>4}: {', '.join(removed[:8])}{' ...' if len(removed) > 8 else ''}")
    if not changed and not removed:
        print("  nothing changed")
    print()


def main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)

    reuse = commands.add_parser("reuse", help="restore unchanged parts from the previous release")
    reuse.add_argument("--dist", type=Path, required=True)
    reuse.add_argument("--previous-manifest", type=Path, required=True)
    reuse.add_argument("--previous-dir", type=Path, required=True, help="the previous release's files, unzipped")
    reuse.add_argument("--rebuilt-out", type=Path, help="write the list of freshly built exes here")

    build = commands.add_parser("manifest", help="write manifest.json (and the delta zip)")
    build.add_argument("--dist", type=Path, required=True)
    build.add_argument("--out", type=Path, required=True)
    build.add_argument("--version", help="defaults to version.py")
    build.add_argument("--previous-manifest", type=Path)
    build.add_argument("--delta-dir", type=Path, help="where to write the delta zip")

    args = parser.parse_args(argv)
    if args.command == "reuse":
        cmd_reuse(args.dist, args.previous_manifest, args.previous_dir, args.rebuilt_out)
    else:
        sys.path.insert(0, str(ROOT / "tools"))
        from release_helpers import current_version
        cmd_manifest(args.dist, args.out, args.version or current_version(), args.previous_manifest, args.delta_dir)


if __name__ == "__main__":
    main(sys.argv[1:])
