# Current-chapter TOC correction

State: IN_PROGRESS, 2026-11-25 (Asia/Shanghai).
Base: 4f9175ed6326b95902aceaccf47258771281eac1, reader branch / PR #5.

Owner-reported problem: the TOC opens at the start of a long book, so locating
the chapter currently being read requires manual scrolling.

Implementation: use the live absolute reading block to resolve its nearest
preceding TOC destination; account for nested EPUB destinations and navigation
order differing from spine order. Open a clean search, center the matching row
and show a checkmark/selected accessibility state. TOC browsing does not change
reading position. No decoding, stored data format or speech changes.

Validation prepared: boundary/nested-EPUB core test and the real 230万-character
synthetic TXT UI flow. Check automatic visibility/selection after manual reading,
searching/jumping to chapter624, and persisted relaunch, without scrolling the
TOC. Exact tested source, Xcode evidence and internal-beta state follow.

Local deterministic Xcode-project check and whitespace checks PASS. This Windows
host has no Xcode; Swift compilation/UI/device results are NOT_RUN until CI.
The pre-existing iOS26.5 native Files import UI failure remains separate and
unresolved; do not relabel it PASS. Owner-phone behavior remains NOT_RUN.

## First actual run and harness correction

[45542499967](https://github.com/Zhangsfish/eBOOK/actions/runs/45542499967), source
ebd9232a72628f3d3fe6cc009f5de56ba5bd86c3: Xcode26.6 (17F113), iOS26.5 ARM64
iPhone17 Pro simulator. 27 tests:25 PASS /2 FAIL /0 skipped. The existing native
Files case failed again. The long-reader case passed its first manual-scroll
TOC visibility/selection check, then the new helper failed to parse the localized
anchor `1,870/1,875` before opening the chapter624 TOC. This is an actual test
harness failure, not a passed late-chapter/relaunch case.

Correct the helper to filter display separators, as the existing anchor assertion
already does. Shipping Sources/ are unchanged by this correction. Rerun the two
affected tests (TOC boundary core test and complete long-reader UI case) through
the explicit reader-toc CI scope on both OS versions. It still checks real
scrolling/selection/search reset/relaunch and bounded renderer telemetry. No
assertion is skipped or weakened; full-suite mode remains the default.
