# S02A.4 模型研究工作区

## 目的与上游

- 服务 eBOOK 后续小说朗读模型，独立于 PR #12 的苏心第一版。
- 工作分支：`codex/s02a4-teacher-student-tts`，PR #11。
- 本轮基线：`c218f0c1cc38a14d6afdd51f2167f1a38d200019`；先读根 `AGENTS.md`、
  `docs/TTS_WORKSTREAMS.md` 与 `tasks/S02A4_TEACHER_STUDENT_TTS.md`。
- 2026-11-25 用户再次明确：本对话负责自训研究；训练全部在 AutoDL，先评估费用。
- 本轮用户明确批准首轮费用上限 **¥50**。随后明确 AutoDL 所需软件可自主安装，
  仅本机安装须先告知；已同步全局 `C:/Users/Zhang S/.codex/AGENTS.md`。

## 文件角色

- `fixtures/teacher_audition.json`：既有六段原创教师试听文本；不得用于学生训练或最终盲听。
- `scripts/autodl_audition.py`：固定资源下载/七段试听编排；plan 可在本机，fetch/run 仅云端。
- `scripts/estimate_cost.py`：有单位与吞吐假设的费用计算；结果不是实测。
- `scripts/check_preparation.py`：CPU 检查本机拒绝执行、文件损坏拒绝和预算单位，不导入模型。
- `scripts/bootstrap_autodl.py`：云端独立环境；先解析发行物并核对官方哈希，再按精确 URL 安装。
- `scripts/audit_audio.py`：完整解码/音频身份与幅度检查；不代表听校通过。
- `scripts/archive_pilot.py`：打包固定模型、所需源码与运行证据；不含环境或下载缓存。
- `config/`：锁定的来源与明确标为估计的预算假设。
- `config/cost_review_20261126.json`：将昨晚实测推理速度、语料留用率、训练更新耗时和
  公开蒸馏规模分列；旧 3 epochs 费用不是完整学生模型报价。公开项目的卡型不可直接套 4090 价格。
- `README.md`：本线操作入口与待执行项。
- `../../reports/S02A4_TEACHER_STUDENT_TTS.md`：本轮技术路线、成本、真实执行状态。
- `../../.local-test-data/s02a4/`：Git 忽略的源码核读缓存、模型、音频、数据与运行证据。

## 已确定的边界

- 首目标仍为固定 MOSS-TTS-Nano 与 `zh_6.wav`，先真实复现新小说声音供用户核听。
- 优先核验官方 SFT（监督微调）与 ONNX 路线；独立学生蒸馏为有证据需要后的备选。
- 云端下载、预处理、合成、训练、导出均归本线；本机不训练、不做持续推理重计算。
- 不修改 App 源码、App 测试、播放接口、工程、依赖或第一版发布状态/工作流。
- 模型、音频、训练数据不入 Git；不得把私人小说上传为训练或试听材料。
- 下载元数据/源码、写脚本或预算不等于合成/训练已发生。时间费用估计与实测分列。
- AutoDL 租卡已有原则授权；本轮成本评估不等于无限预算或批准批量数据生成。
- 不启动、关闭或改动其他任务的运行实例；可复用候选需先检查空间及现有作业。

## 当前状态与交接

- 本轮已在唯一选定的原关机 4090 实例开机，实际确认 ¥2.08/小时，独立目录
  `/root/autodl-tmp/ebook_s02a4`；磁盘初查可用约 41 GB。另一个运行 CPU 实例未动。
- 已设平台定时关机到服务器时间 2026-11-26 01:20；它是兜底，收尾仍要确认实际关机。
- 首轮实际执行 SHA `60a66d7ec1af723a7fe1ec1c7d0fa43f433b663b`；54 份依赖核对官方发行 SHA，
  CUDA 及 7 段原创合成通过，536.32 秒，48 kHz/双声道。新故事 247.60 秒。
- `SYNTHESIZED_UNREVIEWED`：人工核听、ASR 对齐、实际微调、完整恢复、导出、真机仍 `NOT_RUN`。
- 私有归档 `../../.local-test-data/s02a4/outputs/s02a4_pilot_20261126.tar.gz` 共449,500,825 bytes，
  119 文件逐哈希验收，模型/声音不入 Git；`outputs/recovered/` 为恢复的声音/元数据，
  `outputs/listening/` 为便听 MP3。完整归档身份见报告。
- 2026-11-26 00:40 已在 AutoDL 平台确认本次 GPU 实例“已关机”，SSH 已关闭，估算约¥1.7；
  精确账单未提取。后续不占 GPU 等待用户，新的模型评价仍待用户核听。
- 先核读固定源码及权重来源，确定小试成本；实际复现获得用户核听后再扩大训练。
- 不将本分支历史 `STATUS.md` 覆盖到主线；不合并任何 PR 或自动发布。
