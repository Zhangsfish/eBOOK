# S01 API contract notes

Reviewed against public official documentation on **2026-11-23–24,
Asia/Shanghai**. This is request/response engineering evidence, not a live
compatibility test. No authenticated catalogue, synthesis or account API was
called. No provider has been selected.

## Common comparison contract

Original NFC/LF-normalized text is split once, losslessly, into at most 120
Unicode scalars per request. Every provider receives the same text and chunk
boundaries. Output is **24 kHz, mono, 16-bit PCM WAV**; response headers/frames
must validate. Unsupported audio is rejected rather than relabeled/resampled.
Requests use relative rate 1.0 for comparison; numerical rate controls do not
establish equal perceived speed. No special stage-direction tags are added to
one provider's text. No cloning/reference audio, pronunciation replacements,
effects or multi-speaker synthesis is used.

## MiniMax

- [Official synchronous REST/OpenAPI](https://platform.minimax.io/docs/api-reference/speech-t2a-http.md):
  `POST https://api.minimax.io/v1/t2a_v2`, bearer binding at transport time.
- Explicit models: `speech-2.8-hd`, `speech-2.8-turbo`; `stream=false`,
  `output_format=hex`, JSON `voice_setting`, `audio_setting`, `language_boost`.
- The lab requests WAV/24000/mono. It requires `base_resp.status_code=0`,
  `data.status=2`, then decodes `data.audio` hex and validates the WAV itself.
  Null data, unfinished frames, URLs, malformed JSON/hex and provider errors
  are rejected. No second URL fetch or streaming aggregation is involved.
- Gentle means the documented `emotion=calm`; neutral omits emotion. This is
  the closest control, not a claim of identical delivery across vendors.
- [Published sync pricing](https://platform.minimax.io/docs/pricing/overview.md):
  HD USD 100 / million characters; Turbo USD 60. Local scalar counts are a
  text estimate; actual `usage_characters`, normalization and any selected
  voice fees must be reconciled before later live use. Only existing voice IDs
  are accepted by the lab; its default male/female slots remain unconfigured.

## Fish Audio

- [Official JSON REST/OpenAPI](https://docs.fish.audio/api-reference/endpoint/openapi-v1/text-to-speech.md):
  `POST https://api.fish.audio/v1/tts`, bearer binding, explicit `model` header
  `s2.1-pro` or `s2.1-pro-free`. Unknown/omitted model headers can fall back to
  the paid model, so the adapter accepts only its reviewed model allowlist.
- JSON `reference_id` identifies an existing voice, not uploaded reference
  audio. OpenAPI defines a string; the lab does not invent a fixed hex-length
  API restriction. `references` and cloning endpoints are not used.
- WAV/24000, `normalize=true`, prosody speed 1, volume 0,
  loudness normalization false. HTTP audio is validated as common WAV.
  Normalization language is unset as documented for mixed-language input.
- No equivalent gentle parameter is invented. Expressive text tags would
  change the shared corpus, so that comparison condition is **UNSUPPORTED**.
- [Official billing](https://docs.fish.audio/developer-guide/models-pricing/pricing-and-rate-limits.md):
  S2.1 Pro USD 15 / million **UTF-8 bytes**; Free is listed at USD 0. The harness
  measures actual submitted UTF-8 bytes. Free-tier access, limits, commercial
  terms and absence of TTFA/DPA guarantees are not established by offline tests.

## ElevenLabs

- [Official convert contract](https://elevenlabs.io/docs/api-reference/text-to-speech/convert.md):
  `POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}`; `xi-api-key`
  binding, `output_format=wav_24000`, JSON `text`, `model_id`, `voice_settings`.
- [Current model IDs](https://elevenlabs.io/docs/overview/models): `eleven_v4`
  and `eleven_multilingual_v2`. The former can request `language_code=zh`;
  the convert reference explicitly excludes that field for Multilingual v2.
- The lab sets only speed 1.0, retaining other voice defaults. Style
  exaggeration is not a semantic gentle control; audio tags are excluded to
  preserve identical input. Gentle is **UNSUPPORTED** in this comparison.
- Zero-retention `enable_logging=false` is Enterprise-only; it is not sent or
  claimed here. Responses are WAV bytes, not JSON audio URLs.
- [Current published API prices](https://elevenlabs.io/pricing/api) list both
  v4 and Multilingual v2 at USD 0.08 / 1,000 characters (USD 80 / million),
  replacing the older shortlist's v2 price and unknown-v4 assumption.
- [Default-voice transition](https://elevenlabs.io/docs/help-center/product/voices/my-voices/what-are-default-voices)
  makes old default IDs a poor assumption for a new account. The lab leaves
  voice slots unconfigured rather than assuming catalogue access, Mandarin
  suitability or presenting gender from a code example.

## Azure Speech

- [Official REST](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/rest-text-to-speech):
  regional `POST https://{region}.tts.speech.microsoft.com/cognitiveservices/v1`,
  `Ocp-Apim-Subscription-Key`, `application/ssml+xml`, and
  `X-Microsoft-OutputFormat=riff-24khz-16bit-mono-pcm`. No STS token request.
- `neural` and `dragon-hd-flash` are **lab family labels**, not invented JSON
  model IDs. Actual selection is through the SSML voice name. Text is XML
  escaped; user text cannot inject `<audio>` or any other SSML.
- [Documented Chinese voice/style examples](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=text-to-speech):
  XiaoxiaoNeural / gentle, YunxiNeural / narration-relaxed; Chinese HD Flash
  Xiaoyi / gentle and Yunxia / comforting. These are syntax examples; the
  actual configured resource's catalogue and region availability are **NOT_RUN**.
- [HD capabilities](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/high-definition-voices)
  document limited SSML. The lab omits HD prosody and rejects non-default HD
  rates; it does not silently send an ignored setting. Other HD families are
  not guessed from naming patterns.
- [Billing definition](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech#pricing-note):
  Han characters count twice; SSML markup except speak/voice tags can also be
  billable. The estimate doubles Han ideographs/〇 and includes inner serialized
  style/prosody markup. Escaped entities are counted conservatively. Region/SKU
  prices stay **UNKNOWN**, not zero; no global Azure USD price is invented.

## Limits and authorization

All API/model/voice availability, actual response format, audible quality,
latency, billing, rights and retention behavior remain **NOT_RUN** against live
services. Public documentation can change. Recheck it and the selected resource
before any later owner-authorized execution.

The S01 CLI hard-locks `--execute-live`, even with a cap and configured process
environment. The future transport additionally checks explicit opt-in, known
bounded cost, phase authorization, HTTPS host allowlists, ephemeral environment
credentials, response limits and single-attempt I/O. Enabling it requires a
later authorized change; it is not a production billing system. Failed/pending
cache entries require local inspection, never automatic billable retry.
