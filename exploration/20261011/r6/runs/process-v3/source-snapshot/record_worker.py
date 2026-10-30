"""Artificial writer subprocess for interruption-window acceptance."""
import os,sys
from pathlib import Path
import stream_process as s
folder=Path(sys.argv[1]);mode=sys.argv[2];nonce=sys.argv[3]
def stop_after_exit(p):
    (p/'test-window.marker').write_bytes(b'MOCK after exit before summary')
    os._exit(91)
s.capture([sys.executable,str(Path(__file__).with_name('mock_cli.py')),mode,nonce],folder,
          ('MOCK prompt 中文 '+nonce).encode(),'ARTIFICIAL_NO_MODEL',timeout=4,
          after_exit=stop_after_exit if mode=='clean' else None,nonce=nonce)
