"""ELEC5550 transport primitives; Python 3.6+ on the school desktop."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import uuid
import zipfile

MAX_BYTES = 4 * 1024 ** 3


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(path)


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def relative(name):
    path = PurePosixPath(name)
    if not path.parts or path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name:
        raise ValueError('Unsafe relative path')
    return path


def copy_once(source, target):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if sha(source) != sha(target):
            raise ValueError('Existing destination differs: ' + target.name)
        return
    tmp = target.with_name(target.name + '.' + uuid.uuid4().hex + '.partial')
    shutil.copyfile(str(source), str(tmp))
    if sha(source) != sha(tmp):
        raise ValueError('Transfer hash mismatch')
    # Shared-folder workflows have one writer; publish complete bytes only.
    tmp.replace(target)


def extract(archive, target):
    target = Path(target)
    if target.exists():
        raise ValueError('Extraction destination must be new')
    with zipfile.ZipFile(str(archive)) as package:
        entries = package.infolist()
        if len(entries) > 100000 or sum(i.file_size for i in entries) > MAX_BYTES:
            raise ValueError('ZIP exceeds 4 GiB / 100000-entry limit')
        seen = set()
        for item in entries:
            path = relative(item.filename)
            name = str(path).casefold()
            if name in seen or stat.S_ISLNK(item.external_attr >> 16):
                raise ValueError('ZIP has duplicate paths or symbolic links; inspect original archive')
            seen.add(name)
        target.mkdir(parents=True)
        package.extractall(str(target))


def single_design(path, design):
    lines = Path(path).read_text(encoding='utf-8').splitlines()
    starts = [i for i, s in enumerate(lines) if s.strip().strip('_') == 'START']
    ends = [i for i, s in enumerate(lines) if s.strip().strip('_') == 'END']
    if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
        raise ValueError('list_design must have exactly one START/END pair')
    lines[starts[0] + 1:ends[0]] = [design]
    Path(path).write_text('\n'.join(lines) + '\n', encoding='utf-8')
