"""Read and verify returned results using the console importer; never execute EDA/API."""
import datetime,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
import console_bridge as b
import console_school as school

def main():
    rows=[]
    for tool,r in b.read(HERE/'records.json').items():
        side=Path(r['shared'])/'inbox'/r['key']/'console-return.json'
        if not side.exists():rows.append(dict(tool=tool,status='RETURN_NOT_FOUND',path=str(side)));continue
        try:rows.append(dict(tool=tool,**school.collect(r,side)))
        except Exception as exc:rows.append(dict(tool=tool,status='IMPORT_REJECTED',reason=str(exc)))
    report=dict(results=rows,model_calls=0,school_tool_calls=0,meaning='Tool completion, fixed-test outcome, evidence integrity and scientific correctness are separate.')
    dest=HERE/('collection-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
    b.save(dest,report)
    print(json.dumps(report,ensure_ascii=False,indent=2));print('Saved: '+str(dest))
    return 1 if any(r['status'] in ('RETURN_NOT_FOUND','IMPORT_REJECTED') for r in rows) else 0

if __name__=='__main__':sys.exit(main())
