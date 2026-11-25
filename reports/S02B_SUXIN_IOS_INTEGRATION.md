# S02B — 苏心原生接入

日期：2026-11-26（Asia/Shanghai）。状态：IN_PROGRESS，尚未请求最终审查。

本线在 `codex/s02b-suxin-ios-integration` 更新 PR #12。阅读基线 main
`83fa0d90fd4cd0dbcd791eeb4a3edd53ba985656`；交接起点
`1eb0eef18e7011feb8034a393f084a91483b9a8e`。冻结 PR #7 与训练 PR #11 不改。

## 当前事实

| 项目 | 状态与边界 |
| --- | --- |
| 原生 Swift 中文前端 | IMPLEMENTED；全量固定字/词数据、最长匹配、数字/年/时间、一不变调、血、PAD |
| 真实作者前端对照 | SIMULATOR_VERIFIED：92条原创文本逐音素/ID一致，三个测试方法3/3，无跳过 |
| App 真实 ONNX、分段播放、缓存、语速、取消 | IMPLEMENTED；新 CI 仍在运行，不能提前写验证通过 |
| 真机首声/跳转/30分钟连续播放/发热耗电 | DEVICE_VERIFIED=NOT_RUN；本机 Windows，没有已连接的 iPhone/Xcode |
| 新安装包 | TESTFLIGHT_AVAILABLE=NO；旧39.1仍是原有苹果朗读版本 |
| 全包分发许可 | INCOMPLETE；具体材料缺口见下，不影响独立本地测试 |

首轮前端测试 HEAD `e3573b7b7ed56f844fbb0dcfa8647d97466c12f1`：
[真实 macOS CI](https://github.com/Zhangsfish/eBOOK/actions/runs/45648983455)。
Xcode16.4(16F6)、iOS18.5、ARM64虚拟Mac、iPhone16Pro模拟器；没有模型合成。
不要把这次3/3或旧 PR #7 预计算 ID 后端结果当作本次完整 TTS 通过。

## 实现及边界

- Swift前端消费全量41,923单字、47,111词组和1,559通用音节转换条目。
  测试oracle由原装作者代码和pypinyin0.55.0实际计算，未人工填音素；另有训练外
  新文本验证。字典与模型通过版本/大小/SHA256校验；Python/Piper/eSpeak不进App。
- 仅原生中文。含英文、未知字符或分块后不支持的内容，在播放前验证整个有界窗口，
  提示后整窗口使用Apple语音，不静默丢字。苏心失败不自动假装另一音色成功。
  混读回退不是原生英文G2P；不同窗口可能有明确提示的音色变化。
- 直接ORT CPU推理：4 intra/1 inter线程、一个后台actor/session；RunOptions支持取消。
  不在主线程加载模型/词典或推理，不启用CoreML，不带历史sherpa/Kokoro/Matcha包。
- 首块约18字符，后续约36字符，优先标点，保留原始UTF16地址与数字单位。
  最多3个PCM缓冲、一个下一窗口的2个预取子块；禁止整章/整书音频预生成。
  硬切长句仍可能影响边界多音词/变调，需长听核验，不能用92条前端一致性替代音质验收。
- 64MiB缓存保存在App私有Caches并排除备份；身份包括资源清单指纹、文本摘要、
  声音、语速和格式版本；PCM负载哈希验证，损坏失效，容量LRU淘汰。不记录正文。
  缓存不按书籍建索引；移除一本书后其旧派生音频可能保留到淘汰/系统清缓存或删除App数据。
- 音色选择保留苹果语音，苏心0.5–2.0×；旧偏好文件迁移不丢阅读/苹果语音设置。
  暂停不让迟到合成开始播放；跳转/切声/切书取消推理与队列，代际身份挡住迟到事件。
  隐藏面板继续播放；原有目录实时定位、主题和右下角入口保留。
- 听书位置只在短块实际播放回调后推进，重启可重读当前短块；不是逐词/逐帧持久化。
  队列回调欠载统计是软件探针，不能当作手机听感无中断证明；跨外层窗口仍需长听检查。

## 资源及分发核对

固定模型revision `5ee2da546f3635da263602842d238d8624cb7a81`；INT8图67,260,202bytes，
SHA256 `5dbe3500e7d36835e073dad4f3502a579ae497f62c0a6574c736345237e1e7aa`。
6项模型/字典/声明总69,551,510bytes；完整清单由准备脚本确定性生成，权重/音频不入Git。
ORT SPM `8ebc5ebf92190903c274a7621ba4c96a732335ec`，iOS ZIP33,821,118bytes，
SHA256 `2c2299acbb461d26d4bac4bc85985d40e7c7177ed6072703ae0846d88b0b4599`。
实际Info.plist含设备arm64、模拟器arm64/x86_64；原包没有license/notices。
对应Microsoft v1.28.2 tag及LICENSE/ThirdPartyNotices读取404，尚未核验精确源码与静态依赖BOM。

作者根MIT和pypinyin MIT完整随模型准备；作者也明确列出Piper VITS GPL、eSpeak/Piper
GPL、教师模型与语料链。原生App没有Piper/eSpeak运行库，不等于权重/数据分发链已清。
见 [NOTICE](../tools/suxin/NOTICE.md)。不能以另一源码版本的MIT文本冒充已完成整包核对。

## 仍需完成

保存实际原生合成/播放与原阅读器全回归结果、arm64 Release archive与精确SHA。
之后按审查流程交付；真机门槛、内部TestFlight与许可材料单独列NOT_RUN/阻塞。
不自行合并或开始下一阶段。
