"""Read-only project inventory and asset audit. Standard library only.
Run: python tools/audit_project.py
Writes PROJECT_AUDIT.md and PROJECT_AUDIT.json; never moves/deletes project files.
"""
import argparse
import ast
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import struct
import zlib

EXCLUDED = {'.venv', 'venv', '__pycache__', '.idea', '.git', 'build', 'dist',
            'node_modules', '.pytest_cache', '.mypy_cache', '.ruff_cache', 'site-packages'}
REPORTS = {'PROJECT_AUDIT.md', 'PROJECT_AUDIT.json'}
ASSET_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif', '.wav', '.mp3',
                    '.ogg', '.flac', '.ttf', '.otf', '.ico', '.json'}


def project_files(root):
    for directory, folders, filenames in os.walk(root, followlinks=False):
        folders[:] = sorted(name for name in folders if name not in EXCLUDED and not (Path(directory)/name).is_symlink())
        for filename in sorted(filenames):
            path = Path(directory)/filename
            if filename not in REPORTS and not path.is_symlink():
                yield path


def relative(path, root):
    return path.relative_to(root).as_posix()


def png_error(path):
    """Verify PNG structure and all chunk CRCs, without needing pygame or Pillow."""
    try:
        with path.open('rb') as stream:
            if stream.read(8) != b'\x89PNG\r\n\x1a\n':
                return 'Invalid PNG signature'
            first = True
            while True:
                header = stream.read(8)
                if len(header) != 8:
                    return 'Missing or truncated PNG chunk'
                size, kind = struct.unpack('>I4s', header)
                if size > path.stat().st_size:
                    return 'Invalid PNG chunk length'
                data, crc = stream.read(size), stream.read(4)
                if len(data) != size or len(crc) != 4:
                    return 'Truncated PNG chunk'
                if zlib.crc32(data, zlib.crc32(kind)) & 0xffffffff != struct.unpack('>I', crc)[0]:
                    return kind.decode('ascii', errors='replace') + ': CRC error'
                if first and (kind != b'IHDR' or size != 13):
                    return 'Missing or invalid IHDR'
                first = False
                if kind == b'IEND':
                    return ''
    except OSError as exc:
        return str(exc)


def static_string(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = static_string(node.left), static_string(node.right)
        if left is not None and right is not None:
            return left + right
    if isinstance(node, ast.Call):
        name = ast.unparse(node.func)
        if name.endswith('.join') or name in ('Path', 'pathlib.Path'):
            args = [static_string(arg) for arg in node.args]
            if args and all(arg is not None for arg in args):
                return '/'.join(args)
    return None


def normalize_reference(value):
    value = value.replace('\\', '/').removeprefix('./')
    if value.startswith(('assets/', 'data/')) and Path(value).suffix.lower() in ASSET_EXTENSIONS:
        return value
    return None


def scan(root, hashes=True):
    paths = list(project_files(root))
    inventory, references, dynamic, bare, errors = [], defaultdict(list), [], [], []
    basenames = defaultdict(list)
    for path in paths:
        basenames[path.name.lower()].append(relative(path, root))
    def record(value, source):
        ref = normalize_reference(value)
        if ref:
            references[ref].append(source)
        elif '/' not in value.replace('\\', '/') and Path(value).suffix.lower() in ASSET_EXTENSIONS and len(value) < 200:
            bare.append({'filename': value, 'source': source})
    duplicates = defaultdict(list)
    for path in paths:
        rel = relative(path, root)
        if 'saves' in path.relative_to(root).parts or 'profiles' in path.relative_to(root).parts:
            # Inventory names only: never read or export personal save contents.
            inventory.append({'path': rel, 'kind': 'save (contents omitted)', 'bytes': path.stat().st_size})
            continue
        try:
            size = path.stat().st_size
            entry = {'path': rel, 'bytes': size, 'kind': 'python' if path.suffix == '.py' else 'asset' if rel.startswith('assets/') else 'data' if path.suffix == '.json' else 'other'}
            if hashes and size:
                digest = hashlib.sha256()
                with path.open('rb') as stream:
                    for block in iter(lambda: stream.read(1024*1024), b''):
                        digest.update(block)
                duplicates[(size, digest.hexdigest())].append(rel)
            if path.suffix == '.py':
                source = path.read_text(encoding='utf-8-sig')
                tree = ast.parse(source, filename=rel)
                entry.update(lines=len(source.splitlines()), classes=sum(isinstance(n, ast.ClassDef) for n in ast.walk(tree)),
                             functions=sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(tree)),
                             imports=sorted(set(n.module or '' for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)) | set(a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names)))
                for node in ast.walk(tree):
                    loc = f'{rel}:{getattr(node,"lineno",0)}'
                    if isinstance(node, (ast.Constant, ast.BinOp, ast.Call)):
                        value = static_string(node)
                        if value is not None:
                            record(value, loc)
                    elif isinstance(node, ast.JoinedStr):
                        pattern = ''.join(v.value if isinstance(v, ast.Constant) else '{...}' for v in node.values)
                        if 'assets/' in pattern or 'data/' in pattern:
                            dynamic.append({'source': loc, 'pattern': pattern})
                # Solitaire's rating art table combines folder names and filenames at runtime.
                # Read its literal table without importing/executing project code.
                if path.name == 'rating_unlocks.py':
                    for node in tree.body:
                        if isinstance(node, ast.Assign) and any(isinstance(t,ast.Name) and t.id == 'RATING_ART' for t in node.targets):
                            table = ast.literal_eval(node.value)
                            for key, pair in table.items():
                                kind = 'backgrounds' if key.startswith('bg_') else 'felts' if key.startswith('f_') else 'titles' if key.startswith('t_') else None
                                if kind:
                                    record(f'assets/ui/menu_ui/{kind}/{pair[0]}', f'{rel}:RATING_ART[{key}]')
            elif path.suffix == '.json':
                data = json.loads(path.read_text(encoding='utf-8-sig'))
                def walk(value, location):
                    if isinstance(value, str): record(value, location)
                    elif isinstance(value, dict):
                        for key, item in value.items():walk(item, f'{location}.{key}')
                    elif isinstance(value, list):
                        for i,item in enumerate(value):walk(item, f'{location}[{i}]')
                walk(data, rel)
            if path.suffix.lower() == '.png':
                error = png_error(path)
                if error:errors.append({'path':rel,'error':error})
            inventory.append(entry)
        except (OSError, ValueError, SyntaxError) as exc:
            errors.append({'path':rel,'error':str(exc)})
    refs = []
    for value, sources in sorted(references.items()):
        path = root/value
        inside = path.resolve().is_relative_to(root.resolve())
        refs.append({'path':value,'exists':inside and path.is_file(),'sources':sorted(set(sources)),
                     'development_only':all(source.startswith(('tests/', 'tools/')) for source in sources)})
    unresolved = []
    seen = set()
    for item in bare:
        key = (item['filename'],item['source'])
        if key in seen:continue
        seen.add(key)
        item['matching_files'] = basenames.get(item['filename'].lower(), [])
        # Basename matches are clues, not proof of the intended runtime folder.
        unresolved.append(item)
    return {'root_name':root.name,'excluded_directories':sorted(EXCLUDED),'inventory':inventory,
            'references':refs,'dynamic_paths':dynamic,'basename_references':unresolved,
            'file_errors':errors,'identical_files':[{'bytes':key[0],'files':values} for key,values in duplicates.items() if len(values)>1]}


