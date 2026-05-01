#!/usr/bin/env python3
import sys, json, subprocess

data = json.load(sys.stdin)
cmd = data.get('tool_input', {}).get('command', '')
if not cmd.strip().startswith('git commit'):
    sys.exit(0)

result = subprocess.run(
    ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
    capture_output=True, text=True, cwd='/root/erlau-app'
)
py_files = [f for f in result.stdout.splitlines() if f.startswith('app/') and f.endswith('.py')]

if not py_files:
    sys.exit(0)

scan = subprocess.run(
    ['venv/bin/bandit'] + py_files + ['-f', 'json', '-ll'],
    capture_output=True, text=True, cwd='/root/erlau-app'
)

try:
    report = json.loads(scan.stdout)
    high = int(report['metrics']['_totals']['SEVERITY.HIGH'])
    if high > 0:
        issues = [
            f"  - {r['filename']}:{r['line_number']} [{r['test_id']}] {r['issue_text']}"
            for r in report['results'] if r['issue_severity'] == 'HIGH'
        ]
        detail = '\n'.join(issues[:5])
        print(json.dumps({
            'continue': False,
            'stopReason': f'Guvenlik taramasi {high} HIGH severity sorun buldu:\n{detail}'
        }))
except Exception:
    sys.exit(0)
