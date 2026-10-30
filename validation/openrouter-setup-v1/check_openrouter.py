"""Read-only OpenRouter setup check. No generation endpoint or automatic retries."""
import argparse
import datetime
import json
import os
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

MODELS = ['openai/gpt-5.6-luna', 'openai/gpt-5.6-terra', 'openai/gpt-5.6-sol']
BASE = 'https://openrouter.ai/api/v1'

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None

def select_models(data):
    indexed = {m['id']: m for m in data['data']}
    return [{'requested_id': name, 'catalog_present': name in indexed,
             'context_length': indexed.get(name, {}).get('context_length'),
             'supported_parameters': indexed.get(name, {}).get('supported_parameters')}
            for name in MODELS]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--proxy', default='', help='Explicit local HTTP proxy, otherwise direct')
    ap.add_argument('--offline', action='store_true')
    args = ap.parse_args()
    if args.proxy:
        u = urllib.parse.urlsplit(args.proxy)
        if u.scheme != 'http' or u.hostname not in ('127.0.0.1', 'localhost') or not u.port or u.username or u.password or u.query or u.fragment or u.path not in ('', '/'):
            ap.error('Only a credential-free localhost HTTP proxy is allowed')
    report = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'generation_calls': 0, 'metadata_requests': 0, 'automatic_retries': 0,
              'proxy_mode': 'explicit_local' if args.proxy else 'direct',
              'status': 'OFFLINE_ONLY', 'models': [],
              'meaning': 'Catalog visibility and key authentication only; not proof of inference permission, provider identity, or formal readiness.'}
    key = os.environ.get('OPENROUTER_API_KEY', '')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({'http': args.proxy, 'https': args.proxy} if args.proxy else {}), NoRedirect())
    def get(path):
        if path not in ('/key', '/models'):
            raise ValueError('Read-only endpoint allowlist')
        report['metadata_requests'] += 1
        req = urllib.request.Request(BASE + path, headers={'Authorization': 'Bearer ' + key, 'Accept': 'application/json'}, method='GET')
        with opener.open(req, timeout=30) as response:
            raw = response.read(16 * 1024 * 1024 + 1)
        if len(raw) > 16 * 1024 * 1024:
            raise ValueError('Metadata too large')
        return json.loads(raw)
    if not args.offline:
        if not key:
            report['status'] = 'MISSING_KEY_IN_THIS_PROCESS'
        else:
            try:
                info = get('/key')
                if not isinstance(info.get('data'), dict):
                    raise ValueError('Unexpected key metadata')
                report['key_authenticated'] = True
                report['models'] = select_models(get('/models'))
                report['status'] = 'CATALOG_VISIBLE_NOT_RELEASED' if all(x['catalog_present'] for x in report['models']) else 'EXACT_MODELS_MISSING_STOP'
            except urllib.error.HTTPError as exc:
                report.update(status='HTTP_ERROR_STOP_NO_RETRY', http_status=exc.code)
            except Exception as exc:
                report.update(status='CHECK_FAILED_NO_RETRY', error_type=type(exc).__name__)
    # Never persist raw key metadata, headers, error bodies, or exception messages.
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if key and key in text:
        text = json.dumps({'status': 'SECRET_ECHO_REDACTED', 'generation_calls': 0})
    out = Path(__file__).parent / 'receipts'
    out.mkdir(exist_ok=True)
    path = out / ('check-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json')
    with path.open('x', encoding='utf-8') as f:
        f.write(text + '\n')
    print(text)
    print('Receipt:', path)
    return 0 if report['status'] in ('OFFLINE_ONLY', 'CATALOG_VISIBLE_NOT_RELEASED') else 2

if __name__ == '__main__':
    raise SystemExit(main())
