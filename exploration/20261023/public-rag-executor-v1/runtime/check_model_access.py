"""Read-only official model metadata. No generation; never log credentials/body."""
import datetime
import json
import os
from pathlib import Path
import urllib.request
import urllib.error

MODELS = ['gpt-5.6-luna', 'gpt-5.6-terra', 'gpt-5.6-sol']

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def main():
    report = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'model_generation_calls': 0, 'metadata_requests': 0,
              'meaning': 'Catalog visibility only; not proof of inference access or billing.',
              'models': []}
    key = os.environ.get('OPENAI_API_KEY')
    if not key:
        report['status'] = 'MISSING_ENV_IN_THIS_TERMINAL'
    else:
        opener = urllib.request.build_opener(NoRedirect())
        for model in MODELS:
            row = {'model': model}
            req = urllib.request.Request('https://api.openai.com/v1/models/' + model,
                                         headers={'Authorization': 'Bearer ' + key})
            report['metadata_requests'] += 1
            try:
                with opener.open(req, timeout=30) as response:
                    data = response.read(1048577)
                    if len(data) > 1048576:
                        raise ValueError('Oversized metadata')
                    obj = json.loads(data)
                    row['http_status'] = response.status
                    row['status'] = 'VISIBLE' if obj.get('id') == model else 'ID_MISMATCH'
            except urllib.error.HTTPError as exc:
                row.update(http_status=exc.code, status='HTTP_ERROR')
            except Exception as exc:
                row.update(status='CONNECTION_OR_PARSE_ERROR', error_type=type(exc).__name__)
            report['models'].append(row)
            if row.get('status') != 'VISIBLE':
                break
        report['status'] = 'CATALOG_VISIBLE' if len(report['models']) == 3 and all(r['status'] == 'VISIBLE' for r in report['models']) else 'CHECK_STOPPED_NO_RETRY'
    output = Path(__file__).resolve().parent / ('model-access-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json')
    output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    print('Receipt: ' + str(output))

if __name__ == '__main__':
    main()
