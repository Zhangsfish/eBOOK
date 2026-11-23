# S01 — Mandarin TTS Voice Lab (READY)

## Goal

Build a repeatable, local-only audition workbench to choose a high-quality Mandarin voice for long-form Chinese fiction. S00 is merged. The existing iOS app must continue to work with local Apple speech. S01 is about evidence-based voice selection, not yet shipping cloud TTS.

## Read first

1. AGENTS.md
2. STATUS.md
3. README.md
4. docs/PRODUCT_SPEC.md
5. docs/TECHNICAL_PLAN.md
6. docs/TTS_VOICE_LAB.md
7. This task
8. GitHub Issue #3 (linked from STATUS.md when created)

## Authorized scope

1. Create tools/tts-lab/ as a local Python CLI/workbench. Prefer Python standard library; any optional dependency must be pinned and justified.
2. Create a compact, original Chinese sample suite covering narration, dialogue, restrained emotion, punctuation, proper nouns, numbers, mixed Chinese/English and chunk boundaries. No commercial-book text.
3. Implement provider adapters for the shortlist in docs/TTS_VOICE_LAB.md: MiniMax Speech 2.8, Fish Audio S2.1 Pro, ElevenLabs, and Azure Speech. Before coding each adapter, read its current official API schema/docs; do not infer request/response fields from third-party examples.
4. Add an offline mock transport and tests for request serialization, response/error handling, chunking, byte/character accounting, caching and cost-unit calculations.
5. Implement --dry-run as the default. Any actual network call must require both --execute-live and a user-supplied explicit spend cap. S01 CI must never make live vendor calls.
6. Read credentials only from environment variables. Add .env to .gitignore if missing and provide .env.example containing variable names only. Never print or log secret values.
7. Save all generated audio, provider metadata, manifests, local listening HTML and rating files under ignored .local-test-data/tts-auditions/. Do not commit any generated audio or real provider output.
8. Generate a blind A/B listening page with anonymous sample labels and a separate local mapping manifest. Include a score sheet using the weighted criteria in docs/TTS_VOICE_LAB.md.
9. Provide a cost estimate for each provider using its actual billing unit. For Fish Audio, measure UTF-8 bytes; do not treat bytes as characters. For Azure, account for Chinese characters being billed as two characters. Mark unknown or region-dependent prices as unknown rather than guessing.
10. Add a concise reports/S01_TTS_EVALUATION.md template/report. Distinguish completed dry-run/mock tests from actual human listening and actual live API calls.
11. Keep the app build and S00 tests passing. Do not alter the current iOS playback implementation unless a narrowly scoped shared utility is demonstrably necessary; ask in the report rather than expanding scope.

## Candidate models

- MiniMax Speech 2.8 HD; Turbo only as a speed/cost control.
- Fish Audio S2.1 Pro; S2.1 Pro Free may be used for a later no-cost audition.
- ElevenLabs Eleven v4; Multilingual v2 as a long-form stability control.
- Azure Chinese Neural and available Neural HD/DragonHD voices, selected from the actual configured region's voice list.

These are candidates, not pre-approved vendors or a final ranking. Re-check current models, request limits, prices, regions, commercial terms and data-retention terms from official sources.

## Hard constraints

- No live API request, paid usage, voice cloning, or vendor account creation in S01.
- Do not request credentials from the owner in chat or place keys in GitHub. The harness must be testable with mock transports and no secrets.
- No public backend, proxy, deployment, user accounts, subscriptions, or App Store submission.
- No cloud TTS integration into the iOS app in S01.
- Never transmit a commercial novel or user-imported ebook. The audition corpus is original synthetic text only.
- Do not automatically retry a request that may already have been billed.
- Preserve existing S00 code and behavior. Do not merge to main.

## Acceptance criteria

- python3 -m unittest discover -s tools/tts-lab/tests passes offline.
- python3 tools/tts-lab/run.py --dry-run --provider all works without credentials or network access.
- python3 scripts/generate_xcode_project.py --check and the S00 Xcode simulator CI workflow remain green.
- Mock tests cover each provider adapter and errors without contacting vendors.
- Cost accounting is provider-specific, reproducible and unit-tested.
- All audio and audition output paths are ignored by Git.
- No secrets, commercial book text, real generated audio or personal voice recordings enter the repository.
- Report clearly identifies which parts remain unrun pending owner authorization and human listening.

## Deliverables

- tools/tts-lab/ CLI, adapters, mock transport, sample suite, tests and local player generator.
- docs/TTS_VOICE_LAB.md (evaluation protocol and current official references).
- reports/S01_TTS_EVALUATION.md (results, cost, limitations and next recommendation).
- Updated README.md and STATUS.md.
- PR to main with exact tested HEAD SHA and actual test results.

## Stop condition

Open a PR to main, report exact tested HEAD SHA and actual checks, set state to READY_FOR_AUDIT, and STOP. Do not merge, do not integrate a cloud provider into the iOS app, and do not begin S02.
