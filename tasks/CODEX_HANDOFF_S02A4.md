# 另一个对话交接 — 第二版自训模型

仓库 `Zhangsfish/eBOOK`，分支 `codex/s02a4-teacher-student-tts`，PR #11。
用独立 worktree；先拉取最新分支，读 `AGENTS.md`、`STATUS.md`、产品/技术规格、
`docs/TTS_WORKSTREAMS.md` 与 `tasks/S02A4_TEACHER_STUDENT_TTS.md`。

用户最新决定：第一版在另一个对话直接接入苏心，验证延迟后交付手机使用；
本对话独立做后续模型。**第一版不等待本线；本线不修改第一版 App 或发布流程。**
当前 App 线为 `codex/s02b-suxin-ios-integration`，任务
`tasks/S02B_SUXIN_IOS_INTEGRATION.md`。共享接口需求按协作约定同步。

第一目标是上一轮用户说“这个可以”的 MOSS-TTS-Nano「深夜温柔晚安」。
精确代码/演示 revision、`zh_6.wav` 参考身份及输出 blob 见任务。
先用真正模型/参考生成现有六段原创小说和连贯 2–5 分钟 WAV，交付用户核听。
不是重新泛找教师，不把官方 demo 当本次合成。偏好平静自然的小说陈述，
单音色/混读是实现者决定，用户没有强制其中一种。

随后在研究目录验证 direct ONNX、官方 SFT 或必要时的蒸馏；固定数据划分、
版本、哈希和可恢复 recipe，小 train/resume/export/infer 试验通过才扩量。
AutoDL 租卡已原则同意，当前没有连接实例或运行作业。架构/数据准备归执行者，
不要再让用户替我们挑架构或找教师。用户只判断实际声音是否满意。

苏心实验 PR #7 已交付，冻结 HEAD `eeee1443c1aac561035cf30590ff323c30ccab8a`，
报告已存在；它不是 load-only，亦未完成原生文字前端和真机验收。
后续以新 App 线的真实测量作为最新部署基线，不覆盖其源码或状态。

只改 `tools/tts-training/`、本线任务/交接和报告。第一版合入后更新到最新 main，
用完整资源清单、推理/训练/导出命令、前端/运行时要求、许可、声音和性能证据
交接第二版模型；不直接改第一版 Xcode/播放/签名/版本号。实际发生的合成、
训练和设备测试分列，写文档不算执行。遵循独立审查，不自动合并或发布。
