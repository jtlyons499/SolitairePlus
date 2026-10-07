"""Inspect batch installation, logo and local Git without changing game files."""
EXPECTED = {'multiplayer/main.py': {'latest': 'ddecbe248e0109c3f81180c8deaa8b7f8a55af9fb57d6dc6a4f4c57d2d1c1f54', 'previous': '97261477c337164d1b5bbe458fbdbeecefdc0380925452cf6675edb1cc4973a9'}, 'multiplayer/mp_options.py': {'latest': '1305033a58ddaee27b2f0fb9138bab1eba5e20bad55ae6edee46f5c90fb8ce6c', 'previous': '5ce7d2528549da3184215a04e263953689b9fca4628e2f5afe7b36ebc8a5d1b1'}, 'multiplayer/mp_presentation.py': {'latest': 'ef66e70cf3c9913bb8a50031eb89512fd3a7770e300586db7ebb7fab3dd9856f', 'previous': 'd18516d569c55967b5799ef8da7ae3ba798dd3b62132ff4e62a2fffea9e467fb'}, 'multiplayer/mp_profile_ui.py': {'latest': 'aa13229c00d83b089a7360d631d42a96a3dc4d3041ec83963979edb53c2d3bd1', 'previous': '7c8ffe5476f1335fb534776e20c31e4e882bf970c1dc6cac6509a391734cdf94'}, 'multiplayer/mp_widgets.py': {'latest': '184a7c99df66e231a4440ddfba42372384b4d959c96f9a8facf10b64ec32880c', 'previous': None}, 'multiplayer/room_relay.py': {'latest': 'a376048aa3820513f9e7e6deb3ccf0f9b039af495fcb22c55598ebc616f4cba3', 'previous': '94c60801e41ccf85c9efacc1076c026d6c5b4493dff63c0c70a3c5026b266b72'}, 'multiplayer/room_session.py': {'latest': '6d0f1e155b8af612c03b79104364381b14a1ddb7db5ba451242be789a17659b7', 'previous': '28bc00cef5448500a22e65461806467340ca767ef83b752f374b847f2ed4a530'}, 'multiplayer/room_table.py': {'latest': 'ea4832dce3ef08bd2e963abab27458a54089929538f4b6121672f85826997277', 'previous': '438618a622204195df0ca6452e46205430637e9c60e928f03104b967e61b3cd8'}, 'multiplayer/room_view.py': {'latest': '1a21c305cc3180eec99d19f35dcc270b74567287072c18b11e6f5c295945031a', 'previous': '88a632362b19bdff427da98f1204d867cc84f77e96224961d67c88e65fa929b4'}, 'multiplayer/tests/test_six_seat.py': {'latest': 'dd1740ca4b5e5ac1d0685bba3fd22f234be2c6bc87ebf13526d39e182e910383', 'previous': '027db66e91428475bbdc2f1b0a6406b8478236a900631a9b61e7ae3b168fe0fa'}, 'multiplayer/tests/test_table_flow.py': {'latest': 'ee6d8ce542cca70b99fa728a257fabe6a27eb43de040f2cf3894614c010a958a', 'previous': None}, 'multiplayer_launcher.py': {'latest': '0640a0075a9f89ebb4e497950bd619d27168651c0b2933eaa5fec83f2084b100', 'previous': '70ce1a56bd48e1f34645a9d165b2c83865e6c53d513eb6a22eca5f864c296247'}}

import ast
import hashlib
import os
from pathlib import Path
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parent
lines=[]
def out(text=''):
    lines.append(str(text));print(text)
def git(*args):
    try:
        result=subprocess.run(['git','-C',str(ROOT),*args],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=15)
        return (result.stdout or result.stderr).strip()
    except (OSError,subprocess.TimeoutExpired) as error:return str(error)
def read(path):
    try:return path.read_text(encoding='utf-8-sig')
    except (OSError,UnicodeError):return ''
