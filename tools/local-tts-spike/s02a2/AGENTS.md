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

## Measured handoff
- f015d3dcef870381bc7f7f19fc32bcf8dee5f4e0: Kokoro final run 45442045004
  and Matcha run 45445046800 both actually compiled/generated on ARM64 iOS 18.5
  simulator, Xcode 16.4. JSON-only ZIP digests/CRCs/member hashes were verified.
- Kokoro CPU/CoreML weighted RTF 1.7122/1.6536; real CoreML profile events exist
  but no ANE measurement. No replacement ORT build; final opportunity CLOSED.
- Matcha 2/4T weighted RTF 0.9205/0.5759 with p95 3.7696/1.0837. Full-buffer
  first mixer outputs 8.916/9.815 s. This is not device/continuous-playback proof.
- Full Matcha pack 145676531 bytes; its model card explicitly warns about
  non-commercial training data and omits separate weight license metadata.
- Desktop Matcha original 5 real WAVs are at f015. Private comparison A/B has
  10 real Windows WAVs, all fully decoded; ratings remain OWNER_PENDING.
- Suxin load-only formal source 39522a04ca4f4426633516f396323aa5421eb76e,
  existing ORT 1.20.1; initialization 6.590 s, peak RSS 179015680 bytes. No
  session.run, WAV or native frontend inference; new dependencies NOT_INSTALLED.
- stage_device.py only prepared an ignored Matcha test package. It did not
  sign/install/run anything. Physical device, 15 min, heat and battery NOT_RUN.
- Product NO_GO; recommend existing Apple system speech. Delivery READY_FOR_AUDIT
  with device/license/Suxin-approval blockers. No S02B, merge or further research.
