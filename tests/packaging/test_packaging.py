"""Packaging guards that can be checked without building the exe."""
import ast
import functools
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MULTIPLAYER = ROOT / "multiplayer"


def module_constant(path, name):
    """The literal value assigned to name at the top level of the Python file at path."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f"{name} not found in {path.name}")


def spec_constant(name):
    return module_constant(ROOT / "SolitairePlus.spec", name)


@functools.lru_cache(maxsize=None)
def source_selftest():
    """(exit code, report) of `main.py --multiplayer --selftest`, run once from source.

    LOCALAPPDATA points at a temporary folder: importing multiplayer/main.py opens its
    log file there, so the real save and log folders are left alone."""
    with tempfile.TemporaryDirectory() as tmp:
        report = Path(tmp) / "report.txt"
        env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", LOCALAPPDATA=tmp)
        done = subprocess.run([sys.executable, "main.py", "--multiplayer", "--selftest", "--selftest-report", str(report)],
                              cwd=ROOT, env=env, capture_output=True, timeout=120)
        text = report.read_text(encoding="utf-8") if report.exists() else done.stdout.decode(errors="replace")
    return done.returncode, text


def selftest_modules(report):
    """Every module name the self-test report has an 'ok' or 'FAILED' line for."""
    return {match.group(1) for match in re.finditer(r"^(?:ok {5}|FAILED )([A-Za-z_]\w*)", report, re.MULTILINE)}


def shipped_multiplayer_files():
    """The multiplayer/*.py files the player install gets (the mp_files rule in SolitairePlus.spec)."""
    excluded = spec_constant("MP_EXCLUDED")
    return sorted(path for path in MULTIPLAYER.rglob("*.py")
                  if not any(part in {"tests", "__pycache__", ".venv"} for part in path.relative_to(ROOT).parts)
                  and path.name not in excluded)


IMPORT_FUNCTIONS = {"import_module", "__import__"}


def imported_modules(node):
    """The module names one AST node imports ('<dynamic>' when a call's name is not a literal)."""
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if isinstance(node, ast.ImportFrom):
        return ["." * node.level + (node.module or "")]
    if isinstance(node, ast.Call):
        func = node.func
        name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
        if name in IMPORT_FUNCTIONS:
            first = node.args[0] if node.args else None
            literal = isinstance(first, ast.Constant) and isinstance(first.value, str)
            return [first.value if literal else "<dynamic>"]
    return []


def function_level_imports(source, label):
    """[(function, module, line)] for every import in source that only runs when a function is called.

    Imports at module level, in if/try blocks and in class bodies run when the module is
    imported, so the multiplayer self-test sees them. An import inside a function, method,
    nested function or lambda runs only when that is called, so a module missing from the
    game exe would only fail in front of a player. Decorators and default values belong
    to the enclosing scope: they run when the function is defined."""
    tree = ast.parse(source, filename=label)
    found = []

    def visit(node, qualname, in_function):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            definition_time = [*getattr(node, "decorator_list", []), *node.args.defaults,
                               *(value for value in node.args.kw_defaults if value is not None)]
            for child in definition_time:
                visit(child, qualname, in_function)
            inner = qualname + [getattr(node, "name", "<lambda>")]
            for child in node.body if isinstance(node.body, list) else [node.body]:
                visit(child, inner, True)
            return
        if isinstance(node, ast.ClassDef):
            for child in [*node.decorator_list, *node.bases, *node.keywords]:
                visit(child, qualname, in_function)
            for child in node.body:
                visit(child, qualname + [node.name], in_function)
            return
        if in_function:
            found.extend((".".join(qualname), module, node.lineno) for module in imported_modules(node))
        for child in ast.iter_child_nodes(node):
            visit(child, qualname, in_function)

    visit(tree, [], False)
    return sorted(found, key=lambda item: item[2])


_MP_PROFILE_REASON = ("left in place: mp_profile.py was outside the Phase 11 packaging change. It needs only "
                      "pygame and solitaireplus modules, which the game exe bundles (the packaged build's "
                      "PYZ-00.toc check confirms the solitaireplus ones)")

# Imports that may stay inside a function in the shipped multiplayer files:
# (file, function, module) -> why the import is not at module level.
FUNCTION_IMPORT_ALLOWLIST = {
    ("net_client.py", "open_peer", "relay_transport"):
        "relay_transport is test-only (MP_EXCLUDED), so the player install does not have it; only the "
        "in-process test mode (SOLITAIRE_NET_INPROCESS=1, set by tools/run_tests.py) imports it",
    ("mp_profile.py", "catalogs", "solitaireplus.app.settings"): _MP_PROFILE_REASON,
    ("mp_profile.py", "catalogs", "solitaireplus.profile.achievements"): _MP_PROFILE_REASON,
    ("mp_profile.py", "MultiplayerProfile.avatar_choices", "solitaireplus.profile.avatar"): _MP_PROFILE_REASON,
    ("mp_profile.py", "MultiplayerProfile.render_avatar_surface", "pygame"): _MP_PROFILE_REASON,
    ("mp_profile.py", "MultiplayerProfile.rebuild_avatar", "pygame"): _MP_PROFILE_REASON,
    ("mp_profile.py", "MultiplayerProfile.import_avatar", "pygame"): _MP_PROFILE_REASON,
}

SCANNER_SAMPLE = '''\
import os
from pathlib import Path
try:
    import json
except ImportError:
    json = None
if os.name:
    import queue
class Widget:
    import copy
    def draw(self):
        import pygame
        def inner():
            from types import SimpleNamespace
        return inner
    async def fetch(self, loader=__import__('io')):
        importlib.import_module('ssl')
handler = lambda: __import__('uuid')
def later(name):
    def decorate(function):
        return function
    @decorate
    class Inside:
        import base64
    return importlib.import_module(name)
'''


def iss_sections(text):
    """(section names in file order, {section: its lines without comments and preprocessor lines})."""
    order, sections, current = [], {}, None
    for line in text.splitlines():
        stripped = line.strip()
        if re.fullmatch(r"\[\w+\]", stripped):
            current = stripped[1:-1]
            order.append(current)
            sections.setdefault(current, [])
        elif current and stripped and not stripped.startswith((";", "#")):
            sections[current].append(stripped)
    return order, sections


class PackagingTests(unittest.TestCase):
    def test_multiplayer_selftest_passes_from_source(self):
        returncode, text = source_selftest()
        self.assertEqual(returncode, 0, text)
        self.assertIn("PASSED", text)
        self.assertIn("ok     net_client", text)

    def test_selftest_lists_new_modules_and_no_copies(self):
        returncode, text = source_selftest()
        self.assertEqual(returncode, 0, text)
        lines = text.splitlines()
        for name in ("room_protocol", "room_game", "mp_assets"):
            self.assertIn(f"ok     {name}", lines)
        # The report covers every multiplayer module except the server and test-only ones.
        excluded = {name.removesuffix(".py") for name in spec_constant("MP_EXCLUDED")}
        self.assertEqual(selftest_modules(text), {path.stem for path in MULTIPLAYER.glob("*.py")} - excluded)
        old_names = module_constant(ROOT / "tests" / "packaging" / "test_shared_imports.py", "OLD_NAMES")
        self.assertIn("texas_holdem", old_names)   # the list of deleted copies really was read
        self.assertEqual(sorted(selftest_modules(text) & set(old_names)), [])
        for name in old_names:
            self.assertIsNone(re.search(rf"\b{re.escape(name)}\b", text), f"{name} is in the report:\n{text}")

    def test_no_function_level_imports_in_shipped_multiplayer(self):
        files = shipped_multiplayer_files()
        labels = {path.relative_to(MULTIPLAYER).as_posix() for path in files}
        self.assertLessEqual({"main.py", "room_session.py", "net_client.py", "mp_profile.py"}, labels)
        self.assertEqual(labels & spec_constant("MP_EXCLUDED"), set())
        found = {}
        for path in files:
            label = path.relative_to(MULTIPLAYER).as_posix()
            for function, module, line in function_level_imports(path.read_text(encoding="utf-8"), label):
                found.setdefault((label, function, module), line)
        unexpected = [f"multiplayer/{label}:{found[(label, function, module)]}: {module} in {function}"
                      for label, function, module in sorted(set(found) - set(FUNCTION_IMPORT_ALLOWLIST))]
        self.assertEqual(unexpected, [], "Move these imports to module level, so the packaged multiplayer "
                                         "self-test sees them (or allowlist one here, with the reason):")
        stale = sorted(set(FUNCTION_IMPORT_ALLOWLIST) - set(found))
        self.assertEqual(stale, [], "These imports are no longer inside a function; remove their allowlist entries.")

    def test_function_import_scanner_sees_every_form(self):
        self.assertEqual(function_level_imports(SCANNER_SAMPLE, "sample.py"), [
            ("Widget.draw", "pygame", 12),
            ("Widget.draw.inner", "types", 14),
            ("Widget.fetch", "ssl", 17),
            ("<lambda>", "uuid", 18),
            ("later.Inside", "base64", 24),
            ("later", "<dynamic>", 25),
        ])

    def test_selftest_skips_exactly_the_modules_the_package_leaves_out(self):
        sys.path.insert(0, str(ROOT))
        from solitaireplus.app import multiplayer_launcher
        excluded = {name.removesuffix(".py") for name in spec_constant("MP_EXCLUDED")}
        self.assertEqual(excluded, multiplayer_launcher.SELFTEST_SKIP)

    def test_version_ships_as_a_loose_file_not_inside_the_game_exe(self):
        spec = (ROOT / "SolitairePlus.spec").read_text(encoding="utf-8")
        self.assertIn("excludes=['version', 'netservice', 'updater']", spec)
        self.assertIn("(str(project / 'version.py'), '.')", spec)
        self.assertEqual(spec_constant("CONTENTS"), "SolitairePlus_Data")


class InstallerAndSigningTests(unittest.TestCase):
    ISS = (ROOT / "installer" / "SolitairePlus.iss").read_text(encoding="utf-8")

    def test_installer_is_per_user_and_never_needs_admin(self):
        self.assertIn("PrivilegesRequired=lowest", self.ISS)
        self.assertIn(r"DefaultDirName={autopf}\SolitairePlus", self.ISS)

    def test_installer_identity_never_changes(self):
        # Windows recognises an existing install by AppId; changing it would break upgrades.
        self.assertIn("AppId={{6B0E4C5A-3D7F-4B0E-9A61-2F7C1D9E5A42}", self.ISS)

    def test_uninstaller_only_deletes_saves_when_the_player_says_yes(self):
        section = self.ISS.split("[UninstallDelete]")[1].split("[Code]")[0]
        self.assertNotIn("localappdata", section.lower())
        self.assertIn("MB_DEFBUTTON2", self.ISS)  # "No" is the default answer to deleting saves

    def test_installer_removes_stale_multiplayer_files(self):
        """Multiplayer ships as loose .py files: an upgrade must not keep files a release removed."""
        order, sections = iss_sections(self.ISS)
        self.assertIn("InstallDelete", order)
        self.assertLess(order.index("InstallDelete"), order.index("Files"))  # delete first, then copy the new set
        folder = "{app}\\" + spec_constant("CONTENTS") + "\\multiplayer"
        lines = sections["InstallDelete"]
        self.assertIn(f'Type: files; Name: "{folder}\\*.py"', lines)
        self.assertIn(f'Type: filesandordirs; Name: "{folder}\\__pycache__"', lines)
        for line in lines:   # an install never deletes saves or anything outside the program folder
            self.assertNotIn("localappdata", line.lower())
            self.assertIn('Name: "{app}\\', line)

    def test_signing_script_understands_the_trusted_publisher_list(self):
        """tools/sign_release.ps1 -CheckTrusted must find a thumbprint written the documented way."""
        import re
        script = (ROOT / "tools" / "sign_release.ps1").read_text(encoding="utf-8")
        pattern = re.compile(re.search(r"-Pattern '([^']+)'", script).group(1))
        publishers = (ROOT / "updater" / "trusted_publishers.py").read_text(encoding="utf-8")
        example = next(line for line in publishers.splitlines() if '"thumbprint"' in line)
        uncommented = example.replace("# ", "", 1)   # what a maintainer gets by removing the "#"
        self.assertRegex(uncommented, pattern)
        self.assertIsNone(pattern.match(example))    # a commented-out entry must NOT count as trusted

    def test_release_builds_refuse_to_publish_unsigned(self):
        workflow = (ROOT / ".github" / "workflows" / "release-windows.yml").read_text(encoding="utf-8")
        self.assertIn("Release builds must be signed", workflow)
        self.assertIn("-CheckTrusted", workflow)


if __name__ == "__main__":
    unittest.main()
