"""Validate existing flat school returns; no tool/model execution."""
import argparse,datetime,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P/'reuse'));import console_bridge_v3 as b;import console_school_v3 as school
b.STATE=P/'state'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--shared',default='C:/Users/A/Documents/FYP');args=ap.parse_args()
 lock=b.read(P/'delivery-lock.json')
 b.require(all(b.sha(P/n)==h for n,h in lock.items()),'School delivery files changed')
 rows=[]
 for item in b.read(P/'records.json'):
  rec=item['record'];side=Path(args.shared)/('return-'+rec['key']+'.json')
  row={k:item[k] for k in ('ordinal','slot','task','tool','model','condition','sample')}
  if not side.exists():row['import_status']='RETURN_NOT_FOUND'
  else:
   try:row.update(import_status='VERIFIED',result=school.collect(rec,side))
   except Exception as e:row.update(import_status='IMPORT_REJECTED',error_type=type(e).__name__,detail=str(e))
  rows.append(row)
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
 out=P/'collections'/('collection-'+stamp+'.json');b.save(out,{'rows':rows,'model_calls':0,'school_calls':0})
 counts={k:sum(r['import_status']==k for r in rows) for k in set(r['import_status'] for r in rows)}
 print(json.dumps({'counts':counts,'report':str(out)},ensure_ascii=False))
 return 1 if counts.get('IMPORT_REJECTED') else 0
if __name__=='__main__':sys.exit(main())
