#!/usr/bin/env python3
"""Check metadata recorded by the actual simulator's virtualized reader."""
from pathlib import Path
import json

path = Path('build/reader-metrics.json')
samples = json.loads(path.read_text())
assert samples, 'No real reader samples'
blocks = {sample['block'] for sample in samples}
sessions = {}
for sample in samples:
    sessions.setdefault(sample['session'], []).append(sample)
summary = {
    'samples': len(samples),
    'process_sessions': len(sessions),
    'indexed_blocks': max(sample['blocks'] for sample in samples),
    'distinct_top_blocks': len(blocks),
    'furthest_top_block': max(blocks),
    'maximum_visible_cells': max(sample['visibleCells'] for sample in samples),
    'maximum_rendered_text_utf16': max(sample['maximumTextUTF16'] for sample in samples),
    'maximum_window_blocks': max(sample['windowBlocks'] for sample in samples),
    'early_scroll_window_shift_observed': any(0 < sample['windowStart'] < sample['blocks'] * 0.9 for sample in samples),
    'maximum_process_peak_rss_bytes': max(sample['processPeakRSSBytes'] for sample in samples),
    'per_session_peak_growth_bytes': [max(s['processPeakRSSBytes'] for s in group) - group[0]['processPeakRSSBytes'] for group in sessions.values()],
}
Path('build/reader-metrics-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
assert summary['process_sessions'] >= 2, 'Relaunch not observed'
assert summary['distinct_top_blocks'] >= 4, 'Insufficient scrolling samples'
assert summary['furthest_top_block'] >= summary['indexed_blocks'] * 0.95, 'Late chapter not exercised'
assert 0 < summary['maximum_visible_cells'] <= 16, 'Unexpected live cell count'
assert 0 < summary['maximum_rendered_text_utf16'] <= 1600, 'Unbounded rendered text'
assert summary['maximum_window_blocks'] <= 12, 'Unbounded accessibility/render tree'
assert summary['early_scroll_window_shift_observed'], 'Progressive window scrolling was not exercised'
assert 0 < summary['maximum_process_peak_rss_bytes'] <= 768 * 1024 * 1024, 'Simulator reader RSS ceiling exceeded'
