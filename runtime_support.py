"""Early startup paths and crash reports for source and packaged builds."""
from pathlib import Path
import logging
import os
import sys
import threading

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)).resolve()

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

def bootstrap():
    os.chdir(ROOT)
    logdir=user_data_dir()/'logs'
    logdir.mkdir(parents=True, exist_ok=True)
    logfile=logdir/f'game-{os.getpid()}.log'
    logging.basicConfig(filename=logfile,level=logging.WARNING,
                        format='%(asctime)s %(levelname)s %(message)s',force=True)
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
                    'Simple Solitaire',0x10)
            except Exception:
                pass
        original(kind,value,trace)
    sys.excepthook=report
    threading.excepthook=lambda args:logging.error('Background thread exception',exc_info=(args.exc_type,args.exc_value,args.exc_traceback))
    return logfile
