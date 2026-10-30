"""Read GitHub status using the existing credential helper, never print tokens."""
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

result = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n\n',
                        text=True, capture_output=True, check=True)
values = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
env = os.environ.copy()
env['GH_TOKEN'] = values['password']
result = subprocess.run([r'C:\Program Files\GitHub CLI\gh.exe'] + sys.argv[1:],
                        env=env, capture_output=True, encoding='utf-8', errors='replace')
print(result.stdout)
print(result.stderr, file=sys.stderr)
raise SystemExit(result.returncode)
