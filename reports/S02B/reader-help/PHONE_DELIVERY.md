# Reader help — owner phone delivery

State: **WAITING_OWNER_FEEDBACK — TESTFLIGHT_AVAILABLE=YES**.

- Actual available version/build: **0.1.0 (49.1)**, workflow number49/attempt1.
- Reader: `1619c200ed7552be5687c4446240daefe676fb4c`.
- Bridge: `ba2c4417f3302f0f8a16c8d7003a167149993dec`.
- [Actual run46017595137](https://github.com/Zhangsfish/lecture-asset/actions/runs/46017595137).
- Actual18.5 and26.5 focused native/XCTest each14/14,0skips; both unsigned arm64/6+2 PASS. [Test report](DELIVERY.md).
- Apple accepted49.1 at **2026-11-27 22:41:35 Beijing**; at **22:43:46 Beijing** it returned `VALID`, `INTERNAL_ONLY`, verified the existing Owner iPhone association, and returned `IN_BETA_TESTING`/`EBOOK_TESTFLIGHT_AVAILABLE build=49.1`. The existing helper also rejects expired builds before declaring availability. [Safe actual events](phone-delivery-evidence.json).
- Physical installation/upgrade, gesture feel, tutorial first-visit experience and VoiceOver: NOT_RUN; owner will test after availability.

Owner explicitly requests direct internal delivery after validation, without another web review for this UI scope. Keep49.1 separate from old48.1 and retain prior builds. No merge or public release.

The actual49.1 runner used Xcode26.6. Its no-map and with-map Release archives have the same executable SHA256 `bf67b38b9e0bb664fa0823b84f515c17ac46d25438ea126f71a582256b3ae091`. The existing guard proved static ONNX linkage/no dynamic dependency, removed only the unused33,798-byte framework, and verified the unchanged executable and6+2 resources. App bytes93,182,237→93,148,439. Model SHA remains `5dbe3500e7d36835e073dad4f3502a579ae497f62c0a6574c736345237e1e7aa`. CI unsigned hashes use different build settings/numbers and are not substituted for this actual-build baseline.

Update notes: four quiet reader icons in one bottom row; smaller-dot progress slider below; replayable/skippable animated tutorial and feedback/contact in bookshelf settings. Existing Suxin, books, saved positions, themes and page modes remain unchanged.

Update the existing app in TestFlight, retaining its library. Try the bottom controls/progress, and open tutorial/feedback from bookshelf settings. Stop development/uploads now and await the owner's actual phone feedback; installation, touch/VoiceOver feel and long-listening/thermal/battery acceptance are not inferred from Apple availability or the focused UI suite.
