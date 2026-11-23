# Agent Instructions

## Source of truth and collaboration
- GitHub is the durable source of truth. Read this file, STATUS.md, the product/technical specs, and the currently authorized task before editing.
- Execute only the task explicitly marked READY. Do not infer permission to start later phases.
- Work on a task-specific codex/* branch. Never push implementation directly to main.
- Open a PR to main, attach real build/test evidence, report the exact tested HEAD SHA, then stop at READY_FOR_AUDIT. Do not merge, mark the task PASS, or start another phase.
- Do not fabricate simulator, device, build, test, or App Store results. If macOS/Xcode or signing is unavailable, state BLOCKED_ENV and provide the exact blocker.
- Preserve unrelated user changes and existing repository history.

## Product constraints
- iOS only; native SwiftUI. This is a deliberately narrow ebook reader, not a bookstore or social platform.
- Only import books selected by the user through the iOS document picker / Files. Initial supported formats: EPUB and TXT.
- Never scrape, download, commit, push, bundle, or redistribute unauthorized copies of copyrighted books. Do not bypass DRM or platform restrictions.
- Do not place complete copyrighted novels or user-imported commercial ebooks in this repository, even if it is private. Do not include them in CI artifacts, screenshots, issue comments, PR descriptions, crash reports, or logs.
- Automated tests must use original synthetic text or public-domain text with verified status. Use docs/TEST_DATA.md and scripts/generate_long_gb18030_fixture.py for large Chinese TXT performance fixtures.
- The app's normal user-selected file import must remain local. Do not upload imported book contents automatically.
- S00 uses local AVSpeechSynthesizer only. Do not send book text to a cloud TTS provider or other external service in S00.
- S01 is a local TTS audition harness only. No live provider API calls, paid usage, voice cloning, provider account creation or credential requests are authorized in S01. All provider adapters must be mock-testable offline; CI must never contact vendors.
- Any later cloud TTS integration must be behind a backend/proxy boundary. Never ship provider credentials in the client. Keep local Apple speech as a fallback.
- Never embed vendor API keys, private tokens, or secrets in the app, repository, build settings, logs or screenshots. Read local credentials only from environment variables when a later task is explicitly authorized.
- Do not add accounts, social features, ads, a bookstore, recommendations, analytics, or subscriptions in this MVP unless a later task explicitly authorizes them.
- Accessibility, VoiceOver labels, Dynamic Type, and safe handling of imported files matter.

## Engineering
- Prefer simple native frameworks and minimal dependencies.
- Keep EPUB parsing, plain-text decoding, reading-position persistence, speech synthesis, and audio playback as separate components.
- Handle long books without loading the entire parsed book into a single giant UI view.
- Test import errors, malformed files, large text, chapter boundaries, playback interruption/resume, and persistence.
- Never claim a feature works unless it is implemented and tested.