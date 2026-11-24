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
