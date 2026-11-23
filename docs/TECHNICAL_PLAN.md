# Technical Plan

## Baseline architecture
- UI: SwiftUI.
- App lifecycle / persistence: SwiftData or a small Codable/SQLite persistence layer; choose the simplest robust option compatible with the deployment target.
- File import: SwiftUI `fileImporter` / UIDocumentPicker integration with security-scoped URL handling and app-owned copies.
- EPUB: use a maintained, license-compatible parser/library if necessary; inspect dependency license and maintenance before adoption. Parse metadata, spine, navigation/TOC, XHTML content, and images defensively.
- TXT: detect BOM first; support strict UTF-8, UTF-16 LE/BE, and GB18030/GBK decoding. Many Chinese novel TXT files are GBK-encoded. Normalize line endings while preserving paragraph boundaries. Do not silently accept mojibake or lossy replacement characters; report a clear decoding error if the encoding cannot be determined.
- Reading renderer: native text/layout components with chapter-aware navigation. Avoid a giant single Text view for a multi-million-character novel.
- Local speech: AVSpeechSynthesizer adapter for offline fallback and initial playback proof.
- Audio session: AVAudioSession configured for spoken audio / background playback; handle interruptions, route changes, lock-screen controls, and remote commands.
- State: persist book identity, chapter/anchor, reading progress, listening progress, voice preference, rate, theme, font size.

## TTS provider abstraction
Define a provider protocol independent of UI/player, conceptually:
- voice catalog / capability metadata
- synthesize(text, voice, style, rate) -> audio asset or stream
- cancellation and error reporting
- optional word/sentence timing metadata

Separate:
1. Text preparation: remove navigation noise, normalize punctuation, preserve dialogue and paragraph pauses.
2. Chunking: split on paragraph/sentence boundaries, enforce vendor payload limits, keep stable chunk IDs.
3. Synthesis: provider adapter.
4. Cache: local audio cache keyed by book fingerprint + chapter/chunk + voice/model + synthesis settings.
5. Playback queue: AVPlayer-based queue for generated audio; AVSpeechSynthesizer fallback adapter.
6. Position mapping: map audio chunk/time back to chapter and text position.

Do not expose vendor API keys in the iOS binary. Production cloud synthesis requires a small authenticated backend/proxy that stores provider credentials server-side, enforces quotas, and returns audio securely. Do not deploy or incur costs in S00. A future provider evaluation should compare Mandarin samples from at least Azure Neural/HD, ElevenLabs, MiniMax, and Fish Audio (subject to current API availability and commercial terms). Evaluate voice warmth, prosody, punctuation, dialogue differentiation, long-form consistency, latency, stability, cost per million Chinese characters, data retention, and licensing. Select by listening tests, not marketing claims.

## Long-form performance
- Do not synthesize an entire novel in one request.
- Generate the current chunk and prefetch only a small number of following chunks.
- Cache audio locally with an eviction policy and clear-cache control.
- Keep book text local by default. Before any cloud synthesis, disclose that the selected text is sent to the provider for processing.
- A provider failure must not corrupt reading/listening progress.

## Security and privacy
- No secrets in source, plist, app bundle, GitHub Actions logs, or client-side configuration.
- No analytics or account system in the MVP.
- Imported books remain in the app sandbox; no background upload of full books.
- Review third-party SDK privacy manifests and data collection before adding dependencies.

## Testing
- Unit tests for TXT decoding (UTF-8, UTF-16, and GB18030/GBK), EPUB metadata/TOC extraction, paragraph/chunk segmentation, progress persistence, and malformed-file handling.
- UI/simulator tests for import -> open -> change typography/theme -> navigate TOC -> resume.
- Playback tests for play/pause/seek, background audio, interruption/resume, and position persistence where simulator/device support permits.
- Include synthetic Chinese test books in UTF-8 and GBK/GB18030 encodings with multiple chapters, dialogue, punctuation, and long paragraphs. Do not include copyrighted novel text.
- ZIP is a container, not an ebook text encoding. S00 only needs EPUB/TXT import; users can extract a ZIP containing a TXT in the iOS Files app before importing the TXT. Do not add ZIP support or a dependency unless a later task explicitly authorizes it.

## Real-world compatibility note
A user supplied a ZIP containing one `绝境黑夜.txt` file. The inner TXT decodes strictly as GBK and its header identifies the title and author; its chapter structure runs through chapter 624 and an afterword. This establishes a useful format/scale test case, not the file's distribution rights. The archive and novel text must not be committed to GitHub, fixtures, CI, or app bundles. A private local smoke test may be performed only at the user's direction and subject to the user's rights to use the file.