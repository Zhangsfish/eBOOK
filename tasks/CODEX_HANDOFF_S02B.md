# 当前对话交接 — 第一版苏心接入

## 当前交付状态

本轮 **READY_FOR_AUDIT**；Files在两系统真实验证通过，整体仍保留BLOCKED_QA/真机BLOCKED_ENV。
正式App包含原生Swift中文前端、真实ORT、短段PCM播放、有界缓存/预取、苏心音色和独立语速。
App Sources树 `6d9339b31da7acd614971037c2e9151e493bdc48`，冻结自16fe15d。

- 7ff918a1c02f730bf37d351821b37dc79709c2e3 /18.5完整45769244490：42PASS/0FAIL/0SKIP。
- 同7ff918a /26.5完整45769249483：41PASS/1FAIL/0SKIP，Apple sawRange断言失败。
  两系统实际外部Files导入/取消、全部UI、真实苏心12项通过；两轮设备归档均验证6项模型和2份同源码声明。
- 只做一次干净26.5复核：565bae04468e9ae1c16eefb4fe08ad84120fac69 /45771793206。
  实际6项UI通过，但EBookTests在XCTest连接前signal abrt；摘要的第7项是启动错误记录，
  不是完成的测试方法。原生单测及设备归档未执行，没有完成Apple回调复核。
- App/测试/工程/脚本/资源准备在7ff918a、565bae0及d84ceb4间逐Git对象核对一致，
  见source-identity-d84ceb4.json。此后的交付只补文档和小型证据。

VoiceDB警告在旧通过日志也存在；现有artifact没有启动崩溃的完整stack，不能唯一归因代码或runner。
所有旧Files失败、超时部分结果及本次Apple/宿主失败保留；不再重跑、不降断言、不标阶段PASS。
真机首声/p95/各30分钟/发热耗电与新TestFlight未执行，独立分发审查待进行。

见 [报告](../reports/S02B_SUXIN_IOS_INTEGRATION.md) 和
[真机清单](../reports/S02B/DEVICE_CHECKLIST.md)。停在独立审查，不自批、自并或提前分发。
冻结PR #7、训练PR #11及Android线不改。

## 原始实施交接（保留背景）

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
