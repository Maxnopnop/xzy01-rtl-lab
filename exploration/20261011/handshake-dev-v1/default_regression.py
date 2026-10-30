"""One required default regression invocation; preserve failures, no proxy override."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[2];OUT=R/'default-regression-v1'
assert not OUT.exists(),'Default regression must not be retried or overwritten'
OUT.mkdir();cmd=[sys.executable,'-m','unittest','-v','test_lab','test_batch','test_dev']
start=time.monotonic()
receipt=dict(argv=cmd,cwd=str(ROOT),environment='Inherited unchanged; no proxy or transport isolation',proxy_presence={n:bool(os.environ.get(n)) for n in ['HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','NO_PROXY']},source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['test_lab.py','test_batch.py','test_dev.py']},model_scope='Tests use offline references/local synthetic HTTP and explicit unconfigured-live guard, not model outputs',timeout_seconds=180)
try:
 p=subprocess.run(cmd,cwd=ROOT,capture_output=True,timeout=180)
 stdout,stderr=p.stdout,p.stderr;receipt.update(returncode=p.returncode,timeout=False)
except subprocess.TimeoutExpired as e:
 stdout,stderr=e.stdout or b'',e.stderr or b'';receipt.update(returncode=None,timeout=True,descendant_cleanup='UNVERIFIED; no other desktop processes killed')
(OUT/'stdout.bin').write_bytes(stdout);(OUT/'stderr.bin').write_bytes(stderr)
receipt.update(seconds=time.monotonic()-start,stdout_sha256=hashlib.sha256(stdout).hexdigest(),stderr_sha256=hashlib.sha256(stderr).hexdigest())
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt));print(stderr.decode(errors='replace')[-4500:])
