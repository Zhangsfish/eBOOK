#!/usr/bin/env python3
"""Repository-scoped content checks; outputs counts/hashes, never book bodies."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--ref', default='HEAD')
parser.add_argument('--output', default='reports/S00/evidence/source-safety.json')
args = parser.parse_args()


def git(*command): return subprocess.check_output(['git', *command])


patterns = [rb'gh[pousr]_[A-Za-z0-9]{30,}', rb'github_pat_[A-Za-z0-9_]{30,}',
            rb'sk-[A-Za-z0-9_-]{32,}', rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----', rb'AKIA[0-9A-Z]{16}']
base = 'ab0aa0079c74f0de17a4a7bc7facd2cbbc9532ea'
historical_sizes = []
for entry in git('rev-list', '--objects', base).decode().splitlines():
    sha = entry.split()[0]
    if git('cat-file', '-t', sha).strip() != b'blob': continue
    data = git('cat-file', 'blob', sha)
    assert not any(re.search(pattern, data) for pattern in patterns), 'Historical credential pattern'
    historical_sizes.append(len(data))
assert max(historical_sizes) < 100_000, 'Unexpected large historical object'

files = git('ls-tree', '--full-tree', '-r', '--name-only', args.ref).decode().splitlines()
assert not any(name.startswith('.local-test-data/') for name in files), 'Local-only data tracked'
assert not any(name.endswith(('.zip', '.ipa', '.p12', '.mobileprovision', '.dpapi')) for name in files), 'Unexpected binary/archive'
sizes = []
for name in files:
    data = git('show', f'{args.ref}:{name}')
    assert not any(re.search(pattern, data) for pattern in patterns), f'Credential pattern in {name}'
    sizes.append(len(data))
    if name.startswith('Sources/') and name.endswith('.swift'):
        assert not re.search(rb'\b(URLSession|URLRequest|NWConnection|HTTPClient|WebSocket)\b', data), 'Unexpected network client'
    if name.endswith('.txt'): assert name.startswith('Tests/Fixtures/'), 'Unexpected tracked book text'
assert max(sizes) < 200_000, 'Unexpected large tracked file'

long = Path('.local-test-data/synthetic_long_gb18030.txt')
data = long.read_bytes()
text = data.decode('gb18030', errors='strict')
assert len(text) == 2_301_482 and len(text.splitlines()) == 73_176
assert git('check-ignore', str(long)).strip(), 'Generated large fixture is not ignored'
result = {
    'source_ref': git('rev-parse', args.ref).decode().strip(),
    'pre_publication_history_ref': base,
    'historical_blob_count': len(historical_sizes), 'maximum_historical_blob_bytes': max(historical_sizes),
    'tracked_file_count': len(files), 'maximum_tracked_file_bytes': max(sizes),
    'credential_pattern_matches': 0, 'swift_network_client_pattern_matches': 0,
    'large_fixture_tracked': False, 'large_fixture_bytes': len(data),
    'large_fixture_unicode_characters': len(text), 'large_fixture_lines': len(text.splitlines()),
    'large_fixture_sha256': hashlib.sha256(data).hexdigest(),
    'scope': 'Pattern/size/provenance checks only; not a general security certification.',
}
output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
