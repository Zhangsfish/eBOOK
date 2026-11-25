# S02A.3 owner-directed Suxin / Matcha audition

## Authority and decisions
Issue #10, tasks/S02A3_SUXIN_MATCHA_LISTENING.md and the owner message on
2026-11-25 supersede S02A.2's Apple-only recommendation and pending installation
approval. Continue PR #7 / codex/s02a-kokoro-ios-spike. Matcha was the starting
preferred candidate; the owner decides subjective sound quality after listening.
Kokoro is paused. No new model search, cloud TTS, production integration or merge.
After hearing the real same-text page, the owner replied "更喜欢 Suxin-Light"
on2026-11-25. Suxin is now the preferred voice candidate; Matcha remains available.
This is short-audition preference, not device/long-session/release approval.

## File map and provenance
- scripts/: isolated hash-checked frontend environment, actual author-code speech,
  private listening packaging and bounded native-backend diagnostic orchestration.
- manifests/: exact installed dependency versions/hashes and declared licenses.
- evidence/: sanitized measured metadata, never models, audio or generated pages.
- ../fixtures/corpus.json: unchanged canonical five original passages.
- ../s02a2/manifests/: existing pinned Suxin / Matcha asset sources.
- ../../../.local-test-data/s02a2/: ignored assets, new isolated environment,
  immutable run directories, real WAVs and private HTML/ZIP. Preserve old results.
- ../../../reports/S02A3_SUXIN_MATCHA_LISTENING.md: final review handoff.

## Evidence boundaries
Use the unmodified author's SuxinTTS.from_pretrained / synthesize_long frontend.
Never invent phonemes. A native test with author-produced IDs is only
PRECOMPUTED_FRONTEND_ONLY, not end-to-end native Mandarin TTS. Desktop, simulator
and physical device data remain separate. Model-load-only is not speech failure.
Private audition, product portability and redistribution rights are separate gates.
Stop at READY_FOR_AUDIT; retain the actual owner preference and separate pending
device/long-session/license gates. Do not start S02B.

## Measured handoff
- Desktop a7b073d572fe7e4862679678dc872f0887a5e19d: five real author-frontend
  WAVs plus stream WAV, init8.418s, weightedRTF0.249534, peak265641984bytes.
- Native9713f7596c9f9a3b9565cfb61dd836b1b3602b5b, run45584309079: Xcode16.4,
  ARM64 iOS18.5, five real graph WAVs, init3.358s, weightedRTF0.598536,
  p95=1.210590, peak255180800bytes; first full-buffer mixer11.273s. Backend only;
  no native Mandarin frontend, phone, acoustic or continuous-playback approval.
- First run45583501783 failed the SHA preflight after Git newline conversion,
  before model execution. The author IDs were preserved byte-for-byte with a
  narrowly scoped -text attribute, not changed or fabricated. Failure retained.
- Owner short-audition preference is Suxin; Matcha retained. Final private page
  /ZIP path and exact digests are in reports/S02A3_SUXIN_MATCHA_LISTENING.md.
- The CI ZIP was verified against GitHub digest/CRC/member hashes; JSON only.
  Do not upload the real WAVs/models or infer complete native text inference.
