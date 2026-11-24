# eBOOK immersive reading / owner iPhone delivery — 2026-11-24

State: READY_FOR_AUDIT. PR #5 stays draft with the actual iOS26.5 Files failure
explicitly gated for independent audit before merge. Internal38.1 is available;
owner installation/feedback is pending. S01 PR #4 remains frozen.

## Requested behavior and implementation

The owner confirmed that installed internal37.1 opens/closes speech controls and
keeps speaking after closing them. They then requested a quiet reading screen:
back, speech, TOC, font and progress should appear only when needed. Their latest
accepted option is one unobtrusive button, rather than a body-tap gesture.

ReaderView now shows text and a lower-right ellipsis only. The entry has no white
background/border, uses the selected theme's ink at60% opacity (full ink for the
system's increased contrast setting), and keeps a44-point touch target outside
the text. It opens one control panel with back, TOC, typography, speech and progress.
Body taps and scrolling do not reveal controls. The panel overlays a fixed text
viewport; opening/closing it does not change the text's available size. Entering
TOC, settings or speech hides the panel; closing those sheets returns to quiet
reading. Loading/error screens retain an explicit way back to the library.

Only ReaderView presentation changed. Parser, decoder, table virtualization,
storage, speech engine and core tests remain identical to merged S00. No private
book was acquired; the owner's private TXT reading report is non-textual evidence.

