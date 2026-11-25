# S02A.4：AutoDL 模型路线与首轮记录

研究日期：2026-11-25–26（Asia/Shanghai）。分支 `codex/s02a4-teacher-student-tts`，PR #11。
本轮来自用户的明确任务：自训研究独立推进，训练全部使用 AutoDL，不修改第一版 App 或发布流程。

## 基线与权限

- 接手 PR #11 HEAD：`c218f0c1cc38a14d6afdd51f2167f1a38d200019`，仍为未合并草稿。
- 接手时 main：`83fa0d90fd4cd0dbcd791eeb4a3edd53ba985656`。
- 首版准备代码测试提交：`86ac3e7de55ff0e58a15a8ca23cad3c3bd80521d`。
  **实际云端执行/测试提交：`60a66d7ec1af723a7fe1ec1c7d0fa43f433b663b`**。
  云端六份 Python 脚本的 SHA256 与该提交对应的本机来源逐一匹配；之后仅更新文档。
- 用户已选首轮上限 **¥50**；只批准这一轮费用，不表示批准任何规模的后续训练。
- 用户随后明确：AutoDL 所需软件可以自主安装，本机新安装仍须先告知确认。
  已写入全局 `C:/Users/Zhang S/.codex/AGENTS.md` 的安装规则；本轮本机没有安装软件。
- 另一个对话负责 PR #12。没有改动 `Sources/`、App 测试、工程、签名、版本或发布工作流。

## 技术路线评估

选用已确认目标 **MOSS-TTS-Nano + 固定 zh_6.wav**，先真实复现原创小说，再验证官方
SFT（supervised fine-tuning，监督微调）链。更小学生模型的蒸馏保留为手机性能确有瓶颈时的备选。

该选择的依据是官方已有约 100M TTS、独立 codec、微调脚本和 ONNX 导出工具。
这允许从现成可训练基座进行声音/小说文本域适配，而不必先另造一套学生架构。
对同一模型自产的语音再微调不会自动创造教师没有的能力；它是否改善长篇声音、稳定性或
部署条件，必须用未参与训练的同文对照及用户核听判断。上述顺序是工程判断，不是已经实现的质量提升。

| 方案 | 本轮定位 | 主要待验证项 |
| --- | --- | --- |
| 原模型 + 固定参考，直接 ONNX | 必须保留的基线对照 | 新小说音色、流式首声、实际手机包体/内存/速度 |
| 官方 MOSS 全参数 SFT | 优先自训路径 | 原创数据质量、完整恢复、泛化/漂移、导出后声音一致性 |
| 独立小学生蒸馏 | 后备 | 基座/前端/许可、是否损失声音、端到端训练与手机收益 |

