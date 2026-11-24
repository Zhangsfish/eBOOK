# eBOOK physical-device preparation

## Authority and scope
- The owner requested parallel installation/device testing on 2026-11-24.
- Base: main `adc9f340a2ff427b30cddce33ad8a4d9efdac55a`.
- Use `codex/s00-device-validation` in the separate device worktree.
- Preserve S01 PR #4 and its reviewed HEAD `3bfb4429fe7a42e50df62f4857bcb9909bf00ab3`.
- This follow-up prepares the existing reader for owner installation; it is not S02.
- Original S00 excluded TestFlight. Prepare and test the concrete package first;
  obtain the owner's explicit internal-TestFlight authorization before creating
  Apple records or using the existing Lecture Asset signing credentials.
- No App Review submission, public release, new paid service, cloud TTS or merge.

## File map and provenance
- `DEVICE_CHECKLIST.md`: owner checks, initially NOT_RUN.
- `DELIVERY.md`: exact implementation/build/installation state and blockers.
- `scripts/ci_device.sh`: real unsigned iPhone archive and package inspection.
- `.github/workflows/s00-device.yml`: standard public macOS runner; no secrets.
- `Sources/eBOOK/Assets.xcassets`: original geometric book icon, no external art.
- `.local-test-data/device-01/`: ignored private local outputs; no Apple secrets
  or private device identifiers in this folder, Git, logs or screenshots.

## Handoff
Keep compile, unsigned archive, signing, upload acceptance, Apple processing,
owner installation and physical behavior as separate evidence states.
Only owner-observed device results can change checklist rows from NOT_RUN.
