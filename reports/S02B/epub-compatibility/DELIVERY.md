# EPUB import compatibility —2026-11-28

State: **WAITING_OWNER_FEEDBACK — TESTFLIGHT_AVAILABLE=YES,0.1.0(50.1)**.
Base425ea4d7bdbff7f6b4035d48314c5ccebeea0a26; exact tested reader
`dfbcc0f9204a47960e16bb4a3270c9811a7da697`. Existing PR12/branch only.
Previous installable internal version0.1.0(49.1) is retained.

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

## Actual verification

Fourteen tiny newly written original EPUB fixtures cover bare and paired void
tags, UTF-16 in both orders with/without BOM, comments/CDATA/quoted attributes,
non-void mismatches, truncation and internal/file/remote entity declarations.
Five new actual-import unit methods plus five existing EPUB/ZIP/TOC methods and
one actual import/read/TOC/relaunch UI method form the11-method native scope.
No book content from the owner's attachment is included.

| Environment | Actual XCTest | Real unsigned Release arm64 | Evidence |
|---|---|---|---|
| Xcode16.4(16F6), iOS18.5, iPhone16Pro simulator | 11PASS /0FAIL /0SKIP; exact11-method set | PASS;6 model files +2 runtime notices | [run46042489928](https://github.com/Zhangsfish/eBOOK/actions/runs/46042489928), [JSON](native-ios18.json) |
| Xcode26.6(17F113), iOS26.5, iPhone17Pro simulator | 11PASS /0FAIL /0SKIP; exact11-method set | PASS;6+2; original device archive entry actually executed | [run46042481531](https://github.com/Zhangsfish/eBOOK/actions/runs/46042481531), [JSON](native-ios26.json) |

Both are standard free public GitHub macOS ARM64/M1 Virtual3CPU runners. The
UI test actually imports the original malformed fixture, reads both chapters,
navigates the TOC, relaunches and checks the restored selected chapter. Original
first/second-chapter screenshots from both OS versions were visually inspected.
This scope does not rerun the full suite, neural synthesis, physical iPhone or
long-listening/performance tests. The private book was not sent to either runner.

Local PASS: Python3.11.11 syntax of generator/CI scripts,14 deterministic original
fixtures/all CRCs, `python scripts/generate_xcode_project.py --check`,
`python -m unittest discover -s Tests/Packaging -v` (5/5), and `git diff --check`.
Native entry: `python3 tools/suxin/scripts/ci_integration.py --scope epub` after
existing verified-resource preparation, long original fixture and project checks.

Workflow-edit push also triggered redundant default-all run46042395921. It was
cancelled in favor of the two deliberately scoped runs, never counted as PASS.
Artifacts retain7days; exact method states, raw-file hashes and archive metadata
are preserved in the two committed JSON records. See [evidence index](evidence.json).

## Actual internal phone delivery

Existing bridge `8a27770a05bfe997359abcb9764be637b1e29706` changes only two reader
pins and scope memory. YAML, exact two-pin-only workflow diff and shell syntax
PASS; release helpers, paired executable baseline, resource/static-link checks,
Secrets and owner group are unchanged. [Actual upload run46044956972](https://github.com/Zhangsfish/lecture-asset/actions/runs/46044956972)
is workflow50/attempt1, actual build0.1.0(50.1). Apple accepted it at
**2026-11-28 01:54:45 Beijing**, then returnedVALID/INTERNAL_ONLY, verified the
existing owner-group association, and returnedIN_BETA_TESTING/TESTFLIGHT_AVAILABLE
at **01:57:00 Beijing**. The unchanged helper checks expired=false before declaring
availability. No public release or merge. [Phone update](PHONE_DELIVERY.md) and
[safe actual events](phone-delivery-evidence.json).

The actual50.1 paired no-map/with-map executable SHA256 is
`7eba3d410451c6b0d81e45bba5742b1b84b2ba536005ae1c736cc611d22bf13c` in both
archives. The static-link guard proves activeOrtGetApiBase/no dynamic ONNX
dependency. Removing only the unused33,798-byte embedded framework leaves the
executable unchanged;6+2 reverified, app bytes93,199,189→93,165,391. This actual-build
baseline is distinct from the two CI unsigned executable hashes. Source, model
hash and all resources match their fixed manifests.

## Limits

Recovery is deliberately limited to HTML void-tag closure in UTF-8/UTF-16 XHTML;
arbitrary broken nesting, truncation, invalid attributes and custom entities
remain rejected. It is not a general browser HTML parser. The supplied original
book still requires the owner's phone retry; desktop structural checks and
original-fixture simulator tests do not establish that private phone result.

## References

- [HTML void elements](https://html.spec.whatwg.org/dev/syntax.html)
- [Apple XML external entities](https://developer.apple.com/documentation/foundation/xmlparser/shouldresolveexternalentities)
- [Apple never-resolve policy](https://developer.apple.com/documentation/foundation/xmlparser/externalentityresolvingpolicy-swift.enum/never)
