import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;OLD=P.parent/'main36-school-v1';REPO=P/'repo'
REPO.mkdir(exist_ok=False)
def write(p,data):
 with p.open('xb') as f:f.write(data)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(OLD/'main36-school-v1.zip')=='b5a9a138b78952b4c2ae7c639b8518ca070cf7838453efd6ef2a9cd8ff8d441b'
write(REPO/'main36-school-v1.zip',(OLD/'main36-school-v1.zip').read_bytes())
text=(OLD/'school_main.py').read_text(encoding='utf-8')
text=text.replace('BASE=Path(__file__).resolve().parent',"BASE=Path.home()/'xzy01-main36-school-v1'\nsys.path.insert(0,str(BASE))")
text=text.replace("  if not (Path.home()/'tsclient/FYP').is_dir():errors.append('SHARE: $HOME/tsclient/FYP')", "  if not (Path.home()/'xzy01-main36-git-outbox').is_dir():errors.append('LOCAL OUTBOX missing; run Git stage first')")
text=text.replace("share=Path.home()/'tsclient/FYP'", "share=Path.home()/'xzy01-main36-git-outbox'")
text=text.replace('Shared FYP unavailable; no tool started','Local outbox unavailable; run Git stage first')
write(REPO/'school_case.py',text.encode())
write(REPO/'.gitattributes',b'* -text\n')
write(REPO/'.gitignore',b'__pycache__/\n*.pyc\n')
index=json.loads((OLD/'outgoing/index.json').read_bytes())
write(REPO/'case-index.json',json.dumps(index,ensure_ascii=False,indent=2).encode())
write(P/'parent-lock.json',json.dumps({str(OLD/n):sha(OLD/n) for n in ('main36-school-v1.zip','school_main.py','records.json','delivery-lock.json')},indent=2).encode())
print(str(REPO))
