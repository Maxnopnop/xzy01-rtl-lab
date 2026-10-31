"""Transfer-only; bounded shared-folder copy, no EDA or model calls."""
import subprocess,sys
from pathlib import Path
import runner
def main():
 m=runner.verify();out=runner.export(m)
 dest=Path.home()/'tsclient/FYP/rtl285-school-v2'/out.name
 if not (Path.home()/'tsclient/FYP').is_dir():raise ValueError('FYP share absent; export retained in HOME: '+str(out))
 try:
  return subprocess.call([sys.executable,str(runner.ROOT/'runner.py'),'ship','--source',str(out),'--dest',str(dest)],timeout=120)
 except subprocess.TimeoutExpired:
  print('TRANSFER_TIMEOUT. HOME export retained; partial shared files retained. Do not rerun EDA.');return 2
if __name__=='__main__':
 try:sys.exit(main())
 except Exception as e:print('TRANSFER_STOP '+str(e));sys.exit(2)
