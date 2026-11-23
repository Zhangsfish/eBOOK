# S00 delivery

State: **READY_FOR_AUDIT**. Issue [#1](https://github.com/Zhangsfish/eBOOK/issues/1),
branch `codex/s00-reader-foundation`, target `main`. S00 only; independent review
is pending. No merge or S01 work is authorized by this handoff.

## Revision and runnable result

- Starting branch commit: `ab0aa0079c74f0de17a4a7bc7facd2cbbc9532ea`.
- Main/PR merge base: `a8dbfec304dae3a24ee204230e9d723c036ac235`.
- Complete-suite evidence snapshot: `5714f20c7fce3956b282d04ef10e47d11025b5ae`.
- [Successful real Xcode run](https://github.com/Zhangsfish/eBOOK/actions/runs/45180857046): Debug test build, **26/26 tests,
  0 failures, 0 skips**, reader metadata gate, Release simulator build.
- This report and evidence follow that snapshot. Later changes align the chapter
  top, correct a speech-test string length, and wait for Files Browse on a fresh
  simulator (`2d46391` / `da6295a`). The PR records the final delivery HEAD and
  its own complete Actions result; do not substitute the snapshot for that run.

The app is a native SwiftUI iOS 17+ reader with local EPUB/TXT import, a book
shelf, searchable TOC, persistent reading/listening positions, font size, line
spacing and light/warm/dark themes. `eBOOK.xcodeproj` includes a shared eBOOK
scheme and no runtime third-party dependencies. Open it in Xcode and choose an
iPhone simulator. [README](../README.md) contains build/run instructions.

## Delivered behavior

| Area | Implementation and evidence |
|---|---|
| Files import | System fileImporter, security-scoped and coordinated reads, bounded copy into app storage; actual TXT and EPUB picker imports pass a UI test without the DEBUG import shortcut |
| TXT | BOM-first strict UTF-8/UTF-16 LE/BE, legacy GBK/GB18030 validation and lossless decode; manual encoding selection for ambiguity; invalid input produces visible errors |
| EPUB | Defensive ZIP/CRC/size/path checks; OPF/spine, EPUB 3 nav and EPUB 2 NCX, fragments, inline text and local raster illustrations |
| Long reading | Disk byte-range blocks <=1,600 UTF-16 units; moving window <=12 native rows; measured row heights preserve absolute anchors through typography changes |
| TOC | Conservative mixed Chinese heading forms, numbered-heading confidence checks and readable continuous fallback; heuristic TXT TOCs are labeled |
| Persistence | Atomic Codable library state, independent reading block/fraction and listening block/UTF-16 positions; damaged library state blocks writes rather than overwriting it |
| Local speech | AVSpeechSynthesizer, <=280-unit sentence/paragraph chunks, voice/rate, pause/resume, paragraph/chapter seeking, saved progress; real Apple range/finish callback smoke test passes |
| Audio lifecycle | Spoken-audio session, background audio declaration, interruptions, headphone loss, Now Playing and remote play/pause/chapter commands; state tests pass, physical behavior remains NOT_RUN |
| Future TTS | Provider-neutral request/event/voice contracts and future audio-asset synthesis protocol; no cloud implementation, backend, API keys or paid model |

## Large synthetic book

The required generator produced **2,301,482 Unicode characters, 73,176 lines,
4,236,594 GB18030 bytes**, 624 chapters plus afterword. SHA-256:
`162f7549408043c610a49b11b68a80aff07587447e72e478d948a18fc2c483e8`.
The generated file stays in ignored `.local-test-data/`; only its generator,
small original fixtures, metadata and synthetic screenshots are committed.
The 4,439,158-byte commercial planning sample is not the synthetic fixture and
was not downloaded, imported, committed or used in CI.

Real simulator import: **10.003 s**, 1,875 indexed blocks, 625 TOC entries.
The UI test scrolls 42 times, navigates to chapter 624 (block 1869), changes font
and night theme, terminates and relaunches, and asserts that exact block remains.
Runtime samples cover two process sessions; peak process RSS **266.18 MiB**,
<=12 window rows, <=2 visible cells and <=1599 UTF-16 units per
rendered label. These are finite simulator measurements, not a device-wide
memory guarantee or a full-book endurance test.

## Known limits and remaining owner checks

- **NOT_RUN:** signed physical-device installation, screen-lock/background
  endurance, actual calls/interruption notifications, Bluetooth/headset remote
  controls, iOS 17 runtime, manual VoiceOver/Dynamic Type audit, and human voice
  naturalness assessment. No App Store/TestFlight action was taken.
- EPUB uses native reflowed text/raster images. CSS, tables, SVG, fixed layout,
  multimedia and complex typography have reduced fidelity or are unsupported.
  DRM/encrypted resources, ZIP64 and unsafe containers are rejected.
- BOM-less encoding can be ambiguous; explicit selection is available. Apple
  GB18030 decoding was validated against the supplied original fixtures, not
  every codec edition or a commercial-book corpus.
- TXT is capped at 32 MiB; EPUB at 64 MiB compressed / 96 MiB declared expanded.
  Import can transiently decode a bounded source; ongoing reading uses bounded
  disk reads. Raster resources are capped and downsampled before display.
- The block is preserved across font changes; the word within that block is
  approximate. Listening can repeat a word after a process kill. No fabricated
  audio duration/time-seek is exposed on the lock screen.
- `org.example.eBOOK` is a placeholder bundle ID. The owner chooses signing and
  a unique ID in a later device-validation step. S00 does not establish that
  Apple's baseline voice meets the final naturalness target.

## Safety and handoff

The unrelated `lecture_asset` checkout and its existing files were preserved;
eBOOK has a separate checkout. The existing remote branch/history was retained.
Following the owner's explicit instruction, eBOOK was made public after checking
its planning history for large content and credential patterns. CI uses the
standard public `macos-15-intel` runner, no paid/larger runner or new tool install.

No complete commercial novel, cloud synthesis, HTTP client, credentials, account,
analytics, subscription or release pipeline was added. Source-pattern checks
are documented in [source-safety.json](S00/evidence/source-safety.json); their
scope is limited and is not an independent security certification.

See [test results](S00_TEST_RESULTS.md) and
[evidence provenance](S00/evidence/PROVENANCE.json). **READY_FOR_AUDIT** requests
ChatGPT's independent review; it does not declare the stage audited or approved.
