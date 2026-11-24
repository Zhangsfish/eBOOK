# eBOOK device preparation — 2026-11-24

State: INTERNAL_BETA_INSTALLED / OWNER_REQUESTED_UI_REFINEMENT. PR #5 remains draft.
The owner installed/opened `0.1.0 (35.1)`; remaining physical checks are separate.

- Base: `adc9f340a2ff427b30cddce33ad8a4d9efdac55a` (merged S00).
- S01 remains frozen at `3bfb4429fe7a42e50df62f4857bcb9909bf00ab3`, PR #4.
- Installed35.1 kept app Swift sources unchanged. The owner now explicitly asks
  to show speech controls only when needed: ReaderView moves its bottom player
  into an on-demand sheet with a toolbar entry and a Close action that does not
  stop speech. Decoder/parser/persistence/speech engine and core tests stay unchanged.
- Package-only changes: unique eBOOK identifier, original icon, version/build
  metadata, export-compliance declaration and iPad orientation metadata.
- Uploaded reader source: `1e556ae1622b4d56fa3c0c9e05ca0a14877073ac`.
- Real iPhone archive passed; Xcode26 rerun 45325097146 is pending at that SHA.
- Export/upload succeeded, Apple VALID / Internal Only / Ready to Test read back;
  owner reported successful iPhone installation and launch. Details below.
- Owner completed official Apple login; eBOOK's explicit Bundle ID and app record
  `6838578846` were created/read back in the UI. Initial TestFlight had no builds;
  current Internal Only build is `0.1.0 (35.1)`.
- Isolated existing-signing-repository helper `2444af3cdcbb0bf47c3993719fe987084809179e`
  passed prepare-only run 45324168773: real Swift typecheck and unsigned archive,
  no Apple credential environment. No Lecture Asset runtime/release changes.
- Physical background/call/Bluetooth, memory and accessibility checks: NOT_RUN.

First attempt: `615ea7f82a134b3dba33af55ebeb5c241be0e7ee`, Actions
https://github.com/Zhangsfish/eBOOK/actions/runs/45321224169 .
The real arm64 iPhone Release archive and package metadata passed with Xcode
26.6 (17F113), iOS SDK 26.5, macOS 26.7.2 arm64; package `0.1.0 (1.1)`.
Unsigned IPA SHA-256:
`b686439deac78acf2b97570d72891371d9115c8124c8099132c84f6504c2242d`.
No books/keys/profile were bundled. It is unsigned and cannot be installed.
The job then failed during the fresh iPhone 17 Pro simulator's system migration:
`simctl bootstatus` exceeded 300 seconds. App tests had not started. This is not
a passing simulator run. The next attempt retains a 300-second default for the
original CI and uses a bounded 900-second cold-boot wait for this Xcode 26 job,
with migration output saved to a separate log.

Second attempt: `424aa49be067880d73030860c32af19316db9f6c`, Actions
https://github.com/Zhangsfish/eBOOK/actions/runs/45322210390 .
The extended cold boot completed in about six minutes. Real Debug test build,
arm64 Release archive and Release simulator build passed. XCTest: **25/26 pass,
one native Files import UI failure, zero skips** on iPhone 17 Pro / iOS 26.5
(23F77). The long-book UI test including chapter 624/typography/relaunch passed.
The native picker remained open after its thumbnail-coordinate tap; its AX log
shows a translucent navigation overlay covering the top of that cell. A fallback
to the visible filename is added to the UI test; it still must import both real
Files-selected TXT/EPUB and assert two library books. Until the rerun succeeds,
do not classify this as a passing suite or a proven test-only issue.

## Successful original baseline / current rerun

