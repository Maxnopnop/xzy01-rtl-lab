"""No external sockets, no subprocess; synthetic-only console regression."""
import contextlib,io,json,os,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
blocked=[]
def guard(event,args):
    if event in ('subprocess.Popen','os.system','os.posix_spawn'):
        blocked.append(event);raise RuntimeError('No subprocess in console offline tests')
    if event=='socket.connect' and (not isinstance(args[1],tuple) or args[1][0] not in ('127.0.0.1','::1')):
        blocked.append(event);raise RuntimeError('No external network')
    if event=='socket.getaddrinfo' and args[0] not in ('127.0.0.1','::1','localhost'):
        blocked.append(event);raise RuntimeError('No external DNS')
sys.addaudithook(guard)
for key in list(os.environ):
    if any(x in key.upper() for x in ('API_KEY','TOKEN','SECRET')):os.environ.pop(key,None)
suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in ('test_console_recovery_r1','test_console_multimodel','test_console_bridge'))
log=io.StringIO()
with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
(HERE/'tests.txt').write_text(log.getvalue(),encoding='utf-8')
summary=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skips=len(result.skipped),blocked_events=blocked,real_model_calls=0,school_tool_calls=0)
(HERE/'tests.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary))
sys.exit(0 if result.wasSuccessful() else 1)
