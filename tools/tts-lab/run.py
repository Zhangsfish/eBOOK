#!/usr/bin/env python3
"""Offline Mandarin Voice Lab. No live provider execution is authorized in S01."""
import argparse
import sys
from tts_lab.adapters import ADAPTERS
from tts_lab.core import LabError
from tts_lab.lab import run_lab
from tts_lab.transport import LivePolicy


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider', choices=['all', *ADAPTERS], default='all')
    execution = parser.add_mutually_exclusive_group()
    execution.add_argument('--dry-run', action='store_true', help='Default: plan only; no credentials or network.')
    execution.add_argument('--mock-audio', action='store_true', help='Offline plumbing demo with identical test tones, not vendor speech.')
    execution.add_argument('--execute-live', action='store_true', help='Reserved gate; hard-disabled throughout S01.')
    parser.add_argument('--max-spend-usd', help='Future live preflight cap; never authorizes S01 requests.')
    parser.add_argument('--output', help='Optional subdirectory under ignored .local-test-data/tts-auditions/.')
    parser.add_argument('--seed', type=int, help='Optional reproducible blind-order seed; kept out of the HTML.')
    parser.add_argument('--voices-config', help='Local ID-only JSON, under ignored tts-auditions/. No credentials.')
    parser.add_argument('--azure-region', help='Region for request planning; no resource lookup is performed.')
    args = parser.parse_args(argv)
    try:
        if args.execute_live:
            # No CLI/environment switch can authorize a phase that forbids live use.
            LivePolicy(True, args.max_spend_usd, phase_authorized=False).authorize([])
        if args.max_spend_usd is not None:
            raise LabError('--max-spend-usd is meaningful only with the reserved live gate.')
        directory, result, mapping = run_lab(args.provider, 'mock' if args.mock_audio else 'dry_run',
                                            args.output, args.seed, args.voices_config, args.azure_region)
    except LabError as error:
        print(f'Voice Lab: {error}', file=sys.stderr)
        return 2
    print(f"Mode: {result['mode']} | vendor requests: 0 | incurred USD: 0 | human listening: NOT_RUN")
    for row in mapping:
        voice = row['voice'] or 'UNCONFIGURED (male/female slot, not a real voice ID)'
        print(f"{row['provider']} / {row['model']} / {row['slot']} / {row['style']} / voice={voice} / style_supported={row['style_supported']}")
    for row in result['cost_estimates']:
        value = row['estimated_usd_if_all_configured_and_executed']
        print(f"Estimate only: {row['provider']} / {row['model']} / {row['billable_units_estimate']} {row['billing_unit']} / USD={value if value is not None else 'UNKNOWN (region/SKU required)'}")
    print('Original text counts:')
    from tts_lab.corpus import load_samples
    from tts_lab.core import text_counts
    for sample in load_samples():
        print(f'{sample.id}: {text_counts(sample.text)}; chunks={len(sample.pieces)}')
    print(f'Local output: {directory}')
    print(f'Blind page: {(directory / "index.html").as_uri()}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
