"""Bounded original-fixture CI diagnostics and exact XCTest-method accounting."""
from pathlib import Path
import json
import re
import subprocess


def method_coverage(root, build, scope, summary):
    expected = set()
    for folder, target in [('CoreTests', 'EBookTests'), ('UITests', 'EBookUITests')]:
        for path in (root / 'Tests' / folder).glob('*.swift'):
            source = path.read_text()
            classes = re.findall(r'class\s+(\w+)\s*:\s*XCTestCase', source)
            if len(classes) != 1:
                raise ValueError('Expected one explicit XCTestCase class per source file')
            cls = classes[0]
            for name in re.findall(r'^\s*func\s+(test\w+)\s*\(', source, re.MULTILINE):
                selected = (scope == 'all' or (scope == 'integration' and cls.startswith('Suxin'))
                            or (scope == 'frontend' and cls == 'SuxinFrontendTests')
                            or (scope == 'picker' and name in ['testFilesPickerImportsSelectedTXTAndEPUB', 'testSystemDocumentPickerPresentsAndCanCancel']))
                if selected:
                    expected.add(f'{target}.{cls} {name}')
    states = {}
    for case, state in re.findall(r"Test Case '-\[([^\]]+)\]' (started|passed|failed)", (build / 's02b-test.log').read_text()):
        states[case] = state
    missing = sorted(expected - states.keys())
    unexpected = sorted(states.keys() - expected)
    unfinished = sorted(k for k, v in states.items() if v == 'started')
    errors = []
    if missing or unexpected or unfinished or summary['totalTestCount'] != len(expected) or summary['skippedTests']:
        errors.append('Actual method set/count differs from source-declared scope, or methods skipped/incomplete')
    data = {'scope': scope, 'expected_method_count': len(expected), 'expected_methods': sorted(expected),
            'observed_method_states': states, 'missing_methods': missing, 'unexpected_methods': unexpected,
            'unfinished_methods': unfinished, 'xctest_summary_count': summary['totalTestCount'], 'errors': errors,
            'scope_note': 'Host startup errors are summary records, never counted as executed methods.'}
    (build / 's02b-method-coverage.json').write_text(json.dumps(data, indent=2) + '\n')
    return errors


def collect_crashes(root, build, device, env):
    exports = build / 's02b-private-diagnostics'
    try:
        with (build / 's02b-diagnostics-export.log').open('w') as log:
            subprocess.run(['xcrun', 'xcresulttool', 'export', 'diagnostics', '--path', str(build / 'S02B-tests.xcresult'),
                            '--output-path', str(exports)], env=env, stdout=log, stderr=subprocess.STDOUT, timeout=60)
    except subprocess.TimeoutExpired:
        pass
    roots = [Path.home() / 'Library/Logs/DiagnosticReports', exports,
             Path(device['dataPath']) / 'Library/Logs/CrashReporter']
    metadata, texts, budget = [], [], 4 * 1024 * 1024
    for folder in roots:
        if not folder.is_dir(): continue
        for path in folder.rglob('*'):
            name = path.name.lower()
            if path.suffix not in ['.ips', '.crash'] or not ('ebook' in name or 'xctest' in name): continue
            size = path.stat().st_size
            if size > min(budget, 1024 * 1024): continue
            text = path.read_text(errors='replace')
            text = re.sub(r'[0-9A-Fa-f]{8}(?:-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}', '<SIMULATOR_OR_INCIDENT_ID>', text)
            text = text.replace(str(root), '$WORKSPACE').replace(str(Path.home()), '$RUNNER_HOME')
            texts.append(text); budget -= size
            metadata.append({'kind': path.suffix, 'original_bytes': size, 'sanitized_bytes': len(text.encode())})
    (build / 's02b-test-host-crashes.log').write_text('\n\n'.join(texts) if texts else 'No matching crash stack found; no cause inferred.\n')
    (build / 's02b-test-host-diagnostics.json').write_text(json.dumps({'crash_files': metadata,
        'complete_stack_available': bool(texts), 'bounded_original_ci_only': True,
        'no_stack_is_not_a_pass': True}, indent=2) + '\n')
