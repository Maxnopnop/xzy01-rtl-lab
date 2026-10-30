import json,sys,hashlib,unittest,tempfile
from pathlib import Path
from unittest.mock import patch
import launch
H=Path(__file__).resolve().parent;B=H.parent/'direct-api-v1'
sys.path.insert(0,str(B));import dispatcher
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
class GateTests(unittest.TestCase):
    def test_gate(self):
        with tempfile.TemporaryDirectory() as d:
            h=Path(d);b=h/'base';(b/'runtime').mkdir(parents=True)
            (h/'fixture').write_text('fixed');save(h/'launch-lock.json',{'fixture':sha(h/'fixture')})
            release={'launch_lock_sha256':sha(h/'launch-lock.json'),'permitted_ordinals':[1,2,3]}
            with patch.object(launch,'HERE',h),patch.object(launch,'BASE',b):
                with self.assertRaises(FileNotFoundError):launch.launch_gate()
                save(b/'runtime/technical-release.json',release);self.assertEqual(launch.launch_gate(),release)
                for ords in [[1],[1,2,3,4],[1,3,2]]:
                    save(b/'runtime/technical-release.json',dict(release,permitted_ordinals=ords))
                    with self.assertRaises(ValueError):launch.launch_gate()
                save(b/'runtime/technical-release.json',dict(release,launch_lock_sha256='bad'))
                with self.assertRaises(ValueError):launch.launch_gate()
                save(b/'runtime/technical-release.json',release);(h/'fixture').write_text('drift')
                with self.assertRaises(ValueError):launch.launch_gate()
if __name__=='__main__':
    route=read(H/'route.json');dispatcher.route_check(route)
    selected=[]
    for m in ['luna','terra','sol']:
        cat=read(H/(m+'-endpoints.json'))['data']['endpoints']
        normal=[e for e in cat if e['provider_name']=='OpenAI' and e.get('service_tier') is None]
        assert len(normal)==1 and normal[0]['tag']=='openai'
        assert all(e['tag'] in ['openai','openai/fast','openai/flex'] for e in cat if e['provider_name']=='OpenAI')
        selected.append({k:normal[0].get(k) for k in ['model_id','tag','provider_name','context_length','max_prompt_tokens','pricing']})
    slots=dispatcher.prepare_slots(route);groups={}
    for s in slots:
        obj=dispatcher.validate_payload(s,s['wire_bytes']);obj.pop('model')
        key=s['task']+'__'+s['condition'];groups.setdefault(key,[]).append(obj)
    assert len(slots)==240 and len(groups)==40 and all(all(o==g[0] for o in g) for g in groups.values())
    lengths=[len(json.dumps(g[0]['messages'],ensure_ascii=False).encode('utf-8')) for g in groups.values()]
    assert max(lengths)<min(e['context_length'] for e in selected)
    locks={}
    for name in ['direct-api-v1','cli-cache-repair-v1','public-rag-all20-v1','public-rag-executor-v1']:
        root=H.parent/name;lock=read(root/'packet-lock.json')
        bad=[p for p,h in lock.items() if sha(root/p)!=h];assert not bad
        locks[name]={'entries':len(lock),'mismatches':bad,'packet_sha256':sha(root/'packet-lock.json')}
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(GateTests))
    save(H/'audit.json',{'passed':result.wasSuccessful(),'gate_assertions':7,'network_requests':0,'generation':0,'slots':240,'groups':40,'max_messages_json_utf8_bytes':max(lengths),'tokenization':'Not measured; byte size is conservative scale check, not billed token count','first_three':[{k:s[k] for k in ['id','ordinal','model','task','condition']} for s in slots[:3]],'selected_endpoints':selected,'preservation':locks})
    raise SystemExit(0 if result.wasSuccessful() else 1)
