# S00 follow-up — owner iPhone installation and validation

State: READY for unsigned device preparation; signed internal distribution needs
the explicit follow-up authorization described below.

Owner request on 2026-11-24: Codex handles tests while the owner installs on the
iPhone; ChatGPT web independently reviews S01. This is separate from S02.

- Work on `codex/s00-device-validation`, based on merged S00 main.
- Preserve S01 PR #4 and `3bfb4429fe7a42e50df62f4857bcb9909bf00ab3`.
- Keep all reader/parser/decoder/persistence/speech Swift sources unchanged.
- Prepare unique bundle identity, original icon and build/export metadata.
- Run real Xcode 26 iPhone Release archive and the 26-case simulator regression
  on standard free public GitHub-hosted macOS. No paid/larger runner.
- Export an explicitly unsigned arm64 package with no test books or secrets.
- Original S00 forbade TestFlight submission. After producing a concrete tested
  package, ask the owner once to authorize the separate internal-TestFlight
  follow-up, Apple app records and use of the existing Lecture Asset signing
  pipeline. Do not request key values in chat or create a new paid account.
- No App Review, App Store release, live cloud TTS, merge or S02.
- Record exact source/run/package identity in `reports/S00/device-01/`.
- Physical behavior remains NOT_RUN until the owner reports device observations.
