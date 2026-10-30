"""Coordinator offline audit; deny external sockets and subprocess/EDA execution."""
from pathlib import Path
import contextlib, hashlib, io, json, os, sys, unittest
from unittest.mock import patch

OUT = Path(__file__).resolve().parent / 'r1'
OUT.mkdir(exist_ok=False)
ROOT = OUT.parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
blocked = []
def guard(event, args):
    if event in ('subprocess.Popen', 'os.system', 'os.posix_spawn'):
        blocked.append(event); raise RuntimeError('OFFLINE_AUDIT_NO_SUBPROCESS')
    if event == 'socket.connect':
        address = args[1]
        if not isinstance(address, tuple) or address[0] not in ('127.0.0.1', '::1'):
            blocked.append(event); raise RuntimeError('OFFLINE_AUDIT_NO_EXTERNAL_NETWORK')
    if event == 'socket.getaddrinfo' and args[0] not in ('127.0.0.1', '::1', 'localhost'):
        blocked.append(event); raise RuntimeError('OFFLINE_AUDIT_NO_EXTERNAL_DNS')
sys.addaudithook(guard)
for key in list(os.environ):
    if any(x in key.upper() for x in ('API_KEY', 'TOKEN', 'SECRET')):
        os.environ.pop(key, None)

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_bytes().decode('utf-8-sig'))
def dump(name, value):
    with (OUT/name).open('x', encoding='utf-8') as f: json.dump(value, f, ensure_ascii=False, indent=2)

delivery = ROOT/'validation/console-v3-recovery-r1-20261028'
locks = {}
for name, base in [('delivery-source-lock.json', ROOT), ('evidence-lock.json', delivery)]:
    lock = read(delivery/name)
    errors = [n for n,h in lock.items() if not (base/n).is_file() or sha(base/n)!=h]
    locks[name] = {'files':len(lock), 'errors':errors}
    if name=='delivery-source-lock.json':
        original = OUT/'original-v3'; original.mkdir(exist_ok=False)
        for n in lock: (original/n).write_bytes((base/n).read_bytes())
dump('locks-before.json', locks)
if any(v['errors'] for v in locks.values()): raise SystemExit('Locked delivery drift: stop')

import console_bridge_v3 as b
import test_console_multimodel as tests
log = io.StringIO()
suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromName(n) for n in ('test_console_multimodel','test_console_bridge','test_console_recovery_r1')])
with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
(OUT/'independent-tests.txt').write_text(log.getvalue(), encoding='utf-8')

# A durable result followed by a crash before STOP must still prevent the next call.
probes=[]
for label in ('HTTP_ERROR', 'LOCAL_INFRASTRUCTURE_FAILURE'):
    case=tests.ModelTests('test_all_three_authors_exact_wire_single_post_per_slot');case.setUp()
    original_save=b.save
    def crash_on_stop(path, value):
        if Path(path).name=='STOP.json': raise SystemExit('SIMULATED_PROCESS_DEATH_BEFORE_STOP')
        return original_save(path,value)
    try:
        if label=='HTTP_ERROR':
            case.adapter.send_once.side_effect=None
            case.adapter.send_once.return_value={'outcome':'HTTP_ERROR','status':429,'body':'offline fixture','client_post_invocations':1}
        local={'fixed_test':'INFRASTRUCTURE_ERROR','synthesis':'NOT_RUN','infrastructure_stop':True}
        try:
            with patch.object(b,'save',side_effect=crash_on_stop),patch.object(b,'transport',return_value=case.adapter),patch.object(b,'local_replay',return_value=local):
                case.pkg.dispatch(case.release,'offline-1','synthetic-secret')
        except SystemExit: pass
        prior=read(case.pkg.state/'offline-1/result.json')
        try:
            case.pkg.gate(case.release,'offline-2')
            next_blocked=False;reason=None
        except ValueError as exc: next_blocked=True;reason=str(exc)
        probes.append({'case':label,'result_status':prior['status'],'STOP_exists':(case.pkg.state/'STOP.json').exists(),'next_slot_blocked':next_blocked,'reason':reason,'mock_posts':case.adapter.send_once.call_count})
    finally: case.doCleanups()

after={}
for name,base in [('delivery-source-lock.json',ROOT),('evidence-lock.json',delivery)]:
    lock=read(delivery/name);after[name]=[n for n,h in lock.items() if not (base/n).is_file() or sha(base/n)!=h]
dump('audit.json',{'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'crash_window_probes':probes,'locked_changes':after,'guard_blocked_events':blocked,'real_model_calls':0,'real_eda_calls':0,'status':'PASS' if result.wasSuccessful() and all(p['next_slot_blocked'] for p in probes) and not any(after.values()) else 'NOT_ACCEPTED'})
print(json.dumps(read(OUT/'audit.json'),ensure_ascii=False))
