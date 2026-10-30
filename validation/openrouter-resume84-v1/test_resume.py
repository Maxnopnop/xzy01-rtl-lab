import json
from pathlib import Path
import tempfile
import unittest
import launch
from launch import core, dispatcher

class ResumeTests(unittest.TestCase):
    def prepare(self, root):
        slots = dispatcher.prepare_slots(core.read(launch.HERE / 'route.json'))
        parent = root / 'parent'
        ledger = core.Ledger(parent, slots, 'LIVE')
        core.save(parent / 'run-binding.json', {'fixture': True})
        for s in slots[:83]:
            ledger.reserve(s, s['request_sha256'])
            ledger.finish(s, {'slot': s['id'], 'request_sha256': s['request_sha256'],
                'status': 'REFERENCE_PASS' if s['ordinal'] < 83 else 'SERVICE_ERROR',
                'http_status': 200 if s['ordinal'] < 83 else 429,
                'complete_http_return': s['ordinal'] < 83})
        ledger.stop('SERVICE_ERROR')
        manifest = {p.relative_to(parent).as_posix(): core.sha(p) for p in parent.rglob('*') if p.is_file()}
        target = root / 'continuation'
        launch.seed(parent, target, slots, manifest)
        self.assertEqual(core.read(parent/'identity.json')['start_epoch'], core.read(target/'identity.json')['start_epoch'])
        self.assertTrue((parent/'STOP.json').exists())
        self.assertFalse((target/'STOP.json').exists())
        return parent, target, slots, manifest

    def test_success_starts84_preserves_prefix_and_no_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent, target, slots, manifest = self.prepare(Path(tmp))
            calls = []
            def send(s, folder, timeout):
                calls.append(s['ordinal'])
                return {'outcome': 'HTTP_OK', 'request_sha256': s['request_sha256'],
                    'body': json.dumps({'model': s['wire_model'], 'provider': 'OpenAI',
                    'choices': [{'message': {'role':'assistant','content':'module TopModule; endmodule'},'finish_reason':'stop'}]})}
            judge = lambda *a: {'status':'MOCK_ONLY','stop':False}
            dispatcher.execute(target, slots, 'LIVE', send, judge, permitted=[84,85])
            dispatcher.execute(target, slots, 'LIVE', send, judge, permitted=[84,85])
            self.assertEqual(calls, [84,85])
            self.assertEqual(len(list((target/'reservations').glob('*.json'))),85)
            launch.verify_parent(parent, manifest, slots)

    def test_error_stops_without_next_or_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent, target, slots, manifest = self.prepare(Path(tmp)); calls=[]
            def send(s, folder, timeout):
                calls.append(s['ordinal'])
                return {'outcome':'HTTP_ERROR','http_status':429,'request_sha256':s['request_sha256']}
            dispatcher.execute(target, slots, 'LIVE', send, permitted=list(range(84,241)))
            dispatcher.execute(target, slots, 'LIVE', send, permitted=list(range(84,241)))
            self.assertEqual(calls,[84]);self.assertTrue((target/'STOP.json').exists())
            launch.verify_parent(parent,manifest,slots)

    def test_unknown_reservation_never_resent(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent,target,slots,manifest=self.prepare(Path(tmp));calls=[]
            core.Ledger(target,slots,'LIVE').reserve(slots[83],slots[83]['request_sha256'])
            result=dispatcher.execute(target,slots,'LIVE',lambda *a:calls.append(1),permitted=list(range(84,241)))
            self.assertEqual(calls,[]);self.assertTrue(result['stopped']);self.assertEqual(result['unknown'],1)

    def test_parent_drift_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent,target,slots,manifest=self.prepare(Path(tmp))
            (parent/'STOP.json').write_text('{}')
            with self.assertRaises(AssertionError):launch.verify_parent(parent,manifest,slots)

if __name__=='__main__': unittest.main(verbosity=2)
