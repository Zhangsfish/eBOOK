# S00 follow-up — owner iPhone installation and validation

State: READY_FOR_AUDIT — internal38.1 available; implementation326c543 tested on
18.5 and26.5. The26.5 native Files failure is retained as a pre-merge audit gate.
No remaining implementation is authorized without new owner/auditor feedback.

Owner request on 2026-11-24: Codex handles tests while the owner installs on the
iPhone; ChatGPT web independently reviews S01. This is separate from S02.

- Work on `codex/s00-device-validation`, based on merged S00 main.
- Preserve S01 PR #4 and `3bfb4429fe7a42e50df62f4857bcb9909bf00ab3`.
- Keep parser/decoder/persistence/speech engine Swift sources unchanged.
  Owner feedback after installing35.1 explicitly requests on-demand speech controls:
  hide the persistent bottom player, add a toolbar entry and dismissible control
  sheet, preserve playback while hidden, and verify show/hide preserves reading.
  The owner confirmed37.1 works, then requested immersive reading: hide back,
  speech/TOC/font buttons and progress until needed. The latest accepted option
  is one subtle theme-aware ellipsis entry (no white background/border), opening
  the complete reading controls. Body taps/scrolls must not open it. Keep a clear
  accessible way back to the library and preserve the reading anchor.
  Repair native UI-test interaction only when actual new-OS evidence requires it;
  keep real file selection and final imported-book assertions.
- Prepare unique bundle identity, original icon and build/export metadata.
- Run real Xcode 26 iPhone Release archive and the 26-case simulator regression
  on standard free public GitHub-hosted macOS. No paid/larger runner.
- Export an explicitly unsigned arm64 package with no test books or secrets.
- Original S00's TestFlight exclusion applied to that development task. The
  owner's later phone-installation request authorizes this separate internal
  testing follow-up, its eBOOK app records and reuse of the existing Lecture
  Asset signing pipeline. The owner handles Apple login/verification directly.
  Do not request key values in chat, copy secrets into eBOOK, create a new paid
  account or ask again for already-authorized routine installation steps.
- No App Review, App Store release, live cloud TTS, merge or S02.
- Record exact source/run/package identity in `reports/S00/device-01/`.
- Physical behavior remains NOT_RUN until the owner reports device observations.
