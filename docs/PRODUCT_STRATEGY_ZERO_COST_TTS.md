# eBOOK — zero-cost listening product decision

Decision date: 2026-11-24. Status: **Kokoro selected as the only AI TTS engine**; owner accepts its public audio quality. **Google, all cloud voices and the previous multi-provider comparison are cancelled.** S02A actual iOS runtime feasibility remains NOT_YET_VERIFIED.

## User job to be done

A user imports an EPUB/TXT they already have, reads on their iPhone, and occasionally listens to a short section during a walk, commute or household chore. The product does not distribute books, transform an entire catalog into audio, require daily heavy usage, or sell hearing time.

**Invariant:** 0 CNY charged to the user, no subscription/account/API key, no per-character quota the user must understand, and no paid backend required to use the primary read/listen workflow.

## Narrow first-release voice offering

Four user-facing choices, no marketplace and no 100-voice scrolling list:

1. **系统中文** — built-in Apple AVSpeechSynthesizer; always available if Chinese system voice installed. Prefer available enhanced/premium system assets if installed; do not assume particular voice IDs exist.
2. **AI 女声 A** — Kokoro v1.1 Chinese, initial speaker `zf_001` (sid 3); verify actual speech before shipping.
3. **AI 女声 B** — same Kokoro model, initial speaker `zf_002` (sid 4); verify actual speech before shipping.
4. **AI 男声 C** — same Kokoro model, initial speaker `zm_009` (sid 58); verify actual speech before shipping.

The two female and one male Kokoro IDs share **one set of model weights and tokenizer resources**, not three downloads. Exact speaker choices are replaceable within Kokoro only if local verification reveals a concrete problem. No additional provider auditions.

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

## External providers: removed from scope

The owner explicitly cancelled **Google Cloud, MiniMax, Fish Audio, ElevenLabs, Azure and every other network TTS service**. No free-tier quota, billing account, API token, backend proxy or remote book-text transmission belongs in the product, trial or next-stage milestones.

The previous S01 multi-provider Voice Lab is historical engineering work only and does not drive product integration. An internet connection may be used solely for the optional, user-approved one-time download of the pinned open-source model pack; speech synthesis itself is fully offline and free.

## Staging and gates

**S02A (now): Native Kokoro feasibility only.**
- No production app source changes while S01 PR #4 and immersive-reader PR #5 remain open.
- Pin upstream release/asset integrity, prove Chinese audio on a real iOS simulator if feasible, measure startup/RTF/RSS and generate a few original-text Kokoro clips to validate the three default speaker IDs. The owner already accepts Kokoro demos; no blind multi-vendor audition.
- Stop with evidence; no merge or App Store release.

**S02B (after S02A evidence plus PR #4/#5 resolution): integrate local model into actual app.**
- Four voices, single shared optional AI asset pack, offline cache, continuous playback and local fallback.
- Preserve existing reader UX and all S00 tests. Real-device lock-screen and performance validation is an explicit acceptance gate.

**S03 (later): signed device beta, UX iteration, App Store review.**

## Explicit exclusions

No Google or other cloud TTS APIs, remote book text upload, model re-training, voice cloning, accounts, subscriptions, paid SDK/runner, analytics, bookstore, extra ebook formats or catalog scraping. No copyrighted novel in Git or CI. Do not present model inference on desktop as proof of iPhone capability.
