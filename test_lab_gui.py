"""GUI boundary checks: no real API, native Tk smoke only with a display."""
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import tkinter as tk

import lab_gui as gui


class WindowTests(unittest.TestCase):
    def test_original_prompt_bytes_and_budget(self):
        prompt = gui.OriginalPrompt()
        data = '  \r\n完整提示词\r\n\t尾部  \n'.encode('utf-8')
        prompt.set(data)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'prompt.txt'
            prompt.save(path)
            self.assertEqual(path.read_bytes(), data)
            with self.assertRaises(FileExistsError):
                prompt.save(path)
        args, count = gui.build_command(1, Path('run'), Path('prompt'), 've_count10', 3, 6, 2)
        self.assertEqual(count, 6)
        self.assertIn('--prompt-dir', args)
        self.assertNotIn('--prompt-keys', args)
        with self.assertRaises(ValueError):
            gui.build_command(1, Path('run'), Path('prompt'), 'all', 1, 30, 2)
        with self.assertRaises(ValueError):
            gui.build_command(2, Path('run'), Path('prompt'), 'all', 3, 59, 2)
        with self.assertRaises(ValueError):
            prompt.set(b'\xff')

    def test_csv_rejects_key_column_and_duplicate_profiles(self):
        row = dict(id='a', enabled='true', protocol='chat_completions', base_url='https://api.example.com/v1', model='fixture', api_key_env='FIXTURE_KEY')
        self.assertEqual(gui.csv_rows(gui.csv_text([row])), [row])
        with self.assertRaises(ValueError):
            gui.csv_rows(gui.csv_text([row, row]))
        with self.assertRaises(ValueError):
            gui.csv_rows('id,api_key\na,do-not-store-secrets\n')

    def test_native_window_paste_launch_and_async_doctor(self):
        try:
            window = tk.Tk()
        except tk.TclError:
            self.skipTest('Native Tk display unavailable; run on Windows or xvfb')
        window.withdraw()
        try:
            app = gui.LabWindow(window)
            window.update()
            self.assertEqual(app.tabs.index('end'), 4)
            with tempfile.TemporaryDirectory() as config_temp, patch.object(gui.ece_synthesis, 'CONFIG', Path(config_temp) / 'config.json'):
                app.save_synthesis()
                self.assertIn('standard-cell library paths', app.status.get())
                app.synth_tool.set('genus')
                app.switch_synthesis()
                self.assertEqual(app.synth_active, 'genus')
                app.synth_options = {'synthetic': dict(run_dir=config_temp, job_id='case')}
                app.synth_selection.set('synthetic')
                with patch.object(app, 'start') as synth_start:
                    app.pack_synthesis()
                self.assertEqual(synth_start.call_args.kwargs['script'], 'ece_synthesis.py')
                self.assertIn('genus', synth_start.call_args.args[0])
            data = ' \r\n粘贴原文\r\n end  '.encode('utf-8')
            with patch.object(gui, 'clipboard_text', return_value=data.decode('utf-8')):
                app.paste_prompt()
            self.assertEqual(app.prompt.data, data)
            self.assertEqual(app.prompt_view.cget('state'), 'disabled')
            row = dict(id='a', enabled='true', protocol='chat_completions', base_url='https://api.example.com/v1', model='fixture', api_key_env='FIXTURE_KEY')
            app.csv.delete('1.0', 'end')
            app.csv.insert('1.0', gui.csv_text([row]))
            with tempfile.TemporaryDirectory() as folder, patch.object(gui, 'ROOT', Path(folder)), \
                    patch.object(gui, 'CONFIG', Path(folder) / 'config.local.models.csv'):
                app.keys['FIXTURE_KEY'] = 'fake-secret-only'
                with patch.object(app, 'start') as start:
                    app.run()
                args = start.call_args.args[0]
                self.assertEqual(args[0], 'generate')
                prompt_file = Path(args[args.index('--prompt-file') + 1])
                self.assertEqual(prompt_file.read_bytes(), data)
                self.assertNotIn('fake-secret-only', gui.CONFIG.read_text())
            # The actual doctor process is read-only, no network/model calls.
            app.start(['doctor'])
            deadline = time.monotonic() + 15
            while app.busy and time.monotonic() < deadline:
                window.update()
                time.sleep(.02)
            self.assertFalse(app.busy)
            self.assertIn('退出码 0', app.status.get())
            self.assertIn('No API/network/EDA request', app.log.get('1.0', 'end'))
            self.assertEqual(app.redact('key=fake-secret-only'), 'key=[REDACTED]')
        finally:
            window.destroy()


if __name__ == '__main__':
    unittest.main()
