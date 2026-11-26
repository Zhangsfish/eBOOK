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
The publisher's pinned workflow names microsoft/onnxruntime tag v1.28.2;
direct tag/material queries returned404. Both actual binary slices embed
git-commit-id33ca962. The same source commit is available in the binary
publisher's csukuangfj/onnxruntime fork at full commit
33ca9628233dc8f002435e868d4c2e9f82766ca1. Its Microsoft MIT LICENSE and complete
ThirdPartyNotices.txt are fetched by immutable URL, byte count and SHA256,
then bundled as ONNXRuntime-LICENSE.txt and ONNXRuntime-ThirdPartyNotices.txt.
The Release archive check verifies these actual bundled bytes. This is not
a different-version notice substitution. The original ZIP's zero notices
and past404 evidence remain recorded.

The source-commit match is an embedded build-stamp check, not a reproduced
binary build or exhaustive platform dependency BOM. Material presence and
independent distribution review are separate states.

The model's root declaration also names Piper VITS (GPL-3.0), eSpeak-ng via
Piper (GPL-3.0), Fun-CosyVoice3 teacher speech and pypinyin (MIT). Omitting
Piper/eSpeak binaries from this App does not establish clearance for model
training, distilled weights or data. No complete distribution-clearance
claim is made. Local native integration/testing proceeds independently;
TestFlight/public distribution requires the unresolved materials and review.
