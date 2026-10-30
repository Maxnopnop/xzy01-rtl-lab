"""Optional hidden-key terminal entry. No automatic requests or retries."""
import argparse
import getpass
import json
import os
from pathlib import Path
import sys
import console_bridge as b

def export_launcher(manifest,release,destination):
    package=b.Package(manifest)
    release=Path(release).resolve()
    # Export does not imply execution approval; run-next rechecks everything.
    def quote(value):return "'"+str(value).replace("'","''")+"'"
    python=Path(sys.executable)
    if python.name.lower()=='pythonw.exe':python=python.with_name('python.exe')
    args=[str(b.ROOT/'console_cli.py'),'run-next','--manifest',str(package.path),'--release',str(release),'--manifest-sha',package.identity,'--release-sha',b.sha(release)]
    text="$ErrorActionPreference = 'Stop'\n# Key is read with getpass in Python; never stored here.\n& "+quote(python)+' '+' '.join(quote(x) for x in args)+'\nexit $LASTEXITCODE\n'
    with Path(destination).open('x',encoding='utf-8') as f:f.write(text)
    return str(destination)

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['preview','run-next','export'])
    parser.add_argument('--manifest',required=True);parser.add_argument('--release',required=True)
    parser.add_argument('--manifest-sha');parser.add_argument('--release-sha');parser.add_argument('--output')
    args=parser.parse_args(argv)
    pkg=b.Package(args.manifest)
    if args.manifest_sha:b.require(pkg.identity==args.manifest_sha,'Frozen manifest changed')
    if args.release_sha:b.require(b.sha(args.release)==args.release_sha,'Release changed')
    if args.action=='export':print(export_launcher(args.manifest,args.release,args.output));return 0
    rows=pkg.rows();pending=[r for r in rows if r['status']=='NOT_STARTED']
    if args.action=='preview':
        print(json.dumps(dict(rows=rows,max_calls=pkg.data['max_calls'],budget_policy=pkg.data['budget_policy'],network_requests=0),ensure_ascii=False,indent=2));return 0
    b.require(pending,'No unreserved slots; no resend')
    slot=pending[0]['id'];pkg.gate(args.release,slot)
    print('NEXT FROZEN SLOT: '+slot)
    if input('One POST may consume API credit. Type RUN to proceed: ')!='RUN':return 0
    secret=os.environ.get('OPENROUTER_API_KEY') or getpass.getpass('OpenRouter API key (hidden): ')
    try:result=pkg.dispatch(args.release,slot,secret)
    finally:secret=''
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result['status']=='GENERATED_UNVERIFIED' else 1

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:print('STOP: '+type(exc).__name__+'; no automatic retry.');sys.exit(2)
