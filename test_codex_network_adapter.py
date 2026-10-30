"""Network inheritance checks; no real model requests."""
import os
import unittest
from unittest.mock import patch

import codex_network_adapter as adapter
import rtl_lab as lab


class NetworkEnvironmentTests(unittest.TestCase):
    def test_existing_proxy_forwarded_without_secrets_or_global_changes(self):
        values = {'HTTPS_PROXY': 'http://127.0.0.1:3213',
                  'NO_PROXY': 'localhost,127.0.0.1',
                  'OPENAI_API_KEY': 'TEST_SENTINEL',
                  'UNRELATED_SECRET': 'TEST_SENTINEL'}
        with patch.dict(os.environ, values, clear=True):
            env = adapter.model_network_env()
            self.assertEqual(env['HTTPS_PROXY'], values['HTTPS_PROXY'])
            self.assertEqual(env['NO_PROXY'], values['NO_PROXY'])
            self.assertNotIn('OPENAI_API_KEY', env)
            self.assertNotIn('UNRELATED_SECRET', env)
            self.assertEqual(dict(os.environ), values)
            self.assertNotIn('HTTPS_PROXY', lab.clean_env())

    def test_os_proxy_discovery_without_process_proxy(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(
                adapter.urllib.request, 'getproxies', return_value={
                    'http': 'http://127.0.0.1:3213',
                    'https': 'http://127.0.0.1:3213'}):
            env = adapter.model_network_env()
            self.assertEqual(env['HTTPS_PROXY'], 'http://127.0.0.1:3213')
            self.assertNotIn('HTTPS_PROXY', os.environ)
            self.assertNotIn('HTTPS_PROXY', lab.clean_env())

    def test_absent_proxy_keeps_clean_environment(self):
        with patch.object(adapter.urllib.request, 'getproxies', return_value={}):
            self.assertEqual(adapter.model_network_env(), lab.clean_env())


if __name__ == '__main__':
    unittest.main()
