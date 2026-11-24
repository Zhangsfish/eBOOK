# S02A.2 — Mobile TTS performance and lightweight model evaluation

Status: IN_PROGRESS (2026-11-25, Asia/Shanghai). Actual measurements will replace
the template below; unknown fields remain NOT_RUN rather than marketing claims.

Execution base: `d41b80d88780d5b483a1a2af873b1293ee22ba70`. Existing worktrees were
clean; the three owner-authored task/template commits were safely fast-forwarded.
No production App or PR #4/#5 changes. Current host is Windows; only Bluetooth
iPhone surfaces are present, no Xcode/authorized device deployment channel:
DEVICE_NOT_RUN. Existing repository device workflow is unsigned preparation.

Initial verified assets: exact existing ORT XCFramework contains CoreML provider
implementation symbols (not yet runtime-registration/node-execution proof).
No replacement ORT build started. Matcha **zh-baker**, not the supplied zh-en
example, has been downloaded and checked: 129,339,291 combined download bytes,
145,676,531 unpacked bytes including Vocos and the complete original data tree.
Its original-corpus Windows preflight produced 5 real WAVs; formal committed-source
measurement and private listening delivery follow. Suxin frontend dependencies
are absent; installation approval was requested per global AGENTS.md and remains
pending. M5 is metadata/demo reference only; no M5 weights are downloaded.

## Exact source and environment
- Tested HEAD SHA:
- iPhone model / SoC / iOS / Xcode:
- Simulator model/runtime (if any):
- Device signing method (no secrets in report):
- Commands and CI URLs:

## Kokoro CPU vs CoreML
- Runtime binary SHA and CoreML EP availability:
- Actual assigned CoreML nodes / CPU fallback:
- iPhone weighted RTF / p95 / first audible / peak physical memory:
- Simulator metrics (separate):
- 10–15 minute session / thermal / battery / interruptions:
- Decision: PASS / PERFORMANCE_NOT_READY / DEVICE_NOT_RUN

## Matcha zh-baker
- Model revision, license, complete download/unpacked size:
- Voice ID:
- iPhone / simulator / desktop evidence (clearly separate):
- Weighted RTF / p95 / first audible / peak memory:
- Human listening notes:
- Decision:

## Suxin-Light
- Model revision, decoder/frontend versions and licenses:
- Complete download/unpacked size:
- Native iOS portability result:
- Device/simulator/desktop metrics:
- Human listening notes:
- Decision:

## M5-TTS reference only
- Official sample/reference examined:
- Mobile portability blocker(s):
- No port attempted: YES/NO

## Product recommendation
- GO / NO-GO:
- Selected model (if any):
- Number of AI voices justified by evidence:
- Apple system fallback:
- Unresolved license/thermal/device issues:
- Exact next action:

## Privacy
- Original synthetic text only:
- All model/audio outputs ignored locally:
- No cloud API / no private book text uploaded:
