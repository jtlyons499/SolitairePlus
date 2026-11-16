"""runtime_support.bootstrap() keeps only the newest 10 game-*.log files (#15).

Each test runs bootstrap() against a temporary LOCALAPPDATA and then puts back
what bootstrap changes for the whole process: the working folder, the root
logger's handlers and level, sys.excepthook and threading.excepthook.
"""
import logging
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from solitaireplus.app import runtime_support as runtime

OLD_LOGS = 15
OTHER_FILES = ('netservice.log', 'notes.txt', 'game-1.txt', 'crash.log', 'old-game-2.log')


def old_log_names(count):
    """Names for made-up old logs. They are not numbered, so none of them can be this
    process's own game-<pid>.log (that log is always kept, which would change the result)."""
    return [f'game-old{index:02d}.log' for index in range(count)]


class LogPruningTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.logdir = self.root / 'SimpleSolitaire' / 'logs'
        self.logdir.mkdir(parents=True)
        self._cwd = os.getcwd()
        self._excepthook = sys.excepthook
        self._thread_hook = threading.excepthook
        logger = logging.getLogger()
        self._handlers = logger.handlers[:]
        self._level = logger.level
        # bootstrap() calls basicConfig(force=True); give it an empty root logger so the
        # runner's own handlers are not closed, and put them back afterwards.
        logger.handlers = []
        self._env = patch.dict(os.environ, {'LOCALAPPDATA': str(self.root)})
        self._env.start()

    def tearDown(self):
        self._env.stop()
        logger = logging.getLogger()
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()
        logger.handlers = self._handlers
        logger.setLevel(self._level)
        sys.excepthook = self._excepthook
        threading.excepthook = self._thread_hook
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def make_old_logs(self, names=None):
        """Write old game logs, oldest first, each a minute apart and at least a day old."""
        names = names or old_log_names(OLD_LOGS)
        start = time.time() - 86400 - 60 * len(names)
        paths = []
        for index, name in enumerate(names):
            path = self.logdir / name
            path.write_text(f'old log {index}\n')
            stamp = start + 60 * index
            os.utime(path, (stamp, stamp))
            paths.append(path)
        return paths

    def make_other_files(self):
        """Files and a folder that must never be touched (oldest of all)."""
        stamp = time.time() - 30 * 86400
        others = []
        for name in OTHER_FILES:
            path = self.logdir / name
            path.write_text('keep me\n')
            os.utime(path, (stamp, stamp))
            others.append(path)
        folder = self.logdir / 'game-folder.log'
        folder.mkdir()
        (folder / 'inside.txt').write_text('keep me\n')
        os.utime(folder, (stamp, stamp))
        others.append(folder)
        return others

    def game_logs(self):
        return sorted(path.name for path in self.logdir.glob('game-*.log') if path.is_file())

    def test_keeps_the_ten_newest_including_the_new_log(self):
        old = self.make_old_logs()
        others = self.make_other_files()
        logfile = runtime.bootstrap()
        self.assertEqual(logfile, self.logdir / f'game-{os.getpid()}.log')
        self.assertTrue(logfile.is_file())
        expected = sorted([path.name for path in old[-(runtime.KEPT_GAME_LOGS - 1):]] + [logfile.name])
        self.assertEqual(self.game_logs(), expected)
        self.assertEqual(len(self.game_logs()), 10)
        for path in old[:OLD_LOGS - 9]:
            self.assertFalse(path.exists(), path.name)
        for path in old[OLD_LOGS - 9:]:
            self.assertEqual(path.read_text(), f'old log {old.index(path)}\n')
        for path in others:
            self.assertTrue(path.exists(), path.name)
            if path.is_file():
                self.assertEqual(path.read_text(), 'keep me\n')
        self.assertTrue((self.logdir / 'game-folder.log' / 'inside.txt').is_file())

    def test_few_logs_are_all_kept(self):
        old = self.make_old_logs(old_log_names(5))
        logfile = runtime.bootstrap()
        self.assertEqual(self.game_logs(), sorted([path.name for path in old] + [logfile.name]))

    def test_current_process_log_is_never_pruned(self):
        # An old log that happens to have this process's name (a reused process id) is the
        # current log: bootstrap appends to it, keeps it and counts it as one of the 10.
        names = [f'game-{os.getpid()}.log'] + old_log_names(OLD_LOGS - 1)
        old = self.make_old_logs(names)
        logfile = runtime.bootstrap()
        self.assertEqual(logfile, old[0])
        self.assertTrue(logfile.is_file())
        self.assertEqual(logfile.read_text(), 'old log 0\n')
        expected = sorted([path.name for path in old[-(runtime.KEPT_GAME_LOGS - 1):]] + [logfile.name])
        self.assertEqual(self.game_logs(), expected)

    def test_undeletable_and_vanished_logs_do_not_stop_start_up(self):
        old = self.make_old_logs()
        locked, vanished = old[0], old[1]
        real_unlink = Path.unlink

        def unlink(path, *args, **kwargs):
            if path.name == locked.name:
                raise PermissionError(13, 'locked by another running copy', str(path))
            if path.name == vanished.name:
                real_unlink(path)
                raise FileNotFoundError(2, 'already gone', str(path))
            return real_unlink(path, *args, **kwargs)

        with patch.object(Path, 'unlink', unlink):
            logfile = runtime.bootstrap()
        self.assertTrue(locked.exists())
        for path in old[2:OLD_LOGS - 9]:
            self.assertFalse(path.exists(), path.name)
        expected = sorted([locked.name] + [path.name for path in old[OLD_LOGS - 9:]] + [logfile.name])
        self.assertEqual(self.game_logs(), expected)
        # Nothing about the skipped files is written to the new log.
        logging.getLogger().handlers[0].flush()
        self.assertEqual(logfile.read_text(), '')

    @unittest.skipUnless(sys.platform == 'win32', 'an open file only blocks deletion on Windows')
    def test_log_open_in_another_copy_is_skipped(self):
        old = self.make_old_logs()
        with open(old[0], 'a') as stream:  # Windows refuses to delete a file that is open
            logfile = runtime.bootstrap()
            self.assertTrue(old[0].exists())
            stream.write('still writing\n')
        for path in old[1:OLD_LOGS - 9]:
            self.assertFalse(path.exists(), path.name)
        self.assertIn(logfile.name, self.game_logs())
        self.assertEqual(len(self.game_logs()), 11)

    def test_rest_of_bootstrap_is_unchanged(self):
        os.chdir(self.root)
        logfile = runtime.bootstrap()
        self.assertEqual(Path(os.getcwd()).resolve(), Path(runtime.ROOT).resolve())
        logger = logging.getLogger()
        self.assertEqual(logger.level, logging.WARNING)
        self.assertEqual(len(logger.handlers), 1)
        handler = logger.handlers[0]
        self.assertIsInstance(handler, logging.FileHandler)
        self.assertEqual(os.path.normcase(handler.baseFilename), os.path.normcase(os.path.abspath(logfile)))
        self.assertIsNot(sys.excepthook, self._excepthook)
        self.assertIsNot(threading.excepthook, self._thread_hook)
        logging.warning('pruning test line')
        handler.flush()
        self.assertIn('WARNING pruning test line', logfile.read_text())


if __name__ == '__main__':
    unittest.main()
