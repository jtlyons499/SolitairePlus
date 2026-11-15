"""Parent side: start harness children, manage baseline worktrees, compare the output."""
from __future__ import annotations

import concurrent.futures
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HARNESS = Path(__file__).resolve().parent
CHILD = HARNESS / "child.py"
FIXTURES = ROOT / "tests" / "support" / "fixtures"
OUT_ROOT = ROOT / ".harness_out"           # git-ignored
CHILD_TIMEOUT = 600                        # seconds per script
DEFAULT_JOBS = max(1, min(8, (os.cpu_count() or 2) // 2))

APP_SETTINGS = {
    "auto_update_check": False,
    "window_size": [1366, 768],
    "fullscreen": False,
}


def child_env(appdata: Path) -> dict:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.update(
        SDL_VIDEODRIVER="dummy",
        SDL_AUDIODRIVER="dummy",
        PYGAME_HIDE_SUPPORT_PROMPT="1",
        PYTHONHASHSEED="0",
        PYTHONIOENCODING="utf-8",
        PYTHONDONTWRITEBYTECODE="1",
        LOCALAPPDATA=str(appdata),
        SOLITAIRE_NET_INPROCESS="1",
    )
    return env


def prepare_appdata(folder: Path, with_profile: bool = True) -> Path:
    data = folder / "SimpleSolitaire"
    saves = data / "saves"
    saves.mkdir(parents=True, exist_ok=True)
    (data / "app_settings.json").write_text(json.dumps(APP_SETTINGS, indent=1), encoding="utf-8")
    if with_profile:
        fixture = FIXTURES / "profile_1.json"
        if not fixture.is_file():
            raise SystemExit(f"missing {fixture}; create it with: python tools/screen_harness.py make-fixture")
        shutil.copyfile(fixture, saves / "profile_1.json")
    return folder


def run_script(checkout: Path, kind: str, name: str, out_dir: Path, with_profile: bool = True) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob(f"{name}.*"):
        old.unlink()
    for old in out_dir.glob(f"{name}__*.png"):
        old.unlink()
    with tempfile.TemporaryDirectory(prefix="harness-") as temporary:
        appdata = prepare_appdata(Path(temporary) / "appdata", with_profile)
        command = [sys.executable, str(CHILD), "--checkout", str(checkout), "--kind", kind,
                   "--name", name, "--out", str(out_dir)]
        try:
            done = subprocess.run(command, cwd=checkout, env=child_env(appdata), capture_output=True,
                                  text=True, encoding="utf-8", errors="replace", timeout=CHILD_TIMEOUT)
            output = done.stdout + done.stderr
        except subprocess.TimeoutExpired as expired:
            output = f"{expired.stdout or ''}{expired.stderr or ''}\n(timed out after {CHILD_TIMEOUT}s)"
        result_path = out_dir / f"{name}.json"
        if result_path.is_file():
            result = json.loads(result_path.read_text(encoding="utf-8"))
        else:
            result = {"name": name, "ok": False, "error": "the child process crashed:\n" + output[-4000:],
                      "shots": [], "checkpoints": []}
        result["output"] = output[-4000:]
        if with_profile is False:
            result["appdata"] = None
        return result


def run_scripts(checkout: Path, kind: str, names, out_dir: Path, jobs: int = DEFAULT_JOBS,
                progress=None) -> dict:
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = {pool.submit(run_script, checkout, kind, name, out_dir): name for name in names}
        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            results[name] = future.result()
            if progress:
                progress(name, results[name])
    return {name: results[name] for name in names}


# ------------------------------------------------------------------ git / baselines

def git(*args, cwd=ROOT) -> str:
    done = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if done.returncode:
        raise SystemExit(f"git {' '.join(args)} failed:\n{done.stderr.strip()}")
    return done.stdout.strip()


def resolve_commit(revision: str) -> str:
    return git("rev-parse", "--verify", f"{revision}^{{commit}}")


def baseline_checkout(sha: str) -> Path:
    """A detached worktree at `sha`, kept under .harness_out/worktrees/ for reuse."""
    folder = OUT_ROOT / "worktrees" / sha[:12]
    if (folder / "main.py").is_file():
        try:
            if git("rev-parse", "HEAD", cwd=folder) == sha and not git("status", "--porcelain", cwd=folder):
                return folder
        except SystemExit:
            pass
        remove_worktree(folder)
    folder.parent.mkdir(parents=True, exist_ok=True)
    git("worktree", "prune")
    git("worktree", "add", "--detach", "--force", str(folder), sha)
    return folder


def remove_worktree(folder: Path) -> None:
    try:
        git("worktree", "remove", "--force", str(folder))
    except SystemExit:
        shutil.rmtree(folder, ignore_errors=True)
        git("worktree", "prune")


def harness_digest() -> str:
    """Changes whenever the scripts, the runner or the fixtures change (invalidates cached baselines)."""
    digest = hashlib.sha256()
    for path in sorted([*HARNESS.glob("*.py"), *FIXTURES.glob("*")]):
        if path.is_file():
            digest.update(path.name.encode())
            digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()[:12]


# ------------------------------------------------------------------ image comparison

def _init_pygame():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame
    if not pygame.display.get_init():
        pygame.display.init()
    return pygame


def compare_images(first: Path, second: Path, diff_path: Path | None = None) -> int:
    """Number of differing pixels (-1 if the sizes differ). Writes a diff image when they differ."""
    pygame = _init_pygame()
    a = pygame.image.load(str(first))
    b = pygame.image.load(str(second))
    if a.get_size() != b.get_size():
        return -1
    a = a.convert(32) if a.get_bitsize() != 32 else a
    b = b.convert(32) if b.get_bitsize() != 32 else b
    if pygame.image.tobytes(a, "RGB") == pygame.image.tobytes(b, "RGB"):
        return 0
    width, height = a.get_size()
    import array
    pa = array.array("B", pygame.image.tobytes(a, "RGB"))
    pb = array.array("B", pygame.image.tobytes(b, "RGB"))
    out = array.array("B", bytes(len(pa)))
    differing = 0
    for index in range(0, len(pa), 3):
        if pa[index:index + 3] != pb[index:index + 3]:
            differing += 1
            out[index:index + 3] = array.array("B", (255, 0, 0))
        else:
            grey = (pa[index] + pa[index + 1] + pa[index + 2]) // 9
            out[index:index + 3] = array.array("B", (grey, grey, grey))
    if diff_path is not None:
        diff_path.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(pygame.image.frombytes(out.tobytes(), (width, height), "RGB"), str(diff_path))
    return differing


def compare_results(kind_label: str, names, baseline: dict, work: dict, base_dir: Path, work_dir: Path,
                    diff_dir: Path, compare_values: bool = False) -> bool:
    """Print a report; True when every script ran on both sides and everything matched."""
    if diff_dir.exists():
        shutil.rmtree(diff_dir)
    problems, identical = [], 0
    for name in names:
        left, right = baseline[name], work[name]
        if not left.get("ok") or not right.get("ok"):
            for side, result in (("baseline", left), ("working tree", right)):
                if not result.get("ok"):
                    problems.append(f"  FAILED  {name} ({side}): {first_line(result.get('error'))}")
            continue
        differences = []
        if left["shots"] != right["shots"]:
            differences.append(f"different screenshots taken: {left['shots']} vs {right['shots']}")
        for shot in sorted(set(left["shots"]) & set(right["shots"])):
            count = compare_images(base_dir / shot, work_dir / shot, diff_dir / shot)
            if count:
                differences.append(f"{shot}: " + ("size differs" if count < 0 else f"{count} pixels differ"))
        if compare_values:
            for a, b in zip(left["checkpoints"], right["checkpoints"]):
                if a["label"] != b["label"] or a["values"] != b["values"] or a["frame"] != b["frame"]:
                    changed = {key: (a["values"].get(key), b["values"].get(key))
                               for key in sorted(set(a["values"]) | set(b["values"]))
                               if a["values"].get(key) != b["values"].get(key)}
                    differences.append(f"checkpoint {a['label']!r}: {changed or 'label/frame differ'}")
            if len(left["checkpoints"]) != len(right["checkpoints"]):
                differences.append(f"{len(left['checkpoints'])} vs {len(right['checkpoints'])} checkpoints")
        if differences:
            problems.append(f"  DIFFERS {name}:\n" + "\n".join("          " + d for d in differences))
        else:
            identical += 1
    total = len(list(names))
    if not problems:
        print(f"IDENTICAL {identical}/{total} {kind_label}")
        return True
    print(f"DIFFERENT: {identical}/{total} {kind_label} identical")
    print("\n".join(problems))
    if diff_dir.exists():
        print(f"Diff images (red = changed pixels): {diff_dir}")
    return False


def first_line(text) -> str:
    text = (text or "unknown error").strip()
    lines = text.splitlines()
    return lines[-1] if len(lines) > 1 else lines[0]


def render_side(checkout: Path, kind: str, names, out_dir: Path, jobs: int, label: str) -> dict:
    print(f"Rendering {len(names)} {kind}(s) in {label} ...", flush=True)

    def progress(name, result):
        mark = "ok " if result.get("ok") else "ERR"
        print(f"  {mark} {label}: {name}", flush=True)

    return run_scripts(checkout, kind, names, out_dir, jobs, progress)


def cached_baseline(sha: str, kind: str, names, jobs: int, use_cache: bool) -> tuple[dict, Path]:
    cache = OUT_ROOT / f"{kind}-renders" / f"{sha[:12]}-{harness_digest()}"
    index = cache / "results.json"
    known = json.loads(index.read_text(encoding="utf-8")) if use_cache and index.is_file() else {}
    missing = [name for name in names if name not in known or not known[name].get("ok")]
    if missing:
        checkout = baseline_checkout(sha)
        known.update(render_side(checkout, kind, missing, cache, jobs, f"baseline {sha[:10]}"))
        index.parent.mkdir(parents=True, exist_ok=True)
        index.write_text(json.dumps(known, indent=1), encoding="utf-8")
    return {name: known[name] for name in names}, cache


def compare_command(kind: str, kind_label: str, names, baseline_rev: str, jobs: int, use_cache: bool,
                    compare_values: bool) -> int:
    sha = resolve_commit(baseline_rev)
    baseline, base_dir = cached_baseline(sha, kind, names, jobs, use_cache)
    work_dir = OUT_ROOT / f"{kind}-renders" / "working-tree"
    work = render_side(ROOT, kind, names, work_dir, jobs, "working tree")
    ok = compare_results(kind_label, names, baseline, work, base_dir, work_dir,
                         OUT_ROOT / f"{kind}-diff", compare_values)
    return 0 if ok else 1


def selfcheck_command(kind: str, kind_label: str, names, jobs: int, compare_values: bool, tag: str = "") -> int:
    """Render the working tree twice: proves the scripts are deterministic."""
    folder = OUT_ROOT / (f"{kind}-selfcheck-{tag}" if tag else f"{kind}-selfcheck")
    first_dir = folder / "first"
    second_dir = folder / "second"
    first = render_side(ROOT, kind, names, first_dir, jobs, "run 1")
    second = render_side(ROOT, kind, names, second_dir, jobs, "run 2")
    ok = compare_results(kind_label, names, first, second, first_dir, second_dir,
                         folder / "diff", compare_values)
    return 0 if ok else 1
