# EPUB compatibility repair —2026-11-28

Owner supplied a failing EPUB and phone screenshot after49.1; WeChat Reading/WPS
open it. This owner-reported core defect reopens PR12 on the existing branch from
425ea4d7bdbff7f6b4035d48314c5ccebeea0a26. Diagnose/fix import, retain all books,
reader UI and Suxin. Existing direct internal-TestFlight authorization for phone
fixes persists; no merge/public release or unrelated optimization/model work.

The attached commercial book remains local. Never put its text/file, corrected
copy, screenshots, paths or raw XML in Git, CI or public logs. Private evidence and
the corrected user copy belong in ignored .local-test-data/epub-compatibility/.
Public tests use newly written original EPUBs reproducing only the markup defect.

Initial local read-only diagnosis: ZIP CRCs all pass; one spine XHTML contains a
bare br void element, causing strict XML mismatched-tag failure. Six other XML
documents parse. Repair must not skip spine items, invent content, fetch DTDs or
relax entity/path/CRC/size/depth limits. Metadata and NCX remain strict XML.

DELIVERY.md and evidence.json will hold sanitized diagnosis, exact source/commands,
real native tests and packaging. Private-file checks are desktop structural checks,
not an iOS import claim. Match direct phone delivery to actual tested code and read
Apple availability before declaring a new version installable. Stop for phone feedback.

Final delivery: WAITING_OWNER_FEEDBACK,0.1.0(50.1) available. Exact reader
dfbcc0f9204a47960e16bb4a3270c9811a7da697;18.5/46042489928 and26.5/46042481531
each11PASS/0FAIL/0SKIP, exact method sets, unsigned arm64 and6+2 PASS. The cancelled
redundant push/all run46042395921 is not a passing test. Original screenshots only.
Bridge8a27770a05bfe997359abcb9764be637b1e29706/run46044956972 actually accepted50.1
at01:54:45Beijing and returnedVALID/INTERNAL_ONLY/existing-group/IN_BETA_TESTING
at01:57:00 on2026-11-28. Safe events inphone-delivery-evidence.json; raw logs and
private book evidence remain ignored. PHONE_DELIVERY.md is canonical phone status.
No new neural/long-listening/private-book native result inferred. Freeze changes
and uploads pending owner retry; no merge/public release or other workstream.
