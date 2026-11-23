# Mandarin Voice Lab — S01

Python **3.11+**, standard library only. The iOS app is unchanged. This tool is
offline by default; **S01 cannot make live provider calls**, even if
`--execute-live`, a spend cap and process credentials are present.

From the repository root:

```bash
python3 -m unittest discover -s tools/tts-lab/tests
python3 tools/tts-lab/run.py --dry-run --provider all
python3 scripts/generate_xcode_project.py --check
```

The no-flag CLI is also a dry run. `--provider` accepts `all`, `minimax`, `fish`,
`elevenlabs`, `azure`. `--seed 42` reproduces the anonymous ordering; omitting it
uses system randomness. Mapping remains outside the HTML in either case.

The command prints a local session path. Open that directory's `index.html`
directly in a browser; no local server, deployment or network is needed.

## Outputs and evidence

Everything generated stays below ignored `.local-test-data/tts-auditions/`.
`--output` can select a subdirectory there; outside paths/symlinks are refused.

- `index.html`: blind A/B controls, common transcript, pause-all and rubric.
  Dry Run has no audio source and says NOT_RUN.
- `ratings.csv`: one anonymous voice-condition row, seven blank 1–5 scores,
  weighted result and notes. Do not turn blank scores into zero.
- `LISTENING_GUIDE.md`: weights, fatigue/pronunciation/continuity notes.
- `private-mapping.json`: separate provider/model/voice/style mapping and
  request/cost plans. Reveal only after listening/scoring.
- `session.json`: source revision/dirty flag, provenance, aggregate cost/counts.
- `original-samples.json`: exact original normalized corpus and chunk hashes.
- `cache/mock/` and later `cache/live/`: separate cache provenance. Keys cover
  provider/model/voice/text/settings/audio/region/contract version. Corrupt,
  failed or pending entries block automatic requests instead of rebilling.

For an optional **plumbing demonstration**, without speech or credentials:

```bash
python3 tools/tts-lab/run.py --mock-audio --provider all --seed 42
```

This passes synthetic responses through the real adapters and cache. All audio
is the **same 0.16-second test tone per chunk**, not vendor speech. The page says
so prominently. Joined multi-chunk tones verify the player/container path only.
Neither Dry Run nor Mock yields any valid voice score, measured vendor latency,
human listening result or preferred provider. Rerunning Mock reuses its cache;
that cache can never satisfy a future live request.

## Corpus, voices and styles

Six original samples cover narration, dialogue, restrained emotion, numbers and
mixed language, continuous chunk boundaries, fictional names and rare Han text.
The normalized suite has 930 scalars / 2,643 UTF-8 bytes / 931 UTF-16 units and
12 shared chunks, each <=120 scalars. There is no user-book/text-file input.

Eight model/family choices × two presenting-voice slots × neutral/gentle yields
32 planned conditions. Fish/ElevenLabs gentle is explicitly unsupported under
the identical-text comparison rule. Default MiniMax/Fish/ElevenLabs slots are
unconfigured, not fictitious voice IDs or guaranteed Mandarin voices. Azure
uses published Chinese examples with unverified regional access. Mock mode's
placeholder IDs identify no real vendor voice.

A later local voice selection can be planned without credentials using
`--voices-config` pointing to an ignored JSON object, for example keys
`minimax/speech-2.8-hd/female` or `fish/s2.1-pro/male`, whose values are existing
voice IDs selected by the owner. Only reviewed provider/model/slot keys are
accepted; do not put credentials or audio in that file. `--azure-region` changes
regional planning syntax; it does not query or prove resource availability.

See [API contract notes](../../docs/TTS_PROVIDER_API_CONTRACTS.md) for exact
official sources, style mappings and current pricing. Relative rate 1.0 and a
common format do not guarantee identical loudness or speaking speed.

## Credentials and later execution

`.env.example` is a names-only inventory, not a file to source. The tool does
not load dotenv files. Dry Run/Mock never read provider credential values.
For later explicitly authorized work, the transport binds process environment
values directly to a wire request after authorization; they never enter public
plans, error bodies, cache identities, JSON outputs or HTML.

The reserved `--execute-live --max-spend-usd ...` path is hard-disabled in S01.
Tests verify this even with environment values present. The guarded future
transport is tested only with a fake opener; its phase permit is never granted
by the CLI. A later review must authorize activation, recheck quotes, selected
voices/regions, commercial rights, retention and the full-batch spend policy.
No automatic retry follows an ambiguous timeout or incomplete cache record.

## Optional browser verification

The optional `tests/browser_check.cjs` uses an **already installed** Playwright
and Chrome; neither is an app/CLI dependency. It was validated with Playwright
1.62.1, Node 24.15.0 and Chrome 157.0.8103.79. No package installation is needed
for the Python tests or CLI. Set `PLAYWRIGHT_MODULE` to an existing module path
and `CHROME_EXECUTABLE` to the installed browser, then pass a generated dry-run
session, a generated mock session, and an existing verification subdirectory
under ignored `tts-auditions/`. All browser outputs remain there.

The check runs offline, tests three widths, anonymous labels, mock audio decode,
exclusive A/B playback and pause-all. It reports no vendor listening result.

## Handoff

The provider decision remains OPEN. Results/limitations are recorded in
`reports/S01_TTS_EVALUATION.md`. No cloud TTS is linked to the iOS app, no backend
is deployed, and no paid use or credentials are requested. Stop after the PR at
READY_FOR_AUDIT; do not merge or start S02.
