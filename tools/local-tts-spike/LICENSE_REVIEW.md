# S02A 许可证与来源核对（2026-11-24）

结论：**LICENSE_REVIEW_INCOMPLETE，不构成 App Store 分发许可放行。**
已核对权重/运行时的上游声明、固定版本源文件和完整模型包哈希；S02A.1 已实读
两份实际 iOS XCFramework、Info.plist、库文件和公开头文件；归档未附独立
许可证或完整第三方 notices/BOM，也未完成词典等数据的逐项
来源链核对。这里不把“模型 Apache-2.0”扩大为整包所有依赖均已放行。

| 组件 | 固定版本/来源 | 实际核对结果 | 分发状态 |
| --- | --- | --- | --- |
| Kokoro 中文权重 | hexgrad/Kokoro-82M-v1.1-zh；INT8 转换包 revision `1355334be009ccce397060ee639a874137a128fa` | 原始模型卡声明 Apache-2.0；下载包根 LICENSE 为完整 Apache-2.0，SHA256 `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`；INT8 权重哈希已实读校验 | 上游许可声明已核对，量化生成的完整 provenance 尚非重建验证 |
| voices.bin / 103 个说话人向量 | 同一固定转换包；仅 sid 3/4/58 用于本实验 | 文件 SHA/字节数已校验；根许可证声明可见，无另附逐声线许可证清单 | 不额外推断训练数据/声音人格权已独立法律验收 |
| tokens.txt | 同一转换包，1111 bytes | 内容哈希已校验，运行时使用 token 表；未安装 Python Misaki/tokenizer | 继承包内声明，生成来源没有单独证明 |
| sherpa-onnx / Swift wrapper | v2.0.3，commit `38016c6e0622e90bf417c35e8b47e0eb805af417` | 根 Apache-2.0 已实读；Package.swift 与 Swift wrapper 哈希已固定 | 根声明核对完成；预编译库完整 notices 待核 |
| ONNX Runtime iOS binary | onnxruntime-libs 1.28.2，commit `8ebc5ebf92190903c274a7621ba4c96a732335ec` | 33,821,118-byte ZIP 的固定 SHA 已实读校验；实际 lipo 确认 device arm64 / simulator arm64+x86_64；包内 C API 头文件明确引用 MIT；未附独立 LICENSE/ThirdPartyNotices | **UNRESOLVED_BINARY_NOTICES**，头文件 MIT 注释不等于完整静态依赖通知已齐 |
| 内置 Kokoro lexicon frontend | 固定 sherpa v2.0.3 C++ `offline-tts-kokoro-impl.h` | 使用 lexicon longest-match 路径；配置源明确写明 v2 起不再使用 eSpeak；源码在 sherpa 根 Apache 声明下 | 源路径已核对，链接产物/BOM 未核 |
| lexicon-us-en / lexicon-gb-en / lexicon-zh | 固定模型包，逐文件 SHA 已记录 | 已核对固定 sherpa 导出脚本：英文合并 Misaki gold/silver JSON，中文使用 Misaki ZHG2P + pypinyin 字/词数据；脚本用 moving main / 未锁定依赖，未证明此归档生成时的精确数据版本 | **UNRESOLVED_DATA_REVISIONS_AND_NOTICES**；本实验只使用 us-en + zh |
| date/number/phone FST | 固定 Kokoro 文件，已追溯共享源 revision `57345c004e13ed640e408c4c29ab56187b18f065` | 沿 Kokoro 固定 export workflow 的下载链接，3 个文件与共享源逐字节 SHA/尺寸完全一致；源库声明 Apache-2.0；只下载这三个 FST，没有下载/运行其他模型权重 | **MATCHED_ARTIFACT_SOURCE**；底层语法/数据的完整生成版本与 notices 仍待核 |
| dict/ | 固定模型包，14,572,387 bytes | dict/README 说明 CppJieba；上游 CppJieba 根为 MIT，但包未标明该目录的精确上游提交；新 Swift 配置不传 dictDir | **未用于新 Swift 前端，不据此清除归档再分发义务** |
| espeak-ng-data/ | 固定模型包，17,991,651 bytes | 模型包未附此目录的来源版本/独立 notices；所核对 eSpeak NG 1.52.0 COPYING 为 GPLv3；不能认定包内数据正是这个版本 | **未用于 v2.0.3 合成路径**，整包再分发来源/许可未完成；不宣称当前运行时链接 GPL 代码 |
| kaldifst / OpenFst / utf8proc 等静态传递依赖 | 固定 sherpa 源 CMake；kaldifst v1.9.0、OpenFst v1.8.5-2026-07-09 的源码下载 SHA 已见上游脚本 | 只核对了声明，未从实际 iOS 二进制还原完整组件表/对应源与 notices | **UNRESOLVED_TRANSITIVE_BOM** |
| 桌面 Python wheels | sherpa/core 2.0.3，NumPy 1.26.4；独立 CPython 3.11.11 | 官方 PyPI wheel SHA/尺寸已核；只在本机实验使用，没有放入产品/仓库 | 桌面依赖不是 iOS 分发许可证证据 |

