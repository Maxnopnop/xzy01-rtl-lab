"""Freeze new packet and capture one final read-only audit; never overwrite."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not (R/'packet-lock.json').exists()
excluded={'packet-lock.json','seal-verification.json','seal-audit.stdout.bin','seal-audit.stderr.bin'}
save(R/'calibration-execution.json',dict(kind='RECORDED_FROM_DESKTOP_EXEC_COMMAND_RESULT',argv=['C:/Users/A/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe','exploration/20261011/handshake-dev-v2/calibrate.py'],cwd=str(R.parents[2]),returncode=1,wall_time_seconds=2.4139236,aggregate_stdout='Original console retained in desktop tool result; structured summary/fixture/native verdict files retained. No fabricated aggregate raw log.',native_process_logs='calibration-v2/rtl/*/{0,1}.{stdout,stderr}.bin',invocations=1,retry=False))
files={p.relative_to(R).as_posix():sha(p) for p in sorted(R.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name not in excluded}
save(R/'packet-lock.json',files)
cmd=[sys.executable,str(R/'audit.py')];start=time.monotonic()
p=subprocess.run(cmd,cwd=R,capture_output=True,timeout=120)
(R/'seal-audit.stdout.bin').write_bytes(p.stdout);(R/'seal-audit.stderr.bin').write_bytes(p.stderr)
result=dict(argv=cmd,returncode=p.returncode,seconds=time.monotonic()-start,packet_sha256=sha(R/'packet-lock.json'),packet_bindings=len(files),stdout_sha256=sha(R/'seal-audit.stdout.bin'),stderr_sha256=sha(R/'seal-audit.stderr.bin'),new_model_calls=0,calibration_returncode=1,default_regression_returncode=1,default_rerun=False,elapsed_since_preparation=time.time()-json.loads((R/'preparation.json').read_text())['start_unix'],packet_bytes=sum(x.stat().st_size for x in R.rglob('*') if x.is_file()),audit=json.loads(p.stdout) if p.returncode==0 else None)
save(R/'seal-verification.json',result);print(json.dumps(result));raise SystemExit(p.returncode)
