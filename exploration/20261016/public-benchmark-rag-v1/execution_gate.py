"""Fail-closed review gate, not a model dispatcher. No transport/EDA imports."""
import argparse,hashlib,json
from pathlib import Path
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--plan-sha',required=True)
    args=parser.parse_args();here=Path(__file__).resolve().parent
    raw=(here/'plan.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=args.plan_sha:
        print(json.dumps({'status':'BLOCKED_PLAN_HASH_MISMATCH','calls':0}));return 2
    plan=json.loads(raw)
    print(json.dumps({'status':'BLOCKED_NO_EXECUTION_AUTHORIZATION_OR_VALIDATED_TRANSPORT',
                      'calls':0,'blockers':plan['blockers']}))
    return 2
if __name__=='__main__':raise SystemExit(main())