运行时的重要版本差异：`kokoro-data-dir` 在 v2.0.3 固定配置源码中明确标为
ignored since v2.0.0；新 Swift 配置不传 eSpeak/dataDir/dictDir。旧模型归档
仍包含这些资源。**“未使用”与“可以把整个含这些文件的包直接分发”是不同结论。**
S02A 保留原包进行完整性校验，没有未经等价性验证就删包/改权重。

实际 iOS 二进制架构已确认；正式分发前仍必须取得完整第三方 notices、词典/FST/
声音资源的来源和许可证说明；确定可分发的最小资源集后重新生成版本化清单，
并验证与原包的输出等价性。此处不绕过这些待查项，也不另选供应商。

## S02A.1 实际资源复核

- sherpa iOS ZIP：21,010,826 bytes，SHA256 `36603efc0908a18a3b4b5ec1a81a15accddbe9948720bf4d931ee14506f42481`。
- ONNX Runtime iOS ZIP：33,821,118 bytes，SHA256 `2c2299acbb461d26d4bac4bc85985d40e7c7177ed6072703ae0846d88b0b4599`。
- [CI 中实际 lipo/归档清单](evidence/s02a1-native-audit-be36e9b.json) 确认两份库的 device arm64、simulator arm64+x86_64，lipo 退出码均为 0；这解决二进制切片检查，不能代替加载/推理。
- 两份归档都未附独立 LICENSE/NOTICE 文件。公开 C API header 中的版权/许可引用也已实读并保存摘要；不把“没找到单独文件”说成头文件没有任何声明。
- [实际 header 声明与 SHA](evidence/s02a1-header-notices.json) 保留 Xiaomi 版权和 ONNX Runtime MIT 引用。[ONNX Runtime 构建配方摘要](evidence/s02a1-ort-build-provenance.json) 固定了 packaging 仓库源码；配方 checkout `microsoft/onnxruntime` 的 `v1.28.2`，但本轮对该上游源码 ref 的 API/原始 LICENSE 查询返回 404。二进制来源/哈希可验证，不代表对应 Microsoft 源码和完整第三方 notices 已取得；不能用别的版本许可证替代这个缺口。
- [词典生成源摘要](evidence/s02a1-generator-source-digests.json) 与 [FST 源文件匹配](evidence/s02a1-fst-provenance.json) 保留精确源提交、链接和哈希。
- 精简候选只另存 10 个文件：权重、voices、tokens、us-en/zh lexicon、3 个 FST、LICENSE、README。176,296,499 bytes；比完整包少 38,930,673 bytes。原包/归档没有删除或改写。S02A.1 已在 ARM/Intel 两组实际 iOS 模拟器、同一 runtime/1 线程/相同 warmup 与请求顺序下验证 7 段 PCM16 WAV 哈希与帧数逐项完全一致。只确认这些原创输入下的资源等价性；不扩展为所有文本兼容或允许分发。

上游证据（源码摘要哈希另见 evidence/license-source-digests.json）：

- [原始模型许可声明](https://huggingface.co/hexgrad/Kokoro-82M-v1.1-zh)
- [固定转换包 LICENSE](https://huggingface.co/csukuangfj/kokoro-int8-multi-lang-v1_1/blob/1355334be009ccce397060ee639a874137a128fa/LICENSE)
- [固定 sherpa LICENSE](https://github.com/k2-fsa/sherpa-onnx/blob/38016c6e0622e90bf417c35e8b47e0eb805af417/LICENSE)
- [固定 Kokoro 配置，eSpeak 弃用声明](https://github.com/k2-fsa/sherpa-onnx/blob/38016c6e0622e90bf417c35e8b47e0eb805af417/sherpa-onnx/csrc/offline-tts-kokoro-model-config.cc)
- [固定 lexicon frontend](https://github.com/k2-fsa/sherpa-onnx/blob/38016c6e0622e90bf417c35e8b47e0eb805af417/sherpa-onnx/csrc/offline-tts-kokoro-impl.h)
- [ONNX Runtime SPM 包声明](https://github.com/csukuangfj/onnxruntime-libs/blob/8ebc5ebf92190903c274a7621ba4c96a732335ec/Package.swift)
- [CppJieba 上游 MIT，尚非本包版本证明](https://github.com/yanyiwu/cppjieba/blob/master/LICENSE)
- [eSpeak NG 1.52.0 GPLv3 原文](https://github.com/espeak-ng/espeak-ng/blob/1.52.0/COPYING)

不提交任何第三方模型/二进制，也没有模型转换或声音克隆。原创新代码只调用
上游公开 API；本文件为工程证据清单，不声称完成尚缺的分发审查。
