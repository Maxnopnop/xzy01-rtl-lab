"""Create independent transport sources; never edit frozen v2 or root adapters."""
from pathlib import Path
import hashlib, json
P=Path(__file__).resolve().parent;ROOT=P.parents[1];BASE=P/'r3-runner-v3';OLD=P/'r3-runner-v2'
assert not BASE.exists()
BASE.mkdir()
adapter=(ROOT/'codex_network_adapter.py').read_text(encoding='utf-8')
adapter=adapter.replace('import rtl_lab as lab','import rtl_lab as lab\nfrom stdin_process import run_process_stdin')
adapter=adapter.replace("lab.write_text(folder / 'codex_prompt.txt', prompt)","(folder / 'codex_prompt.txt').write_bytes(prompt.encode('utf-8'))")
adapter=adapter.replace("str(output), prompt])","str(output), '-'])")
adapter=adapter.replace("'network_adapter': 'configured_proxy_v1',","'network_adapter': 'configured_proxy_stdin_v3',\n        'prompt_transport': 'stdin_utf8_file', 'prompt_bytes': len(prompt.encode('utf-8')),\n        'prompt_sha256': lab.digest(prompt.encode('utf-8')),")
adapter=adapter.replace("result = lab.run_process(command, working, args.api_timeout, env)","result = run_process_stdin(command, working, args.api_timeout, env, folder / 'codex_prompt.txt')")
assert "str(output), '-'])" in adapter and 'run_process_stdin(command' in adapter
(BASE/'cli_adapter.py').write_text(adapter,encoding='utf-8',newline='\n')
rootlab=(ROOT/'rtl_lab.py').read_text(encoding='utf-8')
process=rootlab[rootlab.index('def run_process('):rootlab.index('\ndef save_process(')]
process=process.replace('def run_process(command, cwd, timeout, env=None):','def run_process_stdin(command, cwd, timeout, env, stdin_path):')
start=process.index('    proc = subprocess.Popen(');end=process.index('    chunks =',start)
process=process[:start]+'''    with Path(stdin_path).open('rb') as source:
        proc = subprocess.Popen(command, cwd=cwd, env=env or clean_env(),
                                stdin=source, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, **kwargs)
'''+process[end:]
header='"""Versioned process adapter: exact UTF-8 file on stdin, existing time/output/tree bounds."""\nimport os,subprocess,time,threading\nfrom pathlib import Path\nfrom rtl_lab import clean_env,kill_tree,MAX_LOG\n\n'
(BASE/'stdin_process.py').write_text(header+process,encoding='utf-8',newline='\n')
runner=(OLD/'runner.py').read_text(encoding='utf-8').replace('import tasks,judge,batch,rtl_lab as lab,codex_network_adapter as adapter','import tasks,judge,batch,rtl_lab as lab,cli_adapter as adapter')
runner=runner.replace('R3 runner v2','R3 runner v3').replace("RUN=BASE/'runs/prepared-v2'","RUN=BASE/'runs/prepared-v3'")
runner=runner.replace("batch.read(BASE/'runs/acceptance-v1/summary.json')", "batch.read(BASE.parent/'r3-runner-v2/runs/acceptance-v1/summary.json')")
runner=runner.replace("assert not run.exists();run.mkdir", "assert batch.read(BASE/'runs/transport-v1/summary.json')['status']=='PASS'\n    assert not run.exists();run.mkdir")
runner=runner.replace('R3_RUNNER_V2_ENGINEERING_PREPARATION','R3_RUNNER_V3_ENGINEERING_PREPARATION')
(BASE/'runner.py').write_text(runner,encoding='utf-8',newline='\n')
(BASE/'judge.py').write_bytes((OLD/'judge.py').read_bytes())
(BASE/'derivation.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [OLD/'runner.py',OLD/'judge.py',ROOT/'codex_network_adapter.py',ROOT/'rtl_lab.py']},indent=2)+'\n',encoding='utf-8')
print('Created independent v3; no model calls')
