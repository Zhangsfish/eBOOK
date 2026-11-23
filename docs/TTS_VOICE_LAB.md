# S01 — Mandarin TTS Voice Lab

Status: S01 scope definition, dated 2026-11-23. This is a candidate shortlist, not a model ranking or purchase decision. Vendor model names, regional availability, limits, privacy terms and prices change; re-check the linked official docs immediately before any live request.

## Product objective

Choose a Mandarin voice that is comfortable for long-form Chinese fiction: warm, calm, natural, unhurried, clear on names/numbers, with sensible sentence and paragraph pauses. The desired result is not a newsreader, navigation voice, advertising voice, or theatrical over-acting.

S01 builds an audition harness only. It does not enable cloud TTS in the iOS app, deploy a backend, transmit a commercial novel, or make paid API requests. The existing on-device AVSpeechSynthesizer remains the working fallback.

## Candidate shortlist

| Provider | Candidate model(s) | Why include it | Important constraints to verify |
|---|---|---|---|
| MiniMax | Speech 2.8 HD; Speech 2.8 Turbo as speed/cost control | Chinese TTS, configurable voice/speed/pitch/volume, WebSocket chunk streaming | Confirm exact Chinese voice IDs, style controls, regional endpoint, long-form consistency and current billing |
| Fish Audio | S2.1 Pro; S2.1 Pro Free for no-cost initial audition | S2.1 Pro supports expressive direction tags; REST and real-time streaming are documented | Free tier has no TTFA/DPA guarantees; production billing is by UTF-8 bytes, not generic character count; do not select deprecated S1 |
| ElevenLabs | Eleven v4; Multilingual v2 as a long-form stability control | v4 is positioned for expressive narration; Multilingual v2 explicitly supports Chinese and stable long-form generation | API voice-library access is restricted on free tier; zero-retention mode is Enterprise-only; confirm model-specific request limits and current v4 price |
| Azure Speech | Chinese Neural voices and available Chinese Neural HD / DragonHD voices | Broad Chinese voice catalogue, SSML controls, styles such as gentle/story where supported | Voice/style availability depends on region and preview status; HD supports only a subset of SSML; query the actual resource's voice list |

### Official references checked for this shortlist

- MiniMax Speech 2.8 WebSocket T2A: https://platform.minimax.io/docs/api-reference/speech-t2a-websocket
- MiniMax synchronous HTTP T2A used by this offline workbench: https://platform.minimax.io/docs/api-reference/speech-t2a-http.md
- MiniMax token plan / speech pricing: https://platform.minimax.io/subscribe/token-plan?tab=api-enterprise
- Fish Audio API quickstart: https://docs.fish.audio/developer-guide/getting-started/quickstart
- Fish Audio API and model/pricing reference: https://docs.fish.audio/developer-guide/models-pricing/pricing-and-rate-limits
- Fish Audio canonical OpenAPI: https://api.fish.audio/openapi.json
- ElevenLabs model selection: https://elevenlabs.io/docs/zh/overview/intro
- ElevenLabs TTS endpoint: https://elevenlabs.io/docs/zh/api-reference/text-to-speech/convert
- ElevenLabs API pricing: https://elevenlabs.io/pricing/api
- Azure Chinese voice catalogue: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=text-to-speech
- Azure HD voice overview: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/high-definition-voices
- Azure REST TTS: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/rest-text-to-speech
- Azure TTS overview, SSML and long-audio synthesis: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech

## Pricing facts observed on 2026-11-23

These are published list prices, not a quote, and do not include taxes, regional differences, resource packs, promotions or negotiated rates.

