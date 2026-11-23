# S00 test results

State: **READY_FOR_AUDIT**. Real simulator tests passed; physical-device checks
listed below remain **NOT_RUN**. Independent acceptance is pending.

## Exact revision and environment

- Complete-suite evidence snapshot SHA: `5714f20c7fce3956b282d04ef10e47d11025b5ae`.
- [Actions run 45180857046](https://github.com/Zhangsfish/eBOOK/actions/runs/45180857046), conclusion **success**.
- Standard public `macos-15-intel` runner; macOS 15.7.9 x86_64.
- Xcode 16.4, build 16F6; iOS Simulator SDK 18.5.
- iPhone 16 Pro simulator, iOS 18.5 (22F77); unsigned simulator builds.
- Starting branch: `ab0aa0079c74f0de17a4a7bc7facd2cbbc9532ea`.
- Later commits align chapter tops, correct a speech-test offset and wait for
  Files Browse on fresh simulators. The final delivery HEAD and its own full
  run are linked in the PR; all snapshot files here identify the SHA above.

## Actual commands and outcomes

Windows host 10.0.26200 has no Xcode/Swift/xcrun. The `python3` Windows Store
alias did not execute the generator; the existing Python ran it successfully:

```powershell
& 'C:\conda_envs\myenv\python.exe' scripts/generate_long_gb18030_fixture.py
& 'C:\conda_envs\myenv\python.exe' scripts/generate_xcode_project.py --check
& 'C:\conda_envs\myenv\python.exe' scripts/check_source_safety.py
git diff --check
```

The original checkout's Git state was inspected first and its unrelated files
left untouched. A separate eBOOK checkout synchronized the existing branch.
No local package/tool installation was needed.

The successful macOS job executed:

```bash
python3 scripts/generate_long_gb18030_fixture.py
python3 scripts/generate_xcode_project.py --check
bash scripts/ci_xcode.sh
```

That checked-in script boots an installed iPhone simulator, installs the Debug
app and seeds only original fixtures into that simulator's Documents. The
effective Xcode commands (ID is captured in environment.json) are:

```bash
xcodebuild -project eBOOK.xcodeproj -scheme eBOOK -destination "id=$SIMULATOR_ID" -derivedDataPath build/DerivedData CODE_SIGNING_ALLOWED=NO -configuration Debug build-for-testing
xcodebuild -project eBOOK.xcodeproj -scheme eBOOK -destination "id=$SIMULATOR_ID" -derivedDataPath build/DerivedData CODE_SIGNING_ALLOWED=NO -configuration Debug test-without-building -parallel-testing-enabled NO -resultBundlePath build/Test.xcresult
python3 scripts/check_reader_metrics.py
xcodebuild -project eBOOK.xcodeproj -scheme eBOOK -configuration Release -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' -derivedDataPath build/Release CODE_SIGNING_ALLOWED=NO build
```

| Check | Actual result |
|---|---|
| Deterministic Xcode project | PASS, generated project matches tracked project |
| Debug build-for-testing | PASS, `TEST BUILD SUCCEEDED` |
| ReaderCoreTests | PASS, 14 tests |
| SpeechControllerTests | PASS, 8 tests including real Apple speech callback smoke test |
| ReaderUITests | PASS, 4 tests |
| Total | **26 passed / 26, 0 failed, 0 skipped** |
| Reader metadata gate | PASS, bounds/scrolling/late chapter/relaunch/RSS assertions |
| Release iOS Simulator build | PASS, `BUILD SUCCEEDED` |
| Repository content checks | PASS within documented pattern/size/provenance scope |

Xcode emits standard XCTest binary-stripping and unused AppIntents metadata
warnings. They do not prevent the successful builds. Runtime voice-asset console
messages are not proof of failed speech: the actual range/finish test passed.

## What the 26 tests exercise

- Strict UTF-8/BOM, UTF-16 LE/BE with/without BOM or explicit hint, GBK and
  four-byte GB18030 supplementary characters; malformed/truncated/binary/lossy
  data and wrong-hint errors.
- Conservative mixed heading patterns and fallback, scalar-safe UTF-16 chunk
  offsets, 12-block window movement in both directions, storage rollback,
  removal preserving the original, preferences and separate positions.
- EPUB 3 metadata/spine/nav/fragments/images and EPUB 2 NCX; malformed spine,
  traversal/entities, truncation, CRC and declared expansion limits.
- Large fixture import/navigation/bounded reads/reopen and process peak RSS.
- Real controller with a fake provider for pause/resume, cancellation, seeking,
  speed/failure, interruption/route policies and corruption protection. A
  separate AVSpeechSynthesizer test observes real word-range and finish events.
- UI: EPUB opening/TOC/controls; actual **system Files TXT and EPUB selection**
  resulting in two shelf items, without the DEBUG fixture-import flag; picker
  cancellation; long-reader scrolling/late TOC/font/night/relaunch assertions.

The long UI flow uses a DEBUG fixture-seeding shortcut to avoid typing a large
file selection repeatedly; the separate Files test uses the production picker
and production import path. Neither is claimed as a physical-device test.

## Long-book results

Input: 2,301,482 Unicode characters including CRLF, 73,176 lines, 4,236,594 bytes,
624 chapters plus afterword. SHA-256
`162f7549408043c610a49b11b68a80aff07587447e72e478d948a18fc2c483e8`.
CRLF-normalized length is 2,228,307 characters. The generated GB18030 file uses
the shared GBK repertoire, so automatic detection truthfully returns GBK; the
small supplementary fixture separately exercises actual four-byte GB18030.

| Measurement | Observed |
|---|---|
| Unit-test import elapsed | 10.003 s (90 s test ceiling) |
| Indexed blocks / TOC entries | 1,875 / 625 |
| Maximum stored text block | 1,600 UTF-16 units |
| Unit process peak increase | 24.80 MiB (<180 MiB test ceiling) |
| UI metadata samples / process sessions | 256 / 2 |
| Distinct top blocks / furthest | 9 / 1869 |
| Maximum reader window / visible cells | 12 / 2 |
| Maximum rendered label | 1599 UTF-16 units |
| Maximum process peak RSS | 266.18 MiB (<768 MiB CI guard) |

The UI test performs 42 swipes and confirms early window movement, selects TOC
chapter 624, asserts absolute block 1869 (footer 1870/1875), changes font and
night mode, and asserts the same block after process termination/relaunch.
RSS is macOS getrusage process high-water memory, not the current heap, an
Instruments allocation trace or a physical-device measurement. Finite scrolling
and explicit row/read bounds do not establish unlimited-duration endurance.

## Failure history retained honestly

| Run / commit | Outcome before the final fix |
|---|---|
| 45168180629 / 7555fdd; 45168328594 / 4116063 | Failed project-generation portability check; source sorting/IDs fixed |
| 45168518608 / 9d55978 | Debug test build and 17 unit tests passed; cancelled before full UI/Release completion |
| 45169725445 / 742492d | Debug/Release builds passed; 21/22 tests, long-reader accessibility timeout |
| 45172278240 / c511704 | Builds passed; 21/23 tests, Files hit target and long UI failures |
| 45173753132 / db82759 | Builds passed; 23/24 tests; bounded window fixed timeout, but metadata exposed font anchor drift despite weak original assertion |
| 45176234060 / d0f73d4 | Builds passed; 25/26 tests; old Files filename tap did not select the thumbnail |
| 45178103965 / c58976e | Strict long-anchor test passed, 25/26 total; cancelled obsolete run; old Files test still failed |
| 45180857046 / 5714f20 | Full success, 26/26, 0 skips; Files thumbnail selection corrected |
| 45183998913 / 2d46391 | Builds passed, 25/26, 0 skips; strict long-reader test passed; Files started at empty Recents and the test skipped a not-yet-loaded Browse tab |

The final reader measures bounded native row heights to preserve the absolute
anchor. The Files test now taps the observed thumbnail hit area and asserts
both imported books. `da6295a` also waits for the remote Browse tab and recognizes
the observed unspaced Chinese iPhone location label before entering the app
folder. The final delivery's complete run is recorded in the PR. Assertions
were strengthened, not removed.

## NOT_RUN and remaining limits

Signed device build/install; iOS 17 runtime; real screen lock/background
endurance/calls/headset/Bluetooth/remote-command delivery; human listening
quality; manual VoiceOver and extreme Dynamic Type review; broad EPUB corpus,
CSS/fixed-layout/SVG fidelity; Instruments/device memory and full-book soak.
No App Store/TestFlight submission, paid service or cloud synthesis was run.

See [delivery limits](S00_DELIVERY.md), the raw small logs/JSON in
[evidence](S00/evidence/PROVENANCE.json) and unmodified original-fixture PNGs.
CI artifacts omit imported books, app bundles, raw xcresult/video and secrets.
Only original synthetic text/images appear in screenshots. Stage acceptance
remains with the independent reviewer.
