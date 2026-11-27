# Owner EPUB import defect —2026-11-28

State: **WAITING_OWNER_FEEDBACK — TESTFLIGHT_AVAILABLE=YES,0.1.0(50.1)**.
Branch codex/s02b-suxin-ios-integration / PR12.
Base425ea4d7bdbff7f6b4035d48314c5ccebeea0a26; exact compiled/tested source
dfbcc0f9204a47960e16bb4a3270c9811a7da697. Native18.5/26.5 each11/11,0fail/0skip,
unsigned arm64/6+2 PASS. Bridge8a27770/run46044956972; Apple accepted01:54:45 and
verifiedVALID/INTERNAL_ONLY/existing owner group/IN_BETA_TESTING at01:57:00Beijing
on2026-11-28. [Delivery](../reports/S02B/epub-compatibility/PHONE_DELIVERY.md).
Prior49.1 retained. Stop further changes/uploads and await the owner's original-file
phone retry; private native import remainsNOT_RUN until that feedback.

Owner supplied an EPUB that other readers open but eBOOK rejects as XML/XHTML
damaged. Diagnose locally, repair narrowly, add original fixture/native regressions
for HTML-style void tags and unchanged security boundaries. Keep every spine item
and all text; keep metadata/NCX strict and external entities disabled.

The private book and any repaired copy remain ignored/local, never Git/CI. Provide
a minimally changed private copy for immediate retry, while fixing the generic App
parser. Document private structural validation separately from real iOS tests using
original fixtures. No new tools, model changes, paid services, merge or public release.

Continue the owner's existing direct internal phone-test path after real focused
validation; no new web review gate for this owner-reported core defect. Record exact
source/build and Apple availability, then WAITING_OWNER_FEEDBACK.
