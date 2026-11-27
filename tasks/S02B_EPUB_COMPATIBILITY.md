# Owner EPUB import defect —2026-11-28

State: IN_PROGRESS. Branch codex/s02b-suxin-ios-integration / PR12.
Base425ea4d7bdbff7f6b4035d48314c5ccebeea0a26, available49.1.

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
