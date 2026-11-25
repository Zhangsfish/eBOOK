# S02B Suxin production integration support

Authority: tasks/S02B_SUXIN_IOS_INTEGRATION.md and docs/TTS_WORKSTREAMS.md.
Work only in E:/myself/eBOOK-s02b, branch codex/s02b-suxin-ios-integration / PR12.
Start baseline1eb0eef18e7011feb8034a393f084a91483b9a8e (reader main83fa0d9).
Frozen S02A.3 reference checkout E:/myself/eBOOK-s02a remains read-only at eeee144.
No model training, model search or cloud synthesis. Preserve reader controls/TOC.

## Planned file map
- manifests/: exact source hashes and generic linguistic conversion data, not weights.
- scripts/: verified model/data preparation and author-frontended original-text oracle.
- tests/: resource/cache/source security checks; native tests belong to App Tests.
- ../../.local-test-data/s02b/: ignored model/frontend resources, real audio/logs.
- ../../reports/S02B/: task memory and public-safe evidence only.

## Implementation decisions
Use the already validated ORT1.28.2 iOS runtime directly, not the full historical
Kokoro/Matcha experiment. Swift Mandarin G2P uses the full pinned pypinyin0.55
character/phrase lexicons, maximal phrase matching and exact author rules.
Generic syllable conversion data is a linguistic lookup, never per-book IDs.
Native text handling must be checked against actual author's Python on unseen
original texts; diagnostic five-case precomputed IDs are not end-to-end proof.

Initial English/unsupported-character scope may explicitly use Apple system speech
with a visible notice, as permitted by the task; never silently drop letters or
pretend eSpeak/English G2P was ported. Keep Apple voices and existing rate settings.
Suxin uses short PCM chunks, one background session, bounded prefetch/cache and
generation identities so cancellation cannot play or persist late results.

Actual host is Windows, not the preparer's historical Linux statement. Xcode is
available only through ordinary free macOS CI. The authorized internal TestFlight
bridge exists, but new code must retain independent audit and real device gates.
No new dependency installation is currently needed: reuse the already approved
Suxin Python environment for local oracle generation, standard-library build tools,
and pinned native framework/source/data downloads. No global environment edits.
