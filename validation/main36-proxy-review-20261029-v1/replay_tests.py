"""Independently rerun supplied finite offline suite in separate evidence directory."""
import importlib.util, json, socket, sys, unittest
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1]
N=R/'exploration/20261029/main36-proxy-newbatch-v1'
sys.path.insert(0,str(N))
def deny(*a,**k):raise AssertionError('Coordinator network prohibition')
socket.socket.connect=deny
spec=importlib.util.spec_from_file_location('reviewed_suite',N/'tests.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
t.T=P/'offline-replay';t.T.mkdir(exist_ok=False)
with (P/'replay-tests.txt').open('x',encoding='utf-8') as f:
 result=unittest.TextTestRunner(stream=f,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(t.Tests))
out={'passed':result.wasSuccessful(),'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'live_model_calls':0,'real_network_calls':0,'eda_calls':0,'note':'Actual filesystem plus injected response/judge; child only abrupt-exit crash probe.'}
(P/'replay-tests.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out));sys.exit(not result.wasSuccessful())

