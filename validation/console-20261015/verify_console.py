"""Offline console acceptance; no real credentials, model calls or school tools."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import lab_gui as gui
import lab_flow
import test_lab_gui

with tempfile.TemporaryDirectory() as tmp, patch.object(gui.ece_synthesis, 'CONFIG', Path(tmp)/'synth.json'), patch.object(gui, 'CONFIG', Path(tmp)/'models.csv'):
    with (OUT/'gui-tests-isolated.txt').open('w', encoding='utf-8') as log:
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_lab_gui))
    assert result.wasSuccessful()
    window = tk.Tk()
    window.withdraw()
    try:
        app = gui.LabWindow(window)
        row = dict(id='fixture', enabled='true', protocol='chat_completions', base_url='https://api.example.com/v1', model='fixture', api_key_env='CONSOLE_FIXTURE_UNUSED')
        app.csv.delete('1.0', 'end')
        app.csv.insert('1.0', gui.csv_text([row]))
        app.set_prompt('  中文\r\n\tverbatim  \n'.encode('utf-8'))
        with patch.object(app, 'start', side_effect=AssertionError('preview must not launch')):
            app.preview()
        facts = {'preview_no_subprocess': True, 'preview_writes_config': gui.CONFIG.exists(), 'preview_status': app.status.get()}
        with patch.object(gui.messagebox, 'showerror') as error:
            app.cap.set('0')
            app.guarded(app.preview)()
            assert error.call_count == 1
            facts['invalid_budget_error'] = error.call_args.args[1]
        (OUT/'boundary-results.json').write_text(json.dumps(facts, ensure_ascii=False, indent=2), encoding='utf-8')
    finally:
        window.destroy()

run = ROOT/'runs/console-validation-20261015-01'
mode = lab_flow.synthesis_mode('auto', 'Ubuntu')
with (OUT/'synthesis-mode.txt').open('w', encoding='utf-8') as log:
    log.write(mode + '\n')
try:
    lab_flow.synthesize(run, mode)
    synthesis_outcome = 'completed'
except ValueError as exc:
    synthesis_outcome = str(exc)
(OUT/'synthesis-outcome.json').write_text(json.dumps({'mode': mode, 'outcome': synthesis_outcome}), encoding='utf-8')
rows = lab_flow.report(OUT/'workflow', run)
assert len(rows) == 1 and rows[0]['icarus'] == 'PASS'
files = [ROOT/name for name in ('lab_gui.py', 'lab_flow.py', 'model_platform.py', 'Open-Lab.cmd', 'Open-Lab.ps1', 'test_lab_gui.py')]
files += [run/'summary.json']
if (run/'synthesis-review/summary.json').exists():
    files.append(run/'synthesis-review/summary.json')
(OUT/'evidence-hashes.json').write_text(json.dumps({str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}, indent=2), encoding='utf-8')
print(json.dumps({'gui_tests': result.testsRun, 'synthesis_mode': mode, 'rows': rows}, ensure_ascii=False))
