"""R6 recovery v2: original plan/job/parent/prompt binding, new output only."""
import argparse,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(BASE));sys.path.insert(1,str(BASE.parents[2]))
import stream_process as s,prompts,batch
def recover(run,out,artificial=False):
    run=Path(run);out=Path(out);assert not out.exists() and run.resolve()!=out.resolve()
    assert (run/'run.lock').exists(),'Original batch lock required; never create in frozen evidence'
    p=s.read(run/'plan.json');assert s.digest((run/'plan.json').read_bytes())==s.read(run/'plan-lock.json')['sha256']
    if not artificial:
        assert p['kind']=='R6_PREPARATION_NOT_RELEASE' and len(p['jobs'])==48
        for rel,h in p['source_hashes'].items():assert s.digest((BASE.parents[2]/rel).read_bytes())==h
    else:assert p.get('label')=='ARTIFICIAL_RECOVERY_FIXTURE'
    rows=[];saved={}
    def raw(jid):
        f=run/'jobs'/jid
        if jid in saved:return saved[jid]
        gen=s.read(f/'generation.json');b=(f/'response.txt').read_bytes()
        assert s.digest(b)==gen['response_sha256'];return b.decode('utf-8')
    def expected(j):
        if 'prompt' in j:return j['prompt']
        if j['role']=='first_rtl':return prompts.first(j['task'],'structured',raw(j['intent_id']))
        if j['role']=='direct_second':return prompts.second(j['task'],raw(j['first_id']))
        feedback=s.read(run/'jobs'/j['first_id']/'public-feedback.json') if j['arm']=='feedback' else None
        return prompts.branch(j['task'],j['representation'],None,raw(j['first_id']),feedback)
    with batch.lock(run):
        for j in p['jobs']:
            folder=run/'jobs'/j['id'];call=folder/'call'
            if not (folder/'started.json').exists():rows.append(dict(id=j['id'],status='PENDING',usage=None));continue
            if (folder/'generation.json').exists():
                rows.append(dict(id=j['id'],status='ORIGINAL_GENERATION_PRESENT',source_sha256=s.digest((folder/'generation.json').read_bytes())));continue
            r=s.recover(call)
            if r['status']=='ACTIVE_CHILD':raise RuntimeError('Associated child alive; no closure/reconstruction permitted')
            if r['status']=='GENERATED':
                try:
                    req=s.read(call/'request.json');prompt=expected(j).encode()
                    assert req['model']==p['model'] and req['prompt_sha256']==s.digest(prompt)
                    assert (call/'prompt.bin').read_bytes()==prompt and (call/'exact-prompt.txt').read_bytes()==prompt
                    if not artificial:
                        assert req['context']['reasoning']==p['reasoning'] and req['context']['final_output_name']=='model_output.raw.txt'
                        assert req['context']['adapter_sha256']==s.digest((BASE/'cli_adapter.py').read_bytes())
                        assert req['context']['process_sha256']==s.digest((BASE/'stream_process.py').read_bytes())
                        assert req['timeout']==p['api_timeout'] and req['output_limit']==p['output_byte_limit']
                except (OSError,ValueError,KeyError,AssertionError):
                    r=dict(status='UNKNOWN_INTERRUPTED',usage=None,source='READ_ONLY_SAVED_EVIDENCE',boundary='PLAN_JOB_PARENT_PROMPT_MISMATCH')
                else:saved[j['id']]=r['response'];r['plan_sha256']=s.read(run/'plan-lock.json')['sha256'];r['job_id']=j['id']
            rows.append(dict(id=j['id'],**r))
        out.mkdir(parents=True)
        s.atomic(out/'recovery.json',dict(label='ARTIFICIAL' if artificial else 'OFFLINE_SAVED_EVIDENCE_ONLY',model_calls=0,rows=rows,planned_denominator=len(p['jobs']),unknown_usage=None,fees='UNKNOWN'))
        s.atomic(out/'evidence-lock.json',{x.name:s.digest(x.read_bytes()) for x in out.iterdir() if x.is_file()})
    return rows
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('run');parser.add_argument('new_output');a=parser.parse_args();recover(a.run,a.new_output)