- MiniMax token-plan page lists Speech 2.8 HD at USD $100 per million characters and Speech 2.8 Turbo at USD $60 per million characters.
- Fish Audio lists S2.1 Pro at USD $15 per million UTF-8 bytes; S2.1 Pro Free is listed at zero cost for developer evaluation. Its docs state that free tier has no TTFA/DPA guarantees. Do not compare Fish's byte-based unit directly with a per-character price without measuring UTF-8 bytes.
- **Implementation-time refresh (2026-11-23–24):** the current [official API pricing page](https://elevenlabs.io/pricing/api) lists Eleven v4 and Multilingual v2 at USD $0.08 per 1,000 characters (USD $80 per million). This supersedes the initial shortlist's v2 $0.10 and unknown-v4 observations. No account-specific price or live invoice has been verified.
- Azure bills Chinese code points at two billable characters each; inner SSML markup other than speak/voice can also be billable. Exact price must be read for the selected Speech SKU and deployment region; do not hard-code a global estimate.

No provider has been selected. Do not generate a whole-book audiobook during evaluation. Use only the short original sample suite below.

## S01 implementation interpretation

The implemented request/response contracts and dated official sources are in
[TTS_PROVIDER_API_CONTRACTS.md](TTS_PROVIDER_API_CONTRACTS.md). The workbench
uses synchronous REST, original normalized text, shared <=120-scalar boundaries
and validated 24 kHz / 16-bit / mono WAV. It does not claim equal perceived rate,
loudness or style across vendors. Unsupported gentle conditions are marked,
not silently substituted or supplied with vendor-only direction tags.

For this authorized **offline-only** S01, `--execute-live` is a reserved,
hard-disabled entry point even when a spend cap/environment values are supplied.
The future transport/authorization contracts can be reused only after a later
explicitly authorized change and billing/rights review. No current command can
turn S01 into a paid/live audition. Mock tones verify plumbing only; real audio,
human scores, vendor latency/reliability and final voice selection remain NOT_RUN.

## Standard audition set

All sample text must be original and stored in tools/tts-lab/samples/. Never copy dialogue or narration from a commercial novel, including 绝境黑夜.

Create a compact, repeatable set covering:

1. Narration / baseline: calm descriptive prose, varied sentence lengths, full stops and commas.
2. Dialogue: short exchanges with Chinese quotation marks, question/exclamation punctuation, and different speaker turns. Keep a single voice for the first comparison; later test multi-voice only if a provider supports it.
3. Emotional restraint: a tense scene that should sound concerned but not melodramatic; a comforting scene that should sound warm but not sugary.
4. Numbers and mixed language: dates, times, decimals, percentages, units, common abbreviations and short English names embedded in Chinese.
5. Long sentence and paragraph boundaries: subordinate clauses, semicolons, ellipses, em dashes, blank-line transitions and a sentence split across adjacent synthesis chunks.
6. Proper nouns / pronunciation: a small original list of fictional Chinese names and places; do not use real-person voice impersonation.

Keep each sample short enough for all shortlisted APIs. Record exact UTF-8 bytes, Unicode scalar count and UTF-16 count. Use the same normalized text and equivalent chunk boundaries across providers. Do not add provider-specific stage directions to only one provider's text.

## Evaluation protocol

For each provider/model, test at least:
- one female-presenting and one male-presenting Mandarin voice when available;
- neutral narration and the provider's closest supported gentle/story style;
- identical sample text, normalized rate target and audio output format where possible;
- the same chunk boundaries and a multi-chunk continuity sample.

Blind the listening labels (A/B/C...) in the local audition page. Keep the provider/model/voice mapping in a separate local manifest so the listener can score before seeing the source.

Score each voice from 1–5:
- Long-session comfort / warmth: 30%
- Natural prosody, phrasing and pauses: 25%
- Mandarin pronunciation and proper nouns: 15%
- Dialogue and restrained emotion: 10%
- Voice consistency across chunks: 10%
- Artifact-free audio / intelligibility: 5%
- Latency and operational reliability: 5%

Record written notes for fatigue, breathiness, sibilance, robotic cadence, over-enunciation, incorrect polyphonic characters, number reading and abrupt chunk transitions. Human listening is the deciding evidence; model marketing claims are not.

## Harness requirements

The local CLI must:
- run offline by default and support --dry-run;
- require a separate explicit --execute-live flag for any network request;
- refuse live execution unless the user has configured the provider's environment variables and explicitly supplies a maximum spend guard;
- print the provider, model, voice, text byte/character counts and estimated cost before sending;
- never retry a billable request automatically after an ambiguous timeout;
- cache by provider + model + voice + exact text hash + synthesis settings, so reruns do not rebill;
- save MP3/WAV output, metadata manifest and a local HTML listening page under ignored .local-test-data/tts-auditions/;
- produce a rating template that can be completed without revealing provider labels;
- never upload audio, text, credentials, logs or manifests to GitHub.

No API keys may be written to source, app plist, Xcode settings, GitHub Actions, .env.example, screenshots or reports. Read keys only from process environment. .env and all audition output must be gitignored. No live requests in CI.

## Privacy, rights and cost gates

- S01 samples are original synthetic text only. No commercial novel, user-imported book, or full-book content may be sent to any vendor.
- S01 does not connect the iOS app to cloud TTS and does not deploy a public endpoint.
- Before a future production provider is selected, review commercial-use terms, output rights, data retention/training policy, regional processing, subprocessors, deletion options, and whether user text is retained. Record the exact terms URL and review date.
- Before any future cloud reading feature, the app must clearly tell the user that selected book text is sent to the chosen provider, offer local-only Apple speech, and require an affirmative choice. Do not send the entire book; synthesize only the next bounded chunks.
- Do not create a public proxy with an embedded provider key. A production backend needs authentication/abuse controls, quotas, rate limits, spend caps, request-size limits and server-side secrets. This is outside S01.
- No provider spend is authorized by this task. The harness must be safe to build and test without credentials or network calls.

## S01 exit criteria

- A deterministic original Chinese sample suite and offline tests exist.
- Provider adapters are isolated and covered by mocked transport tests; no live vendor call is required to pass CI.
- Dry-run output and cost-unit calculations are tested.
- If the owner later supplies credentials and explicitly authorizes a capped live audition, the same harness can generate local audio samples.
- A local blind-listening page and score template are generated.
- A report compares all successfully auditioned voices, clearly marks unavailable/unrun candidates, and recommends a shortlist with evidence and caveats.
- Codex stops at READY_FOR_AUDIT. Do not integrate cloud TTS into the app or begin S02.