官方指南报告在单卡、batch 1、累积 1、`max-length=1024`、bf16 条件下，训练进程峰值约
3.23 GiB。因此 4090 24 GB 是合理的初期候选；该数字不是我们自己的显存实测，也不能外推到更长序列。
来源：[固定版本微调指南](https://github.com/OpenMOSS/MOSS-TTS-Nano/blob/8b7bcc9341b3b4ef3a3a58ba1338a7d85ff133eb/finetuning/README.md)。

### 源码核读发现的实际缺口

1. 固定 `sft.py` 保存模型/分词器/配置和步数记录，但未保存 optimizer、scheduler、RNG 或
   dataloader 进度，也没有完整 resume 入口。加载旧权重重新训练只能算 warm start。
   正式扩量前要补齐恢复，并真实比较中断前后状态与输出；当前未宣称已有可恢复训练。
2. `dataset.py` 会将超出 `max_length` 的完整序列直接截断。必须在准备阶段统计参考、文本、
   目标音频和结束标记的完整长度，拒绝截断样本，不能只按音频秒数筛选。
3. 指南说依赖已包含 `accelerate/tqdm`，但固定版 `requirements.txt/pyproject.toml` 并未完整列出；
   ONNX 导出另需 `onnx`。环境应依据实际代码核验，不能照抄指南后声称安装完成。
4. `infer.py` 的参数帮助文字和 `resolve_sampling_kwargs` 的实际默认值不同。
   本轮脚本显式固定实际默认值（text temperature 1.0，audio 0.8，audio top-p 0.95，
   repetition penalty 1.2 等），随机种子 42；官方演示当时完整采样设置未确认，不承诺相同波形。

核读出处：[sft.py](https://github.com/OpenMOSS/MOSS-TTS-Nano/blob/8b7bcc9341b3b4ef3a3a58ba1338a7d85ff133eb/finetuning/sft.py)、
[dataset.py](https://github.com/OpenMOSS/MOSS-TTS-Nano/blob/8b7bcc9341b3b4ef3a3a58ba1338a7d85ff133eb/finetuning/dataset.py)、
[infer.py](https://github.com/OpenMOSS/MOSS-TTS-Nano/blob/8b7bcc9341b3b4ef3a3a58ba1338a7d85ff133eb/infer.py)。

## 来源与资源锁定

完整清单在 `tools/tts-training/config/sources.lock.json`。

| 资源 | 固定身份 |
| --- | --- |
| 官方代码 | `8b7bcc9341b3b4ef3a3a58ba1338a7d85ff133eb`；19 份核读文件记录 Git blob/字节/SHA256 |
| HF TTS 可训练基座 | `OpenMOSS-Team/MOSS-TTS-Nano`，`44502f80dbf9743528fa921cc544d662c685ebec` |
| HF codec | `OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano`，`6aa02b01e445cc585582cf0ba480bc3ea6c8dd68` |
| 固定参考 zh_6.wav | 837,198 bytes；SHA256 `f618138a1bcb6833e9092cb06c8993c1299cd587eb4dabe61232a4ca93288ae3` |

训练资源清单共 17 个文件、323,443,057 bytes。锁定时大权重 SHA256 来自官方 LFS 元数据，
小型代码/配置和参考音频已逐字节下载核对；实际大权重验收须在下载完成后另记，不能混称。

现有官方 ONNX 资源元数据合计 762,688,159 bytes，约 763 MB（十进制，含 TTS、codec 编解码与分词资源）。
这说明“100M 参数”不能直接等同于小包体或低手机峰值内存。这里没有下载/执行 ONNX，
更没有 iPhone 性能结果。权重卡声明 Apache-2.0；代码许可、权重说明及参考发声人权限分别记录，
参考声音的产品使用权限尚未建立。声音批准不能代替这些证据。

云端不能直连 HF，实际经官方 README 指向的 ModelScope 镜像取回上述 17 个文件，
全部通过冻结 HF 清单的字节数与 SHA256 验收。镜像 master 仅作为传输入口，文件身份仍由冻结哈希决定。

## AutoDL 成本估算

2026-11-25 通过官方已登录控制台读取现有 4090：¥2.08/时，另列普通价 ¥2.19/时。
预算按较高的 ¥2.19/时；实际开机确认框显示 ¥2.08/时。官网 ¥1.88/时是起价，不当作本实例保证价。
计费依据实例开关机时长，精确到秒；并非只按 GPU 忙碌时间。
来源：[AutoDL 官网](https://www.autodl.com/)、[官方计费规则](https://api.autodl.com/docs/price/)。

| 范围 | 模型中估计总开机时间，含环境准备 | 含 30% 余量的费用 |
| --- | --- | --- |
| 首轮复现与后续小闭环准备 | 6–10 小时 | ¥17–29 |
| 首批 10 小时语料 + 3 epochs 微调 + 导出调试 | 11.51–34.13 小时 | ¥33–97 |
| 首批 20 小时语料 + 同配置 | 17.03–58.25 小时 | ¥48–166 |

这些是敏感性预算，**不是训练时长实测或花费承诺**。10/20 小时语料是后续规划场景，尚未批准生成；
首轮的小训练闭环也必须等待用户认可新声音并补齐恢复能力。后续多轮可先留 ¥100–300 研究预算，
能复用已合格语料时无需每轮重新支付整批合成成本；是否扩量以真实小试为准。

可复算输入：`tools/tts-training/config/cost_assumptions.json`；
命令：`python tools/tts-training/scripts/estimate_cost.py --audio-hours 1 10 20`。

假设为：环境准备 4 小时、教师 RTF 0.5–2.0、codec 编码 RTF 0.02–0.1、平均训练段 12 秒、
batch 1、梯度累积 8、3 epochs、有效 optimizer steps/s 0.1–1.0，以及固定调试/导出 2–6 小时。
RTF 是计算墙钟秒数/生成或编码音频秒数。所有速度均待测；30% 余量覆盖部分返工，不保证足以覆盖低合格率。

例：10 小时 / 12 秒 = 3,000 段；3 × ceil(3,000 / 8) = 1,125 次参数更新。
按上述速度，纯训练约 0.31–3.13 小时；合成与调试可能比这更占预算。
48 kHz 双声道 PCM16 每小时约 0.6912 GB，10/20 小时分别约 6.9/13.8 GB，另加环境、检查点和临时文件。
本次实测原始 WAV 为 FLOAT32，因此原样保留时音频占用加倍：10/20 小时约 13.8/27.6 GB。
预算工具的 PCM16 数值仅是格式情景，不代表已批准转换；正式语料须另定格式并重新检查磁盘余量。

官方无卡模式 ¥0.1/时适合传输，但每主账号只可同时运行一个；本次看到另一个 CPU 实例正在运行，
因此保守预算把环境准备计入 GPU 开机时间，没有擅自停掉其他任务或假定无卡名额可用。
费用估计假定不买额外存储；付费扩容盘关机后仍可能计费。
来源：[省钱模式](https://www.autodl.com/docs/save_money/)、[本地盘规则](https://www.autodl.com/docs/local_disk/)。

## 首轮真实执行结果

已复用原关机单卡 4090，确认剩余磁盘约 41 GB，驱动 580.76.05，原有任务环境保留。
在独立 `/root/autodl-tmp/ebook_s02a4/.venv/bin/python` 完成环境与合成：
Python 3.10.8、PyTorch/torchaudio 2.7.0+cu118、Transformers 4.57.1、NumPy 1.26.4、
WeTextProcessing 1.3.0、pynini 2.1.6。54 个发行物先核对官方 PyTorch 索引或 PyPI 发行 SHA256，
再安装；`pip check` 与真实 CUDA 运算通过。复用了云端完整旧依赖安装包，未修改旧环境。
本机只辅助传输并哈希核验了一份 Linux Triton wheel，没有安装或导入它。

实际命令入口为本线 README；最终运行使用
`autodl_audition.py run --run-id audition-001 --max-seconds 1800`，随后执行 `audit_audio.py`，退出码 0。
日志保留早期网络/启动失败和修复过程，包括官方 R2 下载域名适配、镜像传输、缓存复用与启动脚本 LF 换行修正。
不能把最终通过写成所有早期尝试均通过。

| 原创试听 | WAV 秒数 |
| --- | ---: |
| 临河书屋 | 29.28 |
| 一碗热汤 | 29.04 |
| 楼上的脚步 | 27.04 |
| 没有寄出的信 | 29.52 |
| 车站记录 | 28.32 |
| 渡口的灯 | 145.52 |
| 新增：末班车之后 | 247.60 |

全部实际输出为 **48 kHz、双声道 FLOAT32 WAV**，合计 **536.32 秒**。完整逐块解码、
帧数/有限值/非空与音频哈希检查通过，近满幅采样比例均为 0。它们是本次模型对原创文本的新合成，
不是官方演示录音。ASR/逐字对齐和人工听校尚未执行，不能据此宣称无漏读或更好听。

七段串行编排墙钟 **203.03 秒**，RTF 约 **0.379**；包含各段重新加载模型和首次文本前端准备。
这不是首声延迟、纯解码吞吐或 iPhone 性能。每秒采样一次的整卡显存观测最大为 **4,365 MiB**，
不是 PyTorch allocator 峰值或训练显存测量。纯训练吞吐仍待真实小试，预算假设未用本次推理值冒充替换。

## 备份、费用与关机验收

原始模型、参考、运行所需源码、输入、日志、环境锁、音频及清单已取回：
`E:/myself/eBOOK-s02a4/.local-test-data/s02a4/outputs/s02a4_pilot_20261126.tar.gz`。
归档 **449,500,825 bytes**，SHA256
`a0fb7b718a0519d065e1dbf58511091545fb235447949635f5c333cbdea66150`。
119 个文件成员逐哈希通过（另有一份成员清单，共 120 个 tar 成员）；其中 37 个文件还独立对照
先前冻结清单，包括 17 份模型、19 份核读源码及参考音频。模型和音频均不提交 Git。

本机恢复位置 `.../outputs/recovered/`，便听 MP3 位于 `.../outputs/listening/`；
原 WAV 保持原样。七份 128 kbps 便听 MP3 经既有 FFmpeg 转换并完整解码通过，未做响度或降噪处理；
衍生文件哈希在 `outputs/listening/listening-files.json`。核验记录为 `.../evidence/archive-verification.json`，运行概要在恢复后的
`notes/pilot-summary.json`，每段参数/音频身份在 `runs/audition-001/manifest.json`。

用户要求睡前收尾：平台兜底原设 03:50，随后提前至 01:20，**实际已手动关机**。
2026-11-26 **00:40（Asia/Shanghai）** 在已登录 AutoDL 控制台明确观察到本次 GPU 实例
**“已关机”**，SSH 已关闭；其他任务实例未操作。没有停留在“关机中”或把定时设置当作关机证据。
按约 23:51 开机、00:40 观察关机及 ¥2.08/时估算，本轮约 **¥1.7**，低于 ¥50 上限；
该数包含环境准备、下载、重试、合成及传输，精确账单未提取，以平台结算为准。
没有购买扩容盘、充值或建立新的付费协议。无需占着 GPU 等待用户明早核听。
SSH 密码仅临时内存/剪贴板使用并清空，不进入 Git 或报告。

| 项目 | 状态 |
| --- | --- |
| 本机代码语法、计划输出、本机 fetch/run 拒绝、损坏文件拒绝、预算单位 | PASS |
| 七段原创材料及固定资源清单 | PREPARED |
| 云端 17 份模型、54 份依赖、CUDA 环境 | PASS |
| 本次原创小说真实合成 | SYNTHESIZED_UNREVIEWED |
| 音频完整解码/哈希、归档 119 成员核验 | PASS |
| 本次 GPU 实例实际关机 | PASS — 平台显示已关机 |
| 新音频人工核听/偏好确认、ASR 对齐 | NOT_RUN |
| SFT、完整恢复、ONNX 导出与推理 | NOT_RUN |
| 实际训练显存/吞吐、iPhone 目标 | NOT_RUN |

本机检查环境为既有 `C:/conda_envs/myenv/python.exe` / Python 3.11.11，仅标准库；
`check_preparation.py` 明确检查没有导入 torch/soundfile，没有本机训练。
没有运行 iOS 构建或原有 App 测试：本轮未改 App，不能把旧 CI 当作本模型证据。

下一项是用户核听新故事，判断音色与朗读方式是否符合目标。随后在剩余授权预算内完成小训练闭环，
扩大训练前另做场景隔离的原创语料、质量筛查及完整 train/resume/export/infer 验证。
本轮仍没有自训权重、完整断点恢复、ONNX 导出或真机结果；本任务未整体 PASS，也不合并/发布。
