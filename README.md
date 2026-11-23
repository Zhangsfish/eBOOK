# eBOOK — iOS Reader

A focused iOS ebook reader for user-imported EPUB/TXT books, with a calm, high-quality Mandarin text-to-speech experience.

## Build and run S00

Requires a Mac with Xcode 16.4 or later and an iOS 17+ simulator/device. There
are no runtime third-party packages and no XcodeGen dependency. The bundle ID
`org.example.eBOOK` is a placeholder; select your own team/unique identifier for
device signing. S00 does not configure a developer account or distribution.

```bash
python3 scripts/generate_long_gb18030_fixture.py
open eBOOK.xcodeproj
```

Choose the shared **eBOOK** scheme and an iPhone simulator, then Run. Product →
Test runs unit and UI tests. For the complete reproducible CI flow:

```bash
bash scripts/ci_xcode.sh
```

The script uses installed Xcode (prefers `/Applications/Xcode_16.4.app` when
available), boots an installed iPhone simulator, builds without signing, seeds
original test files into that simulator's app Documents, runs the tests, and
builds the Release simulator app. It does not install tools or call paid APIs.

`scripts/generate_xcode_project.py` recreates the checked-in project with Python
stdlib; use `--check` to verify it matches the sources. Recreate small original
fixtures with `python3 scripts/generate_small_fixtures.py`.

## Use

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
Mandarin voice through iOS accessibility settings if none is present. No book
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
  word/chunk position and can repeat a word after process termination.
- Audio background mode, spoken-audio session, interruption/route handling and
  lock-screen play/pause/chapter commands are implemented. Physical lock-screen,
  calls and Bluetooth behavior require device validation; simulator state tests
  cannot establish those results. Audio has no trustworthy precomputed duration,
  so the lock-screen time-seek command is disabled; text/chapter seeking is in-app.
- Future synthesis contracts are design seams only. No cloud provider, backend,
  audio-cache implementation or vendor credentials ship in S00.

## Evidence and review

See `STATUS.md`, `reports/S00_DELIVERY.md`, `reports/S00_TEST_RESULTS.md` and the
S00 native iOS Actions run. Build/test evidence is tied to the run's exact commit.
Never infer device success from simulator results. Do not merge or begin S01
until independent audit authorization.

## Product boundary

- iOS only; native SwiftUI application.
- User-imported books only. No built-in catalog, scraping, redistribution, or bundled copyrighted books.
- Initial formats: EPUB and TXT, including common Chinese encodings.
- Reading and listening are the only primary workflows.

## Codex handoff

The currently authorized task is [S00 — Reader Foundation](tasks/S00_READER_FOUNDATION.md). The copy-ready local Codex prompt is [tasks/CODEX_HANDOFF_S00.md](tasks/CODEX_HANDOFF_S00.md). Track progress in [GitHub Issue #1](https://github.com/Zhangsfish/eBOOK/issues/1).

## Test data

Read [docs/TEST_DATA.md](docs/TEST_DATA.md). Generate the large original GB18030 test book locally with:

```bash
python3 scripts/generate_long_gb18030_fixture.py
```

The generated file is written under `.local-test-data/`, which is ignored by Git. Do not commit full copyrighted novels or user-imported commercial books.
