# S02A — Kokoro 本地原生可行性审查交付

日期：2026-11-24（Asia/Shanghai）。Issue：[#6](https://github.com/Zhangsfish/eBOOK/issues/6)。
交付状态：**READY_FOR_AUDIT**。技术门槛：**BLOCKED_IOS_RUNTIME**。
许可证门槛：**LICENSE_REVIEW_INCOMPLETE**。当前不满足 S02B 的 GO 条件。

## 本轮交付与版本

- 正确仓库/分支：`Zhangsfish/eBOOK` / `codex/s02a-kokoro-ios-spike`。
- 继承任务文档基准：`7d9f0e1dee06c36e5791ceac3f7064f370020ceb`；main 基准 `adc9f340a2ff427b30cddce33ad8a4d9efdac55a`。
- **实际桌面模型合成源码 commit：`691f68ed3dded6fce4e820a521253444a8a6f4e4`**。完整参数和实际执行源文件 SHA256 在 [desktop-metrics.json](../tools/local-tts-spike/evidence/desktop-metrics.json)。最终交付 HEAD 另列于 PR；报告/检查脚本后续提交不冒充重新测量过的模型源码。
- 本机先检查了 eBOOK 两个 worktree 及旧设备辅助目录，没有找到既有原生 S02A 工程。已有的是 Windows 实际试听和资产校验；原件全部保留，未 reset、cherry-pick、清理或覆盖。
- 本轮在新的 `eBOOK-s02a` worktree 整理源码，复用已有隔离解释器和只读模型资源；不重装环境，不再做供应商研究或使用私人正文。
- 新增仅为 `tools/local-tts-spike/` 和本报告。生产 Sources、原 Core/UI Tests、Xcode 工程、STATUS、现有 workflow、PR #4/#5 均不修改。

## 证据矩阵：明确区分运行平台

| 项目 | 实际结果 | 不能据此声称 |
| --- | --- | --- |
| Windows CPU / Python / 原创中文 | **PASS_DESKTOP_ONLY**，7 个真实 WAV，3 个 speaker 输出不同 | iOS 已运行、iPhone 可以实时生成 |
| Swift SPM 原生实验源码 | 已提供官方固定 API、资源校验、串行有界合成、XCTest 和运行入口 | 已编译通过 |
| iOS 模拟器构建 | **NOT_RUN** | 模拟器构建 PASS |
| iOS 模拟器实际推理 | **BLOCKED_IOS_RUNTIME**；本机检测为 Windows，xcodebuild/xcrun 均无，运行 helper 实际返回码 3 | 原生中文 WAV 已生成 |
| 原生二进制架构/依赖 notices | **NOT_RUN / UNRESOLVED**；只固定上游 SPM 声明的 checksum | 已实读 XCFramework、架构和许可证均放行 |
| 真机、后台/锁屏、电池/发热 | **NOT_RUN** | 后台 audio entitlement 可保证无限 ML 推理 |
| 10–15 分钟有界多块会话 | **NOT_RUN**；仅提供可重复执行的 600/900 秒探针 | 7 个短 WAV 可替代耐久测试 |
| 本轮 S00 Xcode 回归 | **NOT_RUN**；生产文件未改，保留此前 S00 结果，不冒充新跑 | 本轮重新通过全部 reader 测试 |

iOS 检测证据：[ios-runtime.json](../tools/local-tts-spike/evidence/ios-runtime.json)。
本机没有真实 Apple runtime；现有免费 public macOS workflow 只调用 S00，未接 S02A
入口。本轮遵守“只改 spike/report”的文件边界，没有向旧工作流/生产测试注入
新执行逻辑，也未启用付费 runner。独立审查后仍需要在 macOS/Xcode 真正执行
`run_ios.py`；该脚本的存在不是运行成功证据。

## 模型、依赖与实际空间

模型：Kokoro-82M-v1.1-zh INT8，单模型支持 103 speaker；本实验只验证
zf_001/sid3、zf_002/sid4、zm_009/sid58，没有其他供应商或新一轮品质排名。

固定来源 revision：`1355334be009ccce397060ee639a874137a128fa`。
归档 **147,052,523 bytes（140.24 MiB）**；解包 **215,227,172 bytes（205.26 MiB）**。
`model.int8.onnx` 114,203,914 bytes，`voices.bin` 53,790,720 bytes。
归档 SHA256 `259c9c8bc906d6078e4e0570421885dabb68b539c2f970fcbb890a58eeaf3e9c`。
377 个文件全部以 SHA256/字节数实读校验，和此前已核验的上游固定资源清单一致。
[完整逐文件源 URL/清单](../tools/local-tts-spike/manifests/model.json)。

桌面：CPython 3.11.11、sherpa-onnx/core 2.0.3、NumPy 1.26.4，既有独立环境。
Windows，Intel i5-13500H（12 核/16 线程），本次配置 CPU provider / 4 threads。
Swift：官方 sherpa-onnx 2.0.3，commit `38016c6e0622e90bf417c35e8b47e0eb805af417`；
传递 ONNX Runtime SPM 1.28.2，commit `8ebc5ebf92190903c274a7621ba4c96a732335ec`。
[桌面 wheel 哈希](../tools/local-tts-spike/manifests/desktop-runtime.json) /
[原生依赖和上游声明的二进制哈希](../tools/local-tts-spike/manifests/native-runtime.json)。
原生二进制尚未下载/检查，不能把声明中的 checksum 当作本机校验通过。
归档/解包字节数是模型资源大小，不是最终 iOS 安装占用。

## Windows 实际性能（原创文本）

进程内模型构造时间 **9.269892 秒**；整个运行累计
峰值工作集 **511,217,664 bytes（487.54 MiB）**。
初始化前做了资源哈希读取，因此这里只是 fresh-process 初始化，**不是受控冷磁盘启动**。
第一回调延迟指真实 native callback 首次返回非空 samples 的时间，不是 UI 点击到出声。
RTF = 生成耗时 / 实际音频秒数；RSS 为同一进程累计高水位，不是各声线独立占用。

| 标签 / speaker | 原创 case | 首回调 s | 生成 s | 音频 s | RTF | 累计峰值 MiB |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| A / zf_001 | narration | 9.787 | 40.408 | 8.913 | 4.5337 | 442.38 |
| B / zf_002 | narration | 10.371 | 44.342 | 9.696 | 4.5734 | 484.76 |
| C / zm_009 | narration | 9.567 | 41.283 | 8.929 | 4.6234 | 484.76 |
| A / zf_001 | dialogue | 10.359 | 34.521 | 6.725 | 5.1333 | 484.76 |
| A / zf_001 | numbers | 13.796 | 47.717 | 10.497 | 4.5459 | 487.45 |
| A / zf_001 | polyphones | 12.950 | 35.529 | 7.833 | 4.5356 | 487.54 |
| A / zf_001 | mixed | 12.432 | 30.906 | 6.584 | 4.6940 | 487.54 |

三条同文 speaker PCM WAV 哈希互异。全部输出为 24 kHz / mono / PCM16；
7/7 个文件已独立检查实际 WAV header/帧数/哈希，并用既有 FFmpeg 完整解码无错误。
参见 [解码结果](../tools/local-tts-spike/evidence/desktop-validation.json)。
数字/日期、多音字、对话、停顿和中英混合 case 均实际合成，**不等于逐字人工
读音判定通过**。没有把机器识别或 waveform 差异当成自然度/耐听度评分。
倍速测量仅为 **1.0**；0.5–2.0 是接口输入边界，不是所有速度已测试的结论。

另复用既有 faster-whisper 1.2.1 / CTranslate2 4.8.2 / 本地 large-v3 / CUDA，
独立识别了前三条 narration；识别结果覆盖完整原句。zf_001 被识别成繁体，
另外两条为简体，原始字符序列相似度为 0.4857/0.9714/0.9714，因此检查状态
保留 **REVIEW_ASR_DIFFERENCES**。不能把繁简差异或同音字“合/河”算成已经
确认的模型读音故障，也不能用这些数字当发音准确率。原始机器结果和脚本
哈希保留在 [original-asr.json](../tools/local-tts-spike/evidence/original-asr.json)。
本轮没有再试听排名、筛选别的 speaker 或供应商。

在这台电脑上全部 case RTF > 1，生成慢于播放。不能据此保证 iPhone 性能，也
不能反过来宣布模型在 iOS 不可用；需要实际 arm64 simulator/device 结果。

## 真实命令与本地检查

命令中的 python 分别使用既有 CPython/批准的隔离 sherpa 环境；MODEL_DIR
为既有官方模型资源目录，正文不作为参数或输入。

```text
python -m unittest discover -s tools/local-tts-spike/Tests -v
python tools/local-tts-spike/scripts/assets.py --verify MODEL_DIR
python tools/local-tts-spike/scripts/run_desktop.py --model-dir MODEL_DIR
python tools/local-tts-spike/scripts/run_ios.py --model-dir MODEL_DIR
python tools/local-tts-spike/scripts/verify_generated.py --metrics LOCAL_METRICS --ffmpeg EXISTING_FFMPEG
python tools/local-tts-spike/scripts/check_speech.py --metrics LOCAL_METRICS --local-whisper-model EXISTING_LOCAL_LARGE_V3
python tools/local-tts-spike/scripts/check_delivery.py --desktop-metrics tools/local-tts-spike/evidence/desktop-metrics.json
python scripts/generate_xcode_project.py --check
```

离线测试 15/15 通过，覆盖坏哈希、缺文件/多文件、路径穿越、链接/重复成员、
已有目录保护、长度/速度输入边界及原创 fixture 类别。它们不是 Mock iOS 推理
PASS。原模型验证 377/377 通过；项目生成器检查为 current。最终 commit 的实际
检查摘要随 PR 提供；生成耗时只来自上述固定模型源码版本。

## 许可证结论与剩余门槛

已实读上游模型 Apache-2.0 声明和 sherpa 根 Apache-2.0；**未完成整个原生
分发物的许可证核验**。v2.0.3 lexicon 路径不再调用 eSpeak，但下载的旧模型包
仍含 espeak-ng-data 和 dict；“未使用”不是“整包可无条件再分发”。词典/FST
来源链、声音资源说明、实际 iOS 二进制完整 notices/BOM 仍待核。
逐项版本、证据和 UNRESOLVED 见 [LICENSE_REVIEW.md](../tools/local-tts-spike/LICENSE_REVIEW.md)。

本轮没有把权重、原生库、音频、私人小说、密钥或完整日志加入 Git。所有新音频
只在本机 ignored 目录；旧私人试听目录保持原样。没有付费服务/API、云合成、
签名、App Store 动作或其他模型研究。

## 集成提案与决定

[接口/下载/缓存提案](../tools/local-tts-spike/INTEGRATION_PROPOSAL.md) 包含单模型
四声音、显式 Wi-Fi 下载、哈希/中断恢复、删除与存储控制、短块/速度缓存键、
位置恢复、系统语音回退和后台预缓冲。它尚未写入正式 App。

**决定：交付供独立审查，暂不允许进入 S02B。** 后续必须补上固定 Swift runtime
的实际 iOS 构建/中文推理、架构与 notices 核验，再做 10–15 分钟分块和真机
性能/锁屏测试。当前 Apple fallback 保持原有功能；不自行合并、不开始集成。
