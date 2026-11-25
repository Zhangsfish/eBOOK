# eBOOK owner iPhone / immersive reading handoff

## Purpose and authority
- Owner requested parallel phone installation/testing while ChatGPT web audits S01.
- Owner confirmed37.1's speech-panel flow, then requested all reading chrome hidden.
  Latest accepted option: one subtle theme-aware ellipsis entry, no white frame,
  no body-tap gesture. This is a separate S00 follow-up, not S02.
- Base main: adc9f340a2ff427b30cddce33ad8a4d9efdac55a.
- Implementation:326c5438794c76a8978c3cdb049b905ace703f66,
  branch codex/s00-device-validation, PR5. S01 PR4 stays frozen at
  3bfb4429fe7a42e50df62f4857bcb9909bf00ab3.
- No commercial book body/tester identity, paid API/CI, cloud TTS client,
  backend, App Review/public release, self-approval, merge or S02.

## File map
- DELIVERY.md: canonical behavior, tested implementation, real build/upload evidence,
  historical failed/cancelled runs and limitations.
- TEST_RESULTS.json: per-run outcomes, source/provenance hashes, unsigned package,
  owner observations and current available beta (availability is not installation).
- DEVICE_CHECKLIST.md: actual owner phone checks, with unobserved cases NOT_RUN.
- INSTALL_PLAN.md: separate eBOOK identity and existing-credential signing route.
- draw_icon.py: original geometric icon, generated with already-installed Pillow.
- .local-test-data/device-01/: Git-ignored original fixtures, raw CI logs/metadata,
  screenshots and metrics provenance. Never add private books or Apple credentials.

## Result and verification
- ReaderView only: text plus transparent44pt ellipsis, adaptive ink, fixed-viewport
  overlay with back/TOC/type/speech/progress. Loading/error return remains possible.
  Body taps/scroll do not open controls. No engines/table/library/core-test changes.
- Xcode16.4 / iOS18.5 run45335498953: Debug/Release and26/26 PASS,0skips.
- Xcode26.6 / iOS26.5 run45335480364: iPhone Release archive and Debug/Release
  simulator builds PASS;25/26,1 native Files import UI FAIL,0skips. All changed
  reader UI,3themes, viewport/anchor, back and long624/font/relaunch cases PASS.
- Three theme screenshots and expanded controls inspected. Current render check
  PASS:256samples,2sessions,<=12windowblocks/1599UTF16/2visiblecells. Simulator peaks
  410910720bytes(26.5 local replay) and270245888bytes(18.5 original job).
- Files failure stays real/unresolved; icon/filename/List-row attempts failed on26.5.
  No skips/injected import/relaxed assertion.18.5 real Files case passes. Keep PR
  draft as pre-merge compatibility/audit gate. READY_FOR_AUDIT does not mean PASS.

## Internal beta / owner observations
- Available0.1.0(38.1), reader326c543. Helperf22b891bf885c17c288ad62961be4ee188e6fb89
  in isolated unmerged lecture-asset:codex/ebook-device-installation, run45338159157.
  Preflight/archive PASS; upload accepted06:10:10UTC; VALID and exact existing
  manual/internal owner-group build relationship read back06:11:48UTC.
- Existing encrypted credentials remain in the signing repository; no values read/
  copied into eBOOK. No Lecture Asset source/default branch/release change/reupload.
- Direct upload retained no signed IPA; signed digest/CDHash/profile inspection
  unavailable. Unsigned8.1 digest is separate and not an installable package.
- Owner confirmed older35.1 install/open/private TXT read and37.1 panel/ongoing
  speech flow.38.1 update/quiet-entry feedback is pending; do not infer it from API.
- Model/iOS version, original EPUB/all encoding phone cases,10min locked audio,
  physical restore/memory/calls/Bluetooth/manual accessibility remain unconfirmed.

## Stop / handoff
- READY_FOR_AUDIT, PR5 draft; hand real known failure to independent web audit.
- Final evidence commits after326c543 are documentation only; compare Sources,
  Tests and build scripts to that tested implementation before reporting finalHEAD.
- Preserve S01 and all unrelated user work. No merge, paid service or S02.
