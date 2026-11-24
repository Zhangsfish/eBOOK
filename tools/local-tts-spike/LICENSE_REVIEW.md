# S02A 许可证与来源核对（2026-11-24）

结论：**LICENSE_REVIEW_INCOMPLETE，不构成 App Store 分发许可放行。**
已核对权重/运行时的上游声明、固定版本源文件和完整模型包哈希；尚未取得
实际 iOS XCFramework 的完整第三方 notices/BOM，也未完成词典等数据的逐项
来源链核对。这里不把“模型 Apache-2.0”扩大为整包所有依赖均已放行。

| 组件 | 固定版本/来源 | 实际核对结果 | 分发状态 |
| --- | --- | --- | --- |
| Kokoro 中文权重 | hexgrad/Kokoro-82M-v1.1-zh；INT8 转换包 revision `1355334be009ccce397060ee639a874137a128fa` | 原始模型卡声明 Apache-2.0；下载包根 LICENSE 为完整 Apache-2.0，SHA256 `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`；INT8 权重哈希已实读校验 | 上游许可声明已核对，量化生成的完整 provenance 尚非重建验证 |
| voices.bin / 103 个说话人向量 | 同一固定转换包；仅 sid 3/4/58 用于本实验 | 文件 SHA/字节数已校验；根许可证声明可见，无另附逐声线许可证清单 | 不额外推断训练数据/声音人格权已独立法律验收 |
| tokens.txt | 同一转换包，1111 bytes | 内容哈希已校验，运行时使用 token 表；未安装 Python Misaki/tokenizer | 继承包内声明，生成来源没有单独证明 |
| sherpa-onnx / Swift wrapper | v2.0.3，commit `38016c6e0622e90bf417c35e8b47e0eb805af417` | 根 Apache-2.0 已实读；Package.swift 与 Swift wrapper 哈希已固定 | 根声明核对完成；预编译库完整 notices 待核 |
| ONNX Runtime iOS binary | onnxruntime-libs 1.28.2，commit `8ebc5ebf92190903c274a7621ba4c96a732335ec` | 上游 Package.swift 的下载 URL/校验和已记录；未下载/解包二进制，未验证其中 LICENSE/ThirdPartyNotices | **UNRESOLVED_BINARY_NOTICES**，不把一般 ONNX Runtime 许可知识当作该二进制证据 |
| 内置 Kokoro lexicon frontend | 固定 sherpa v2.0.3 C++ `offline-tts-kokoro-impl.h` | 使用 lexicon longest-match 路径；配置源明确写明 v2 起不再使用 eSpeak；源码在 sherpa 根 Apache 声明下 | 源路径已核对，链接产物/BOM 未核 |
| lexicon-us-en / lexicon-gb-en / lexicon-zh | 固定模型包，逐文件 SHA 已记录 | 包中没有逐词典来源版本/独立 notices；本实验使用 us-en + zh，未使用 gb-en | **UNRESOLVED_DATA_PROVENANCE** |
| date/number/phone FST | 固定模型包，3 个独立 SHA | 实际加载并生成数字/日期测试音频；缺少这些具体二进制的完整生成源/数据 notices | **UNRESOLVED_DATA_PROVENANCE**，模型根声明不能替代此核对 |
| dict/ | 固定模型包，14,572,387 bytes | dict/README 说明 CppJieba；上游 CppJieba 根为 MIT，但包未标明该目录的精确上游提交；新 Swift 配置不传 dictDir | **未用于新 Swift 前端，不据此清除归档再分发义务** |
| espeak-ng-data/ | 固定模型包，17,991,651 bytes | 模型包未附此目录的来源版本/独立 notices；所核对 eSpeak NG 1.52.0 COPYING 为 GPLv3；不能认定包内数据正是这个版本 | **未用于 v2.0.3 合成路径**，整包再分发来源/许可未完成；不宣称当前运行时链接 GPL 代码 |
| kaldifst / OpenFst / utf8proc 等静态传递依赖 | 固定 sherpa 源 CMake；kaldifst v1.9.0、OpenFst v1.8.5-2026-07-09 的源码下载 SHA 已见上游脚本 | 只核对了声明，未从实际 iOS 二进制还原完整组件表/对应源与 notices | **UNRESOLVED_TRANSITIVE_BOM** |
| 桌面 Python wheels | sherpa/core 2.0.3，NumPy 1.26.4；独立 CPython 3.11.11 | 官方 PyPI wheel SHA/尺寸已核；只在本机实验使用，没有放入产品/仓库 | 桌面依赖不是 iOS 分发许可证证据 |

运行时的重要版本差异：`kokoro-data-dir` 在 v2.0.3 固定配置源码中明确标为
ignored since v2.0.0；新 Swift 配置不传 eSpeak/dataDir/dictDir。旧模型归档
仍包含这些资源。**“未使用”与“可以把整个含这些文件的包直接分发”是不同结论。**
S02A 保留原包进行完整性校验，没有未经等价性验证就删包/改权重。

正式分发前必须取得：实际 iOS 二进制支持的架构与第三方 notices、词典/FST/
声音资源的来源和许可证说明；确定可分发的最小资源集后重新生成版本化清单，
并验证与原包的输出等价性。此处不绕过这些待查项，也不另选供应商。

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
