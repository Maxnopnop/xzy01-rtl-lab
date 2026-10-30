"""Portable Python 3.6+ synthesis configuration and evidence primitives."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import uuid
import zipfile

TOOLS = {
    'dc': dict(name='Synopsys Design Compiler', version='X-2025.06-SP2',
               setup='/usr/eelocal/synopsys/syn-vx2025.06-sp2/.cshrc', executable='dc_shell'),
    'genus': dict(name='Cadence Genus', version='21.14-s082_1',
                  setup='/usr/eelocal/cadence/genus211/.cshrc', executable='genus')}
INPUTS = {'job.json', 'dut.sv', 'constraints.sdc', 'synthesis.tcl', 'launch.csh',
          'ece_synth_common.py', 'ece_synth_school.py'}
ARTIFACTS = {'execution.json', 'doctor.json', 'tool.log', 'tool_version.log', 'tool_path.txt',
             'receipt.txt', 'outputs/netlist.v', 'outputs/constraints.sdc', 'outputs/design.ddc',
             'reports/area.rpt', 'reports/timing.rpt', 'reports/check_design.rpt', 'reports/constraints.rpt'}
REQUIRED = ('outputs/netlist.v', 'outputs/constraints.sdc', 'reports/area.rpt', 'reports/timing.rpt')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def template():
    return dict(schema=1, tools={tool: dict(libraries=[], corner='', sdc_file='',
        constraints_reviewed=False, timeout_seconds=600) for tool in TOOLS})


def validate_profile(tool, profile):
    if tool not in TOOLS:
        raise ValueError('Select exactly one tool: dc or genus')
    libraries = profile.get('libraries')
    if not isinstance(libraries, list) or any(not isinstance(p, str) or not p.startswith('/') or
        any(c in p for c in '\r\n\x00') or not p.endswith(('.db',) if tool == 'dc' else ('.lib', '.lib.gz')) for p in libraries):
        raise ValueError('Use absolute school .db paths (DC) or .lib/.lib.gz paths (Genus)')
    if len(libraries) != len(set(libraries)):
        raise ValueError('Duplicate library paths')
    if not isinstance(profile.get('corner'), str) or not isinstance(profile.get('sdc_file'), str):
        raise ValueError('Corner and local SDC path must be strings')
    if type(profile.get('constraints_reviewed')) is not bool:
        raise ValueError('constraints_reviewed must be true or false')
    if type(profile.get('timeout_seconds')) is not int or not 10 <= profile['timeout_seconds'] <= 3600:
        raise ValueError('Timeout must be 10..3600 seconds')
    missing = []
    if not libraries: missing.append('standard-cell library paths')
    if not profile['corner'].strip(): missing.append('corner label')
    if not profile['sdc_file']: missing.append('reviewed SDC file')
    if not profile['constraints_reviewed']: missing.append('constraints_reviewed=true')
    return missing


def verify(root):
    lock = read(root / 'payload-lock.json')
    if set(lock) != INPUTS:
        raise ValueError('Unexpected synthesis input manifest')
    for name, digest in lock.items():
        path = root / name
        if path.is_symlink() or sha(path) != digest:
            raise ValueError('Synthesis input changed: ' + name)
    job = read(root / 'job.json')
    validate_profile(job['tool'], job['profile'])
    if job['rtl_sha256'] != lock['dut.sv'] or job['sdc_sha256'] != lock['constraints.sdc']:
        raise ValueError('Job/input hash mismatch')
    if not re.fullmatch(r'[a-f0-9]{32}', job['nonce']):
        raise ValueError('Invalid nonce')
    return job


def extract(archive, destination, allowed):
    if destination.exists():
        raise ValueError('Extraction destination already exists')
    with zipfile.ZipFile(archive) as zipped:
        members = zipped.infolist()
        if len(members) > 100 or sum(m.file_size for m in members) > 100 * 1024 ** 2:
            raise ValueError('Synthesis archive exceeds limits')
        seen = set()
        for item in members:
            name = item.filename
            if name not in allowed or name in seen or '\\' in name or ':' in name or '..' in PurePosixPath(name).parts or stat.S_ISLNK(item.external_attr >> 16):
                raise ValueError('Unexpected synthesis ZIP member')
            seen.add(name)
        destination.mkdir(parents=True)
        for item in members:
            path = destination / item.filename
            path.parent.mkdir(parents=True, exist_ok=True)
            with zipped.open(item) as source, path.open('xb') as target:
                target.write(source.read())


def copy_once(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if sha(source) != sha(destination):
            raise ValueError('Existing transport file differs: ' + destination.name)
        return
    tmp = destination.with_name(destination.name + '.' + uuid.uuid4().hex + '.tmp')
    tmp.write_bytes(source.read_bytes())
    if sha(tmp) != sha(source):
        raise ValueError('Transport hash mismatch')
    tmp.replace(destination)


def quote(value):
    return '"' + ''.join('\\' + c if c in '\\"$[]' else c for c in value) + '"'


def tcl(tool, top, profile, nonce):
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', top):
        raise ValueError('Unsupported top module name')
    validate_profile(tool, profile)
    libs = '[list ' + ' '.join(quote(p) for p in profile['libraries']) + ']'
    if tool == 'dc':
        flow = '''set_app_var target_library %s
set_app_var link_library [concat [list "*"] $target_library]
define_design_lib WORK -path ./WORK
if {![analyze -format sverilog dut.sv]} {error "RTL analyze failed"}
if {![elaborate %s]} {error "RTL elaboration failed"}
current_design %s
if {![link]} {error "Library/design linking failed"}
source constraints.sdc
redirect reports/check_design.rpt {check_design}
if {![check_design]} {error "check_design failed"}
if {![compile]} {error "compile failed"}
report_area > reports/area.rpt
report_timing -max_paths 10 > reports/timing.rpt
report_constraint -all_violators > reports/constraints.rpt
write -format verilog -hierarchy -output outputs/netlist.v
write_sdc outputs/constraints.sdc
write -format ddc -hierarchy -output outputs/design.ddc
''' % (libs, top, top)
    else:
        flow = '''set_db library %s
read_hdl -sv dut.sv
elaborate %s
read_sdc constraints.sdc
check_design -unresolved > reports/check_design.rpt
syn_generic
syn_map
syn_opt
report_area > reports/area.rpt
report_timing > reports/timing.rpt
write_hdl > outputs/netlist.v
write_sdc > outputs/constraints.sdc
''' % (libs, top)
    return ('# One manually selected design; libraries stay on the school host.\n'
        'if {[catch {\nfile mkdir reports outputs WORK\n' + flow +
        'foreach artifact {outputs/netlist.v outputs/constraints.sdc reports/area.rpt reports/timing.rpt} {\n'
        '  if {![file exists $artifact] || [file size $artifact] == 0} {error "Missing output: $artifact"}\n}\n'
        'set receipt [open receipt.txt w]\nputs $receipt "XZY01_SYNTH_V1 ' + nonce + ' COMPLETE"\nclose $receipt\n'
        '} detail]} {puts stderr "XZY01_SYNTH_ERROR: $detail"; exit 2}\nexit\n')


def launcher(tool):
    info = TOOLS[tool]
    invocation = 'dc_shell -f synthesis.tcl' if tool == 'dc' else 'genus -no_gui -abort_on_error -files synthesis.tcl'
    return ('#!/bin/tcsh -f\nsource "' + info['setup'] + '"\nif ($status != 0) exit 90\nrehash\n'
        'which ' + info['executable'] + ' > tool_path.txt\nif ($status != 0) exit 91\n'
        + info['executable'] + ' -version >& tool_version.log\n' + invocation + '\nexit $status\n')
