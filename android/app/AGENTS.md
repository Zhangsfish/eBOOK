# App source memory

Purpose: native Android port of accepted quiet iOS reader, system offline TTS only.
Upstream: ../AGENTS.md and ../task-handoff/HANDOFF_ANDROID.md.

`src/main/java/cn/zhangsfish/ebook/core/` is dependency-free Java: strict decoding,
bounded disk blocks, EPUB parsing, TOC lookup and speech segmentation. Native Android
UI, persistence and foreground speech service live in the parent package.
`src/main/res/` contains native resources; no remote content or bundled books.
No internet permission, third-party SDK, Google services, keys or device identifiers.
