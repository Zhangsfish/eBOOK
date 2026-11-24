# S02A.2 — iPhone 本地中文 TTS 筛选

交付状态：**READY_FOR_AUDIT**（2026-11-25，Asia/Shanghai）。
产品门槛：**NO_GO_LOCAL_AI / BLOCKED_DEVICE_AND_LICENSE**。
Suxin 语音实验另为 **BLOCKED_DEPENDENCY_APPROVAL_PENDING**，不是完成或失败的音质测试。

**建议保留苹果系统中文朗读，结束本轮模型扩研。** Kokoro 的最后一次 CoreML 机会已用完，
仍慢于播放；Matcha 真正在 iOS 模拟器生成了中文，但短样本存在延迟、混合英文缺失及
许可问题；Suxin 仅实测模型加载，尚无语音。没有任何候选取得真实 iPhone 性能、
10–15 分钟稳定性及用户音质认可的完整证据。不开始 S02B，不修改正式 App，不合并。

## 版本、范围与原始证据

- 本轮执行基线：`d41b80d88780d5b483a1a2af873b1293ee22ba70`。
  三个用户新增的任务/模板提交已安全 fast-forward；原有文件、模型和试听全部保留。
- Kokoro CPU/CoreML 和 Matcha 2/4 线程的**实际原生测试源码**：
  `f015d3dcef870381bc7f7f19fc32bcf8dee5f4e0`，不是最终报告提交的 SHA。
- 正式 Windows Matcha 音频也在上述 f015 完整提交、干净工作区运行。
  Kokoro 对比音频复用 `691f68ed3dded6fce4e820a521253444a8a6f4e4` 的原创语料
  zf_001 结果，核对全部文本与 WAV 哈希，没有重做或读取私人小说。
- Suxin 可复现的正式 **load-only** 测试源码：
  `39522a04ca4f4426633516f396323aa5421eb76e`，执行时工作区干净。
  后续交付只增加报告/元数据，不改 f015 已测试的 Swift/C++ 原生推理实现。
- 最终交付 HEAD、最终检查及 CI 状态以 PR #7 的精确 SHA/运行链接为准，
  不把文档提交冒称运行过新的模型基准。
- 当前本机 Windows 11 build 26200、Intel Core i5-13500H（12 核/16 逻辑线程）；
  仅观察到 iPhone 蓝牙音频表面，没有已连接、受信任且能通过 Xcode 部署的设备。
  本轮未使用/导出签名凭据。既有 device workflow 是无签名准备，不是真机证据。
- `Sources/`、`Tests/`、正式 Xcode 工程及 PR #4/#5 均未改动。只更新实验目录、
  其专用工作流和本报告；始终在既有分支 `codex/s02a-kokoro-ios-spike`。

