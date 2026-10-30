"""Isolate ONLY synthetic loopback HTTP tests from Windows system proxies."""
import sys,json,runpy,subprocess,urllib.request,urllib.parse,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
WRAPPED={ROOT/'batch.py',ROOT/'api_worker.py'}
original_popen=subprocess.Popen
def local_popen(command,*args,**kwargs):
    if isinstance(command,(list,tuple)) and len(command)>1:
        script=Path(str(command[1])).resolve()
        if script in WRAPPED:command=[command[0],str(Path(__file__).resolve()),'--script',str(script),*command[2:]]
    return original_popen(command,*args,**kwargs)
subprocess.Popen=local_popen

def main():
    if len(sys.argv)>1 and sys.argv[1]=='--script':
        script=Path(sys.argv[2]).resolve();assert script in WRAPPED
        sys.argv=[str(script),*sys.argv[3:]]
        if script.name=='api_worker.py':
            config=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
            endpoint=urllib.parse.urlparse(config['endpoint'])
            assert endpoint.scheme=='http' and endpoint.hostname in ('127.0.0.1','localhost','::1'),'Only local synthetic endpoint permitted'
            original_opener=urllib.request.build_opener
            urllib.request.build_opener=lambda *handlers:original_opener(urllib.request.ProxyHandler({}),*handlers)
        runpy.run_path(str(script),run_name='__main__');return
    run=HERE/'v2-loopback-regression';assert not run.exists();run.mkdir()
    names=['test_lab.Regression.test_mock_http_transport','test_batch.BatchTests.test_call_cap_with_explicit_mock_http_not_real_llm']
    with (run/'unittest.log').open('w',encoding='utf-8') as log:
        result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
    report=dict(status='PASS' if result.wasSuccessful() else 'FAIL',tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skips=len(result.skipped),real_model_calls=0,
                condition='Existing tests unchanged; process-only ProxyHandler({}) for loopback HTTP fixture workers; no production/global proxy changes',
                harness_sha256=__import__('hashlib').sha256(Path(__file__).read_bytes()).hexdigest())
    (run/'summary.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
    if not result.wasSuccessful():raise SystemExit(1)
if __name__=='__main__':main()
