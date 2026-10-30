"""Explicitly deny all sockets/subprocesses, with no key access or release creation."""
import contextlib,io,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
blocked=[]
def guard(event,args):
    if event in ('socket.connect','socket.getaddrinfo','subprocess.Popen','os.system','os.posix_spawn'):
        blocked.append(event);raise RuntimeError('OFFLINE_PATH_TEST_NO_NETWORK_OR_TOOLS')
sys.addaudithook(guard)
import test_paths
log=io.StringIO()
with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_paths))
(HERE/'tests.txt').write_text(log.getvalue(),encoding='utf-8')
summary=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skips=len(result.skipped),guard_blocked_events=blocked,real_model_calls=0,school_tool_calls=0,release_files_created=0,observations=test_paths.OBSERVATIONS)
(HERE/'tests.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k!='observations'}))
sys.exit(0 if result.wasSuccessful() else 1)
