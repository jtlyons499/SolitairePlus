"""updater/: planning, downloading, verifying and applying an update, and undoing one.

Each test builds a fake installed game folder and a fake "next release"
folder on disk, then points the updater at it with a file:// URL - the same
code path as a real update from GitHub, without the internet.
"""
import json
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import make_manifest as mm  # noqa: E402
from updater import core, signing, transaction  # noqa: E402
from updater.plan import UpdateError, installed_version, make_plan, parse_manifest  # noqa: E402
from updater.signing import Verification  # noqa: E402

DATA = "SolitairePlus_Data"
VERIFIED = Verification(verified=True)
UNVERIFIED = Verification(verified=False, problems=["The update's file list (manifest.json) is not signed."])


class FakeUI:
    def __init__(self, accept_unverified=False):
        self.accept_unverified = accept_unverified
        self.messages, self.warnings_shown, self.errors = [], 0, []

    def status(self, text): self.messages.append(text)
    def progress(self, fraction): pass
    def retry_locked(self, files): return False
    def done(self, text): self.messages.append(text)
    def error(self, text): self.errors.append(text)

    def confirm_unverified(self, details):
        self.warnings_shown += 1
        return self.accept_unverified


def write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def build(folder: Path, files: dict) -> Path:
    for relpath, data in files.items():
        write(folder / relpath, data)
    return folder


V1 = {
    "SolitairePlus.exe": b"game exe v1",
    "SolitaireNet.exe": b"net exe v1",
    "SolitaireUpdater.exe": b"updater exe v1",
    f"{DATA}/python3.dll": b"runtime",
    f"{DATA}/assets/AS.png": b"ace v1",
    f"{DATA}/assets/old.png": b"removed in v2",
    f"{DATA}/version.py": b'__version__ = "0.0.7"\n',
}
V2 = dict(V1)
V2.pop(f"{DATA}/assets/old.png")
V2.update({
    "SolitaireNet.exe": b"net exe v2",
    f"{DATA}/assets/AS.png": b"ace v2",
    f"{DATA}/assets/new.png": b"brand new",
    f"{DATA}/version.py": b'__version__ = "0.0.8"\n',
})


class UpdaterTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.install = build(base / "install", V1)
        mm.cmd_manifest(self.install, self.install / "manifest.json", "0.0.7", None, None)
        # The next release, laid out like a GitHub release's downloads.
        self.release = base / "release"
        dist = build(base / "dist", V2)
        mm.cmd_manifest(dist, self.release / "manifest.json", "0.0.8", self.install / "manifest.json", self.release)
        with zipfile.ZipFile(self.release / "Solitaire-Windows.zip", "w") as archive:
            for relpath in V2:
                archive.write(dist / relpath, relpath)
        self.url = (self.release / "manifest.json").as_uri()

    def tearDown(self):
        self.tmp.cleanup()

    def installed(self):
        return {p.relative_to(self.install).as_posix(): p.read_bytes()
                for p in self.install.rglob("*") if p.is_file() and "manifest.json" not in p.name}

    def update(self, ui, verification=VERIFIED):
        with mock.patch.object(signing, "verify", return_value=verification):
            return core.run_update(self.install, self.url, ui)


class PlanTests(UpdaterTestCase):
    def test_plan_lists_exactly_the_changed_new_and_removed_files(self):
        plan = make_plan(self.install, json.loads((self.release / "manifest.json").read_text()))
        self.assertEqual(sorted(plan.changed), sorted(["SolitaireNet.exe", f"{DATA}/assets/AS.png",
                                                       f"{DATA}/assets/new.png", f"{DATA}/version.py"]))
        self.assertEqual(plan.removed, [f"{DATA}/assets/old.png"])
        self.assertTrue(plan.use_delta)           # installed version is exactly the delta's starting point

    def test_check_reports_an_update(self):
        result = core.check(self.install, self.url)
        self.assertEqual(result, {"status": "update_available", "installed": "0.0.7", "latest": "0.0.8"})

    def test_check_with_no_server_is_an_error_not_a_crash(self):
        result = core.check(self.install, (self.release / "nope.json").as_uri())
        self.assertEqual(result["status"], "error")

    def test_paths_that_escape_the_install_folder_are_refused(self):
        manifest = json.loads((self.release / "manifest.json").read_text())
        manifest["files"]["../../Windows/evil.dll"] = {"sha256": "0" * 64, "size": 1}
        with self.assertRaises(UpdateError):
            parse_manifest(json.dumps(manifest).encode())


