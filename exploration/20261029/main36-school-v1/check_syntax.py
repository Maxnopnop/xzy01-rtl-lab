import ast,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent
code='''import pathlib,subprocess,json,sys
p=pathlib.Path(sys.argv[1])
files=list((p/'outgoing').glob('*.sh'))+list((p/'state/school').glob('*/*.sh'))+[p/'main36-school-stage-v1.sh']
bad=[str(f) for f in files if subprocess.run(['bash','-n',str(f)],stdout=subprocess.PIPE,stderr=subprocess.PIPE).returncode]
print(json.dumps({'scripts':len(files),'bad':bad}))
sys.exit(bool(bad))
'''
linux='/mnt/'+P.drive[0].lower()+P.as_posix()[2:]
r=subprocess.run(['wsl.exe','-d','Ubuntu','--exec','python3','-c',code,linux],capture_output=True,timeout=50)
script=(P/'main36-school-stage-v1.sh').read_text();payload=script.split("<<'PY'\n",1)[1].split('\nPY\n',1)[0]
ast.parse(payload,feature_version=(3,6))
with (P/'syntax-stdout.bin').open('xb') as f:f.write(r.stdout)
with (P/'syntax-stderr.bin').open('xb') as f:f.write(r.stderr)
audit={'returncode':r.returncode,'stdout':r.stdout.decode(errors='replace'),'stderr':r.stderr.decode(errors='replace'),'bootstrap_python36':True,'model_calls':0,'eda_calls':0,'prior_command_error':'PowerShell nested quoting caused SyntaxError before execution; moved check into file. First WSL return could not decode stderr as UTF8; repeat syntax-only check preserves raw bytes. No school tools executed.'}
with (P/'syntax-audit.json').open('x',encoding='utf-8') as f:json.dump(audit,f,indent=2)
print(json.dumps(audit));assert r.returncode==0
