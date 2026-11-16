"""Early startup paths and crash reports for source and packaged builds."""
from solitaireplus.app import paths
from pathlib import Path
import logging
import os
import sys
import threading

ROOT = paths.root()

def user_data_dir():
    base = Path(os.environ.get('LOCALAPPDATA') or Path.home()/'.local/share')
    return base/'SimpleSolitaire'

def save_directory():
    if not getattr(sys, 'frozen', False):
        return ROOT/'saves'
    target = user_data_dir()/'saves'
    target.mkdir(parents=True, exist_ok=True)
    # Import old portable saves once, without overwriting existing user saves.
    legacy = Path(sys.executable).resolve().parent/'saves'
    if legacy.is_dir() and legacy.resolve()!=target.resolve():
        for source in legacy.glob('profile_*.json'):
            destination=target/source.name
            if not destination.exists():
                try:
                    content=source.read_bytes()
                    with destination.open('xb') as stream:
                        stream.write(content)
                except FileExistsError:
                    pass
                except OSError:
                    logging.warning('Could not import legacy save %s', source, exc_info=True)
    return target

KEPT_GAME_LOGS = 10

def prune_game_logs(logdir, current, keep=KEPT_GAME_LOGS):
    """Delete all but the newest ``keep`` game-*.log files in ``logdir``.

    ``current`` (this process's log) is never deleted and counts as one of the
    files kept. Files locked by another running copy, or that vanish while we
    look, are skipped silently: nothing is logged, so a normal start leaves the
    new log empty. Other files and folders are never touched."""
    current_name = os.path.normcase(Path(current).name)
    others = []
    try:
        candidates = list(Path(logdir).glob('game-*.log'))
    except OSError:
        return
    for path in candidates:
        if os.path.normcase(path.name) == current_name:
            continue
        try:
            if not path.is_file():
                continue
            others.append((path.stat().st_mtime, path.name, path))
        except OSError:
            continue
    others.sort(reverse=True)
    for _mtime, _name, path in others[max(keep - 1, 0):]:
        try:
            path.unlink()
        except OSError:
            pass

def bootstrap():
    os.chdir(ROOT)
    logdir=user_data_dir()/'logs'
    logdir.mkdir(parents=True, exist_ok=True)
    logfile=logdir/f'game-{os.getpid()}.log'
    logging.basicConfig(filename=logfile,level=logging.WARNING,
                        format='%(asctime)s %(levelname)s %(message)s',force=True)
    prune_game_logs(logdir, logfile)
    original=sys.excepthook
    def report(kind,value,trace):
        if issubclass(kind,KeyboardInterrupt):
            original(kind,value,trace);return
        logging.critical('Unhandled game exception',exc_info=(kind,value,trace))
        if getattr(sys,'frozen',False) and sys.platform=='win32':
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(None,
                    f'The game encountered an error.\n\nCrash report:\n{logfile}',
                    'Solitaire+',0x10)
            except Exception:
                pass
        original(kind,value,trace)
    sys.excepthook=report
    threading.excepthook=lambda args:logging.error('Background thread exception',exc_info=(args.exc_type,args.exc_value,args.exc_traceback))
    return logfile