class ApplyTests(UpdaterTestCase):
    def test_verified_update_replaces_only_what_changed(self):
        game_exe_before = (self.install / "SolitairePlus.exe").stat().st_mtime_ns
        self.assertEqual(self.update(FakeUI()), 0)
        self.assertEqual(self.installed(), V2)
        self.assertEqual(installed_version(self.install), "0.0.8")
        self.assertEqual((self.install / "SolitairePlus.exe").stat().st_mtime_ns, game_exe_before)  # untouched
        self.assertFalse((self.install / ".update").exists())

    def test_unverified_update_cancelled_at_the_warnings_changes_nothing(self):
        ui = FakeUI(accept_unverified=False)
        self.assertEqual(self.update(ui, UNVERIFIED), 2)
        self.assertEqual(ui.warnings_shown, 1)
        self.assertEqual(self.installed(), V1)
        self.assertEqual(installed_version(self.install), "0.0.7")
        self.assertFalse((self.install / ".update").exists())

    def test_unverified_update_installs_only_after_the_player_accepts(self):
        self.assertEqual(self.update(FakeUI(accept_unverified=True), UNVERIFIED), 0)
        self.assertEqual(self.installed(), V2)

    def test_delta_is_enough_when_upgrading_from_the_previous_release(self):
        (self.release / "Solitaire-Windows.zip").unlink()      # only the small delta is available
        self.assertEqual(self.update(FakeUI()), 0)
        self.assertEqual(self.installed(), V2)

    def test_full_download_repairs_damaged_files_too(self):
        write(self.install / "SolitairePlus.exe", b"corrupted")  # not part of the delta
        self.assertEqual(self.update(FakeUI()), 0)
        self.assertEqual(self.installed(), V2)

    def test_damaged_download_is_rejected_and_nothing_changes(self):
        delta = next(self.release.glob("*delta*.zip"))
        with zipfile.ZipFile(delta, "w") as archive:          # wrong bytes for every file
            for relpath in json.loads((self.release / "manifest.json").read_text())["delta"]["paths"]:
                archive.writestr(relpath, b"tampered")
        (self.release / "Solitaire-Windows.zip").unlink()
        ui = FakeUI(accept_unverified=True)
        self.assertEqual(self.update(ui, UNVERIFIED), 1)
        self.assertIn("damaged", ui.errors[0])
        self.assertEqual(self.installed(), V1)

    def test_up_to_date_does_nothing(self):
        shutil.copy2(self.install / "manifest.json", self.release / "manifest.json")
        ui = FakeUI()
        self.assertEqual(self.update(ui), 0)
        self.assertIn("up to date", ui.messages[-1])


class RollbackTests(UpdaterTestCase):
    def test_failure_halfway_restores_the_previous_version(self):
        real_replace = transaction.os.replace
        calls = {"n": 0}

        def flaky_replace(src, dst):
            calls["n"] += 1
            if calls["n"] == 3:
                raise OSError(28, "No space left on device")   # a failure renaming aside cannot fix
            return real_replace(src, dst)

        ui = FakeUI()
        with mock.patch.object(transaction.os, "replace", side_effect=flaky_replace):
            self.assertEqual(self.update(ui), 1)
        self.assertIn("previous version was restored", ui.errors[0])
        self.assertIn("OSError", ui.errors[0])
        self.assertEqual(self.installed(), V1)
        self.assertEqual(installed_version(self.install), "0.0.7")
        self.assertFalse(transaction.needs_recovery(self.install))

    def test_power_cut_mid_update_is_undone_by_recover(self):
        # Simulate a crash: journal + backups written, some files already swapped.
        plan = make_plan(self.install, json.loads((self.release / "manifest.json").read_text()))
        real_replace = transaction.os.replace
        swapped = {"files": 0}

        def crash_after_first_file(src, dst):
            if str(dst).endswith("journal.json"):
                return real_replace(src, dst)          # the journal itself is written normally
            swapped["files"] += 1
            if swapped["files"] == 2:
                raise OSError("power cut")
            return real_replace(src, dst)

        staging = transaction.staging_dir(self.install)
        for relpath in plan.changed:
            write(staging / relpath, V2[relpath])
        # rollback() is disabled here to imitate the process dying before it could clean up.
        with mock.patch.object(transaction, "rollback"), \
             mock.patch.object(transaction.os, "replace", side_effect=crash_after_first_file):
            with self.assertRaises(UpdateError):
                transaction.apply(self.install, plan, b"{}")
        self.assertEqual(swapped["files"], 2)
        write(self.install / "SolitaireNet.exe", b"half-written")   # damage done before the "crash"
        self.assertTrue(transaction.needs_recovery(self.install))
        self.assertTrue(core.recover(self.install))
        self.assertEqual(self.installed(), V1)
        self.assertFalse(transaction.needs_recovery(self.install))


