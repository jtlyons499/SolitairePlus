"""tools/make_manifest.py: which files a release changes, and reuse of unchanged parts."""
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import make_manifest as mm  # noqa: E402

DATA = mm.DATA_DIR
TOOLS = "python 3.14.0 AMD64; pyinstaller 6.22.3"


def write(path: Path, data: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def fake_dist(folder: Path, exe=b"game-v1", net=b"net-v1", dll=b"dll-v1", asset=b"png-v1") -> Path:
    write(folder / "SolitairePlus.exe", exe)
    write(folder / "SolitaireNet.exe", net)
    write(folder / "SolitaireUpdater.exe", b"updater-v1")
    write(folder / DATA / "python3.dll", dll)
    write(folder / DATA / "assets" / "cards" / "AS.png", asset)
    write(folder / DATA / "version.py", b'__version__ = "0.0.7"\n')
    return folder


class ClassificationTests(unittest.TestCase):
    def test_every_part_of_the_install_is_classified(self):
        self.assertEqual(mm.component_of("SolitairePlus.exe"), "game")
        self.assertEqual(mm.component_of("SolitaireNet.exe"), "net")
        self.assertEqual(mm.component_of(f"{DATA}/assets/cards/AS.png"), "content")
        self.assertEqual(mm.component_of(f"{DATA}/multiplayer/main.py"), "content")
        self.assertEqual(mm.component_of(f"{DATA}/version.py"), "content")
        self.assertEqual(mm.component_of(f"{DATA}/python314.dll"), "runtime")


class SourceHashTests(unittest.TestCase):
    def make_repo(self, folder: Path) -> Path:
        write(folder / "main.py", b"print('game')\r\n")
        write(folder / "version.py", b'__version__ = "0.0.7"\n')
        write(folder / "solitaireplus" / "games" / "poker" / "core.py", b"x = 1\n")
        write(folder / "netservice" / "service.py", b"y = 2\n")
        write(folder / "SolitairePlus.spec", b"spec\n")
        return folder

    def test_version_bump_alone_does_not_change_the_game_exe_fingerprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.make_repo(Path(tmp))
            before = mm.source_hash("game", repo, TOOLS)
            write(repo / "version.py", b'__version__ = "0.0.8"\n')
            self.assertEqual(mm.source_hash("game", repo, TOOLS), before)

    def test_code_and_toolchain_changes_do_change_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.make_repo(Path(tmp))
            game, net = mm.source_hash("game", repo, TOOLS), mm.source_hash("net", repo, TOOLS)
            write(repo / "netservice" / "service.py", b"y = 3\n")
            self.assertEqual(mm.source_hash("game", repo, TOOLS), game)   # net code is not in the game exe
            self.assertNotEqual(mm.source_hash("net", repo, TOOLS), net)
            write(repo / "solitaireplus" / "games" / "poker" / "core.py", b"x = 2\n")
            self.assertNotEqual(mm.source_hash("game", repo, TOOLS), game)
            self.assertNotEqual(mm.source_hash("game", repo, "python 3.14.1"), mm.source_hash("game", repo, TOOLS))

    def test_windows_and_linux_line_endings_give_the_same_fingerprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.make_repo(Path(tmp))
            crlf = mm.source_hash("game", repo, TOOLS)
            write(repo / "main.py", b"print('game')\n")
            self.assertEqual(mm.source_hash("game", repo, TOOLS), crlf)


class ManifestAndReuseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def previous_release(self, components):
        """Simulate the previous release: its files and its manifest."""
        previous_dir = fake_dist(self.base / "prev")
        manifest = {"schema": 1, "version": "0.0.6", "files": mm.scan(previous_dir),
                    "components": {name: {"source_hash": value} for name, value in components.items()}}
        write(self.base / "prev.json", json.dumps(manifest).encode())
        return previous_dir

    def test_manifest_lists_every_file_except_itself(self):
        dist = fake_dist(self.base / "dist")
        write(dist / "manifest.json", b"{}")
        manifest = mm.cmd_manifest(dist, dist / "manifest.json", "0.0.7", None, None)
        self.assertNotIn("manifest.json", manifest["files"])
        self.assertEqual(manifest["files"]["SolitaireNet.exe"]["component"], "net")
        self.assertEqual(manifest["files"]["SolitaireNet.exe"]["size"], 6)
        self.assertIsNone(manifest["delta"])

    def test_unchanged_parts_are_restored_byte_for_byte_and_changed_ones_kept(self):
        current = {name: mm.source_hash(name) for name in mm.REUSABLE}
        stale = dict(current, net="something else")         # pretend netservice/ changed
        previous_dir = self.previous_release(stale)
        dist = fake_dist(self.base / "dist", exe=b"game-rebuilt", net=b"net-v2", dll=b"dll-rebuilt")
        rebuilt = self.base / "rebuilt.txt"
        mm.cmd_reuse(dist, self.base / "prev.json", previous_dir, rebuilt)
        self.assertEqual((dist / "SolitairePlus.exe").read_bytes(), b"game-v1")   # unchanged source -> old bytes
        self.assertEqual((dist / DATA / "python3.dll").read_bytes(), b"dll-v1")
        self.assertEqual((dist / "SolitaireNet.exe").read_bytes(), b"net-v2")    # changed -> new build
        self.assertEqual(rebuilt.read_text().split(), ["SolitaireNet.exe"])

    def test_delta_holds_only_changed_and_new_files(self):
        self.previous_release({})
        dist = fake_dist(self.base / "dist", net=b"net-v2", asset=b"png-v2")
        write(dist / DATA / "assets" / "new.png", b"new")
        manifest = mm.cmd_manifest(dist, self.base / "out" / "manifest.json", "0.0.7",
                                   self.base / "prev.json", self.base / "out")
        self.assertEqual(manifest["delta"]["from"], "0.0.6")
        self.assertEqual(sorted(manifest["delta"]["paths"]), sorted(["SolitaireNet.exe", f"{DATA}/assets/cards/AS.png", f"{DATA}/assets/new.png"]))
        with zipfile.ZipFile(self.base / "out" / manifest["delta"]["asset"]) as archive:
            self.assertEqual(sorted(archive.namelist()), sorted([
                "SolitaireNet.exe", f"{DATA}/assets/cards/AS.png", f"{DATA}/assets/new.png"]))


if __name__ == "__main__":
    unittest.main()
