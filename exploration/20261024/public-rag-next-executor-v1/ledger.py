"""Independent96 opportunity ledger. No reuse of historical identities/runs."""
import os,time
from pathlib import Path
import core
MAX_ATTEMPTS=96
class Ledger:
    def __init__(self,root,slots,mode,binding):
        self.root=Path(root);self.slots=slots;self.mode=mode;self.binding=binding;self.held=False
        assert 0<len(slots)<=MAX_ATTEMPTS and len({s['id'] for s in slots})==len(slots)
        assert [s['ordinal'] for s in slots]==list(range(1,len(slots)+1))
    def lock(self):
        self.root.mkdir(parents=True,exist_ok=True)
        core.save(self.root/'exclusive.lock',{'pid':os.getpid(),'utc':core.utc()});self.held=True
        identity={'input_packet_sha256':core.BATCH_SHA,'mode':self.mode,'bindings':self.binding,'slot_ids':[s['id'] for s in self.slots],'request_hashes':[s['request_sha256'] for s in self.slots],'max_attempts':MAX_ATTEMPTS}
        path=self.root/'identity.json'
        if path.exists():
            old=core.read(path);old.pop('start_epoch');assert old==identity,'Existing identity drift; no alternate run'
        else:core.save(path,dict(identity,start_epoch=time.time()))
        for n in ['reservations','results','jobs']:(self.root/n).mkdir(exist_ok=True)
        ids={s['id']:s for s in self.slots}
        for f in (self.root/'reservations').glob('*.json'):
            r=core.read(f);assert f.stem in ids and r['slot']==f.stem and r['request_sha256']==ids[f.stem]['request_sha256'],'Reservation drift'
        for f in (self.root/'results').glob('*.json'):
            r=core.read(f);assert (self.root/'reservations'/f.name).exists() and r['slot']==f.stem and r['request_sha256']==ids[f.stem]['request_sha256'],'Result drift'
    def unlock(self):
        if self.held:(self.root/'exclusive.lock').unlink();self.held=False
    def stop(self,reason):
        if not (self.root/'STOP.json').exists():core.save(self.root/'STOP.json',{'utc':core.utc(),'reason':reason})
    def reservations(self):return list((self.root/'reservations').glob('*.json'))
    def recover(self):
        prior_stop=any(core.read(f).get('stop') is True for f in (self.root/'results').glob('*.json'))
        if prior_stop:self.stop('PERSISTED_STOP_RESULT_NO_CONTINUATION')
        pending=[s for s in self.slots if (self.root/'reservations'/f"{s['id']}.json").exists() and not (self.root/'results'/f"{s['id']}.json").exists()]
        if pending:self.stop('UNFINISHED_RESERVATION_NO_RESEND')
        for s in pending:
            envfile=self.root/'jobs'/f"{s['ordinal']:03d}"/'transport-response.json';env={};body={}
            try:
                env=core.read(envfile)
                if env.get('request_sha256')!=s['request_sha256']:env={}
                import json
                body=json.loads(env.get('body','{}'))
            except (OSError,ValueError,TypeError):pass
            status='RECOVERY_RESPONSE_UNPROCESSED' if env.get('outcome')=='HTTP_OK' else ('RECOVERY_SERVICE_ERROR' if env.get('outcome')=='HTTP_ERROR' else 'UNKNOWN')
            self.finish(s,{'status':status,'stage':'recovery','stop':True,'complete_http_return':env.get('outcome')=='HTTP_OK','usage':body.get('usage') if isinstance(body,dict) else None})
        return bool(pending) or prior_stop
    def reserve(self,s,request_hash):
        assert self.held and not (self.root/'STOP.json').exists(),'Stopped/unlocked'
        assert not self.recover(),'Pending reservation'
        assert len(self.reservations())<min(MAX_ATTEMPTS,len(self.slots)),'96 opportunity cap'
        remaining=[x for x in self.slots if not (self.root/'reservations'/f"{x['id']}.json").exists()]
        assert remaining and s==remaining[0] and request_hash==s['request_sha256'],'Slot/order/hash drift'
        core.save(self.root/'reservations'/f"{s['id']}.json",{'slot':s['id'],'ordinal':s['ordinal'],'utc':core.utc(),'request_sha256':request_hash,'status':'RESERVED_BEFORE_SEND'})
    def finish(self,s,result):
        assert (self.root/'reservations'/f"{s['id']}.json").exists()
        core.save(self.root/'results'/f"{s['id']}.json",dict(result,slot=s['id'],request_sha256=s['request_sha256'],utc=core.utc(),mode=self.mode))
    def summary(self):
        rows=[core.read(f) for f in sorted((self.root/'results').glob('*.json'))];counts={}
        for r in rows:counts[r['status']]=counts.get(r['status'],0)+1
        usage=[core.usage_record(r.get('usage')) for r in rows];totals={};missing={}
        for key in ['input_tokens','output_tokens','reasoning_tokens','cached_input_tokens','total_tokens']:
            observed=[r['values'][key] for r in usage if r['values'][key] is not None];totals[key]=sum(observed) if observed else None;missing[key]=len(self.reservations())-len(observed)
        costs=[r['usage'].get('cost') for r in rows if isinstance(r.get('usage'),dict)];costs=[x for x in costs if type(x) in (int,float) and 0<=x<float('inf')]
        return {'mode':self.mode,'total_slots':len(self.slots),'reserved':len(self.reservations()),'complete_http_returns':sum(r.get('complete_http_return',False) for r in rows),'unknown':counts.get('UNKNOWN',0),'not_started':len(self.slots)-len(self.reservations()),'counts':counts,'stopped':(self.root/'STOP.json').exists(),'reported_usage_totals':totals,'usage_missing_attempts':missing,'reported_cost_sum':sum(costs) if costs else None,'cost_missing_attempts':len(self.reservations())-len(costs),'cost_note':'Raw reported usage.cost only; currency as provider reports, no inferred prices; partial sums not complete bill','independent_oracle':False}
