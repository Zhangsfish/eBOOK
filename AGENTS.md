# Agent Instructions

## Active TTS workstreams (owner direction, 2026-11-25)
- Owner feedback2026-11-28 reopens the existing PR12 branch for `tasks/S02B_EPUB_COMPATIBILITY.md`: a supplied EPUB fails strict XML import while other readers open it. Diagnose privately, preserve all content and safety limits, use original CI fixtures only, and deliver the scoped fix through the existing direct internal phone-test path. Prior freeze text below does not block this reported core repair. No merge/public release/model work. Evidence: reports/S02B/epub-compatibility/.
- Latest delivery2026-11-27: **WAITING_OWNER_FEEDBACK**, internal **0.1.0(49.1)** available for reader-help changes. Exact compiled/tested reader1619c200ed7552be5687c4446240daefe676fb4c; actual18.5/26.5 each14/14, unsigned archives/6+2. Bridgeba2c441/run46017595137 returned AppleVALID/INTERNAL_ONLY, existing owner-group association andIN_BETA_TESTING at22:43:46Beijing. `reports/S02B/reader-help/PHONE_DELIVERY.md`. Owner explicitly requested direct internal testing without another web review for this scope. Stop edits/uploads and wait for phone feedback; no merge/public release. Earlier48.1/47.1 snapshots below remain history.
- Owner request 2026-11-27 reopens the existing PR12 branch for `tasks/S02B_READER_HELP.md`: bottom reader icon row/smaller progress slider, animated tutorial and bookshelf feedback. The owner explicitly authorizes focused real testing followed by direct existing internal-TestFlight delivery, without another web review. This scoped instruction supersedes freeze/audit gates below; no merge or public release. Reports: `reports/S02B/reader-help/`.
- Current delivery on 2026-11-27 is **WAITING_OWNER_FEEDBACK**. TestFlight **0.1.0 (48.1)** contains the approved copy and side-tap reader `03fe0237462f0af0595d47c455c7e5756d6cbd97`. Apple read back availability for the existing owner group in run `45991125943`. See `reports/S02B/owner-polish/PHONE_DELIVERY.md` for the bridge and actual archive evidence. The two prior focused suites each passed 10/10. Freeze development and release work pending actual 48.1 phone feedback. Historical 47.1 evidence refers to reader 6469489.
- Read `docs/TTS_WORKSTREAMS.md` before TTS work. The owner has explicitly split two conversations in this repository.
- `codex/s02b-suxin-ios-integration`: WAITING_OWNER_FEEDBACK on 2026-11-27. Reviewed App source6469489062e6b91d743295cc2c08320334dbbf17 is now available in internal TestFlight0.1.0（47.1）. `tasks/S02B_OWNER_PHONE_TRIAL.md` delivery is complete; see `reports/S02B/OWNER_PHONE_TRIAL.md`. Freeze feature work. No further App feature changes, generic optimization, upload or duplicate full CI before actual owner feedback.
- The owner also authorized `tasks/S02B_READING_MODES.md` after the repair implementation: bookshelf selects vertical/horizontal mode and its own appearance. Existing in-book reader theme remains adjustable and independent. Both changes stay in PR12 and require current-code regression/review.
- Independent review2026-11-27: R1–R3 CLOSED, actual18.5/26.5 each55/55 and original device entry verified. See `reports/S02B/REVIEW_AND_OWNER_TRIAL_20261127.md`. Actual47.1 is VALID/INTERNAL_ONLY, existing-group linked and IN_BETA_TESTING. Owner later reports voice good; detailed upgrade/latency/long listening/thermal results remain unreported. Preserve39.1/47.1. The new owner-polish task above is the only reopened work.
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
