# Technical Plan

## Baseline architecture
- UI: SwiftUI.
- App lifecycle / persistence: SwiftData or a small Codable/SQLite persistence layer; choose the simplest robust option compatible with the deployment target.
- File import: SwiftUI `fileImporter` / UIDocumentPicker integration with security-scoped URL handling and app-owned copies.
- EPUB: use a maintained, license-compatible parser/library if necessary; inspect dependency license and maintenance before adoption. Parse metadata, spine, navigation/TOC, XHTML content, and images defensively.
- TXT: detect BOM first; support strict UTF-8, UTF-16 LE/BE, GBK, and GB18030 decoding. Many Chinese novel TXT files are GBK-encoded. Normalize line endings while preserving paragraph boundaries. Do not silently accept mojibake or lossy replacement characters; report a clear decoding error if the encoding cannot be determined.
- Reading renderer: native text/layout components with chapter-aware navigation. Avoid a giant single Text view for a multi-million-character novel.
- Horizontal renderer: demand-driven TextKit viewport layout with UIPageViewController; at most4 source blocks per page,8 cached small source strings and64 predecessor positions. Never pre-layout a whole book. Optional UTF16 anchors migrate legacy block/fraction positions and preserve reflow location.
- Shelf appearance is a separate persisted preference; root navigation selects shelf/reader color schemes from their respective values. Keep the existing in-book theme control.
- TXT navigation: use conservative heading heuristics for common forms such as `001标题`, `第N章 标题`, and `N.第N章标题`. Do not classify every numbered line as a chapter. If confidence is low, keep the book readable as continuous text and avoid inventing a misleading TOC.
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
   Suxin resolves one bounded source block with phrase/tone context, then slices mapped phoneme IDs into short audio chunks. Number/time protection applies to both outer windows and inner clauses; cache identity includes actual model-input IDs and the contextual schema version.
3. Synthesis: provider adapter.
4. Cache: local audio cache keyed by book fingerprint + chapter/chunk + voice/model + synthesis settings.
5. Playback queue: AVPlayer-based queue for generated audio; AVSpeechSynthesizer fallback adapter.
6. Position mapping: map audio chunk/time back to chapter and text position.

Do not expose vendor API keys in the iOS binary. Production cloud synthesis requires a small authenticated backend/proxy that stores provider credentials server-side, enforces quotas, and returns audio securely. Do not deploy or incur costs in S00. A future provider evaluation should compare Mandarin samples from at least Azure Neural/HD, ElevenLabs, MiniMax, and Fish Audio (subject to current API availability and commercial terms). Evaluate voice warmth, prosody, punctuation, dialogue differentiation, long-form consistency, latency, stability, cost per million Chinese characters, data retention, and licensing. Select by listening tests, not marketing claims.

## Long-form performance
- Do not synthesize an entire novel in one request.
- Generate the current chunk and prefetch only a small number of following chunks.
- Cache audio locally with an eviction policy and clear-cache control.
- Keep book text local by default. Before any future cloud synthesis, disclose that the selected text is sent to the provider for processing.
- A provider failure must not corrupt reading/listening progress.

## Security and privacy
- No secrets in source, plist, app bundle, GitHub Actions logs, or client-side configuration.
- No analytics or account system in the MVP.
- Imported books remain in the app sandbox; no background upload of full books.
- Review third-party SDK privacy manifests and data collection before adding dependencies.

## Testing
- Unit tests for TXT decoding (UTF-8, UTF-16 LE/BE, GBK, and GB18030), EPUB metadata/TOC extraction, paragraph/chunk segmentation, progress persistence, and malformed-file handling.
- UI/simulator tests for import -> open -> change typography/theme -> navigate TOC -> resume.
- Playback tests for play/pause/seek, background audio, interruption/resume, and position persistence where simulator/device support permits.
- Use `scripts/generate_long_gb18030_fixture.py` to create an original synthetic fixture with 624 chapters plus an afterword, 2,301,482 Unicode characters, and 73,176 lines. The generated output is local-only and ignored by Git.
- Test large-file import, incremental rendering/scrolling, memory behavior, reading-position persistence, and heuristic chapter navigation against the generated fixture.
- Do not include complete copyrighted novels or user-imported commercial books in source, fixtures, CI, app bundles, logs, or reports.
- ZIP is a container, not an ebook text encoding. S00 only needs EPUB/TXT import; ZIP import and archive extraction are out of scope.

## Compatibility profile from planning
A ZIP supplied during planning contained one TXT entry. Its inner TXT was 4,439,158 bytes and decoded strictly with both GBK and GB18030 to 2,301,482 Unicode characters including CRLF line endings and 73,176 lines. Its header identified `绝境黑夜` by `滚开` and stated chapter 624 plus an afterword. Heading formats were heterogeneous. These non-text measurements are recorded in `docs/TEST_DATA.md`; the source archive and its text are not in the repository. The synthetic fixture is the reproducible automated test input.
