# S00 follow-up — owner iPhone installation and validation

State: READY for device preparation and owner-only internal TestFlight installation.

Owner request on 2026-11-24: Codex handles tests while the owner installs on the
iPhone; ChatGPT web independently reviews S01. This is separate from S02.

- Work on `codex/s00-device-validation`, based on merged S00 main.
- Preserve S01 PR #4 and `3bfb4429fe7a42e50df62f4857bcb9909bf00ab3`.
- Keep all reader/parser/decoder/persistence/speech app Swift sources unchanged.
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
