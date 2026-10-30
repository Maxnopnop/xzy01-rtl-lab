"""ARTIFICIAL offline emitter. Never calls a model or network."""
import hashlib,json,os,sys,time
from pathlib import Path
mode=sys.argv[1];payload=sys.stdin.buffer.read()
Path('received.json').write_text(json.dumps(dict(bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest(),pid=os.getpid(),mode=mode)))
def emit(o):os.write(1,(json.dumps(o,ensure_ascii=False)+'\n').encode())
emit(dict(type='thread.started',thread_id='MOCK-'+sys.argv[2]))
emit(dict(type='turn.started'))
os.write(2,b'MOCK diagnostics\n')
if mode=='partial':os.write(1,b'{"type":"item.completed","text":"\xe4\xb8');time.sleep(30)
elif mode=='hang':time.sleep(30)
elif mode=='limit':os.write(1,b'x'*10000);time.sleep(30)
elif mode=='nonzero':emit(dict(type='turn.failed'));sys.exit(7)
elif mode=='tool':emit(dict(type='item.completed',item=dict(type='command_execution',text='mock')))
elif mode=='missingusage':pass
else:emit(dict(type='item.completed',item=dict(type='agent_message',text='MOCK 中文 '+sys.argv[2])))
if mode!='missingusage':emit(dict(type='turn.completed',usage=dict(input_tokens=11,output_tokens=3,cached_input_tokens=2)))
else:emit(dict(type='turn.completed'))
if mode=='completed-hang':time.sleep(30)
