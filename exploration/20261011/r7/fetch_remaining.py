"""Bounded original-source acquisition; never retries, skips saved URLs."""
import concurrent.futures, hashlib, json, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone
R=Path(__file__).resolve().parent
revisions=json.loads((R/'revisions.json').read_text())
access=json.loads((R/'source-access.json').read_text())
items=[]
for repo,paths in [('cells',['src/cc_serial_deglitch.sv','src/cc_edge_propagator_ack.sv','src/cc_rr_arb_tree.sv','src/cc_fifo.sv']),('axis',['tb/axis_cobs_decode/test_axis_cobs_decode.py','tb/axis_cobs_encode/test_axis_cobs_encode.py','tb/axis_frame_join/test_axis_frame_join.py','tb/axis_frame_length_adjust/test_axis_frame_length_adjust.py','tb/axis_stat_counter/test_axis_stat_counter.py','tb/axis_broadcast/test_axis_broadcast.py','tb/axis_tap/test_axis_tap.py','tb/axis_async_fifo/test_axis_async_fifo.py','tb/test_axis_frame_join_4.py','tb/test_axis_frame_join_4.v','tb/test_axis_stat_counter.py','tb/test_axis_stat_counter.v','tb/test_axis_tap.py','tb/test_axis_tap.v'])]:
 for path in paths:
  rev=revisions[repo];url=f"https://raw.githubusercontent.com/{rev['repo']}/{rev['commit']}/{path}"
  if any(a['url']==url for a in access):continue
  items.append((repo,path,url,rev))
def fetch(item):
 repo,path,url,rev=item
 record=dict(url=url,utc=datetime.now(timezone.utc).isoformat(),repo=rev['repo'],commit=rev['commit'],path=path,purpose='Original tests or official README-mapped renamed module; no retry')
 try:
  with urllib.request.urlopen(url,timeout=30) as response:
   data=response.read(512*1024+1);record['status']=response.status
  assert len(data)<=512*1024,'source file budget'
  return record,data,repo,path
 except urllib.error.HTTPError as e:record.update(status=e.code,error=str(e))
 except Exception as e:record.update(status='ERROR',error=repr(e))
 return record,None,repo,path
for record,data,repo,path in concurrent.futures.ThreadPoolExecutor(max_workers=2).map(fetch,items):
 if data is not None:
  saved=R/'upstream'/repo/path;saved.parent.mkdir(parents=True,exist_ok=True)
  assert not saved.exists()
  existing=[p for p in (R/'upstream').rglob('*') if p.is_file()]
  assert len(existing)+1<=64 and sum(p.stat().st_size for p in existing)+len(data)<=8*1024*1024
  saved.write_bytes(data);record.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),saved=str(saved.relative_to(R)))
 access.append(record)
 (R/'source-access.json').write_text(json.dumps(access,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in record.items() if k in ('path','status','bytes','error')}))
