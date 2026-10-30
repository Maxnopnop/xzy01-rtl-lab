"""Public source reads only. Durable once-only URL ledger; never retry failures."""
import datetime,hashlib,json,re,sys,urllib.request
from pathlib import Path
HERE=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,obj):p.write_bytes((json.dumps(obj,indent=2)+'\n').encode())
def get(url,name):
    log=read(HERE/'access.json') if (HERE/'access.json').exists() else []
    assert len(log)<70 and url not in {r['url'] for r in log},'Visit cap or duplicate URL'
    row={'url':url,'path':name,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    log.append(row);write(HERE/'access.json',log)
    limit=4194304 if name.startswith('metadata/') else 524288
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'public-benchmark-static-preparation'}),timeout=30) as r:
            b=r.read(limit+1);row['http_status']=r.status
        assert len(b)<=limit
        assert sum(x.get('bytes',0) for x in log if not x['path'].startswith('metadata/'))+len(b)<=8388608
        p=HERE/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
        row.update(status='SAVED',bytes=len(b),sha256=hashlib.sha256(b).hexdigest());write(HERE/'access.json',log)
        return b
    except Exception as e:
        row.update(status='FAILED_NO_RETRY',error=type(e).__name__);write(HERE/'access.json',log);raise
def inventory():
    assert not (HERE/'candidates-predeclared.json').exists()
    info=json.loads(get('https://api.github.com/repos/NVlabs/verilog-eval/commits/main','metadata/commit.json'))
    rev=info['sha']
    tree=json.loads(get(f'https://api.github.com/repos/NVlabs/verilog-eval/git/trees/{rev}?recursive=1','metadata/tree.json'))
    assert not tree.get('truncated')
    paths={x['path'] for x in tree['tree'] if x['type']=='blob'}
    ids=sorted([p.removeprefix('dataset_spec-to-rtl/').removesuffix('_prompt.txt') for p in paths
                if p.startswith('dataset_spec-to-rtl/') and p.endswith('_prompt.txt')],
               key=lambda x:(int(re.search(r'Prob(\d+)',x)[1]),x))
    choices=[];seen=set()
    for category,pattern in [('mux','mux'),('arithmetic','adder|addsub|popcount'),('registers','dff'),
                             ('counter',r'count'),('state_machine','fsm')]:
        matches=[x for x in ids if x not in seen and re.search(pattern,x,re.I)
                 and not (category=='counter' and 'popcount' in x.lower())][:4]
        for x in matches:
            choices.append({'id':x,'stratum':category,'order':len(choices)+1,
                            'files':{suffix:f'dataset_spec-to-rtl/{x}_{suffix}' for suffix in ('prompt.txt','ref.sv','test.sv')}})
            seen.add(x)
    write(HERE/'candidates-predeclared.json',{'repository':'NVlabs/verilog-eval','commit':rev,
        'candidate_count':len(choices),'tree_prompt_id_count':len(ids),'candidates':choices})
    for path in ('LICENSE','README.md','scripts/sv-simulate','scripts/sv-generate','Makefile.in'):
        if path in paths:get(f'https://raw.githubusercontent.com/NVlabs/verilog-eval/{rev}/{path}','upstream/'+path)
    print(json.dumps({'commit':rev,'candidates':choices},indent=2))
def candidates():
    plan=read(HERE/'candidates-predeclared.json');rev=plan['commit']
    for row in plan['candidates']:
        for suffix,path in row['files'].items():
            get(f'https://raw.githubusercontent.com/NVlabs/verilog-eval/{rev}/{path}','upstream/'+path)
    print(json.dumps({'requests':len(read(HERE/'access.json')),'candidates':plan['candidate_count']}))
if __name__=='__main__':
    {'inventory':inventory,'candidates':candidates}[sys.argv[1]]()
