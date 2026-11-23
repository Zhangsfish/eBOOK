# Codex Handoff — S01 Mandarin TTS Voice Lab

Copy the prompt below into Codex from the local checkout of Zhangsfish/eBOOK.

---

You are implementing **only S01 — Mandarin TTS Voice Lab**.

## 1. Synchronize safely

- Run git status --short --branch first. Preserve all unrelated local changes.
- Fetch origin.
- Switch to codex/s01-tts-voice-lab, tracking origin/codex/s01-tts-voice-lab; fast-forward only. Do not force-push and do not work on main.
- S00 is already merged into main. Do not reimplement it.

## 2. Read the source of truth

Read in full:
1. AGENTS.md
2. STATUS.md
3. README.md
4. docs/PRODUCT_SPEC.md
5. docs/TECHNICAL_PLAN.md
6. docs/TTS_VOICE_LAB.md
7. tasks/S01_TTS_VOICE_LAB.md
8. GitHub Issue #3

Follow the current task/spec documents if this prompt and a document differ.

## 3. Implement S01 only

Build a local-only Chinese TTS audition workbench:
- Original Chinese sample suite; no copyrighted novel excerpts.
- Offline-first Python CLI with provider adapters for MiniMax Speech 2.8, Fish Audio S2.1 Pro, ElevenLabs Eleven v4/Multilingual v2, and Azure Chinese Neural/HD.
- Read each provider's current official API docs/schema before implementation. Keep adapters isolated.
- Mock transport and unit tests for every adapter; CI must not contact vendors.
- Default --dry-run; actual network requests require an explicit --execute-live flag and a spend cap. Do not execute live calls in this task.
- Secrets only from environment variables. Never write/print them. Add only variable names to .env.example.
- Local audio, manifests, HTML player, score sheet and caches go under ignored .local-test-data/tts-auditions/.
- Produce blind A/B labels and a weighted rating template for the owner to listen and score.
- Produce provider-specific cost estimates with correct units; clearly mark unknown prices/availability.
- Update README/STATUS and create reports/S01_TTS_EVALUATION.md.
- Preserve S00 iOS code; no cloud TTS integration into the app, no backend, no deployment.

## 4. Safety and spend rules

- No live API calls, paid usage, account creation, voice cloning, or credential requests.
- Do not send any commercial novel or user-imported book to a vendor.
- Do not add provider keys to app code, Info.plist, GitHub, CI, logs or screenshots.
- Do not commit audio samples, manifests with private metadata, or audition outputs.
- Do not auto-retry a billable request after an ambiguous timeout.
- No public proxy or unauthenticated cloud endpoint.

## 5. Validate

Run:
  python3 -m unittest discover -s tools/tts-lab/tests
  python3 tools/tts-lab/run.py --dry-run --provider all
  python3 scripts/generate_xcode_project.py --check

Also run the existing S00 Xcode simulator build/tests if a macOS/Xcode environment is available. Report actual outputs only. If the host lacks Xcode, say so; do not fabricate.

## 6. Handoff

- Commit only to codex/s01-tts-voice-lab.
- Open a PR to main.
- Include exact tested HEAD SHA and actual test results.
- Mark READY_FOR_AUDIT and stop.
- Do not merge and do not begin S02.

The next stage will be selected only after independent review and the owner has listened to and scored the candidate samples.
