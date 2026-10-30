"""Artificial evidence-tamper and batch reconstruction tests; no dispatch."""
import shutil
from pathlib import Path
import stream_process as s,recover_batch
BASE=Path(__file__).resolve().parent;RUN=BASE/'runs/recovery-boundaries-v1';assert not RUN.exists();RUN.mkdir(parents=True)
results=[]
def clone(name):
    p=RUN/name;shutil.copytree(BASE/'runs/process-v3/clean',p);return p
try:
    p=clone('wrong-exit-nonce');d=s.read(p/'exit-proof.json');d['nonce']='wrong';s.atomic(p/'exit-proof.json',d)
    r=s.recover(p);assert r['boundary']=='EXIT_BINDING_MISMATCH' and r['usage'] is None;results.append(r)
    p=clone('wrong-chunk-nonce');lines=(p/'chunks.jsonl').read_text().splitlines();import json
    d=json.loads(lines[0]);d['nonce']='wrong';lines[0]=json.dumps(d);(p/'chunks.jsonl').write_text('\n'.join(lines)+'\n')
    r=s.recover(p);assert r['boundary']=='CHUNK_BINDING_MISMATCH' and r['usage'] is None;results.append(r)
    p=clone('partial-final-byte');b=(p/'stdout.bin').read_bytes();(p/'stdout.bin').write_bytes(b[:-1])
    r=s.recover(p);assert r['boundary']=='STREAM_MISMATCH' and r['usage'] is None;results.append(r)
    p=clone('final-file-required');req=s.read(p/'request.json');req['context']['final_output_name']='model_output.raw.txt';s.atomic(p/'request.json',req)
    rh=s.digest((p/'request.json').read_bytes())
    for filename in ['reservation.json','process-start.json','exit-proof.json']:
        d=s.read(p/filename);d['request_sha256']=rh;s.atomic(p/filename,d)
    r=s.recover(p);assert r['boundary']=='FINAL_FILE_MISMATCH' and r['usage'] is None;results.append(r)
    (p/'model_output.raw.txt').write_bytes(s.read(BASE/'runs/process-v3/clean/capture-summary.json')['response'].encode())
    r=s.recover(p);assert r['status']=='GENERATED';results.append(r)
    batch=RUN/'synthetic-batch';batch.mkdir();(batch/'run.lock').write_bytes(b'0');s.atomic(batch/'plan.json',dict(jobs=[dict(id=str(i)) for i in range(48)]))
    known=batch/'jobs/known';unknown=batch/'jobs/unknown';known.mkdir(parents=True);unknown.mkdir()
    shutil.copytree(BASE/'runs/process-v3/writer-kill-clean',known/'call');shutil.copytree(BASE/'runs/process-v3/reserved-only',unknown/'call')
    s.atomic(known/'started.json',dict(reserved_calls=1));s.atomic(unknown/'started.json',dict(reserved_calls=1))
    before={str(p.relative_to(batch)):s.digest(p.read_bytes()) for p in batch.rglob('*') if p.is_file()}
    rows=recover_batch.recover(batch,RUN/'reconstructed-new-output')
    assert [r['status'] for r in rows]==['GENERATED','UNKNOWN_INTERRUPTED']
    assert before=={str(p.relative_to(batch)):s.digest(p.read_bytes()) for p in batch.rglob('*') if p.is_file()}
    results.append(dict(status='PASS',case='batch reconstruction preserves original bytes',planned_denominator=48,reserved=2,known=1,unknown=1,pending=46,model_calls=0))
    s.atomic(RUN/'summary.json',dict(status='PASS',label='ARTIFICIAL_OFFLINE_RECOVERY',model_calls=0,results=results))
except BaseException as e:s.atomic(RUN/'failure.json',dict(type=type(e).__name__,message=str(e)));raise
finally:s.atomic(RUN/'evidence-lock.json',{str(p.relative_to(RUN)):s.digest(p.read_bytes()) for p in RUN.rglob('*') if p.is_file() and p!=RUN/'evidence-lock.json'})
print('Offline recovery boundaries PASS; 6 checks; no model calls')