- Base main: `adc9f340a2ff427b30cddce33ad8a4d9efdac55a`.
- Current implementation: `326c5438794c76a8978c3cdb049b905ace703f66`.
- Branch / PR: `codex/s00-device-validation`, [#5](https://github.com/Zhangsfish/eBOOK/pull/5).
- Frozen S01: `3bfb4429fe7a42e50df62f4857bcb9909bf00ab3`, [#4](https://github.com/Zhangsfish/eBOOK/pull/4).
- eBOOK identity: `com.zhangsfish.ebook`, original icon, iOS17 minimum,
  version/build metadata, background audio and iPad orientation declarations.

## Current native validation

The local host is Windows without Xcode. Actual Apple builds run on standard
public GitHub-hosted macOS; no new package/tool or paid runner was installed.

| Source326c543 | Run | Actual state |
|---|---|---|
| Xcode26.6 / iOS26.5 | [45335480364](https://github.com/Zhangsfish/eBOOK/actions/runs/45335480364) | iPhone Release archive, Debug test build and Release simulator build PASS;25 passed /1 native Files UI failure /0 skipped |
| Xcode16.4 / iOS18.5 | [45335498953](https://github.com/Zhangsfish/eBOOK/actions/runs/45335498953) | Debug/Release simulator builds and26/26 tests PASS;0 failures /0 skipped |

The updated native UI cases require all reading chrome absent by default,
only the ellipsis opening controls, no activation by body taps/scrolling,
unchanged viewport/reading anchor across open/close, three theme screenshots,
speech access, chapter624/font/relaunch and an actual return to the library.
All changed reader UI cases passed on both runtimes. No native Files test was
skipped, injected or weakened. The repeated26.5 picker failure remains a failure;
the same real TXT/EPUB picker case passed on18.5.

The generated original GB18030 fixture has2,301,482 Unicode characters,73,176 lines,
624 chapters plus an afterword. Current layout telemetry passed the unchanged
checker:256 samples,2 process sessions,1,875 indexed blocks,furthest1,869,
<=2 visible cells /1,599 rendered UTF16 /12 window blocks. Peak simulator RSS:
410,910,720 bytes on26.5 (local replay against unmodified downloaded telemetry,
with raw/checker/derived hashes),270,245,888 bytes on18.5 (original passing CI).
Whole26.5 suite remains FAIL. Physical-device memory is NOT_RUN.
Project generator `--check` and `git diff --check` pass using existing Python3.11.11.

Actual26.5 environment: macOS26.7.2 arm64, Xcode26.6(17F113), SDK26.5,
iPhone17Pro simulator / iOS26.5(23F77).18.5: macOS15.7.9 x86_64,
Xcode16.4(16F6), SDK18.5, iPhone16Pro simulator / iOS18.5(22F77).
All3 theme PNGs and the expanded panel were visually inspected: quiet entry only
while reading, complete controls when requested. Loading/error return is compiled;
a forced file-load failure was not separately injected through the UI.

Unsigned arm64 package `0.1.0 (8.1)`, source326c543:
SHA256 `6764c1c15b66d5042cac50fec8ce5b6c92f92ef56119194adeb3e7b27666d852`.
No test book/key/profile is bundled. It is not installable and is distinct from
signed38.1; no signed digest is inferred from an unsigned digest.

## Actual internal beta installation

Previous installed/confirmed: `0.1.0 (37.1)`, reader
`ddff8c75ad0b95112386df7697b92cf464f1f28b`, helper
`64c7885a49f6e91ac92a56aa0722d2343939f978`,
[45330975786](https://github.com/Zhangsfish/lecture-asset/actions/runs/45330975786).
Real Swift/typecheck/archive preflight passed; upload accepted05:10:19UTC;
Apple VALID and existing owner-group relationship read back05:11:29UTC.
The official website also showed37.1, Internal, Testing. The owner answered
“everything normal” to the exact37.1 update/show/hide/ongoing-speech question.
This does not establish10-minute locked audio or other unasked phone scenarios.

The new ellipsis interface is available as **0.1.0 (38.1)**, source326c543, through
[upload45338159157](https://github.com/Zhangsfish/lecture-asset/actions/runs/45338159157).
Helper `f22b891bf885c17c288ad62961be4ee188e6fb89` pins that source in an isolated,
unmerged Lecture Asset branch. Swift preflight/archive/metadata passed; upload
accepted06:10:10UTC; Apple VALID and the exact existing owner-group relationship
read back06:11:48UTC (`EBOOK_OWNER_GROUP_ASSOCIATION_VERIFIED`). The owner was told
to update in place. This proves availability, not owner installation/behavior.
The helper uses
only pre-existing encrypted Apple credentials, which are not read/copied into
eBOOK. It verifies VALID / INTERNAL_ONLY and the existing internal/manual owner
group before adding only the build relationship and reading it back. One existing
owner tester remains; no external tester/public link is created. No Lecture Asset
runtime/default-branch change or reupload occurred.

Xcode direct uploads of35.1,37.1 and38.1 retained no signed IPA. Their signed IPA SHA,
CDHash and independent final-profile inspection are unavailable. Do not invent
them or substitute an unsigned package digest. New upload evidence must be read
back separately from owner installation and actual physical behavior.

## Earlier evidence retained

| Source | Run | Actual result |
|---|---|---|
| 615ea7f | [45321224169](https://github.com/Zhangsfish/eBOOK/actions/runs/45321224169) | arm64 archive PASS; simulator cold-boot timeout, app tests NOT_RUN |
| 424aa49 | [45322210390](https://github.com/Zhangsfish/eBOOK/actions/runs/45322210390) | Xcode26.6 builds PASS;25 passed /1 native Files UI failure /0 skipped |
| 424aa49 | [45322254825](https://github.com/Zhangsfish/eBOOK/actions/runs/45322254825) | Xcode16.4 Debug/Release and26/26 PASS,0 skipped |
| 1e556ae | [45325097146](https://github.com/Zhangsfish/eBOOK/actions/runs/45325097146) | Xcode26.6:25/26, same Files UI failure; filename fallback unsuccessful |
| ddff8c7 | [45328258860](https://github.com/Zhangsfish/eBOOK/actions/runs/45328258860) | archive/Debug/Release PASS;25/26, Files List-row failure; speech-panel UI PASS |
| ddff8c7 | [45328397297](https://github.com/Zhangsfish/lecture-asset/actions/runs/45328397297) | focused Files case FAIL: exactly1 test,0 passed /1 failed /0 skipped; no Apple credential environment |
| ddff8c7 | [45329155131](https://github.com/Zhangsfish/eBOOK/actions/runs/45329155131) | Debug/Release PASS;24/26; immediate sheet-absence assertion and30s real Apple speech callback timeout; Files/long-reader UI PASS |
| 39c13e3 | [45331753093](https://github.com/Zhangsfish/eBOOK/actions/runs/45331753093) | Xcode16.4 Debug/Release,26/26 PASS,0 skipped; bounded sheet wait; unchanged real speech case PASS on rerun |
| 39c13e3 | [45331730873](https://github.com/Zhangsfish/eBOOK/actions/runs/45331730873) | Xcode26.6:25/26, Files UI still failed;0 skipped |
| 2f8c6f0 | [45334428099](https://github.com/Zhangsfish/eBOOK/actions/runs/45334428099) | first immersive UI archive FAIL_COMPILE: incorrect contrast environment key; no app tests/upload |
| 2f8c6f0 | [45334431210](https://github.com/Zhangsfish/eBOOK/actions/runs/45334431210) | cancelled after that confirmed source compile error; no full-regression claim |
| 4c6d491 | [45334808227](https://github.com/Zhangsfish/eBOOK/actions/runs/45334808227), [45334855775](https://github.com/Zhangsfish/eBOOK/actions/runs/45334855775) | corrected iPhone archive PASS; runs cancelled when loading/error recovery superseded them; no full-regression claim |

The wrong environment key was corrected to Apple's documented
[colorSchemeContrast](https://developer.apple.com/documentation/swiftui/environmentvalues/colorschemecontrast).
Neither failed/cancelled immersive source was uploaded. The old39c13e3 harness
and37.1 share identical shipping Source/project blobs; that identity does not
apply to the newer immersive implementation. Machine-readable details remain in
TEST_RESULTS.json; no earlier failure is erased by a later passing rerun.

The native Files test has repeatedly left the picker open on iOS26.5 after icon,
filename and List-row selection. Both native TXT/EPUB imports and the final
library assertion remain required. The early navigation-overlay explanation was
unproven. The cause is still undetermined; do not call it a proven test-only issue,
a passing suite, or evidence that all physical imports work. It passed on18.5.
Independent audit must consider the compatibility failure before merge.

Previous render checks passed for the original large fixture: DDFF / iOS26.5,
locally replaying the unchanged checker on unmodified telemetry,256 samples,
2 process sessions,1,875 blocks,furthest1,869,<=2 visible cells /1,599 UTF16 units /
12 window blocks,peak391,823,360 bytes. Source39c13e3's successful18.5 job recorded
peak273,657,856 bytes. Raw/derived provenance is in the ignored local directory.
These are simulator observations, not measured physical-device memory.

## Physical boundaries and audit handoff

First internal35.1 / source1e556ae was installed/opened and a private TXT read well
according to the owner.37.1's requested panel/audio flow was also owner-confirmed.
The new38.1 entry, original EPUB/all encodings, physical navigation/restore,10-minute locked
speech, calls/Bluetooth, device memory and manual accessibility remain separate
unconfirmed/NOT_RUN checks; see DEVICE_CHECKLIST.md. Update the same TestFlight
app in place; this presentation change does not require uninstalling or reimport.

Nine original valid test inputs and Chinese instructions remain in a Git-ignored
local ZIP; no book is bundled in the app. Apple local speech remains the sole iOS
provider. S01 vendors remain offline/outside the app. No private book/tester data,
new paid API/service/runner, backend, App Review, public release, merge or S02.
Original S00's TestFlight exclusion applied to its earlier development task; the
owner's later phone-testing instruction authorizes this separate internal beta.
