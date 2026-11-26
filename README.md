# eBOOK — iOS Reader

A focused iOS ebook reader for user-imported EPUB/TXT books, with a calm, high-quality Mandarin text-to-speech experience.

## Current work: S02B local Suxin speech

The selected Suxin-Light voice is implemented and **READY_FOR_AUDIT** on
`codex/s02b-suxin-ios-integration` / [PR #12](https://github.com/Zhangsfish/eBOOK/pull/12).
See [the task](tasks/S02B_SUXIN_IOS_INTEGRATION.md) and
[delivery evidence](reports/S02B_SUXIN_IOS_INTEGRATION.md). Desktop, simulator,
device and TestFlight states are reported separately. A successful CI build is
not a new installable phone release. The later model-training work in PR #11
does not block this implementation.

Native frontend/model/PCM checks pass on iOS18.5 and26.5; final full suites each
report41/42, with system Files selection still failing. Both unsigned arm64
Release archives pass. Physical-phone latency/long listening, complete distribution
materials and a new TestFlight update remain pending; this is not release acceptance.

## Build and run

Requires a Mac with Xcode 16.4 or later and an iOS 17+ simulator/device. There
is no XcodeGen dependency. The App now uses a revision-pinned ONNX Runtime
SPM binary and verified local Suxin/model/dictionary resources. Preparation
downloads data only, installs no Python package and makes no TTS API call.
Models, dictionaries and generated audio stay under Git-ignored directories.
The device-preparation branch uses `com.zhangsfish.ebook`; select your own team
for local device signing. Existing unsigned CI packages require signing and cannot
be installed directly. Apple account setup/internal distribution is a separate
follow-up; see `tasks/S00_DEVICE_VALIDATION.md` and `reports/S00/device-01/`.

```bash
python3 scripts/generate_long_gb18030_fixture.py
python3 tools/suxin/scripts/prepare_resources.py
python3 tools/suxin/scripts/inspect_runtime.py
python3 scripts/generate_xcode_project.py --check
open eBOOK.xcodeproj
```

Choose the shared **eBOOK** scheme and an iPhone simulator, then Run. Product →
Test runs unit and UI tests. For the complete reproducible CI flow:

```bash
python3 tools/suxin/scripts/ci_integration.py --scope all
```

The script uses installed Xcode (prefers `/Applications/Xcode_16.4.app` when
available), boots an installed simulator, builds without signing, seeds original
test files into App Documents, runs unit/UI tests and archives an unsigned arm64
Release App. The `integration` scope runs twelve native frontend, real-graph,
PCM-playback and state/cache test methods; `frontend` checks the author oracle
alone; `picker` performs actual TXT/EPUB selection and cancellation (two methods).
Only allowlisted JSON/log evidence and bounded original-fixture UI failure
screenshots are uploaded by S02B CI. Model-containing
App/IPA/WAV files are not public artifacts. No tool installation or paid API.

`scripts/generate_xcode_project.py` recreates the checked-in project with Python
stdlib; use `--check` to verify it matches the sources. Recreate small original
fixtures with `python3 scripts/generate_small_fixtures.py`.

## Use

The reader opens with only the text and a subtle **⋯** in the lower-right corner.
The entry has no white background/border and adapts to light, warm and dark themes.
Tap it to open back, TOC, typography, speech and progress controls; close the panel
to keep reading. Body taps and scrolling do not open it. Controls overlay the text
without resizing the reading viewport. The 44-point entry remains accessible.
Open 朗读 from that panel for playback; 收起 keeps ongoing speech running.
Voice and rate remain in 阅读设置. Returning from these sheets hides the controls.

Tap **导入书籍** and choose a local TXT or EPUB through Files. TXT defaults to
BOM/strict UTF-8/legacy-encoding detection. Use the **TXT 编码** menu before import
for ambiguous BOM-less UTF-16 or legacy files. A byte stream can be valid in
multiple encodings; automatic detection cannot prove the author's intent.

Open a book, scroll, use the searchable TOC, or drag reading progress. Reading
settings include Dynamic Type-aware font size, line spacing and light/warm/dark
themes. TXT TOCs are explicitly labeled heuristic; low-confidence files retain
continuous reading with progress navigation.

Listening has separate saved progress. Use play/pause, previous/next text block
or chapter, voice selection and rate. **从当前阅读位置开始朗读** explicitly moves
listening to the reading anchor. Apple speech stays local; install/download a
Mandarin voice through iOS accessibility settings if none is present. Choose
**苏心 · 离线中文** in 阅读设置 for native Mandarin synthesis and its separate
0.5–2.0× rate. English or unsupported-character spans explicitly use Apple speech;
the playback panel displays that fallback. Model/resource failures show an error
and let the user select system speech. No book
body is sent by this application to a cloud TTS service.

## Storage, safety and limits

- User-selected files are security-scoped, copied and parsed off the main actor.
  Failed imports leave no partial book. Removing a book deletes only its app copy.
- Text is indexed in `content.utf8` and read by byte range in blocks of at most
  1,600 UTF-16 units. A moving window of at most 12 native rows bounds both
  rendering and the accessibility tree; scrolling shifts that window while
  preserving the absolute reading anchor. Import may
  transiently decode the bounded source file; the reader does not keep the full
  novel in a Text view or decoded-text cache.
- TXT limit: 32 MiB. EPUB compressed limit: 64 MiB, total declared expansion:
  96 MiB, maximum 4,096 entries; XML/image resource limit: 8 MiB.
  Raster illustrations are checked before decoding (40 MP / 16,384 pixels per
  dimension) and displayed as thumbnails of at most 1,600 pixels.
- EPUB 2 NCX and EPUB 3 nav/spine, fragment navigation, inline text and local
  PNG/JPEG/GIF illustrations are supported. Rendering is reflowed native text,
  not CSS/browser layout; tables, complex typography, SVG, audio/video and
  fixed-layout books have reduced fidelity. Encrypted resources/DRM, ZIP64,
  multi-volume archives, traversal, entities and unsupported spine formats are
  rejected. There is no general ZIP import.
- Reading saves a text-block/fraction anchor; restoring after a typography or
  Dynamic Type change is approximate within that block. Listening saves UTF-16
  position. Apple may repeat a word; Suxin commits completed short audio clauses
  only, so process termination can repeat the current clause. Pausing/resuming
  within the same process retains the audio player's frame position.
- Audio background mode, spoken-audio session, interruption/route handling and
  lock-screen play/pause/chapter commands are implemented. Physical lock-screen,
  calls and Bluetooth behavior require device validation; simulator state tests
  cannot establish those results. Audio has no trustworthy precomputed duration,
  so the lock-screen time-seek command is disabled; text/chapter seeking is in-app.
- Suxin uses one background ORT session, a queue of at most three PCM buffers,
  at most two prefetched clauses from one next text window, and a 64 MiB
  App-private cache. Identities contain model/frontend hashes, text digest, voice
  and rate. Cache files contain derived book audio and are excluded from backup;
  deleting App data removes them. There is no cloud provider or vendor credential.
- Resource hashes and author/pypinyin license declarations are bundled. Full
  model/data/static-runtime distribution clearance is incomplete; see
  [the notice status](tools/suxin/NOTICE.md). This is separate from executing local
  tests and remains a gate for a new internal distribution.

## Evidence and review

See `STATUS.md`, `reports/S00_DELIVERY.md`, `reports/S00_TEST_RESULTS.md` and the
S00 native iOS Actions run. Build/test evidence is tied to the run's exact commit.
Never infer device success from simulator results. S02B requires independent
audit before a new internal TestFlight build; do not self-merge.

## Product boundary

- iOS only; native SwiftUI application.
- User-imported books only. No built-in catalog, scraping, redistribution, or bundled copyrighted books.
- Initial formats: EPUB and TXT, including common Chinese encodings.
- Reading and listening are the only primary workflows.

## Codex handoff

The currently authorized task is [S02B — Suxin iOS integration](tasks/S02B_SUXIN_IOS_INTEGRATION.md).
Use [the current handoff](tasks/CODEX_HANDOFF_S02B.md) and [workstream boundaries](docs/TTS_WORKSTREAMS.md).
S00 reports remain historical evidence for the reader baseline.

## Test data

Read [docs/TEST_DATA.md](docs/TEST_DATA.md). Generate the large original GB18030 test book locally with:

```bash
python3 scripts/generate_long_gb18030_fixture.py
```

The generated file is written under `.local-test-data/`, which is ignored by Git. Do not commit full copyrighted novels or user-imported commercial books.
