# Android reader — owner-authorized parallel product

## Authority
On2026-11-25 the owner explicitly requested a NEW chat to implement an Android
edition of eBOOK for a friend's HUAWEI Mate X3 (ALT-AL00), HarmonyOS4.2.0.
Preserve the accepted iOS reading experience; use Android system TTS instead of
the iOS/local-AI speech experiments. Deliver a locally installable signed APK
inside one ZIP, without requiring the friend to install developer tools.
This explicit Android request supersedes iOS-only platform wording for this
module only. Read task-handoff/HANDOFF_ANDROID.md before implementation.

## Workspace / scope
- Dedicated checkout: E:/myself/eBOOK-android.
- Branch: codex/android-system-tts-reader, based on accepted main83fa0d90fd4cd0dbcd791eeb4a3edd53ba985656.
- Android implementation/build/tests and reports stay under android/.
- iOS Sources/, Tests/, project, STATUS, existing workflows and PRs stay unchanged.
  A new Android-only workflow is allowed if needed; standard free CI only.
- Do not modify the separate eBOOK, eBOOK-device-validation or eBOOK-s02a checkouts.
- No merge, store release, paid service, account creation or public APK upload.

## Essential behavior
- EPUB/TXT import, UTF-8/UTF-16/GBK/GB18030, local bookshelf and durable resume.
- Bounded incremental long-TXT rendering, heterogeneous chapter recognition.
- Quiet reader: only a subtle lower-right ellipsis, theme-aware, accessible hit
  target. Its overlay opens back/TOC/settings/speech/progress without reader jump.
- Every TOC opening follows the LIVE visible chapter, marks it, clears previous
  search and preserves reading position when merely browsed/dismissed.
- Font/line spacing/light-warm-dark themes; survive relaunch and fold/unfold.
- System TextToSpeech with installed offline Chinese voice, speed controls,
  real playback callbacks, separate listening resume and background controls.
- No GMS/Google voice download requirement or cloud TTS. Never claim a particular
  voice is installed until actually queried. Missing offline voice must leave
  reading usable and provide an explicit system-settings route, not silent cloud.

## Evidence / privacy / tooling
No novels, weights, WAVs, keys or phone identifiers in Git/CI/reports. The owner
photo was inspected only for model/OS; never copy the screenshot or unique IDs.
Use original synthetic fixtures. Distinguish JVM/unit, emulator and Huawei phone
evidence. Real build/signature checks are mandatory; no mock substitutes.
Inventory existing JDK/SDK/Gradle/IDE/WSL/free-CI tools before installing anything.
Follow global confirmation rules for missing new tools/dependencies; no silent
global installations. Keep new approved tools project-local and hash/versioned.
Do not change Codex model settings or use subagents without owner authorization.

## Delivery
One local ZIP: signed installable APK, Chinese install/use instructions, SHA256,
version/source SHA and truthful test report. Mark internal test signing clearly;
preserve the signing key only in ignored local storage for later upgrades.
Never put the key, private books or device IDs in the ZIP. No Play/AppGallery
submission. Stop READY_FOR_AUDIT after delivery; do not merge PRs automatically.
