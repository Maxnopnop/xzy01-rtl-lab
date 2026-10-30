"""Offline CLI-compatible receiver. No network, no real model/CLI execution."""
import sys,json,time,hashlib
from pathlib import Path
args=sys.argv[1:]
if args==['--version']:
    print('OFFLINE_CLI_FIXTURE 1');sys.exit(0)
if args==['login','status']:
    print('Logged in using ChatGPT (OFFLINE FIXTURE; no account access)');sys.exit(0)
assert args[0]=='exec'
folder=Path.cwd().parent
control=json.loads((folder/'fixture-control.json').read_text(encoding='utf-8'))
mode=control.get('mode','normal')
if mode=='timeout':
    time.sleep(120);sys.exit(0)
data=sys.stdin.buffer.read() if args[-1]=='-' else args[-1].encode('utf-8')
(folder/'received-prompt.bin').write_bytes(data)
receipt=dict(nonce=control['nonce'],source='stdin' if args[-1]=='-' else 'argv',
             bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),argv=args,
             label='OFFLINE_RECEIVER_NOT_MODEL')
(folder/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
if mode=='nonzero':
    print('OFFLINE fixture deliberate failure',file=sys.stderr);sys.exit(7)
if mode=='overflow':
    sys.stdout.write('x'*(3*1024*1024));sys.stdout.flush();time.sleep(120);sys.exit(0)
output=Path(args[args.index('--output-last-message')+1])
output.write_bytes(b'module offline_fixture; endmodule\n')
print(json.dumps({'type':'thread.started','thread_id':'OFFLINE-'+control['nonce']}))
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':0,'output_tokens':0}}))
