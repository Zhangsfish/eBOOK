# S00 — Reader Foundation (READY)

## Goal
Create the first runnable native iOS application foundation for eBOOK. Deliver a thin but real vertical slice: import a local EPUB/TXT file, read it with basic comfort controls, and listen using a working local speech baseline. Establish clean seams for premium cloud TTS without integrating paid services or embedding secrets.

## Read first
1. `AGENTS.md`
2. `STATUS.md`
3. `docs/PRODUCT_SPEC.md`
4. `docs/TECHNICAL_PLAN.md`
5. This task

## Scope
1. Create a clean SwiftUI iOS app project with a sensible deployment target and bundle identifier placeholder.
2. Implement local file import for EPUB and TXT using the system document picker. Copy imported files into app-owned storage safely.
3. Implement library list and book detail/open flow.
4. Parse EPUB title/author/chapters/TOC and render chapter content. For TXT, decode UTF-8 and UTF-16 where practical, split paragraphs, and offer basic navigation without inventing a semantic TOC.
5. Implement reading UI with font-size controls, line spacing, at least light / warm eye-comfort / dark themes, and persisted reading position.
6. Implement listening UI with play/pause/resume, chapter/paragraph progression, playback speed, and persisted listening position. Use AVSpeechSynthesizer as the first local functional adapter.
7. Configure spoken-audio background playback and handle audio interruptions / route changes / remote controls to the extent practical in this milestone.
8. Define a provider protocol and a clearly isolated placeholder for future cloud TTS adapters. No real API calls, no API keys, no backend deployment, and no paid usage.
9. Add synthetic Chinese fixture content (original text written for this project) covering multiple chapters, dialogue, punctuation, and paragraph breaks.
10. Add unit tests for import/parsing, TXT decoding, progress persistence, and text chunking. Add a README with build/run instructions and known limitations.

## Out of scope
- Do not download or bundle `绝境黑夜` or any other copyrighted book.
- Do not scrape Qidian, Shuqi, or other reading sites; do not bypass DRM.
- Do not implement cloud TTS vendors yet. Do not ask for or create secrets.
- Do not add accounts, cloud sync, bookstore, search/discovery, subscriptions, ads, analytics, or social features.
- Do not submit to App Store or TestFlight in this task.

## Acceptance criteria
- Project opens and builds in Xcode on a supported macOS environment.
- A user can import a valid EPUB and a valid TXT through Files and see them in the library.
- EPUB TOC/chapter navigation works for the included fixture; TXT is readable with stable paragraph layout.
- User can change font size, line spacing, and reading theme; settings and position survive app relaunch.
- User can start/pause/resume speech and progress advances through text; playback speed works.
- App has a working local speech fallback and a provider abstraction suitable for a future cloud TTS implementation.
- Tests actually run and results are reported; no fabricated test claims.
- No copyrighted full-text material, embedded credentials, or unauthorized content acquisition.

## Deliverables
- iOS project and source code.
- Synthetic fixture(s) and automated tests.
- Updated README, plus `reports/S00_DELIVERY.md` and `reports/S00_TEST_RESULTS.md` documenting implementation, exact build/test commands, actual results, limitations, and any owner actions.
- Pull request to `main` with exact tested HEAD SHA.

## Stop condition
After opening the PR and updating reports, set the task state to `READY_FOR_AUDIT` in the PR description/report and STOP. Do not merge or start S01. If the environment lacks macOS/Xcode, stop with `BLOCKED_ENV` and provide concrete evidence plus the most useful partial deliverable.