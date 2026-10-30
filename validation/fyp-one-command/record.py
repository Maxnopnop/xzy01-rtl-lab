import ast
import hashlib
import json
from pathlib import Path
import re
import zipfile

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

validation = Path('validation/fyp-one-command')
log = (validation / 'tests-full-linux.txt').read_text(encoding='utf-8')
match = re.search(r'Ran (\d+) tests in ([\d.]+)s\s+OK\b', log)
assert match, 'Full regression has not passed'
catalog = json.loads(Path('ece_git_packages/ece-workflow-catalog.json').read_text())
for p in catalog['packages']:
    assert digest(Path('ece_git_packages') / p['archive']) == p['archive_sha256']
for name in ('ece_git.py', 'ece_station.py', 'ece_desktop.py'):
    ast.parse(Path(name).read_text(), feature_version=(3, 6))
backup = validation / 'evidence-backup.zip'
with zipfile.ZipFile(backup) as z:
    assert z.testzip() is None
    count = len(z.infolist())
files = ['lab_flow.py', 'lab.ps1', 'exact_prompts.py', 'ece_git.py', 'ece_git.sh',
         'ece_station.py', 'model_platform.py', 'test_lab_flow.py', 'FYP_ONE_COMMAND.md']
data = dict(date='2026-10-09',
    linux_full_tests=dict(passed=int(match[1]), seconds=float(match[2]), log_sha256=digest(validation / 'tests-full-linux.txt')),
    windows_new_tests=dict(passed=8, seconds=17.395), linux_related_tests=28,
    school_python_grammar='3.6 compatible', packages=len(catalog['packages']),
    case_tool_selections=sum(len(p['cases']) for p in catalog['packages']),
    new_paid_model_calls=0, new_actual_school_runs=0,
    test_scope='Synthetic loopback API/commercial receipts, actual local Icarus/Yosys, local bare Git remotes',
    prompt_verification='Actual request has exactly one user message, preserving CRLF, Unicode and whitespace',
    limitations=['School Git network/authentication and real run via new Git entry remain unverified',
                 'No new model-provider credentials supplied or tested',
                 'Commercial simulation remains one manually chosen case per invocation',
                 'ELEC5550 course flow deferred'],
    backup=dict(files=count, sha256=digest(backup), upload=False),
    source_sha256={name:digest(Path(name)) for name in files})
out = Path('evidence/fyp-one-command-20261009')
out.mkdir(parents=True, exist_ok=True)
(out / 'verification.json').write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(data, ensure_ascii=False))
