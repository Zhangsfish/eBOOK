# eBOOK — zero-cost listening product decision

Decision date: 2026-11-24. Status: product direction APPROVED; S02A feasibility NOT_YET_VERIFIED.

## User job to be done

A user imports an EPUB/TXT they already have, reads on their iPhone, and occasionally listens to a short section during a walk, commute or household chore. The product does not distribute books, transform an entire catalog into audio, require daily heavy usage, or sell hearing time.

**Invariant:** 0 CNY charged to the user, no subscription/account/API key, no per-character quota the user must understand, and no paid backend required to use the primary read/listen workflow.

## Narrow first-release voice offering

Four user-facing choices, no marketplace and no 100-voice scrolling list:

1. **系统中文** — built-in Apple AVSpeechSynthesizer; always available if Chinese system voice installed. Prefer available enhanced/premium system assets if installed; do not assume particular voice IDs exist.
2. **AI 柔和女声** — Kokoro v1.1 Chinese, candidate speaker slot `zf_001` (sid 3), only a trial ID until original audio is reviewed.
3. **AI 清晰女声** — same Kokoro model, candidate `zf_002` (sid 4), trial ID only.
4. **AI 沉稳男声** — same Kokoro model, candidate `zm_009` (sid 58), trial ID only.

The two female and one male Kokoro IDs share **one set of model weights and tokenizer resources**, not three model downloads. Names are UX placeholders; do not assign voice character until heard. If the sampled voices are poor, try other `zf_*`/`zm_*` speakers in the same model, then update the three selected IDs.

## Technology selection

**Primary local AI engine:** Kokoro-82M-v1.1-zh + sherpa-onnx native Swift/iOS.

- Upstream model: https://huggingface.co/hexgrad/Kokoro-82M-v1.1-zh
- sherpa-onnx multi-language v1.1 Swift example and speaker list: https://k2-fsa.github.io/sherpa/onnx/tts/all/Chinese-English/kokoro-multi-lang-v1_1.html
- sherpa-onnx iOS Swift package guide: https://github.com/k2-fsa/sherpa-onnx/blob/master/ios-swiftui/README.md
- Quantized model assets: https://huggingface.co/csukuangfj/kokoro-int8-multi-lang-v1_1/tree/main

The published INT8 pack is ~215 MB in source form; model weights ~114 MB and voices.bin ~54 MB. Actual downloaded compressed size, installed space, runtime RSS, first-audio latency and iPhone performance are **unknown until tested**. Upstream Kokoro weights are Apache-2.0; runtime, phonemization/data dependencies and redistributed assets need a license/notice audit before distribution.

First use:
- Always show **系统中文** immediately. Do not block importing/reading/listening behind model download.
- When user selects an AI voice, offer a single optional Wi-Fi download with plain language approximate size and delete/control. Verify a pinned manifest (hashes), preserve model state on interrupted download and keep downloaded resources in app-owned storage.
- Synthesis processes **only the next short text chunks** for daily listening, not the entire book. Store bounded local audio cache by book fingerprint + anchor + voice/model/settings; allow delete cache and avoid rereading on every resume.
- Play from cached or synthesized chunks, preserve positions, switch voice safely, and fall back to system speech if unsupported/corrupt/cancelled.
- Background audio and background model inference are distinct. Do not assume the audio background entitlement allows ongoing ML generation after lock; prebuffer bounded audio and actually test on a device.

Target output is an ordinary consumer interface: four voice names, play/pause, speed, local download indicator, continuous resume. No technical model selector in the product UI.

## Google Cloud: optional research, not production dependency

Google Standard and WaveNet currently list 4 million free characters **per billing project per month**, then paid rates. The Google Cloud API requires a billing-enabled project and can charge automatically after free allowance. Budget alerts alone are not hard spend caps. The app importing a user's own book does NOT make the Google quota per user.

Official pricing: https://cloud.google.com/text-to-speech/pricing
Official budget caveat: https://docs.cloud.google.com/billing/docs/how-to/budgets
Official Chinese Standard voice list: https://docs.cloud.google.com/text-to-speech/docs/list-voices-and-types

Thus Google is explicitly **excluded from the next iOS integration**. Do not ship a public service credential in the client, create an unbounded backend, rely on a developer project's monthly free characters, or burden users with their own Google Cloud billing account. A separately approved later experiment must make user and operator charges impossible within an audited hard limit; when unavailable it must silently use local speech.

MiniMax, Fish paid endpoints, ElevenLabs and Azure are likewise not part of the free product MVP. S01's voice-lab code can remain as non-shipping research material without forcing any cloud dependency into the app.

## Staging and gates

**S02A (now): Native Kokoro feasibility and sample voice selection.**
- No production app source changes while S01 PR #4 and immersive-reader PR #5 remain open.
- Pin upstream release/asset integrity, prove Chinese audio on a real iOS simulator if feasible, measure startup/RTF/RSS, generate original sample audio locally.
- Stop with evidence; no merge or App Store release.

**S02B (after S02A evidence plus PR #4/#5 resolution): integrate local model into actual app.**
- Four voices, single shared optional AI asset pack, offline cache, continuous playback and local fallback.
- Preserve existing reader UX and all S00 tests. Real-device lock-screen and performance validation is an explicit acceptance gate.

**S03 (later): signed device beta, UX iteration, App Store review.**

## Explicit exclusions

No cloud provider network request, remote book text upload, model re-training, voice cloning, accounts, subscriptions, paid SDK/runner, analytics, bookstore, extra ebook formats or catalog scraping. No copyrighted novel in Git or CI. Do not present model inference on desktop as proof of iPhone capability.
