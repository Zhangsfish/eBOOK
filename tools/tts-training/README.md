# 后续小说朗读模型：AutoDL 研究入口

本线服务 eBOOK 第二版模型，使用 PR #11；苏心第一版接入和发布由 PR #12 独立负责。
本机只核读源码、编排原创材料、做轻量检查和传输。合成、预处理、训练与导出放在 AutoDL。

## 当前交付

- `config/sources.lock.json`：固定官方代码、训练基座、codec 与参考音频身份。
  训练用资源共 17 个文件，323,443,057 bytes；大权重的 SHA256 来自官方 LFS 元数据，
  **尚未下载核验**。小型配置/加载代码与参考音频已下载核对。`onnx_reference_metadata`
  只记录部署资源体积，不能用于宣称 ONNX 已验证。
- `fixtures/teacher_audition.json`：保持既有六段文本原样。
- `fixtures/continuous_audition_20261125.json`：新增原创连贯故事，目标试听 2–5 分钟；
  实际时长待合成。两个文件都仅用于教师试听，不用于训练或最终盲听。
- `scripts/autodl_audition.py`：`plan/fetch` 只用标准库，`plan` 可在本机运行；`fetch/run` 拒绝本机执行。
  它下载校验固定资源，再串行调用官方 `infer.py`，保留每段日志、文本与音频哈希、
  时长和进程总耗时。它不安装软件、不训练、不自动关机。
  `run` 在云端用官方依赖 `soundfile` 读取 WAV 元数据。
- `config/cost_assumptions.json` 和 `scripts/estimate_cost.py`：可复算的敏感性预算，
  所有吞吐参数都是假设；不能冒充实际账单或训练速度。
- 本轮结论及证据：[研究报告](../../reports/S02A4_TEACHER_STUDENT_TTS.md)。

## 先做什么

先用已选 MOSS-TTS-Nano 与固定 `zh_6.wav` 生成新故事，交付用户核听。
获得对新音频的认可后，再用原创且分组隔离的数据验证官方 SFT（监督微调），
验证完整恢复和导出，再扩至 10–20 小时。若无需训练已满足需求，可保留直接模型作对照；
更小学生的蒸馏按真实手机瓶颈决定，不预设 Piper。

当前只有 `PREPARED`：本次没有 GPU 开机、真实合成、微调、恢复或导出。
这些操作仍为 `NOT_RUN`。官方演示获认可不等于本次新故事获认可。

## 本机轻量命令

从仓库根目录运行，均无需新安装：

```powershell
& 'C:\conda_envs\myenv\python.exe' tools/tts-training/scripts/autodl_audition.py plan
& 'C:\conda_envs\myenv\python.exe' tools/tts-training/scripts/estimate_cost.py --audio-hours 1 10 20
& 'C:\conda_envs\myenv\python.exe' tools/tts-training/scripts/check_preparation.py
```

`plan` 输出 Linux 路径与占位命令 `python`，实际执行应使用核验过的云端独立环境。

## AutoDL 首轮操作约定

使用独立目录 `/root/autodl-tmp/ebook_s02a4`。开机前重新核对实际单价、其余作业、
磁盘可用空间和预算；现有运行实例不因本任务停机或被占用。此前可见的已关机
4090 实例有剩余免费数据盘，可作为复用候选，最终以云端 `df` 与作业检查为准。

先清点已装环境。固定上游要求 PyTorch/torchaudio 2.7.0 与 Transformers 4.57.1；
指南涉及的 `accelerate`、`tqdm` 和导出需要的 `onnx` 并未全部列在该 revision 的依赖文件中。
独立环境和完整依赖锁仍待云端确认；已有环境不足时，按用户安装规则说明后处理，
不直接覆盖其他任务环境。这里没有一条被宣称已验证的安装命令。

将本研究目录传至云端后，在确认好的环境内执行：

```bash
python tools/tts-training/scripts/autodl_audition.py fetch
python tools/tts-training/scripts/autodl_audition.py run --run-id audition-001 --max-seconds 7200
```

`fetch` 不执行模型代码、不安装包；`run` 才加载固定资源并通过官方 CLI 合成。
默认写入七段试听，保持原生 48 kHz / 双声道，不添加未经证实的风格指令。
采样值显式取固定 `infer.py` 的真实默认值；官方演示当时的随机种子和完整采样设置
未公开确认，因此不声称逐样本复现演示波形。

`--max-seconds` 仅限制合成子进程时间，**不会关闭实例或停止计费**。采用平台定时关机时，
必须确认实例专用于本任务并保留日志；任务完成后备份、验收文件并确认关机状态。
程序退出时已有输出保留；继续执行需换新 `--run-id`，不覆盖旧试听。

每段 WAV 头和哈希检查仅证明输出存在且可解析；还需完整解码、漏读/重读筛查与人工听校。
报告的 `wall_rtf_including_model_load` 含每段重新加载模型的时间，不能作为手机首声或纯推理吞吐。

## 正式训练前必须补齐

1. 用户核听新故事，记录音色与自然朗读方式；参考声音权利独立于模型代码许可证。
2. 原创语料先按故事/场景分 train、validation、final listening，再生成；试听七段永不混入。
3. 检查完整 token 序列长度。固定版 `dataset.py` 会截断超长样本；不能只检查 WAV 时长。
4. 补齐并实际验证优化器、调度器、随机状态、采样/批次进度的断点保存与恢复。
   固定版 `sft.py` 没有完整 resume；从权重重新开始只能称 warm start。
5. 真实测量 train/resume/export/infer、显存和吞吐后再改预算，完成同文苏心对照与长听。

跨线交接只通过完整资源/许可/哈希、推理规范及实际证据；不改第一版 App 或发布流程。