def digest(path):return hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
out('SOLITAIRE INSTALLATION AUDIT — read only except this report')
out('Root: '+str(ROOT));out('Python: '+sys.executable);out('Python version: '+sys.version.split()[0])
out('\nLOCAL GIT (origin/main below is cached; no fetch or push performed)')
for args in [('rev-parse','--show-toplevel'),('remote','-v'),('log','-1','--format=%H %s'),('status','--short','--branch'),('rev-parse','origin/main')]:
    out('git '+' '.join(args));out(git(*args))
out('\nGitHub checked by Codex: main was 85b68555245021cab12ac1a7eaf6d95775b48255.')
out('That GitHub commit still had the previous menu and eight-character room codes.')
out('\nLATEST TABLE FLOW BATCH CHECK (Windows line endings ignored)')
counts={}
for relative,known in EXPECTED.items():
    path=ROOT/relative
    if not path.is_file():status='MISSING'
    else:
        value=digest(path)
        status='LATEST' if value==known['latest'] else 'PREVIOUS BATCH' if value==known['previous'] else 'DIFFERENT / CUSTOMIZED'
        try:ast.parse(read(path),filename=str(path))
        except SyntaxError as error:status+=' — SYNTAX ERROR: '+str(error)
    counts[status]=counts.get(status,0)+1
    out(f'{status:24} {relative}')
out('Counts: '+str(counts))
out('\nLAUNCH AND LOGO')
menu=read(ROOT/'multiplayer/main.py');launcher=read(ROOT/'multiplayer_launcher.py');main=read(ROOT/'main.py')
out('Root main.py exists: '+str((ROOT/'main.py').is_file()))
out('Root main dispatches multiplayer: '+str('--multiplayer' in main and 'run_multiplayer' in main))
out('Launcher routes to multiplayer/main.py: '+str("folder / 'main.py'" in launcher))
out('Multiplayer menu references your logo: '+str('assets/multiplayer/logo.png' in menu))
out('Shared-root module: '+read(ROOT/'multiplayer/multiplayer_paths.py').strip())
logo=ROOT/'assets/multiplayer/logo.png'
out('Expected logo: '+str(logo));out('Logo exists: '+str(logo.is_file()))
if logo.is_file():
    data=logo.read_bytes();out('Logo bytes: '+str(len(data)))
    if data[:8]==b'\x89PNG\r\n\x1a\n' and len(data)>=24:
        out('PNG dimensions: '+str(struct.unpack('>II',data[16:24])))
    else:out('WARNING: file does not have a PNG header.')
out('\nPOSSIBLY MISPLACED / DUPLICATE FILES')
# Skip large art, environments, saves, build outputs and repository internals.
targets={'mp_widgets.py','room_relay.py','multiplayer_launcher.py','MP_TABLE_FLOW_SETUP.md'}
for current,dirs,files in os.walk(ROOT):
    dirs[:]=[d for d in dirs if d not in {'.git','.venv','.idea','__pycache__','assets','data','saves','build','dist','node_modules'}]
    folder=Path(current)
    for filename in files:
        path=folder/filename;relative=path.relative_to(ROOT).as_posix()
        if filename in targets or filename.startswith('room_view') or (filename=='main.py' and relative not in ('main.py','multiplayer/main.py')):
            out(relative)
for folder in (ROOT/'dist',ROOT/'multiplayer/dist'):
    if folder.exists():
        for exe in folder.rglob('*.exe'):out('Existing built EXE (may be older than source): '+str(exe))
out('\nRAILWAY CHECK — verify in the existing service, not inferred from GitHub')
out('Source: jtlyons499/Solitaire; branch: main; root directory: blank')
out('Start: python multiplayer/relay_server.py --bind 0.0.0.0 --port 50008')
out('Compare active deployment commit to local HEAD above. A changed source setting alone does not prove the active deployment was rebuilt.')
out('Keep TCP proxy target port 50008. New room code should have exactly five digits after latest code deploys.')
report=ROOT/'SOLITAIRE_STATE_REPORT.txt'
report.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\nReport saved: '+str(report))
