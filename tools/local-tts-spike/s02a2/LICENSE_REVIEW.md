# S02A.2 许可与完整资源复核

2026-11-25，**LICENSE_REVIEW_INCOMPLETE；所有候选均未取得产品分发放行。**
免费获取权重、根代码许可证和可在免费 iPhone 阅读器分发，是三个不同的核验项。
本轮只在隔离实验目录使用，没有将模型或依赖链接进正式 App。

| 对象 | 实际证据 | 尚未通过的事项 |
| --- | --- | --- |
| Kokoro / 既有原生运行库 | 沿用父目录 LICENSE_REVIEW.md、native-runtime.json 和 S02A.1 实读二进制/头文件证据；本轮实际运行确认 ORT 1.28.2 注册并执行 CoreML 分区 | 完整静态传递依赖 notices/BOM、词典/FST 精确生成版本仍未齐全；CoreML 可运行不会解决许可缺口 |
| Matcha zh-baker 权重 | 固定 HF revision `6ccce73a41f1f4be966c485c75bcbf9d13df4819`，声学权重与 release 包逐 SHA 一致。模型卡未声明独立权重许可证，明确称训练数据仅限非商业用途 | 不把 icefall 代码的 Apache 许可推给权重/训练数据/声音权利；免费 App 不自动等于获准非商业分发，当前无法放行 |
| Matcha Vocos 22 kHz ONNX | 官方 sherpa 页面指定此 53,884,024-byte 文件；固定 release 的本地 SHA 已列清单。Vocos 代码仓库根 LICENSE 为 MIT | 未取得该准确导出文件至原始 checkpoint 的完整许可/转换链；不把代码 MIT 自动视为精确权重许可已核验 |
| Matcha lexicon / tokens / 3 FST / dict | 19 个完整资源均有字节数和 SHA，未剪裁；官方文档说明 dict 不再需要，实验仍保留完整包 | 没有本轮音频等价验证，因此不删除资源；dict/词典及规则的逐项来源和 notices 尚未完成，不能称整包许可通过 |
| Suxin-Light 权重和推理源 | 固定 revision `5ee2da546f3635da263602842d238d8624cb7a81`；模型卡及 LICENSE 声明权重/推理代码 MIT，图、配置和代码逐文件哈希 | 作者同时明确英文 G2P 经 Piper 引入 eSpeak NG GPL-3.0；中文前处理依赖 pypinyin。尚未核对整套数据/声音来源链及原生分发义务 |
| Suxin 前端运行依赖 | 所需版本/官方 wheel SHA 另列 frontend proposal；实际没有安装。模型图已被既有 ORT 加载，未注册自定义 op 库 | 依赖安装确认待答复；没有 Swift 原生中文前处理，更没有 iOS 端到端语音证据。67.43 MB 只是选定图+源文件，不含前端运行包/数据 |
| M5-TTS | 只核对官方演示及 HF 元数据；ONNX 模型卡声明 Apache-2.0，未下载权重 | 不开展 codec/训练数据/全依赖分发清关，也不提出移植；声明不构成产品放行 |

Matcha 固定模型卡的 370-byte README SHA256：
`d47ef70781df15845b6f28c6c071dee9e51b52c36797a8130a620c5c8895929c`。
DataBaker 官网本轮读取超时；模型卡关于数据非商业限制的说明已经实读，不能因官网
不可达把许可标成 PASS。原包和本地来源证据均保留。

主要依据：

- [Matcha 精确模型卡](https://huggingface.co/csukuangfj/matcha-icefall-zh-baker/blob/6ccce73a41f1f4be966c485c75bcbf9d13df4819/README.md)
- [sherpa 的 zh-baker 官方配置与资源说明](https://k2-fsa.github.io/sherpa/onnx/tts/all/Chinese/matcha-icefall-zh-baker.html)
- [Vocos 代码根许可证](https://github.com/gemelo-ai/vocos/blob/main/LICENSE)（moving main，仅证明所查代码声明）
- [Suxin 精确 LICENSE](https://huggingface.co/TEQUILA123/suxin-light/blob/5ee2da546f3635da263602842d238d8624cb7a81/LICENSE)
- [Suxin 精确前端与推理代码](https://huggingface.co/TEQUILA123/suxin-light/tree/5ee2da546f3635da263602842d238d8624cb7a81/suxin_tts)
- [M5 官方代码/模型链接](https://github.com/ASLP-lab/M5-TTS)
