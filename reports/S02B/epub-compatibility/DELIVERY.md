# EPUB import compatibility —2026-11-28

State: **IN_PROGRESS**. Base425ea4d7bdbff7f6b4035d48314c5ccebeea0a26;
previous installable internal version0.1.0(49.1). Existing PR12/branch only.

## Diagnosis and repair

The owner's local EPUB is a CRC-valid ZIP. One of its four spine pages contains
an unclosed HTML `br`, so the strict XML parser rejects the complete import.
The other six XML/OPF/NCX/XHTML documents parse strictly. No DRM bypass or content
download is involved. The attachment, repaired book and private evidence stay in
ignored local storage and are not test artifacts or repository files.

A private immediate-use copy inserts only the missing slash in that one tag.
All other uncompressed ZIP members remain byte-identical; every XML and ZIP CRC
passes desktop validation. This is **not** an iOS import result for the private book.

The App first retains strict parsing. Only spine/nav XHTML may retry a bounded,
quote/comment/CDATA-aware closure of HTML void elements, then undergo the same
strict XML validation. UTF-8/UTF-16 byte order/BOM and content are retained. Metadata,
container and NCX remain strict; entities are refused before retry and external
entity resolution is explicitly disabled. Path, CRC, bytes, nodes, depth, text and
staged-import cleanup checks remain active. No chapter is skipped.

## Verification in progress

Fourteen tiny newly written original EPUB fixtures cover bare and paired void
tags, UTF-16 in both orders with/without BOM, comments/CDATA/quoted attributes,
non-void mismatches, truncation and internal/file/remote entity declarations.
Five new actual-import unit methods plus five existing EPUB/ZIP/TOC methods and
one actual import/read/TOC/relaunch UI method form the11-method native scope.
No book content from the owner's attachment is included.

Local Python syntax, fixture generation and deterministic Xcode project checks
PASS. Native iOS XCTest, unsigned archives, signing/upload and installability are
**NOT_RUN/PENDING** until the actual CI and Apple results are recorded.

## References

- [HTML void elements](https://html.spec.whatwg.org/dev/syntax.html)
- [Apple XML external entities](https://developer.apple.com/documentation/foundation/xmlparser/shouldresolveexternalentities)
- [Apple never-resolve policy](https://developer.apple.com/documentation/foundation/xmlparser/externalentityresolvingpolicy-swift.enum/never)
