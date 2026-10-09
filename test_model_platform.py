"""Workbench contract tests. Local HTTP fixtures are not real model evidence."""
import contextlib
import csv
import io
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

import model_platform as mp
import batch


class PlatformTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.csv = self.root / 'profiles.csv'
        self.run = self.root / 'run'
        self.key = 'WORKBENCH_TEST_KEY'
        self.env = patch.dict(os.environ, {self.key: 'synthetic-secret', 'NO_PROXY': '127.0.0.1,localhost'})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.write()

    def write(self, **overrides):
        row = dict(id='fixture', enabled='true', protocol='chat_completions',
                   base_url='https://example.com/v1', model='fixture-model', api_key_env=self.key)
        row.update(overrides)
        with self.csv.open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=mp.FIELDS)
            writer.writeheader()
            writer.writerow(row)

    def call(self, *args):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return mp.main(list(args))

    def prepare(self, budget='1'):
        return self.call('prepare', '--profiles', str(self.csv), '--run-dir', str(self.run),
            '--tasks', 've_count10', '--max-total-calls', budget)

    def test_preview_no_network_or_keys(self):
        with patch.dict(os.environ, {self.key: ''}), patch.object(mp, 'invoke', side_effect=AssertionError('network')):
            self.assertEqual(self.call('check', '--profiles', str(self.csv)), 0)

    def test_strict_profile_security(self):
        for change in ({'base_url': 'https://user:secret@example.com/v1'},
                       {'base_url': 'http://example.com/v1'}, {'id': '../escape'},
                       {'protocol': 'messages'}, {'base_url': 'https://example.com/v1/chat/completions'}):
            self.write(**change)
            with self.assertRaises((ValueError, mp.lab.LabError)):
                mp.profiles(self.csv)

    def test_budget_rejected_before_creation(self):
        self.assertEqual(self.prepare('0'), 2)
        self.assertFalse(self.run.exists())

    def test_prepare_and_tamper(self):
        self.assertEqual(self.prepare(), 0)
        self.assertEqual(mp.report(self.run)[0]['calls'], 0)
        content = '\n'.join(p.read_text(encoding='utf-8-sig') for p in self.run.rglob('*.json'))
        self.assertNotIn('synthetic-secret', content)
        plan = self.run / 'fixture' / 'plan.json'
        plan.write_text(plan.read_text() + ' ')
        self.assertEqual(self.call('run', '--run-dir', str(self.run)), 2)

    def test_unknown_attempt_never_reissued(self):
        self.assertEqual(self.prepare(), 0)
        folder = self.run / 'fixture' / 'jobs' / 've_count10__s001' / 'attempt_001'
        folder.mkdir(parents=True)
        batch.atomic(folder / 'started.json', {'model_call_reserved': True})
        with patch.object(mp, 'invoke', side_effect=AssertionError('must not call')):
            self.assertEqual(self.call('run', '--run-dir', str(self.run)), 2)

    def test_template_exclusive_and_disabled(self):
        path = self.root / 'template.csv'
        self.assertEqual(self.call('template', '--output', str(path)), 0)
        self.assertEqual(self.call('template', '--output', str(path)), 2)
        self.assertEqual(self.call('check', '--profiles', str(path)), 2)

    def test_http_end_to_end_and_resume(self):
        calls = []
        rtl = (mp.ROOT / 'benchmarks/dev10/reference/ve_count10.sv').read_text()

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                calls.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
                body = json.dumps(dict(model='fixture-model', choices=[dict(message=dict(content=rtl),
                    finish_reason='stop')], usage=dict(prompt_tokens=10, completion_tokens=20))).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            self.write(base_url='http://127.0.0.1:' + str(server.server_port) + '/v1')
            self.assertEqual(self.prepare(), 0)
            self.assertEqual(self.call('run', '--run-dir', str(self.run)), 0)
            self.assertEqual(self.call('run', '--run-dir', str(self.run)), 0)
            self.assertEqual(len(calls), 1)
            self.assertIsInstance(calls[0]['max_tokens'], int)
            row = mp.report(self.run)[0]
            self.assertEqual((row['passes'], row['calls']), (1, 1))
            self.assertEqual(row['usage']['completion_tokens'], 20)
            for path in self.run.rglob('*.json'):
                self.assertNotIn('synthetic-secret', path.read_text())
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()
