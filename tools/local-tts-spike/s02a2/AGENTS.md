# S02A.2 mobile TTS gate

## Purpose and authority
Issue #9, tasks/S02A2_MOBILE_TTS_GATE.md and CODEX_HANDOFF_S02A2.md authorize
this bounded screening. Parent AGENTS.md supplies engineering/privacy rules.
Base after safe fast-forward: d41b80d (full SHA is recorded in delivery).

## File map
- scripts/: candidate asset manifests/download verification, native orchestration,
  desktop synthesis and private comparison page generation.
- manifests/: fixed source URLs, revisions, bytes and hashes; never weights.
- evidence/: public-safe actual metadata only.
- ../../../.local-test-data/s02a2/: ignored source audit, models, real WAVs,
  native logs/profiles and private HTML. Preserve previous S02A/S02A.1 results.
- ../fixtures/corpus.json: canonical original text, shared unchanged by candidates.
- ../../../reports/S02A2_MOBILE_TTS_EVALUATION.md: review handoff (path from
  repository root is reports/S02A2_MOBILE_TTS_EVALUATION.md).

## Limits and decisions
- Kokoro final experiment: one CPU/CoreML paired proof, 2 threads, identical
  corpus/warmup and exact existing INT8/native binaries. Runtime EP availability
  and actual profiler node events are required before calling it accelerated.
  If its existing binary supports CoreML, do not rebuild ORT. Do not retry with
  different model/graph/provider settings after a genuine failed attempt.
- Physical device currently has only Bluetooth surfaces on Windows; no Xcode
  deployment channel. Existing device workflow is unsigned preparation, not
  owner-phone execution. Do not claim device performance/thermal/battery.
- Matcha means the named monolingual zh-baker (22050 Hz), not the zh-en model
  in the supplied example URL. Use Vocos 22 kHz from its official instructions.
- Suxin source is pinned; inspect for custom ops/frontend needs before deciding
  whether a small backend-only proof is practical. Native frontend must remain
  NOT_RUN unless actually implemented and tested end to end.
- M5: inspect public demo and metadata only. No large model download/port, no
  network synthesis request. Its pre-recorded demo cannot be a same-text result.
- Quality is owner listening acceptance, never a fabricated score from RTF/ASR.
- New package installation requires the pending owner confirmation; Matcha and
  native CoreML inspection can proceed using existing environments meanwhile.
