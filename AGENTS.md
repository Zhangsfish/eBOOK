# Agent Instructions

## Active TTS workstreams (owner direction, 2026-11-25)
- Read `docs/TTS_WORKSTREAMS.md` before TTS work. The owner has explicitly split two conversations in this repository.
- `codex/s02b-suxin-ios-integration`: APPROVED_FOR_OWNER_BETA on 2026-11-27. App source6469489062e6b91d743295cc2c08320334dbbf17 is reviewed; freeze feature work. The sole READY task is `tasks/S02B_OWNER_PHONE_TRIAL.md`: complete existing owner-only signing/TestFlight delivery, then WAITING_OWNER_FEEDBACK. No further App feature changes, generic optimization or duplicate full CI before feedback.
- The owner also authorized `tasks/S02B_READING_MODES.md` after the repair implementation: bookshelf selects vertical/horizontal mode and its own appearance. Existing in-book reader theme remains adjustable and independent. Both changes stay in PR12 and require current-code regression/review.
- Independent review2026-11-27: R1–R3 CLOSED, actual18.5/26.5 each55/55 and original device entry verified. See `reports/S02B/REVIEW_AND_OWNER_TRIAL_20261127.md`. The previous wait-for-code-review gate is satisfied for the pinned reader; the bounded signing-bridge changes/internal upload listed in the sole READY task may proceed without another same-scope permission request. New phone build is not yet available; do not claim otherwise.
- `codex/s02a4-teacher-student-tts`: READY for independent later-version model research; use `tasks/S02A4_TEACHER_STUDENT_TTS.md`. It must not edit the first-release App, signing/version or deployment workflow.
- Follow the task matching the active branch. First-release Suxin delivery does not depend on training. Historical S00-only / no-S02B restrictions do not cancel this new explicit owner authorization. Keep independent review, local-book privacy and honest device evidence.

## Source of truth and collaboration
- GitHub is the durable source of truth. Read this file, `STATUS.md`, the product/technical specs, and the currently authorized task before editing.
- Execute only the task explicitly marked READY. Do not infer permission to start later phases.
- Work on a task-specific `codex/*` branch. Never push implementation directly to `main`.
- Open a PR to `main`, attach real build/test evidence, report the exact tested HEAD SHA, then stop at `READY_FOR_AUDIT`. Do not merge, mark the task PASS, or start another phase.
- Do not fabricate simulator, device, build, test, or App Store results. If macOS/Xcode or signing is unavailable, state `BLOCKED_ENV` and provide the exact blocker.
- Preserve unrelated user changes and existing repository history.

## Product constraints
- iOS only; native SwiftUI. This is a deliberately narrow ebook reader, not a bookstore or social platform.
- Only import books selected by the user through the iOS document picker / Files. Initial supported formats: EPUB and TXT.
- Never scrape, download, commit, push, bundle, or redistribute unauthorized copies of copyrighted books. Do not bypass DRM or platform restrictions.
- Do not place complete copyrighted novels or user-imported commercial ebooks in this repository, even if it is private. Do not include them in CI artifacts, screenshots, issue comments, PR descriptions, crash reports, or logs.
- Automated tests must use original synthetic text or public-domain text with verified status. Use `docs/TEST_DATA.md` and `scripts/generate_long_gb18030_fixture.py` for large Chinese TXT performance fixtures.
- The app's normal user-selected file import must remain local. Do not upload imported book contents automatically.
- S00 uses local `AVSpeechSynthesizer` only. Do not send book text to a cloud TTS provider or other external service in this phase.
- TTS must be provider-agnostic. Never embed vendor API keys, private tokens, or secrets in the app, repository, build settings, or screenshots.
- Cloud TTS must be designed behind a backend/proxy boundary in a later authorized phase; do not ship provider credentials in the client. Keep local Apple speech as a fallback.
- Do not add accounts, social features, ads, a bookstore, recommendations, analytics, or subscriptions in this MVP unless a later task explicitly authorizes them.
- Accessibility, VoiceOver labels, Dynamic Type, and safe handling of imported files matter.

## Engineering
- Prefer simple native frameworks and minimal dependencies.
- Keep EPUB parsing, plain-text decoding, reading-position persistence, speech synthesis, and audio playback as separate components.
- Handle long books without loading the entire parsed book into a single giant UI view.
- Test import errors, malformed files, large text, chapter boundaries, playback interruption/resume, and persistence.
- Never claim a feature works unless it is implemented and tested.
