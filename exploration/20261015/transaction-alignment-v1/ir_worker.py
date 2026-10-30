"""Stage B IR child, one instrumented stream execution per scheduled case."""
import argparse,json
from pathlib import Path
import metadata as md
from ir_adapter import Feed,load_stream
R=Path(__file__).resolve().parent
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--case',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
 case=next(c for c in json.loads((R/'cases.json').read_text())['cases'] if c['id']==a.case);assert not case.get('skip')
 out=Path(a.out).resolve();assert out.is_relative_to(R/'run-v1') and out.is_dir()
 assert not (out/'ir-events.json').exists()
 mod,stream=load_stream();p=mod.parse((R/'broadcast-ir.json').read_text(),'structured','development_broadcast')
 feed=Feed();g=stream(p,'development_broadcast',feed);index=0;events=[];rows=[]
 plans=md.episodes(case['scene'])
 for cycle in range(80):
  reset=md.is_reset(case['scene'],cycle);epoch=int(len(plans)==2 and cycle>=8)
  beats=plans[epoch]['beats'];payload=beats[index] if index<len(beats) else [0,0]
  if case['scene']==4 and cycle in (6,7):payload=[payload[0]^1,payload[1]]
  r0,r1=md.ready(case['scene'],cycle)
  inputs=dict(s_valid=int(not reset and index<len(beats)),s_data=payload[0],s_last=payload[1],m_ready0=r0,m_ready1=r1)
  packed=md.pack(inputs,md.INPUTS);outputs=[]
  for phase,clk in [('PRE',0),('POST',1)]:
   ev=dict(clk=clk,rst_n=int(not reset),input=packed,expected=None,category=phase)
   feed.events.append(ev);value=next(g);o=md.unpack_outputs(value);outputs.append(o)
   events.append(dict(cycle=cycle,phase=phase,offer_id=[epoch,index],input_event=ev,packed_output=value,outputs=o))
  pre=outputs[0]
  rows.append(dict(cycle=cycle,rst=int(reset),s=dict(valid=inputs['s_valid'],ready=pre['s_ready'],data=inputs['s_data'],last=inputs['s_last']),m=[dict(valid=pre[f'm_valid{i}'],ready=inputs[f'm_ready{i}'],data=pre[f'm_data{i}'],last=pre[f'm_last{i}']) for i in range(2)],offer_id=[epoch,index]))
  if reset:index=0
  elif inputs['s_valid'] and pre['s_ready']:index+=1
 try:next(g)
 except StopIteration:pass
 else:raise AssertionError('IR stream did not end')
 for name,data in [('ir-events.json',events),('ir-pre.json',rows)]:
  (out/name).write_text(json.dumps(data,indent=2)+'\n')
 print(json.dumps(dict(status='IR_STREAM_COMPLETED',executions=1,cycles=80,event_rows=160,instrumentation='one added yield after last update')))
if __name__=='__main__':main()
