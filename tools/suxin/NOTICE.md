# Local Suxin integration — provenance and notice status

Suxin-Light upstream: TEQUILA123/suxin-light, revision
5ee2da546f3635da263602842d238d8624cb7a81. The author's complete LICENSE
and pypinyin 0.55.0 LICENSE are included beside the model resources.
The native Mandarin frontend adapts the author's rules and generic pypinyin
character/phrase data. Python, Piper, eSpeak-ng and English phonemization
binaries are not included in this iOS implementation. Unsupported spans use
the separate Apple system-speech adapter with an explicit notice.

ONNX Runtime is statically linked via csukuangfj/onnxruntime-libs at
8ebc5ebf92190903c274a7621ba4c96a732335ec. The iOS XCFramework ZIP's SHA-256
is 2c2299acbb461d26d4bac4bc85985d40e7c7177ed6072703ae0846d88b0b4599.
Its inspected archive contains no LICENSE/NOTICE/ThirdPartyNotices file.
The publisher's pinned build workflow names microsoft/onnxruntime tag
v1.28.2; attempts to retrieve that tag and its LICENSE/ThirdPartyNotices
on 2026-11-26 returned 404. Do not substitute a different tag's notices
and label them as verified for this binary. Exact source and the complete
static dependency notice set remain an internal-distribution gate.

The model's root declaration also names Piper VITS (GPL-3.0), eSpeak-ng via
Piper (GPL-3.0), Fun-CosyVoice3 teacher speech and pypinyin (MIT). Omitting
Piper/eSpeak binaries from this App does not establish clearance for model
training, distilled weights or data. No complete distribution-clearance
claim is made. Local native integration/testing proceeds independently;
TestFlight/public distribution requires the unresolved materials and review.
