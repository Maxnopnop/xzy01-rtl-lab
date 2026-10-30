"""Only release gate evaluation against synthetic configuration, never dispatch."""
import json,os
from pathlib import Path
from unittest.mock import patch
import core,dispatch
P=Path(__file__).resolve().parent;D=P/'gate-tests';D.mkdir()
route=D/'route.json';core.save(route,{'endpoint':'https://api.openai.com/v1/chat/completions','api_key_env':'RAG_OFFLINE_KEY'})
base=core.read(P/'technical-release.example.json');base.update(decision='TECHNICAL_RELEASE',route_config_sha256=core.sha(route),model_access_verified=True,hard_cap_verified=True,wrapper_boundary_reviewed=True,common_parameter_semantics_reviewed=True,evidence=['OFFLINE_SYNTHETIC_FIXTURE_NOT_ACTUAL_PROVIDER_EVIDENCE'])
results=[]
for name,delta,key_present,expected in [('positive_mock',{},True,True),('missing_key',{},False,False),('unreviewed_wrapper',{'wrapper_boundary_reviewed':False},True,False),('wrong_route_binding',{'route_config_sha256':'0'*64},True,False),('wrong_budget',{'max_attempts':241},True,False)]:
 file=D/(name+'.json');core.save(file,dict(base,**delta))
 with patch.dict(os.environ,{'RAG_OFFLINE_KEY':'MOCK_NOT_REAL' if key_present else ''}):result=dispatch.check_release(route,file)
 assert result['ready']==expected,(name,result);results.append(dict(name=name,expected=expected,result=result))
core.save(D/'results.json',{'kind':'OFFLINE_RELEASE_GATE_ONLY','checks':len(results),'model_calls':0,'dispatch_invocations':0,'results':results});print(json.dumps(results))
