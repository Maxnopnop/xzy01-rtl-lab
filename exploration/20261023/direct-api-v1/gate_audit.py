"""Offline additional route/gate tests; no socket or real credential access."""
import json,pathlib,os
import core,dispatcher,transport

def main():
    r=pathlib.Path(__file__).resolve().parent;out=r/'gate-tests';out.mkdir(exist_ok=False)
    route=core.read(r/'route.example.json');checks={}
    def rejected(fn):
        try:fn();return False
        except (AssertionError,ValueError,KeyError):return True
    checks['unreviewed_provider_blocked']=rejected(lambda:dispatcher.route_check(route))
    checks['plaintext_live_endpoint_blocked']=rejected(lambda:transport.route_values(dict(route,endpoint='http://openrouter.ai/api/v1/chat/completions'),{},False))
    checks['embedded_proxy_credentials_blocked']=rejected(lambda:transport.route_values(dict(route,proxy_url='http://user:secret@127.0.0.1:1234'),{},False))
    checks['missing_explicit_proxy_env_blocked']=rejected(lambda:transport.route_values(dict(route,proxy_env='TEST_PROXY'),{},False))
    resolved=transport.route_values(dict(route,proxy_env='TEST_PROXY'),{'TEST_PROXY':'http://127.0.0.1:1234'},False)
    checks['explicit_proxy_env_resolved']=resolved['proxy_url']=='http://127.0.0.1:1234'
    resolved=transport.route_values(route,{'HTTPS_PROXY':'http://127.0.0.1:1111'},False)
    checks['ambient_proxy_ignored']=resolved['proxy_url'] is None
    routefile=out/'route.json';core.save(routefile,route)
    report=dispatcher.preflight(routefile,out/'missing-release.json')
    checks['unconfigured_preflight_blocked_no_network']=not report['ready'] and report['network_requests']==0
    root=out/'binding';dispatcher.bind_run(root,routefile);dispatcher.bind_run(root,routefile)
    changed=out/'changed-route.json';core.save(changed,dict(route,proxy_url='http://127.0.0.1:1234'))
    checks['run_route_change_rejected']=rejected(lambda:dispatcher.bind_run(root,changed))
    # Strict model/provider response identity checks: complete failure retained, no alias fallback.
    mock=dict(route,provider_only=['mock-only'],expected_provider='MockProvider')
    slot=dispatcher.prepare_slots(mock)[0]
    envelope={'outcome':'HTTP_OK','body':json.dumps({'model':'some-other-model','usage':None,'provider':'MockProvider'})}
    checks['model_alias_rejected']=core.process_response(slot,out,envelope)['status']=='MODEL_ID_MISMATCH'
    envelope['body']=json.dumps({'model':slot['wire_model'],'usage':None,'provider':'OtherProvider'})
    checks['provider_mismatch_rejected']=core.process_response(slot,out,envelope)['status']=='PROVIDER_ID_MISMATCH'
    core.save(out/'summary.json',{'checks':checks,'passed':all(checks.values()),'network_requests':0,'real_model_calls':0})
    print(json.dumps(checks));return 0 if all(checks.values()) else 1

if __name__=='__main__':raise SystemExit(main())