| 真实执行 | 环境与范围 | 结果 |
| --- | --- | --- |
| [Kokoro final CI](https://github.com/Zhangsfish/eBOOK/actions/runs/45442045004) | 免费公开 macos-15 ARM，Apple M1 (Virtual)，Xcode 16.4 (16F6)，iPhone 16 Pro **模拟器** iOS 18.5 (22F77)，Debug 测试宿主 | 实际编译、运行 EP 枚举、CPU 与 CoreML 五段生成、非零混音输出和 ORT profile；XCTest 成功 |
| [Matcha CI](https://github.com/Zhangsfish/eBOOK/actions/runs/45445046800) | 同一类免费 ARM runner/Xcode/模拟器，2/4 线程分别启动测试进程 | 实际编译和 10 次原始语料 WAV 生成，非零混音输出；两个 XCTest 成功 |
| Windows Matcha | 已授权独立 sherpa/core 2.0.3、NumPy 1.26.4、CPython 3.11.11，CPU 4 线程 | 5 条真实 PCM16 WAV，完整解码通过；不是 iOS |
| Windows Suxin | 已有 ORT 1.20.1、CPython 3.11.11，CPU 4 线程 | 真实 ONNX session 加载/接口检查；**没有运行 session.run，没有音频** |
| 真实 iPhone | 型号/SoC/iOS/签名路径不可得 | **DEVICE_NOT_RUN**；不从模拟器推算 |

原生库固定 sherpa commit `38016c6e0622e90bf417c35e8b47e0eb805af417`，
ORT 包装仓库 commit `8ebc5ebf92190903c274a7621ba4c96a732335ec` / ORT 1.28.2。
两份 CI 在解析后实际核对 checkout SHA，禁止随后自动解析漂移。
sherpa XCFramework ZIP SHA256：
`36603efc0908a18a3b4b5ec1a81a15accddbe9948720bf4d931ee14506f42481`；
ORT ZIP：
`2c2299acbb461d26d4bac4bc85985d40e7c7177ed6072703ae0846d88b0b4599`。
实际切片检查继承 S02A.1，并在这两次 CI 再运行；不是只读 Package.swift。

原始 JSON 保留在
[实验 evidence](../tools/local-tts-spike/s02a2/evidence/)。
下载的两个 GitHub artifact 均核对服务端 ZIP SHA、CRC、严格文件名/大小白名单、
成员 SHA 与源码。每个 ZIP 仅 `artifact-manifest.json` 和 `native-result-0.json`：
**0 模型、0 音频、0 raw profile、0 编译产物**。原生 WAV 仅留在临时 runner，
不经 GitHub artifact 传回本机；本机试听不能冒称这些 iOS WAV。

## 测量口径与限制

统一使用未改动的 `fixtures/corpus.json`：叙述、对话、数字、多音字、中英混合五段，
全部原创；固定原速 1.0，同一模型/配置内复用单个实例、先合成“清风吹过窗边。”预热。
文件 SHA256 为 `b03fec6c0ced39735b81fb4793187581603e5f37b2e0d8dae2692eb98c6eaf5c`。
Kokoro 用 zf_001 (sid 3)，Matcha 用其唯一 sid 0，没有虚构额外音色。

加权 RTF = 五段生成总耗时 / 五段实际 PCM 总时长；均值是逐段 RTF 算术均值。
p95 为五段 nearest-rank，样本少时等于最大值，**不是 15 分钟分块分布**。
RSS 为整个 XCTest/Python 进程累计 high-water，不是模型独占内存或 iPhone 物理内存。
模型初始化是 fresh process 构造函数；OS 文件缓存未受控，不称冷磁盘启动。
免费共享虚拟 runner 的调度/负载未控制，单次 2/4 线程差异不能当稳定倍速承诺。

“首 callback”只到第一个非空合成回调；当前探针等**整段生成结束**才启动
AVAudioEngine，记录请求开始到非零 main-mixer buffer。包含引擎启动/路由等待，
没有扬声器回录，也没有真正流式播放。因此回调很快不能替代 <=5 秒首声验收。

## Kokoro：一次 CoreML 机会已结束

实际 `Ort::GetAvailableProviders` 返回 CoreML/XNNPACK/CPU，版本 1.28.2。
已有二进制支持 CoreML，**没有构建替代 ORT**。固定 sherpa 的 provider 配置真实创建
CoreML session；没有靠任意字符串就声称硬件加速。

- 运行日志：3113 原图节点中 1415 被 CoreML 接受，133 个融合分区。
- 实际 profile：CoreML 2527 个执行事件、133 个唯一融合节点；CPU 39054 个事件、
  1710 个唯一执行节点。大量 CPU 回退仍存在。事件含预热，不能与原图节点一一等同。
- profile 中 CoreML 累计节点时长约 5.833 秒、CPU 63.642 秒；不是端到端加速比。
  **ANE_EXECUTION_NOT_MEASURED**，不能把模拟器 CoreML 节点执行称作 iPhone ANE 运行。
- 两组都开 profile、2 线程、相同五段和预热；顺序固定 CPU 后 CoreML，非随机多轮实验。

| iOS 模拟器 | 初始化 s | 预热生成 s | 首 callback s（叙述） | 首混音输出 s（叙述） | RTF 均值 / 加权 / p95 | 进程峰值 MiB |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| Kokoro CPU 2T | 10.524 | 7.179 | 8.164 | 22.518 | 1.7168 / **1.7122** / 2.3643 | 400.47 |
| Kokoro CoreML 2T | 22.458 | 2.858 | 3.011 | 14.865 | 1.6651 / **1.6536** / 1.7871 | 579.67 |

加权 RTF 只下降约 3.4%，单轮不能视为可靠收益；两组仍 >1，CoreML 初始化和
进程峰值更高。**KOKORO_DEVICE_PERFORMANCE_NOT_READY；停止优化**。
没有第二轮 CoreML 配置尝试，没有 ORT 自编译，没有额外真机尝试替代品。
旧自动工作流曾被用户任务文档提交触发；冗余旧 CPU run 45432833676 已取消，
历史保留在 attempt-ledger，不能把那些旧 CPU runs 当本轮 CoreML 重试。

## Matcha：原生运行成功，产品门槛未通过

实际使用 **matcha-icefall-zh-baker（单中文、1 女声、22050 Hz）**。
用户所附 Chinese-English/zh-en 页面是另一变体；未偷换成 zh-en 或其 INT8 大小。

| 资源范围 | 实际字节数 |
| --- | ---: |
| 完整声学 tar.bz2 | 75,455,267 |
| 单独 Vocos 22 kHz ONNX | 53,884,024 |
| **完整合计下载** | **129,339,291** |
| **完整解压/资源集合（19 文件）** | **145,676,531** |
| 其中声学 model-steps-3.onnx | 75,624,188 |

完整包保留 dict、lexicon、tokens、phone/date/number FST 和 Vocos；没有未验证剪裁。
权重与 HF revision `6ccce73a41f1f4be966c485c75bcbf9d13df4819` 的 LFS SHA 一致。
tar 包有 release digest；旧 Vocos asset 没有发布 digest，清单明确标为首次实读固定 SHA，
没有伪称上游签名/发布哈希。清单见 `s02a2/manifests/matcha.json`。

| 环境 | 初始化 s | 预热 s | 首 callback s（叙述） | 首混音输出 s | RTF 均值 / 加权 / p95 | 进程峰值 MiB |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| Windows 4T | 5.903 | 0.153 | 见原始各段 JSON | NOT_MEASURED | 0.0920 / **0.0911** / 0.1087 | 242.54 |
| iOS 模拟器 2T | 2.343 | 0.365 | 0.277 | **8.916** | 0.9961 / **0.9205** / 3.7696 | 274.80 |
| iOS 模拟器 4T | 5.981 | 1.351 | 2.755 | **9.815** | 0.5574 / **0.5759** / 1.0837 | 279.64 |

2T 对话段实际生成 23.682 秒 / 音频 6.282 秒；4T 叙述段 8.688 / 8.017 秒。
未删除这些慢点，也没有用桌面 RTF 替代。4T 总体快于播放不等于已经连续不卡顿；
没有实现/验证分块预取与后台推理。本轮不展开调参矩阵。

桌面五段真实 WAV 的时长约 8.035、6.287、9.802、7.210、4.805 秒。
真实日志显示 mixed 中 Reader、Wi、Fi、Play、Pause 是 OOV，被跳过；保留相同原文，
没有为它改写测试。中文数字/多音字的正确读法与听感仍待人工，未伪造 ASR/评分通过。
官方称 dict 不再需要，但本轮没有等价性实测，所以不删。

**许可是独立阻碍。** 固定模型卡明确训练数据仅限非商业用途，且没有独立权重许可
声明；不能因 App 免费就推定获准分发。声码器精确导出链、词典/FST/notices 也未齐。
[固定模型卡](https://huggingface.co/csukuangfj/matcha-icefall-zh-baker/blob/6ccce73a41f1f4be966c485c75bcbf9d13df4819/README.md)；
[官方资源/API](https://k2-fsa.github.io/sherpa/onnx/tts/all/Chinese/matcha-icefall-zh-baker.html)。
结论：**SIMULATOR_INFERENCE_PASS / DEVICE_NOT_RUN / LICENSE_UNRESOLVED / OWNER_PENDING**。

## Suxin-Light：加载成立，语音未运行

固定 HF revision `5ee2da546f3635da263602842d238d8624cb7a81`，
INT8-excldec 图 **67,260,202 bytes**，SHA256
`5dbe3500e7d36835e073dad4f3502a579ae497f62c0a6574c736345237e1e7aa`。
选择的图+配置+作者代码/说明共 11 文件 **67,430,162 bytes**，完整下载并逐 SHA 核对。
这是选定资源集，不是整个 HF 仓库，也**不包括尚未安装的前端包/数据**，
不能报成完整 iOS 下载/安装大小。

| 实际测试 | 结果 |
| --- | --- |
| Windows ORT 1.20.1 CPU session 加载 | **6.590 s**，进程峰值 **179,015,680 bytes / 170.72 MiB** |
| 接口 | input/int64、input_lengths/int64、scales/float[3] → output/float；无额外 custom-op library 注册 |
| 合成、RTF、首声、WAV、听感 | **NOT_RUN**，不能由 session 加载推算 |
| iOS 图执行 / Swift 中文前处理 / 真机 | **NOT_RUN**；已有 C++ 桥随原生包编译成功，不等于执行成功 |

作者的 SuxinVoc 已在该 ONNX 图内；现有 ORT 能加载，不需要先重写声码器。
但中文/英文前端仍依赖 pypinyin、Piper/eSpeak、数字归一化及自定义音素/PAD 规则；
尚无 Swift 原生前端。轻量 C++ 标准 ORT 后端 proof 已准备，输入若使用作者 Python
预计算 IDs，必须标 `AUTHOR_PYTHON_FRONTEND_PRECOMPUTED_IDS` 和
`end_to_end_native_text=false`，不能冒称完整 iOS 文本到音频。

既有 Windows/WSL/项目环境均无所需前端包。已依全局 AGENTS.md 第 65 行
“Do not install a new package or tool until the user has confirmed that installation should proceed.”
请求项目隔离安装确认，交付时未收到答复；没有擅装或临时手写音素假装同文合成。
初始提议 ORT 1.23.2，随后证明已有 1.20.1 可加载，故取消升级需求。
现只需确认 pypinyin 0.55.0 / piper-tts 1.8.0 / pathvalidate 3.3.1；
官方 wheel SHA/字节数和 **NOT_INSTALLED** 状态在 frontend proposal 中。

作者声明权重及推理代码 MIT，同时明确英文 G2P 通过 Piper 引入 eSpeak NG GPL-3.0；
不能把整个前端链称 MIT 已清关。原生词典/数据体积、许可、实际声音均未验收。
[固定来源](https://huggingface.co/TEQUILA123/suxin-light/tree/5ee2da546f3635da263602842d238d8624cb7a81)。
结论：**BLOCKED_DEPENDENCY_APPROVAL_PENDING / NATIVE_FRONTEND_NOT_IMPLEMENTED**。
没有进行大型前端/推理引擎重写。

## M5-TTS：官方参考，不是同文试验

仅阅读[官方代码说明](https://github.com/ASLP-lab/M5-TTS)、
[预录演示](https://aslp-lab.github.io/M5-TTS-Demo-Page/)和固定 HF 元数据。
官方中文情绪/韵律样本是不同文本、经筛选的演示，**不能混进本轮同文评分**。
作者的 50M 参数不含独立 codec；Xeon 四核的 RTF 0.653 / 预热首包 225 ms 是作者
服务器结果，不是本机、模拟器或 iPhone 实测。

选定流式克隆 ONNX 组件元数据合计 **1,399,844,705 bytes**，没有重复加入可替换
decoder 或 Torch codec；仍只是元数据范围，不能称完整 iPhone 安装大小。
只取小 manifest/说明，**模型权重下载 0 bytes**。未请求在线合成、未移植、
未生成同文 WAV、未给出人工质量分。状态 **REFERENCE_ONLY / NOT_RUN_ORIGINAL_CORPUS**。

## 私有试听与质量验收

本机可直接打开的材料（路径相对仓库；不在 GitHub）：

```text
.local-test-data/s02a2/comparison/listening-e1a04b68b2b44c0d9dbce44dd83df022/index.html
.local-test-data/s02a2/comparison/listening-e1a04b68b2b44c0d9dbce44dd83df022.zip
```

A = Kokoro zf_001，B = Matcha zh-baker，五段完全相同的原创文本、共 10 WAV；
均为 **Windows 实际模型输出**，保留原音量/原速，没有 Mock 或其他音色替代。
完整 FFmpeg 解码 10/10 成功。ZIP 中含音频、文本、来源清单、静态 HTML，解压后打开
index.html；不需要后端/密钥。M5 只保留官方预录演示链接，显式点击才联网，
不发送测试文本。Suxin 明标 NOT_RUN，没有不存在的播放器。

真实 Chrome 157.0.8103.79 / 既有 Playwright 验证：10 音频 metadata 全部加载；
A/B 首条均实际开始**静音**播放；评分初始为空；无 JS error、无自动外网请求，
375px 默认页面无横向溢出。已视觉核读桌面截图。静音浏览器验证不证明物理可听性。
详细 JSON/截图在同一私有目录的 output/playwright/，未上传截图或音频。

评分模板覆盖自然度、柔和、情绪、停顿、发音、长时间耐听，默认全部留空，
本机 localStorage/手动导出，不上传评分。**OWNER_LISTENING_PENDING**：
没有收到对 Matcha 的音质认可，不把之前对 Kokoro 的认可套给它，
也不把几秒短样本当十分钟耐听验收。

## 复现与未完成项目

```text
python -m unittest discover -s tools/local-tts-spike/Tests -v
python scripts/generate_xcode_project.py --check
python tools/local-tts-spike/scripts/check_delivery.py --desktop-metrics tools/local-tts-spike/evidence/desktop-metrics.json
python tools/local-tts-spike/s02a2/scripts/benchmark_desktop.py --model matcha --model-dir .local-test-data/s02a2/assets/matcha-full-v1 --threads 4
python tools/local-tts-spike/s02a2/scripts/screen_suxin.py --load-only --model-dir .local-test-data/s02a2/assets/suxin-full-v1
python tools/local-tts-spike/s02a2/scripts/make_listening_page.py --matcha-metrics LOCAL_MATCHA_METRICS
```

Matcha 使用既有独立 `eBOOK/.local-test-data/tts-preview/runtime/venv`；
Suxin load-only 用已有 `C:/conda_envs/myenv/python.exe`，都没有安装新工具。
本轮离线 Python 检查 **45/45 PASS**，包括路径穿越、ZIP 篡改、伪装音频载荷、
桌面不能冒充 iOS、EP 列表不能冒充执行等防线；这些是元数据/安全单测，
不是 Mock 音频，也不能替代上述真实 Xcode 推理。工程生成检查及范围/忽略检查 PASS。
编译检查仅覆盖脚本语法；没有冒称正式阅读器重新构建。

原生复现通过专用手动 workflow 的 matcha 模式；不再 dispatch kokoro-final。
工作流不在文档 push 时重复跑研究。公开仓库+普通免费 macos-15，权限 contents:read，
无付费 runner/服务/云端 TTS。签名真机最小计划见
[DEVICE_TEST_PLAN.md](../tools/local-tts-spike/s02a2/DEVICE_TEST_PLAN.md)。
staging helper 已在 Windows 验证复制/哈希上下文，只说明准备包可生成，
**没有签名、设备安装或推理**。

| 完整产品验收项 | 本轮状态 |
| --- | --- |
| 真实 iPhone 中文推理 / <=5s 首声 / RTF<1 | DEVICE_NOT_RUN |
| 10–15 分钟无断音、内存不持续增长 | NOT_RUN；没有用批量生成音频冒充播放 |
| 发热、电量、锁屏/来电/蓝牙恢复 | DEVICE_NOT_RUN |
| 替代模型音质获用户认可 | OWNER_LISTENING_PENDING |
| 可分发资源和完整 notices | LICENSE_REVIEW_INCOMPLETE |
| 正式 App 接入、S02B、合并 | NOT_STARTED / NOT_AUTHORIZED |

许可细项见 [S02A.2 LICENSE_REVIEW](../tools/local-tts-spike/s02a2/LICENSE_REVIEW.md)，
继承的原生库/词典缺口没有被新模型结果覆盖。
`.local-test-data/` 全部保持 Git ignore，无模型、真实音频、小说、密钥或编译产物
进入新增提交/CI artifact。只访问公共文档/固定模型下载，无云端合成请求，无收费。

**下一步仅为独立审查。** 没有模型达到完整 GO 条件，推荐正式阅读器继续使用
Apple AVSpeechSynthesizer。Suxin 是否补一次有限语音实验须先解决现有安装确认；
当前不能声称所有候选已试听完毕，也不自动重启研究或开始 S02B。
