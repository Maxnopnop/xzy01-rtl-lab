"""Bounded static public-source retrieval only; no models or RTL execution."""
import datetime,hashlib,json,urllib.request,urllib.error
from pathlib import Path
R=Path(__file__).resolve().parent;access=[];count=0;total=0
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def flush():save(R/'access.json',dict(requests=access,request_count=len(access),raw_files=count,raw_bytes=total,retries=0))
def get(url,path,limit,kind):
 global count,total
 assert len(access)<48 and not path.exists() and url not in {r['url'] for r in access}
 row=dict(url=url,kind=kind,time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),retry=0);access.append(row);flush()
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'XZY01-public-source-static-audit','Accept':'application/vnd.github+json' if kind=='metadata' else '*/*'})
  with urllib.request.urlopen(req,timeout=25) as response:
   data=response.read(limit+1);row.update(http_status=response.status,final_url=response.url)
   if len(data)>limit:raise ValueError('Predeclared per-file size limit exceeded')
  if kind=='raw':assert count<36 and total+len(data)<=8*1024*1024
  path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
  row.update(path=path.relative_to(R).as_posix(),bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),status='SAVED')
  if kind=='raw':count+=1;total+=len(data)
  flush();return data
 except Exception as e:
  row.update(status='ACCESS_FAILED_NO_RETRY',error=repr(e),http_status=getattr(e,'code',row.get('http_status')));flush();return None
def main():
 assert not (R/'access.json').exists(),'Single access session, no overwrite or retries'
 revisions={}
 for repo,short in [('lowRISC/opentitan','opentitan'),('freecores/i2c','i2c')]:
  raw=get(f'https://api.github.com/repos/{repo}/commits/master',R/'metadata'/f'{short}-commit.json',1024*1024,'metadata')
  if raw is None:revisions[short]=dict(repo=repo,status='REVISION_UNRESOLVED');continue
  commit=json.loads(raw);rev=commit['sha'];revisions[short]=dict(repo=repo,commit=rev,author=commit['commit']['author'],committer=commit['commit']['committer'])
  tree_raw=get(f'https://api.github.com/repos/{repo}/git/trees/{rev}?recursive=1',R/'metadata'/f'{short}-tree.json',8*1024*1024,'metadata')
  if tree_raw is None:continue
  tree=json.loads(tree_raw);paths={x['path'] for x in tree['tree'] if x['type']=='blob'};revisions[short]['tree_truncated']=tree.get('truncated')
  wanted=['hw/ip/prim/rtl/prim_packer.sv','hw/ip/prim/rtl/prim_alert_sender.sv','hw/ip/prim/rtl/prim_esc_sender.sv','LICENSE','README.md'] if short=='opentitan' else ['rtl/verilog/i2c_master_bit_ctrl.v','rtl/verilog/i2c_master_byte_ctrl.v','rtl/verilog/i2c_master_top.v','rtl/verilog/i2c_master_defines.v']
  for name in wanted:
   if name not in paths:
    access.append(dict(url=f'https://raw.githubusercontent.com/{repo}/{rev}/{name}',status='PATH_ABSENT_IN_PINNED_TREE_NO_REQUEST',path_requested=name,retry=0));flush();continue
   get(f'https://raw.githubusercontent.com/{repo}/{rev}/{name}',R/'upstream'/short/name,512*1024,'raw')
 save(R/'revisions.json',revisions);print(json.dumps(dict(revisions=revisions,raw_files=count,raw_bytes=total,requests=len(access))))
if __name__=='__main__':main()
