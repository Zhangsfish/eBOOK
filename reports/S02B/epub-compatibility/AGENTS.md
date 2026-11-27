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