def markdown(report):
    items = report['inventory'];missing=[r for r in report['references'] if not r['exists']]
    lines=['# Project audit','',f"Files: {len(items)}. Folders: {len(set(str(Path(x['path']).parent) for x in items))}.",'',
           'Read-only scan. No project code was executed and no files were moved or deleted. Save contents were excluded.', '',
           'Missing literal references may be optional fallbacks, old/dead code, or development-only files. Dynamic paths and basename-only references require review; this report is not a claim that every runtime asset was found.', '',
           '## Folder totals','', '| Folder | Files |', '| --- | ---: |']
    counts=Counter(x['path'].split('/')[0] if '/' in x['path'] else '(project root)' for x in items)
    lines += [f'| {folder} | {count} |' for folder,count in sorted(counts.items())]
    lines += ['', '## Missing asset/data references', '']
    if not missing:lines.append('None among resolved references.')
    for item in missing:
        lines.append(f"- `{item['path']}`" + (' [test/tool reference]' if item['development_only'] else '') + ' — ' + ', '.join(item['sources']))
    lines += ['', '## Unreadable files / PNG integrity errors', '']
    lines += [f"- `{item['path']}`: {item['error']}" for item in report['file_errors']] or ['None detected. PNG checks validate structure/CRCs, not full image decoding.']
    lines += ['', '## Byte-identical files', '', 'These files have identical bytes. They may still be required at different paths; do not delete automatically.', '']
    lines += [f"- {group['bytes']:,} bytes: " + ', '.join('`'+p+'`' for p in group['files']) for group in report['identical_files']] or ['None detected.']
    lines += ['', '## Dynamic path expressions', '']
    lines += [f"- `{item['source']}`: `{item['pattern']}`" for item in report['dynamic_paths']] or ['None detected.']
    lines += ['', '## Basename-only references with no matching file', '', 'Folder cannot be resolved automatically. These are suspects, not confirmed missing paths.', '']
    lines += [f"- `{item['filename']}` — {item['source']}" for item in report['basename_references'] if not item['matching_files']] or ['None detected.']
    lines += ['', '## Python files', '', '| File | Lines | Classes | Functions |', '| --- | ---: | ---: | ---: |']
    lines += [f"| `{x['path']}` | {x['lines']} | {x['classes']} | {x['functions']} |" for x in sorted(items,key=lambda x:x['path']) if x['kind']=='python']
    lines += ['', '## Complete file inventory', '']
    lines += [f"- `{x['path']}` ({x['bytes']:,} bytes)" for x in items]
    return '\n'.join(lines)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--no-hashes',action='store_true',help='Skip identical-file hashing')
    args=parser.parse_args();root=args.root.resolve()
    report=scan(root,hashes=not args.no_hashes)
    (root/'PROJECT_AUDIT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (root/'PROJECT_AUDIT.md').write_text(markdown(report),encoding='utf-8')
    print(f"Inventoried {len(report['inventory'])} project files.")
    print(f"Missing resolved references: {sum(not x['exists'] for x in report['references'])}")
    print(f"File/PNG errors: {len(report['file_errors'])}")
    print(f"Identical-file groups: {len(report['identical_files'])}")
    print('Send PROJECT_AUDIT.json and PROJECT_AUDIT.md for review.')

if __name__=='__main__':main()
