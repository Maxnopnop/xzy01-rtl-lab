"""Offline Git/flow tests. Synthetic EDA receipts are not commercial evidence."""
import contextlib
import io
import json
import os
import csv
import shutil
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import ece_desktop as desktop
import ece_git as transport
import ece_station
import ece_workflow as workflow
import lab_flow
import exact_prompts
from test_ece_workflow import WorkflowTests


class TransportTests(WorkflowTests):
    # Reuse fixture construction without rerunning inherited test methods.
    def setUp(self):
        super().setUp()
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.remote = self.root / 'remote.git'
        subprocess.run(['git', 'init', '--bare', str(self.remote)], check=True, capture_output=True)
        self.g('init')
        self.g('config', 'user.name', 'Offline Test')
        self.g('config', 'user.email', 'test@localhost')
        (self.repo / 'README').write_text('SYNTHETIC TEST REPO')
        self.g('add', 'README')
        self.g('commit', '-m', 'fixture')
        self.g('remote', 'add', 'origin', str(self.remote))
        self.g('push', 'origin', 'HEAD:main')
        self.gitstate = self.root / 'gitstate'
        self.gitstate.mkdir()

    def g(self, *args):
        return transport.git(self.repo, list(args))

    def package_catalog(self):
        source = self.package.with_suffix('.zip')
        with zipfile.ZipFile(source, 'w') as z:
            for path in self.package.rglob('*'):
                if path.is_file() and path.name != 'station-provenance.json':
                    z.write(path, 'package/' + path.relative_to(self.package).as_posix())
        self.entry['archive_sha256'] = desktop.digest(source)
        self.entry['cases'][0]['hashes'] = self.meta['hashes']
        (self.package / 'station-provenance.json').write_text(json.dumps(dict(package_id='pack', archive_sha256=self.entry['archive_sha256'])))
        workflow.saved(self.state / 'registry.json', dict(schema=1, packages=[self.entry], imports=[]))
        transport.export_packages(self.state, self.repo / 'ece_git_packages')

    def copy_return(self):
        self.return_fixture()
        for p in (self.shared / 'inbox').glob('*'):
            transport.copy_exact(p, self.gitstate / 'outbox' / p.name)

    def test_git_roundtrip_preserves_head_index_and_deduplicates(self):
        self.package_catalog()
        self.copy_return()
        (self.repo / 'unrelated.txt').write_text('keep staged')
        self.g('add', 'unrelated.txt')
        head = self.g('rev-parse', 'HEAD')
        index = self.g('diff', '--cached', '--binary')
        self.assertEqual(transport.upload(self.repo, self.gitstate), 0)
        self.assertEqual(transport.upload(self.repo, self.gitstate), 0)
        self.assertEqual(self.g('rev-parse', 'HEAD'), head)
        self.assertEqual(self.g('diff', '--cached', '--binary'), index)
        self.assertEqual(len(transport.read(self.gitstate / 'uploads.json')), 1)
        restored = self.root / 'restored-state'
        self.assertEqual(transport.sync(self.repo, restored), 0)
        self.assertEqual(transport.sync(self.repo, restored), 0)
        reg = workflow.registry(restored)
        self.assertEqual(len(reg['imports']), 1)
        self.assertEqual(reg['imports'][0]['results'][0]['status'], 'PASS')

    def test_failed_push_retries_transport_only(self):
        self.package_catalog()
        self.copy_return()
        with patch.object(transport.subprocess, 'call', return_value=1), patch.object(desktop, 'run_case', side_effect=AssertionError('no EDA')):
            self.assertEqual(transport.upload(self.repo, self.gitstate), 2)
        old = transport.read(self.gitstate / 'uploads.json')[0]['commit']
        with patch.object(desktop, 'run_case', side_effect=AssertionError('no EDA')):
            self.assertEqual(transport.upload(self.repo, self.gitstate), 0)
        self.assertEqual(transport.read(self.gitstate / 'uploads.json')[0]['commit'], old)

    def test_corrupt_git_payload_not_imported(self):
        self.package_catalog()
        self.copy_return()
        zip_path = next((self.gitstate / 'outbox').glob('*.zip'))
        zip_path.write_bytes(b'CORRUPT')
        with self.assertRaises(ValueError):
            transport.upload(self.repo, self.gitstate)
        self.assertFalse((self.gitstate / 'uploads.json').exists())

    def test_bad_remote_zip_fails_import_without_checkout(self):
        self.package_catalog()
        self.copy_return()
        self.assertEqual(transport.upload(self.repo, self.gitstate), 0)
        row = transport.read(self.gitstate / 'uploads.json')[0]
        path = next((self.gitstate / 'outbox').glob('*.zip'))
        prefix = 'ece_git_results/' + row['branch'].split('/')[1] + '/'
        bad = transport.make_commit(self.repo, {prefix + path.name: b'BAD', prefix + path.with_suffix('.json').name: path.with_suffix('.json').read_bytes()})
        self.g('push', 'origin', bad + ':refs/heads/ece-results/bad-fixture')
        self.assertEqual(transport.sync(self.repo, self.root / 'new-state'), 1)
        self.assertTrue(transport.read(self.root / 'new-state' / 'git-sync-issues.json'))


