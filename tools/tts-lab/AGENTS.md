# S01 task memory

## Purpose and authority

Local Mandarin TTS Voice Lab for Issue #3 only. Follow root AGENTS.md,
docs/TTS_VOICE_LAB.md, tasks/S01_TTS_VOICE_LAB.md and its handoff. Starting
branch commit: be5306c0ee1ea2625f22e3045e9346d98efeb95b; S00/main baseline:
adc9f340a2ff427b30cddce33ad8a4d9efdac55a. Do not change the iOS reader.

## File map

- `run.py`: offline-first command entry point.
- `tts_lab/`: typed requests, independent adapters, transports, billing, cache,
  audition planning and blind local player generation.
- `samples/`: original short Mandarin corpus; canonical source, not vendor audio.
- `tests/`: offline unittest coverage. Network and credential access are guarded.
- `../../docs/TTS_PROVIDER_API_CONTRACTS.md`: dated official-document contract
  notes; not a claim of live service compatibility.
- `../../reports/S01_TTS_EVALUATION.md`: canonical results/limits and handoff.
- `../../.local-test-data/tts-auditions/`: ignored generated sessions/cache/audio,
  mappings, HTML and rating files. Never commit these outputs.

## Decisions

- Python standard library only; no package installation or SDK dependency.
- One normalized original corpus and shared chunk boundaries for all providers.
- Common audition container: PCM WAV, 24 kHz, 16-bit mono. Validate headers;
  never silently relabel or resample an incompatible provider response.
- S01 CLI live execution is hard-disabled, including when flags/cap are supplied.
  A guarded transport is an extension point for later owner-authorized work.
- No credential values in request plans, cache identities, errors or exports.
- No actual vendor voice discovery or synthesis. Unconfigured male/female voice
  slots and unsupported styles must remain explicitly unrun, not fabricated.
- Mock signals test plumbing only and must never be scored as vendor speech.
- Provider decision stays OPEN pending real authorization and human listening.

## Handoff

Record actual commands and exact tested revision. Stop at READY_FOR_AUDIT after
PR creation. No merge, cloud integration, backend, spending or S02.

## Validation snapshot (2026-11-24)

- Python 3.11.11 standard library, 38 offline unittest checks; browser verifier
  uses existing Node 24.15.0 / Playwright 1.62.1 / Chrome 157.0.8103.79.
- Six original cases: 930 scalars / 2643 UTF-8 bytes / 931 UTF-16 units, 12 chunks.
- 32 conditions, 24 with documented comparison controls; 8 unsupported gentle
  conditions are retained as NOT_RUN. Default voice slots are not catalogue
  discovery results. Azure region eastus is a planning placeholder when unset.
- Generated HTML and all test/audio/mapping outputs stay ignored. Browser
  verification files: `.local-test-data/tts-auditions/verification/browser/`.
- `--execute-live` is hard-disabled; future HTTP code is exercised with a fake
  opener only. No provider preference, human listening or live billing evidence.
- Final tested HEAD and macOS regression details belong in PR; do not rewrite
  historical S00 evidence or claim its run is the new S01 run.
