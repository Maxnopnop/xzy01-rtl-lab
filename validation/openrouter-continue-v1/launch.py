"""Local gate for the original fixed 240 slots. No independent transport."""
import argparse,hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parent.parent/'exploration'/'20261023'/'direct-api-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def launch_gate():
    lock=HERE/'launch-lock.json'
    for p,h in read(lock).items():
        if sha(HERE/p)!=h:raise ValueError('Launch evidence drift')
    release=read(BASE/'runtime'/'technical-release.json')
    if release.get('launch_lock_sha256')!=sha(lock):raise ValueError('Coordinator launch binding required')
    if release.get('permitted_ordinals')!=list(range(1,241)):raise ValueError('Only original fixed 240-slot plan allowed')
    return release
def main():
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['preflight','run']);args=ap.parse_args()
    try:launch_gate()
    except (OSError,ValueError,KeyError,TypeError) as e:
        print(json.dumps({'ready':False,'network_requests':0,'error':str(e) if isinstance(e,ValueError) else type(e).__name__}));return 2
    sys.path.insert(0,str(BASE))
    import dispatcher
    report=dispatcher.preflight(HERE/'route.json',BASE/'runtime'/'technical-release.json')
    if args.command=='preflight' or not report['ready']:
        print(json.dumps(report));return 0 if report['ready'] else 2
    # Dispatcher checks its own gate again and before each original slot.
    sys.argv=[str(BASE/'dispatcher.py'),'run','--route',str(HERE/'route.json')]
    return dispatcher.main()
if __name__=='__main__':raise SystemExit(main())
