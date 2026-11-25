# Evidence memory

Purpose: exact source/environment/test records and Chinese delivery notes.
Record failed attempts honestly. Separate JVM, emulator and Huawei Mate X3 evidence.
No phone connected at task start: all physical-device checks NOT_RUN.
Tool inventory: Windows JDK 25 in E:/java; WSL OpenJDK11 runtime; no Android SDK,
Gradle, adb, emulator or Kotlin compiler found in PATH, standard locations, tool
roots/cache or WSL. Existing portable gh2.104.0 authenticated. No tools installed.
Owner asked to avoid large one-use local installs; prefer free standard GitHub CI
with preinstalled SDK. AutoDL is a fallback, no instance rented or cost incurred.

## Current work (2026-11-26; supersedes initial tool note above)
Owner chose AutoDL, CNY10 total, and NO additional local tool even for signing.
New Chongqing151 CPU32/120GB at CNY0.88/h is running; timed shutdown07:30
Asia/Shanghai. Close it and VERIFY status off after all required cloud work.
Cloud root /root/autodl-tmp/ebook_android_20261125, isolated new container.
APT JDK17.0.21.1+2 + officially hashed SDK35/build-tools35 are validated.
`cloud-toolchain-manifest.json` is canonical observed tool provenance.

Implementation already exists and compiles: native Java, strict streamed TXT,
disk-backed <=1600 UTF16 blocks, EPUB2/3, quiet reader, TOC, fold anchors, offline
system TTS foreground/media/focus and independent resume. JVM32/32 passes locally
and on AutoDL. A signed candidate from d12e9d6 was verified by official apksigner
v2/v3; it is NOT final delivery. Upgrade key DPAPI backup verified locally at
ignored .local-test-data/private/ebook-upgrade-signing.dpapi. Cloud temporary key
still exists in private-signing/; remove with backup_signing.py remove-cloud ONLY
after final signed APK/backup checks. No signer JAR/tool installed locally.

Native CI is still being debugged, NOT PASS. Early runs:
-45646876583/2f74ffa: inventory only passed.
-45649603106/84d8262: JVM31 passed; app compile lacked SDK lambda stubs (fixed).
-45650821882/fb39423: app compiled; test harness Java compile errors (fixed).
-45651049630/baba799 and45652592344/7c3e6cd: cancelled after emulator could not
 find AVD and old diagnostic adb hung; NOT UI validation. Evidence retained.
-45654239314/6106248 and45654706039/9d81b13: bounded boot FAIL, AVD user homes
 differed between avdmanager and emulator (explicit shared homes fixed).
-45655280244/f23d073: real emulator boots and APKs install. API30 first UI failed
 because custom DocumentsProvider was absent. adb evidence pull denied by scoped
 storage. API35 was still running at last check. Both issues fixed in e68a820:
 use actual system Downloads with pushed original files, rooted TEST VM to collect
 app-private evidence. No root required on friend's real phone.
-45656435724/e68a820: API35 reading12 cases passed; missing test-engine DEFAULT
 category caused later TTS failures. Full suite did not pass.
-45656785782/5c84e34 and45658299140/f88af81: cancelled while fixing the harness's
 startActivitySync wait on an already existing task. Not full-suite evidence.
-45658576919/1f28647: API35 completed18/21 main +4/4 resume. Reading cases all
 passed. Found a production dialog-dismiss race that cleared the newer speech
 panel's status references; fixed by checking dialog identity. Background task
 return check must accept the app's dialog window focus. Test engine error path
 must call SynthesisCallback.done() after error(), per official Android contract.
 Fixed in5d85816. Run45660422346 API35 passed21/21 main +4/4 resume; screenshots
 visually checked unobscured, signed AutoDL APK payload exactly matches tested
 unsigned payload. API30 AOSP grid failed to activate file through accessibility
 click; old resume then timed out without a checkpoint. Fresh harness uses a real
 injected touchscreen tap at the observed file bounds and skips invalid resume
 when main never reaches a checkpoint. This is a test-only change; production
 app source/payload remains5d85816. Run45660422346 cancelled remaining API30 job.

Cloud final candidate5d85816:61,913bytes; official v2/v3 verification PASS, same
upgrade certificate. APK + metadata/core evidence recovered under ignored
.local-test-data/cloud-results/5d85816/. At2026-11-26 01:06 Asia/Shanghai, signing
DPAPI backup reverified, private-signing folder removed. CPU151 shutdown clicked
and console visibly confirmed 已关机 at approximately01:07. No further cloud
operations without intentionally starting this same authorized task instance.

Actual native suite expects21 main +4 resume cases PER API30/35. Process killed
between phases. Test-only PCM engine tests Android callbacks; never a Huawei voice
or sound-quality claim. Memory metrics added to harness. All phone checks NOT_RUN.
CI ciphertext only; download_ci.py validates GitHub artifact SHA256 + CRC + HMAC,
then decrypts with existing local libraries. Do NOT use --include-tools (owner
rejected local signer). Local evidence in ignored .local-test-data/ci/<run>/.

Remaining: get full native results/screenshots, fix real failures, render-check
screenshots, final exact-source cloud rebuild/sign, local download/digest checks,
remove cloud key after verified DPAPI backup, create Chinese report/TEST_RESULTS,
package_delivery.py builds ignored android/delivery/ ZIP. Create draft PR with real
evidence and exact tested implementation SHA. STOP READY_FOR_AUDIT, no merge.
No changes to iOS/S01/S02A checkouts or existing workflows.