# Avoid inherited WorkflowTests appearing twice here; only new Git tests belong
# to this subclass. Existing workflow tests remain in their original module.
for name in list(WorkflowTests.__dict__):
    if name.startswith('test_'):
        setattr(TransportTests, name, None)
del WorkflowTests


class UnifiedTests(unittest.TestCase):
    def test_exact_case_rejects_bulk_before_unpack(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workflow.saved(root / transport.CATALOG, dict(packages=[dict(package_id='p', cases=[dict(job_id='one')])]))
            with patch.object(ece_station, 'unpack', side_effect=AssertionError('must not unpack')):
                self.assertEqual(ece_station.main(['--shared-dir', str(root), '--package-id', 'p', '--case', 'one,two']), 2)

    def test_synthesis_failure_blocks_paid_generation(self):
        with patch.object(lab_flow, 'synthesis_mode', side_effect=ValueError('no yosys')), \
             patch.object(lab_flow.model_platform, 'main', side_effect=AssertionError('no calls')):
            self.assertEqual(lab_flow.main(['local', '--run-dir', 'not-created', '--max-total-calls', '1']), 2)

    def test_local_pipeline_one_request_two_packages_and_resume(self):
        self.pipeline(False)

    def test_verbatim_pipeline_preserves_crlf_unicode_and_whitespace(self):
        self.pipeline(True)

    def pipeline(self, exact):
        requests = []
        rtl = (lab_flow.ROOT / 'benchmarks/dev10/reference/ve_count10.sv').read_text()
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                requests.append(self.rfile.read(int(self.headers['Content-Length'])))
                raw = json.dumps(dict(model='FIXTURE', choices=[dict(message=dict(content=rtl), finish_reason='stop')])).encode()
                self.send_response(200)
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
            def log_message(self, *args): pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {'FYP_FIXTURE_KEY': 'synthetic', 'NO_PROXY': '127.0.0.1,localhost'}):
                root = Path(temp)
                config = root / 'profiles.csv'
                with config.open('w', newline='') as stream:
                    writer = csv.DictWriter(stream, fieldnames=lab_flow.model_platform.FIELDS)
                    writer.writeheader()
                    writer.writerow(dict(id='fixture', enabled='true', protocol='chat_completions',
                        base_url='http://127.0.0.1:' + str(server.server_port) + '/v1', model='FIXTURE', api_key_env='FYP_FIXTURE_KEY'))
                args = ['--state-dir', str(root / 'state'), 'local', '--profiles', str(config),
                        '--run-dir', str(root / 'run'), '--tasks', 've_count10', '--max-total-calls', '1',
                        '--shared-dir', str(root / 'share'), '--synthesis', 'native' if shutil.which('yosys') else 'none']
                original = '  \r\n原始完整提示词；不要添加任何文字。\r\n\t末尾空白  \n'.encode('utf-8')
                if exact:
                    prompts = root / 'prompts'
                    prompts.mkdir()
                    (prompts / 've_count10.txt').write_bytes(original)
                    args += ['--prompt-dir', str(prompts)]
                self.assertEqual(lab_flow.main(args), 0)
                self.assertEqual(lab_flow.main(args), 0)
                self.assertEqual(len(requests), 1)
                self.assertEqual(len(workflow.registry(root / 'state')['packages']), 2)
                row = workflow.read(root / 'state' / 'lab-summary.json')['rows'][0]
                self.assertEqual(row['icarus'], 'PASS')
                self.assertEqual((row['vcs'], row['xcelium']), ('NOT_RUN', 'NOT_RUN'))
                if shutil.which('yosys'): self.assertEqual(row['yosys'], 'SYNTH_PASS')
                if exact:
                    sent = json.loads(requests[0])
                    self.assertEqual(sent['messages'], [{'role': 'user', 'content': original.decode('utf-8')}])
                    self.assertEqual((root / 'run' / 'exact-prompts' / 've_count10.txt').read_bytes(), original)
                    (prompts / 've_count10.txt').write_bytes(original + b'changed')
                    self.assertEqual(lab_flow.main(args), 2)
                    self.assertEqual(len(requests), 1)
                    self.assertEqual(lab_flow.main(['generate', '--profiles', str(config),
                        '--prompt-file', str(root / 'run' / 'exact-prompts' / 've_count10.txt'),
                        '--run-dir', str(root / 'unverified'), '--max-total-calls', '1']), 0)
                    self.assertEqual(json.loads(requests[1])['messages'], [{'role': 'user', 'content': original.decode('utf-8')}])
                    result = workflow.read(root / 'unverified' / 'generation-summary.json')
                    self.assertEqual(result['results'][0]['status'], 'GENERATED_UNVERIFIED')
                    self.assertEqual(result['validation'], 'NONE')
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()
