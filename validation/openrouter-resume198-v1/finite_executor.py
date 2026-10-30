"""Finite remaining slots; user removed total wall-time cap, per-request timeout unchanged."""
import core
from dispatcher import validate_payload

def execute(root,slots,mode,transport_fn,judge_fn=core.judge,gate=None,permitted=None):
    ledger=core.Ledger(root,slots,mode);ledger.lock()
    try:
        if ledger.recover() or (ledger.root/'STOP.json').exists():return ledger.summary()
        for slot in slots:
            if (ledger.root/'results'/f"{slot['id']}.json").exists():continue
            if permitted is not None and slot['ordinal'] not in permitted:break
            if core.size(root)>524288000:
                ledger.stop('STORAGE_LIMIT');break
            if gate and not gate()['ready']:
                ledger.stop('TECHNICAL_GATE_CHANGED');break
            raw=slot['wire_bytes'];validate_payload(slot,raw)
            folder=ledger.root/'jobs'/f"{slot['ordinal']:03d}";folder.mkdir(parents=True)
            core.save_bytes(folder/'request.json',raw)
            ledger.reserve(slot,core.digest(raw))
            envelope=None
            try:
                envelope=transport_fn(slot,folder,180)
                if not (folder/'transport-response.json').exists():core.save(folder/'transport-response.json',envelope)
                if envelope.get('request_sha256')!=slot['request_sha256']:
                    result={'slot':slot['id'],'status':'PAYLOAD_MISMATCH','stage':'transport','stop':True,'complete_http_return':False}
                else:result=core.process_response(slot,folder,envelope,judge_fn)
            except BaseException as exc:
                result={'slot':slot['id'],'status':'UNKNOWN' if not envelope or envelope.get('outcome')!='HTTP_OK' else 'POSTPROCESSING_ERROR','stage':'transport_or_processing','stop':True,'complete_http_return':bool(envelope and envelope.get('outcome')=='HTTP_OK'),'error_type':type(exc).__name__}
            result.update(mode=mode,utc=core.utc(),request_sha256=slot['request_sha256'],source_request_sha256=slot['source_request_sha256'])
            label=next(x for x in core.read(core.BATCH/'task-labels.json') if x['id']==slot['task'])
            result.update(task_label=label['current_label'],clear_subset=label['clear_subset'],not_a_spec_violation_claim=True)
            ledger.finish(slot,result)
            if result.get('stop'):ledger.stop(result['status'])
            if result.get('stop'):break
        return ledger.summary()
    except BaseException:
        ledger.stop('UNEXPECTED_INFRASTRUCTURE_FAILURE_NO_AUTO_RESUME');raise
    finally:ledger.unlock()
