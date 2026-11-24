# S02A.1 — Kokoro 原生 iOS 推理与性能审查交付

日期：2026-11-24（Asia/Shanghai）。继续 [PR #7](https://github.com/Zhangsfish/eBOOK/pull/7)，
执行 [Issue #8](https://github.com/Zhangsfish/eBOOK/issues/8)，回应
[独立审查](https://github.com/Zhangsfish/eBOOK/pull/7#issuecomment-7130117616)。

**交付状态：READY_FOR_AUDIT。原生推理：PASS。产品决定：BLOCKED / NOT_READY_FOR_S02B。**
ARM/Intel 两种 iOS 模拟器都实际加载模型并生成中文波形；全部实测配置仍慢于
播放（PERFORMANCE_NOT_READY），许可证核验仍为 LICENSE_REVIEW_INCOMPLETE。
真机为 DEVICE_PERFORMANCE_PENDING。本轮停止，不合并、不开始 S02B。

## 版本、范围与保留工作

- 分支仍为 `codex/s02a-kokoro-ios-spike`；复用已有 worktree，先检查状态再 fetch，未 reset/清理/覆盖已有用户工作。
- 本次审查基准：`c522d4b4de6abe5277a9e897cc32ae6852c43e9e`。
- 实际原生矩阵/等价性源码 SHA：**`ba17f9c6f15014e4693258ee7170dcb6c0f7e75e`**。
- 历史 Windows 模型合成源码 SHA：`691f68ed3dded6fce4e820a521253444a8a6f4e4`。原脚本哈希与历史测量一致，不重做旧试听。
- 任务文档基准 `7d9f0e1dee06c36e5791ceac3f7064f370020ceb`；main 基准 `adc9f340a2ff427b30cddce33ad8a4d9efdac55a`。
- 除 `tools/local-tts-spike/` 和本报告，仅新增 Issue #8 明确授权的 `.github/workflows/s02a-ios.yml`。生产 Sources/Tests、eBOOK.xcodeproj、STATUS、根 README、原有 workflows 均未修改。
- PR #4 / S01 worktree 仍为 `3bfb4429fe7a42e50df62f4857bcb9909bf00ab3`；PR #5 / 设备辅助目录仍为 `4f9175ed6326b95902aceaccf47258771281eac1`，两者干净未改。
- 最终交付 HEAD 及该 HEAD 自己的 CI 链接在 PR 正文/最终交付消息明确列出；本表中的测量版本不冒充后续报告/检查脚本提交。CI JSON 同时记录自身的精确 source_sha。

## 第一项：真正运行 iOS 版本

| 证据 | 实际结果 |
| --- | --- |
| [Intel 原生矩阵 CI](https://github.com/Zhangsfish/eBOOK/actions/runs/45389424006) | SUCCESS；Xcode 16.4 / 16F6；macOS 15.7.9 / 24G830；iOS Simulator 18.6 / 22G86；i7-8700B / x86_64 |
| [ARM 原生矩阵 CI](https://github.com/Zhangsfish/eBOOK/actions/runs/45392188338) | SUCCESS；Xcode 16.4 / 16F6；macOS 15.8.2 / 24H232；iOS Simulator 18.5 / 22F77；Apple M1 (Virtual) / arm64 |
| 实际编译 | 两组 `xcodebuild build-for-testing` 均返回 0，随后每组 5 次独立 `test-without-building` 均成功 |
| 实际推理 | 每组 1/2/3/4 线程各生成 7 段原创中文；真实 `IOS_SIMULATOR` 标记、完整 callback、24 kHz/mono/PCM16、帧数、非静音 RMS、SHA 与实测 RTF 均有记录 |
| 三个声音 | 同文 zf_001/sid3、zf_002/sid4、zm_009/sid58 均实际生成；每组各配置前三条 WAV SHA 互异 |
| 音频输出 | 8 个线程测试进程均观察到实际 AVAudioEngine realtime mixer 非零输出；不等同于物理扬声器可听度测量 |
| 真机及完整 App | NOT_RUN；没有把桌面/macOS host 音频、编译通过或模拟器数据当作 iPhone 结果 |

这是独立 Swift package 的真实 iOS XCTest，不是把 Python 或 macOS host 合成改名。
模型和 native binary 下载先核 SHA，再执行；仅使用原创新写的五类文本
（旁白、对话、数字日期、多音字、中英混合），无私人正文输入。

[ARM 完整指标](../tools/local-tts-spike/evidence/s02a1-ios-arm-ba17f9c.json) /
[Intel 完整指标](../tools/local-tts-spike/evidence/s02a1-ios-intel-ba17f9c.json)。
JSON 包含实际命令、宿主 CPU、iOS 版本、进程、逐段生成时间/时长/帧数/RMS/
首回调/波形哈希、首输出探针和资源比较结果。听感已由用户选定；本轮未另做
供应商试听，没有把非静音或 ASR 相似度当成自然度、逐字发音人工验收。

初次 [pilot CI](https://github.com/Zhangsfish/eBOOK/actions/runs/45387252960)
在 `be36e9b8e34430b58869033118bbbaf652d32c5b` 已完成编译链接，但 XCTest 在模型
加载前遇到错误的 `Resources/Resources/model.json` 路径，退出 65。
这是本实验的 bundle 定位错误；已修复并由上述真实运行验证。保留
[pilot 失败摘要](../tools/local-tts-spike/evidence/s02a1-pilot-failure.json)，
没有将它写成架构不兼容，也没有隐藏失败。

### CI 附件隐私复核

两份成功 CI ZIP 已实际下载并独立核对 GitHub digest、ZIP CRC、成员白名单、
UTF-8 和 artifact-manifest 每文件 SHA/尺寸。每份只有 **9 个 JSON/脱敏日志文件**；
上传音频 0、模型 0。无 xcresult、Bundle、DerivedData、私人文字或凭据。

- ARM：27,990 bytes，ZIP SHA256 `209ec951cc0b90dd35e88414cee95b0ed6c08b5a8f279892ca13ffe5ae5d025d`。
- Intel：28,976 bytes，ZIP SHA256 `650269404dd31a17c3bf83e12e394bd1f7ed2125ea20a42c1b0ffb954949fc51`。
- [ARM 验收清单](../tools/local-tts-spike/evidence/s02a1-artifact-arm-ba17f9c.json) / [Intel 验收清单](../tools/local-tts-spike/evidence/s02a1-artifact-intel-ba17f9c.json)。原 ZIP 和诊断文件保留在 ignored 本地目录；公开报告仅小型元数据。

新工作流仅允许公开仓库和普通免费 `macos-15` / `macos-15-intel`，不使用 larger
runner、额外账号/密钥或付费服务。实测后默认改为 ARM，Intel 可手动复核。
`publish_evidence.py` 成功后才允许 upload；禁止整个本地输出树上传。

## 第二项：合成速度与连续听书门槛

每个配置独立进程、同一引擎复用 7 段，速度 1.0；短 warmup 单独记录，未计入
稳态 RTF。每段 <=240 Unicode scalars。初始化前哈希验证会读取模型，因此是
fresh-process 构造，**不是受控冷磁盘启动**。每个线程配置只测一轮，固定 1→4
顺序；这些是当前共享 runner 的观察，不是随机化多次性能试验或线程因果结论。

RTF=生成墙钟秒/实际 PCM 秒；平均为逐段算术平均，加权为总生成秒/总音频秒。
p95 使用 nearest-rank，n=7 时就是本轮最大值。RSS 为 Darwin 进程累计高水位，
包含 XCTest、模型与音频图等，不是模型文件大小，也不是 iPhone 内存承诺。

### ARM iOS 18.5 / Apple M1 (Virtual)

| 线程 | 初始化 s | 首回调 s | 首段 mixer 输出 s | 平均 RTF | p95 RTF | 加权 RTF | 峰值 RSS MiB |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 16.906 | 12.255 | 41.368 | 2.8409 | 4.5217 | 2.8676 | 358.88 |
| 2 | 4.121 | 3.034 | 13.669 | 1.4116 | 1.6073 | 1.4213 | 421.19 |
| 3 | 3.251 | 4.105 | 17.902 | 1.6290 | 1.9429 | 1.6372 | 507.11 |
| 4 | 1.955 | 4.038 | 19.857 | 1.6349 | 2.1775 | 1.6548 | 511.23 |

### Intel iOS 18.6 / i7-8700B

| 线程 | 初始化 s | 首回调 s | 首段 mixer 输出 s | 平均 RTF | p95 RTF | 加权 RTF | 峰值 RSS MiB |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 5.574 | 7.554 | 76.101 | 6.4094 | 8.3691 | 6.3636 | 472.97 |
| 2 | 9.253 | 12.874 | 52.782 | 3.9601 | 5.8023 | 3.9609 | 474.50 |
| 3 | 7.760 | 9.272 | 46.968 | 3.5102 | 5.1945 | 3.6104 | 474.32 |
| 4 | 6.230 | 13.385 | 44.005 | 4.9673 | 6.8167 | 4.8124 | 475.11 |

首回调列为本轮第一段 zf_001：有实际非空 samples 返回的时间。
“首段 mixer 输出”是该段请求开始到真实非零音频送入 simulator realtime mixer，
当前探针在整块 WAV 生成后播放，包含文件/音频图启动时间，**不是首回调**。
没有硬件回环，物理 acoustic audibility 为 NOT_MEASURED；不能把模拟器输出
时间直接称作用户 iPhone 点击到扬声器出声时间。

**决定：PERFORMANCE_NOT_READY。** ARM 最快观察为 2 线程，加权 RTF 1.4213，
p95 1.6073，首段 mixer 输出 13.669 秒，峰值 421.19 MiB；Intel 最快加权 RTF
3.6104（3 线程）。所有配置、所有实测段均 RTF >1。首回调有时约 3 秒，不能
用它替代约 14 秒才开始的完整首块输出。

因此按 Issue #8 第 7 条不浪费资源继续生成 10–15 分钟音频，状态
**NOT_RUN_PERFORMANCE_NOT_READY**。没有声称连续播放/预缓冲验收通过；
不同测试的累计音频时长不能拼成一次连续会话。RTF=r>1 时生产速率仅为 1/r，
播放速率为 1；B 秒的小缓冲最终仍按约 B/(1−1/r) 秒耗尽。以 ARM 最快观察
r≈1.42，约 27 秒（3×9 秒）的初始缓冲也只能延后约 91 秒耗尽，不能解决
持续听书。这里是稳态速率解释，不是实际 91 秒播放实验。

后续产品验收目标（尚未通过）：预热请求到可听首输出 <=5 秒，持续加权 RTF
优先 <=0.8、关注逐块 p95，受支持 iPhone 内存/缓存稳定；真实暂停/恢复/定位/
调速/系统语音回退与锁屏连续性验收。DEVICE_PERFORMANCE_PENDING，电池、发热、
来电/耳机、中断恢复和锁屏推理均 NOT_RUN。未采用其他模型、付费硬件或云端方案。

## 第三项：资源、实际二进制与许可证

模型固定 revision `1355334be009ccce397060ee639a874137a128fa`；377 文件，
完整归档 147,052,523 bytes，解包 215,227,172 bytes；SHA256
`259c9c8bc906d6078e4e0570421885dabb68b539c2f970fcbb890a58eeaf3e9c`。
[完整逐文件清单](../tools/local-tts-spike/manifests/model.json) 保持不变。
sherpa-onnx 2.0.3 固定 commit `38016c6e0622e90bf417c35e8b47e0eb805af417`，
ONNX Runtime SPM 1.28.2 固定 commit `8ebc5ebf92190903c274a7621ba4c96a732335ec`。
[依赖/实际二进制 pins](../tools/local-tts-spike/manifests/native-runtime.json)。

两份实际 XCFramework ZIP 已下载并核 SHA/尺寸，Info.plist 和实际库文件皆实读；
macOS `lipo` 确认 **两库均含 device arm64，simulator arm64+x86_64**，非仅引用声明。
[实际 lipo 及库文件 SHA](../tools/local-tts-spike/evidence/s02a1-native-audit-be36e9b.json)。
sherpa ZIP 21,010,826 bytes；ORT ZIP 33,821,118 bytes。包内公开 header 版权/许可
引用已核验，ORT 有 MIT 引用，但两包都没有独立完整 LICENSE/ThirdPartyNotices。

**资源精简已取得有限实测等价性，分发仍未放行：**

- 新候选只复制权重、voices、tokens、us-en/zh lexicon、3 个 FST、LICENSE、README 共 10 文件。原完整包和归档完全保留，没有就地删文件/改权重。
- 候选 176,296,499 bytes（168.13 MiB），比原包少 38,930,673 bytes（约 18.09%）。这是未压缩资源大小，不是已测的下载量、App 安装量或运行内存。
- 候选 manifest 和资源只在 ignored 目录，规范化 manifest SHA256：`5267535f3f171cb6cb00cf17747ade8685bd63e100435e5fb9856c3965530267`。
- 每组真实 iOS runtime 同一 CPU/1 线程/速度 1、fresh engine、相同 warmup 和 7 请求顺序，完整包与候选 PCM16 WAV 的 **7/7 SHA 与帧数逐项相同**；ARM 和 Intel 分别通过。不要求不同架构/线程的 WAV 彼此相同。
- 只证明这些原创输入/设置下的资源等价性，不推断所有语言、输入、倍速都等价，不制作公开下载包或放宽许可证门槛。

已闭合的来源证据：中文词典生成配方使用 Misaki ZHG2P+pypinyin 字/词数据，
英文合并 Misaki gold/silver 数据；三个 FST 沿固定 Kokoro export workflow
追溯到共享源 revision `57345c004e13ed640e408c4c29ab56187b18f065`，三文件尺寸/
SHA 与本包完全一致。只下载了这三个规范化 FST，没有下载或评估另一模型。

**仍为 LICENSE_REVIEW_INCOMPLETE：** 词典生成时的精确依赖/数据版本没有固定，
底层 FST 语法生成链和完整静态依赖 BOM/notices 不齐。ORT packaging recipe
引用的 Microsoft `v1.28.2` 源码 ref 本次查询为 404，不能用别的版本 LICENSE
替代。模型 Apache-2.0、头文件 MIT 注释和音频等价性都不能自动清除这些缺口。
完整逐组件证据/链接见 [LICENSE_REVIEW.md](../tools/local-tts-spike/LICENSE_REVIEW.md)。

## 本地验证、复现与准确边界

使用既有 CPython 3.11.11；没有新安装。桌面实际合成另使用原批准的独立
sherpa/core 2.0.3、NumPy 1.26.4 环境，原始私人试听目录保持原样、未读取正文。

```text
python -m unittest discover -s tools/local-tts-spike/Tests -v
python tools/local-tts-spike/scripts/assets.py --verify MODEL_DIR
python tools/local-tts-spike/scripts/inspect_native.py --require-simulator-arch arm64
python tools/local-tts-spike/scripts/run_ios.py --model-dir MODEL_DIR --benchmark-matrix
python tools/local-tts-spike/scripts/audit_fst_sources.py --output LOCAL_NEW_AUDIT.json
python tools/local-tts-spike/scripts/check_delivery.py --desktop-metrics tools/local-tts-spike/evidence/desktop-metrics.json
python scripts/generate_xcode_project.py --check
```

32 项 Python 离线测试通过；原 15 项资源/输入/原创语料检查保留，新增原生指标
拒绝编译结果冒充推理、错误平台/SHA/线程/帧数/RTF/哈希、伪等价性、ZIP 路径
穿越、缺 XCFramework 信息与日志脱敏检查。测试中的合成 METADATA 仅测解析器，
不是 Mock 音频或原生运行证据。上述原生 CI 在 ba17f9c 时为 29 项，后加的 3 项
等价性 guard 在最终 HEAD 再跑；不把后来测试数倒填为先前 CI 输出。
模型 377/377 校验通过；项目生成器为 current，生产源码 diff 为零；原完整 App
Xcode 回归本轮 NOT_RUN（正式 App 未变），不冒充重新通过 S00 整套测试。

所有真实模型/音频/原 ZIP 均只在 ignored 本地/临时 runner 目录。Git 中只有源码、
脚本、小型 manifests/指标/报告；无真实 WAV、权重、私人小说、密钥或大文件。
未修改 PR #4/#5，未调用付费服务/API、改账号/签名/发布，未开始 S02B。

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
不能反过来宣布模型在 iOS 不可用；本轮 ARM 模拟器数据已列于上文，真机仍待实测。


## 审查交接

原生 iOS 推理与切片检查已取得真实成功证据，七例资源精简比较也通过。
性能与完整 notices/来源版本仍阻塞正式集成。现有
[集成设计输入](../tools/local-tts-spike/INTEGRATION_PROPOSAL.md) 仅是提案；
正式 App/Apple fallback 保持原有实现。停止在 **READY_FOR_AUDIT / BLOCKED**，
等待 ChatGPT 再次独立审查，不合并、不继续 S02B。
