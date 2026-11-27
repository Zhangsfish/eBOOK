# EPUB compatibility — owner phone update

State: **WAITING_OWNER_FEEDBACK — TESTFLIGHT_AVAILABLE=YES**.

- Actual available version/build: **0.1.0(50.1)**, workflow50/attempt1.
- Exact compiled/tested reader: `dfbcc0f9204a47960e16bb4a3270c9811a7da697`.
- Bridge: `8a27770a05bfe997359abcb9764be637b1e29706`.
- [Actual upload46044956972](https://github.com/Zhangsfish/lecture-asset/actions/runs/46044956972), job140661783078.
- Actual native18.5 and26.5 EPUB suites each11PASS/0FAIL/0SKIP, exact method sets; both unsigned Release arm64 archives/6+2 PASS.26 also executes the original device entry. [Tests and limits](DELIVERY.md).
- Apple accepted50.1 at **2026-11-28 01:54:45 Beijing** and returnedVALID/INTERNAL_ONLY, verified existing owner-group association andIN_BETA_TESTING/TESTFLIGHT_AVAILABLE at **01:57:00 Beijing**. Existing helper also rejects expired builds. [Safe readback/archive events](phone-delivery-evidence.json).

更新说明：兼容部分EPUB中的未闭合换行、图片等HTML空标签。补齐后重新严格解析，保留正文、章节、插图和目录；不跳过页面。苏心、书库、位置、主题和阅读操作沿用现有版本。

请在TestFlight直接更新现有App，再选择原来的EPUB重新导入，查看正文和目录。先前失败的导入未保存成书，现有书库继续保留。此前提供的单标签格式修复副本也只在本地保存；原附件未修改。

The owner's private book never entered Git/CI. Its desktop minimal-copy XML/CRC
and unchanged-other-members checks PASS, while its actual phone import remains
NOT_RUN until owner feedback. Simulator evidence uses newly written original
fixtures, including actual import/read/TOC/relaunch. No new synthesis, long-listening,
thermal/battery or VoiceOver acceptance is claimed by this import-only scope.

Prior49.1 remains retained. The owner-authorized direct internal-test path is used;
no new independent audit is claimed, no PR merge or public release. Stop development
and uploads now, and await the owner's original-file phone retry.