class InUseFileTests(UpdaterTestCase):
    def test_a_file_in_use_is_renamed_aside_and_cleaned_up_later(self):
        real_replace = transaction.os.replace
        refused = {"done": False}

        def replace(src, dst):
            # The first attempt to overwrite SolitaireNet.exe fails as if it were running.
            if str(dst).endswith("SolitaireNet.exe") and str(src).endswith("SolitaireNet.exe") \
                    and ".update" in str(src) and not refused["done"]:
                refused["done"] = True
                raise PermissionError("in use")
            return real_replace(src, dst)

        with mock.patch.object(transaction.os, "replace", side_effect=replace):
            self.assertEqual(self.update(FakeUI()), 0)
        self.assertEqual(self.installed().get("SolitaireNet.exe"), V2["SolitaireNet.exe"])
        aside = self.install / ("SolitaireNet.exe" + transaction.config.OLD_SUFFIX)
        self.assertEqual(aside.read_bytes(), V1["SolitaireNet.exe"])
        self.assertIn("SolitaireNet.exe.updating-old", (self.install / "pending-delete.txt").read_text())
        self.assertEqual(transaction.cleanup_pending(self.install), 0)   # next start: leftovers deleted
        self.assertFalse(aside.exists())
        self.assertFalse((self.install / "pending-delete.txt").exists())

    def test_the_game_cleans_up_leftovers_too(self):
        import update_check
        aside = self.install / ("SolitaireUpdater.exe" + transaction.config.OLD_SUFFIX)
        write(aside, b"old updater")
        write(self.install / "pending-delete.txt", b"SolitaireUpdater.exe.updating-old\n../../evil.updating-old\n")
        with mock.patch.object(update_check, "install_dir", return_value=self.install):
            update_check.cleanup_leftovers()
        self.assertFalse(aside.exists())
        self.assertFalse((self.install / "pending-delete.txt").exists())

    def test_updater_never_runs_a_copy_of_itself_from_temp(self):
        # Microsoft Defender flagged that pattern as malware (Trojan:Win32/Bearfoos.A!ml). Keep it out.
        source = "".join(p.read_text(encoding="utf-8") for p in (ROOT / "updater").glob("*.py"))
        self.assertNotIn("gettempdir", source)
        self.assertNotIn("copy2(sys.executable", source)


class SigningDecisionTests(unittest.TestCase):
    """How verify() turns raw signature facts into verified / not verified."""
    TRUSTED = "A" * 40

    def verify_with(self, manifest_thumb, exe_thumb, exe_status="Valid", **kwargs):
        def runner(manifest, signature, exes):
            return {"manifest": {"ok": True, "thumbprint": manifest_thumb, "subject": "CN=Test"},
                    "exes": {str(exes[0]): {"status": exe_status, "thumbprint": exe_thumb, "subject": "CN=Test"}}}
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "manifest.json"
            manifest.write_text("{}")
            sig = Path(tmp) / "manifest.json.p7s"
            if kwargs.get("signature", True):
                sig.write_bytes(b"sig")
            publishers = [{"name": "Solitaire+", "thumbprint": self.TRUSTED}] if kwargs.get("trusted", True) else []
            with mock.patch.object(signing.config, "trusted_publishers", return_value=publishers):
                return signing.verify(manifest, sig, [Path(tmp) / "SolitaireNet.exe"], runner=runner)

    def test_trusted_signatures_verify_even_if_windows_does_not_trust_the_root(self):
        self.assertTrue(self.verify_with(self.TRUSTED, self.TRUSTED, "UnknownError").verified)

    def test_wrong_certificate_is_not_verified(self):
        result = self.verify_with("B" * 40, self.TRUSTED)
        self.assertFalse(result.verified)
        self.assertIn("B" * 40, result.details())

    def test_unsigned_exe_is_not_verified(self):
        self.assertFalse(self.verify_with(self.TRUSTED, None, "NotSigned").verified)

    def test_tampered_exe_is_not_verified(self):
        self.assertFalse(self.verify_with(self.TRUSTED, self.TRUSTED, "HashMismatch").verified)

    def test_missing_manifest_signature_is_not_verified(self):
        self.assertFalse(self.verify_with(self.TRUSTED, self.TRUSTED, signature=False).verified)

    def test_no_trusted_publisher_configured_is_never_verified(self):
        result = self.verify_with(self.TRUSTED, self.TRUSTED, trusted=False)
        self.assertFalse(result.verified)
        self.assertIn("none configured", result.details())


if __name__ == "__main__":
    unittest.main()