[45322254825](https://github.com/Zhangsfish/eBOOK/actions/runs/45322254825), source
`424aa49be067880d73030860c32af19316db9f6c`: **26/26 pass, zero failures/skips**,
real Debug test build and Release simulator build. Xcode16.4 (16F6), SDK18.5,
macOS15.7.9 x86_64; iPhone16Pro / iOS18.5 (22F77).

The 2,301,482-character original fixture exercised chapter624, typography and
relaunch. Render metadata passed:256 samples,two process sessions,1,875 blocks,
furthest block1,869,at most12 window blocks/1,599 rendered UTF-16 units/two visible
cells; observed process peak RSS272,515,072 bytes. The unchanged metrics checker
also passed against the failed iOS26 run's unmodified long-reader telemetry
(395,952,128-byte peak), with separate local derived-data provenance. That does
not make its whole suite PASS or establish physical-device memory.

Third full Xcode26 attempt:
https://github.com/Zhangsfish/eBOOK/actions/runs/45325097146 , reader source
`1e556ae1622b4d56fa3c0c9e05ca0a14877073ac`: **25/26 pass,1 native Files UI failure,
zero skips**. The visible-filename fallback did not resolve the failure. The
actual picker screenshots show valid/readable files with generated thumbnails
but no selection; the earlier overlay explanation is unproven. The next test uses
the system's List view and an actual file row, retaining native selection and the
final imported-book assertions. No test-import shortcut or skipped assertion.

Owner installed35.1 and reported private TXT import/read works well, then requested
the on-demand panel. This does not establish EPUB, all encodings, chapter navigation,
restore, background endurance, memory or accessibility. No private book body was
requested or recorded. The next beta needs new code/build evidence for this UI change.

## Actual internal installation

- Existing-repository helper branch `codex/ebook-device-installation`, code
  `68ec0136774cb147004887ee79e0c1d099c41c01`, pins reader 1e556ae. No Lecture Asset
  runtime/default branch/release change or reupload.
- [Upload/status 45325301937](https://github.com/Zhangsfish/lecture-asset/actions/runs/45325301937)
  succeeded: unsigned archive/metadata verified04:18:18 UTC; export/upload accepted
  04:19:46 UTC; Apple processing **VALID**04:21:23 UTC.
- Official UI readback: eBOOK Reader Lab, `com.zhangsfish.ebook`, `0.1.0 (35.1)`,
  **Internal** badge and **Ready to Test**. The home-screen app name is eBOOK.
- Owner iPhone group has one manually added build and one existing owner tester,
  invited at12:24 Asia/Shanghai. Automatic distribution was explicitly unchecked.
  No external tester/public link. Private tester identifiers stay out of GitHub.
- The owner answered the exact-build installation question with “已安装，能打开”.
  This is **PASS_OWNER_REPORTED**, not an automated physical-device test. Device
  model/iOS version have not yet been supplied.
- Xcode's direct export/upload did **not retain an IPA**. The signed IPA SHA/CDHash
  and independent inspection of its final signed profile are unavailable. Do not
  invent them or reupload solely to obtain them. The first unsigned IPA digest
  above is for615ea7f/version1.1, not the installed signed35.1.

TXT/EPUB import/TOC and locked10-minute speech await owner feedback. Reading and
listening restoration, calls/headphones/Bluetooth, actual device memory profiling,
iOS17 runtime and manual accessibility remain NOT_RUN until observed. See the
checklist and TEST_RESULTS.json; do not infer device success from simulator data.

Nine valid original synthetic inputs plus Chinese instructions are packaged in
the ignored local test ZIP. No test book is in the app. Apple speech is the only
phone provider; S01's cloud vendors remain offline and unintegrated.

The existing Lecture Asset public repository has a working automatic distribution
export/TestFlight pipeline and three encrypted App Store Connect secrets.
The eBOOK repository has no Apple secrets. GitHub secret values cannot be read or
copied back out. No password/key or device identifier is requested in chat.

Original S00 excluded TestFlight within that development task. The owner's later
request to install/test on the iPhone authorizes this separate internal-TestFlight
follow-up and reuse of the existing signing pipeline. The owner completes Apple
login/verification in the official UI. No App Review or public release is included.

Local Windows checks use the existing Python 3.11 environment. No tools installed.
The icon was drawn locally with existing Pillow 11.1.0, using original geometry.
No copyrighted book, cloud TTS request, paid CI or new paid service is used.
