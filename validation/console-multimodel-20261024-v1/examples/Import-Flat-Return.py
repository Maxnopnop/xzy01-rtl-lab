import sys
sys.path.insert(0,'E:\\Codex\\2026-09-25\\xzy01-using-llm-for-digital-chip-2\\outputs\\rtl-batch')
import argparse,json
import console_school_v3 as school
import console_bridge_v3 as b
a=argparse.ArgumentParser();a.add_argument('--record',required=True);a.add_argument('--sidecar',required=True)
args=a.parse_args();print(json.dumps(school.collect(b.read(args.record),args.sidecar),ensure_ascii=False,indent=2))
