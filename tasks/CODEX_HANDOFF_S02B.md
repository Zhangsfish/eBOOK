# 当前对话交接 — 第一版苏心接入

在 `Zhangsfish/eBOOK` 的 `codex/s02b-suxin-ios-integration` 独立 worktree 工作。
先读 `AGENTS.md`、`STATUS.md`、产品/技术规格、`docs/TTS_WORKSTREAMS.md` 和
`tasks/S02B_SUXIN_IOS_INTEGRATION.md`，以该任务为本线的 READY 授权。

用户决定把任务分成两个对话：本线直接接入已经试听认可的苏心，验证延迟和连续
播放，通过后交付现有内部 TestFlight；另一条线在 PR #11 做自训模型，留待第二版。
本线不等训练，不再选择 Kokoro/Matcha 或教师模型，不向用户抛架构问题。

从 main `83fa0d90fd4cd0dbcd791eeb4a3edd53ba985656` 开始；冻结实验参考为 PR #7
的 `eeee1443c1aac561035cf30590ff323c30ccab8a`，按需读其报告/资源清单/原生桥。
不能把实验整包合并进 App。苏心确实合成过，但只有作者预计算 ID 的 iOS 后端
验证，完整原生文字前端和真机首声尚未完成；保留原始慢段证据。

按任务实施：原生前端一致性 → 真实 ONNX 图 → 短首块/有界预取/取消 → App
音色与位置/后台操作 → 真机端到端和长听 → 审查及既有签名/内部 TestFlight。
保留 Apple 系统语音和已验收阅读行为。报告真实执行 SHA、测试和精确环境阻塞；
不得把源码、桌面数据、unsigned IPA 或写好的任务说成已在手机上线。

每次开始先检查两分支的新提交，遵守文件归属；不写 `tools/tts-training/` 或训练
产物，不修改 PR #11 分支。接口需求写入本任务交接给另一线。
