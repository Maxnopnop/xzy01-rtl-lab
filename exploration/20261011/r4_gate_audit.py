"""Actual first-four transport/service gate audit only; no hidden scoring/model calls."""
import sys,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE/'r4';ROOT=HERE.parents[1];sys.path[:0]=[str(BASE),str(ROOT)]
import runner_v2 as runner,batch,rtl_lab as lab
def main():
    plan=runner.verify();run=runner.RUN;gate=batch.read(run/'gate.json');assert gate['passed']
    records=[]
    for j in plan['jobs'][:4]:
        folder=run/'jobs'/j['id'];call=folder/'call';gen=batch.read(folder/'generation.json');assert gen['status']=='GENERATED'
        request=batch.read(call/'codex_request.json');command=batch.read(call/'codex.json');prompt=(call/'exact-prompt.txt').read_bytes()
        assert prompt==(call/'codex_prompt.txt').read_bytes()==request['prompt'].encode('utf-8')
        assert lab.digest(prompt)==gen['prompt_sha256']==request['prompt_sha256'] and len(prompt)==gen['prompt_bytes']==request['prompt_bytes']
        assert command['command'][-1]=='-' and command['returncode']==0 and not command['timeout'] and not command['output_limit']
        events=[json.loads(x) for x in (call/'codex.stdout.log').read_text(encoding='utf-8').splitlines() if x.strip()];completed=[e for e in events if e.get('type')=='turn.completed']
        assert completed and completed[-1]['usage']==gen['usage'] and not any(e.get('type') in ('error','turn.failed') for e in events)
        types={e.get('item',{}).get('type') for e in events if e.get('type','').startswith('item.')};assert types<={'agent_message','reasoning'} and gen['tools_used'] is False
        assert lab.digest((folder/'response.txt').read_bytes())==gen['response_sha256']
        records.append(dict(id=j['id'],role=j['role'],requested_model=request['requested_model'],requested_reasoning=request['reasoning_effort'],version=(call/'codex_version.stdout.log').read_text().strip(),exe_sha256=request['codex_executable_sha256'],prompt_sha256=gen['prompt_sha256'],prompt_bytes=len(prompt),events_sha256=lab.digest((call/'codex.stdout.log').read_bytes()),raw_model_output_sha256=lab.digest((call/'model_output.raw.txt').read_bytes()),response_sha256=gen['response_sha256'],usage=gen['usage'],item_types=sorted(types)))
    result=dict(status='PASS_ACTUAL_SERVICE_GATE',records=records,real_model_calls=4,functional_success='NOT_INFERRED',limit='Only these actual prompt sizes/context and requested model are evidenced; no general max-context guarantee')
    batch.atomic(BASE/'gate-audit.json',result);print(json.dumps(dict(status=result['status'],actual_prompts=4,prompt_bytes=[r['prompt_bytes'] for r in records],functional_success=result['functional_success']),indent=2))
if __name__=='__main__':main()
