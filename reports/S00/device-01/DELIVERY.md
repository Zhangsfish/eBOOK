# eBOOK device preparation — 2026-11-24

State: PREPARING. No signed or installable build has been delivered yet.

- Base: `adc9f340a2ff427b30cddce33ad8a4d9efdac55a` (merged S00).
- S01 remains frozen at `3bfb4429fe7a42e50df62f4857bcb9909bf00ab3`, PR #4.
- Reader, decoder, parser, persistence, speech Swift sources and tests unchanged.
- Package-only changes: unique eBOOK identifier, original icon, version/build
  metadata, export-compliance declaration and iPad orientation metadata.
- Real iPhone archive and Xcode 26 simulator regression: pending Actions.
- Signing, upload, Apple processing and phone installation: NOT_RUN.
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

The existing Lecture Asset public repository has a working automatic distribution
export/TestFlight pipeline and three encrypted App Store Connect secrets.
The eBOOK repository has no Apple secrets. GitHub secret values cannot be read or
copied back out. No password/key or device identifier is requested in chat.

Original S00 excluded TestFlight. Once the unsigned package is concretely tested,
the owner must authorize the separate internal-TestFlight follow-up and reuse of
the existing signing pipeline before any Apple account records are created or
signed upload is attempted. No App Review or public release is included.

Local Windows checks use the existing Python 3.11 environment. No tools installed.
The icon was drawn locally with existing Pillow 11.1.0, using original geometry.
No copyrighted book, cloud TTS request, paid CI or new paid service is used.
