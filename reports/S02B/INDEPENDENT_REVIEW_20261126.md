# S02B 独立审查 — 2026-11-26

结论：**REQUEST_CHANGES。先修复下列问题，再进行有针对性的复核；目前不放行合并或新版本分发。**

审查对象：PR #12，`ae3592fa3305a4d02a5774386c4e0098b95dba8e`。
范围为 iOS 电子书与苏心接入；训练 PR #11 和 Android 线不在本轮审查范围内。
本提交仅保存独立审查报告及小型证据，未修改 App、测试、构建或训练实现。

## 1. P1 — 原有设备打包入口会拒绝当前合法资源包

位置：[scripts/ci_device.sh:37](https://github.com/Zhangsfish/eBOOK/blob/ae3592fa3305a4d02a5774386c4e0098b95dba8e/scripts/ci_device.sh#L37)。

原有校验只允许两个 .txt：
`Suxin/author-LICENSE.txt` 和 `Suxin/pypinyin-LICENSE.txt`。
但当前 Xcode 工程及 `inspect_runtime.py` 已经把以下两份必要声明一起打包：

- `NativeNotices/ONNXRuntime-LICENSE.txt`
- `NativeNotices/ONNXRuntime-ThirdPartyNotices.txt`

因此正常的新包必然不能满足第38行的集合相等断言。
`.github/workflows/s00-device.yml` 仍调用这个设备打包脚本，复用该入口时会在生成 IPA 前失败。

本地直接提取并执行原脚本的 allowlist 赋值与断言 AST，给它当前四份声明的文件列表，
稳定得到 AssertionError。此检查不需要 Xcode，没有声称实际重新归档。
最新 S02B CI 使用 `ci_integration.py` 的另一份包检查；该检查允许四份声明，
所以其 arm64 archive PASS 不能证明旧设备准备入口也能通过。

修复：统一两套资源校验，按模型清单及固定运行库声明校验完整集合和摘要；
保留禁止测试书、音频、密钥的检查。修复后实际运行受影响的设备打包入口，
不要删除随包声明或宽泛允许任意 txt。

## 2. P2 — 时间里的冒号会被当作分句点，触发不必要的整窗口换音色

位置：[SuxinSegmentation.swift:13](https://github.com/Zhangsfish/eBOOK/blob/ae3592fa3305a4d02a5774386c4e0098b95dba8e/Sources/ReaderCore/SuxinSegmentation.swift#L13)，
以及 `SuxinResources.swift:94–99` 的逐子块 preflight。

最小原创例子：15个“甲”后接 `12:05。`。首块18字符的范围刚好以冒号结尾。
当前算法先选冒号分句，只有进入 else 分支才保护数字/时间，所以实际得到：

- 第1块：15个“甲” + `12:`
- 第2块：`05。`

完整 `12:05` 是当前前端支持的时间，但 `12:` 不满足分钟规则。
整窗口 preflight 因此返回 unsupportedText，路由将整段改用 Apple 音色；
不是模型本身不支持这段文本。

本地按 Swift 分支顺序做源级算法复现，确认时间被拆开，所有原字符仍在。
这不是 Swift/Xcode 或真实语音执行，证据中已标明。

修复：在选择标点分句之前识别数字内部的冒号，统一数字/日期/时间边界保护；
把时间放在首块18和后续36字符边界的两侧逐一回归，并验证实际路由仍用苏心。

## 3. P2 — 硬切字符后重新做 G2P，会丢失跨块的读音和变调上下文

位置：[SuxinResources.swift:94](https://github.com/Zhangsfish/eBOOK/blob/ae3592fa3305a4d02a5774386c4e0098b95dba8e/Sources/eBOOK/SuxinResources.swift#L94)，
`wave(text:)` 第104行，`SuxinFrontend.hanPhonemes` 的词组匹配与一/不变调。

preflight 对完整文字计算一次音素，但丢弃结果。真正合成时每个18/36字符子块
重新调用 prepare，因此完整窗口已经识别出的词组和下一字声调会在边界丢失。

可确定的最小例子：17个“甲”后接“不是这样。”。
分段为第一块以“不”结尾、下一块以“是”开头。
本项目固定音节表为 bù=[b,u,4]、shì=[sh,i,4]：

- 完整 prepare 中，“不”看见后续4声，改为 [b,u,2]。
- 子块 prepare 中，“不”已是最后一字，保留 [b,u,4]。

这属于实际合成输入的音素差异，不只是可能出现的听感变化。
同一类边界还会拆开“一个”“重庆”等词。现有92条 oracle 校验的是完整文本
prepare，没有覆盖生产子块的上下文一致性；长听尚未完成也不能抵消确定的输入差异。

修复：按语义/词组选择可安全切分的位置，或先按完整上下文解析并把正确音素
映射到可播放子块，避免对子块重新独立推导上下文。补足边界回归；
短首声和队列上限仍需保留。神经输出听感需要修复后另外核听。

## 已有测试核对与未闭环项

已直接读取 GitHub run/job 日志，而非只采信 PR 自述：

| 执行 | 实际观察 |
| --- | --- |
| 7ff918a / run 45769244490 / job 139737620646 | iOS18.5，42 PASS / 0 FAIL / 0 SKIP；实际原生图与PCM指标；unsigned arm64 archive PASS |
| 7ff918a / run 45769249483 / job 139737645806 | iOS26.5，41 PASS / 1 FAIL / 0 SKIP；Apple sawRange 失败；实际苏心及 archive 有结果，但整轮 FAIL |
| 565bae0 / run 45771793206 / job 139745928149 | 6 UI PASS + 1 宿主启动错误记录；EBookTests 在连接 XCTest 前 signal abrt；没有本轮神经指标或新归档 |

Sources、Tests、scripts、tools/suxin、workflows 及 Xcode 工程在 ae3592f 与7ff918a的
Git对象一致，未将报告提交冒充另一次实际构建。

iOS26.5 的 Apple 范围回调失败仍未解释，干净复核又未启动单测宿主。
目前无完整 crash stack，不能确定是 App、系统语音、测试进程还是 runner 问题；
不把它直接描述为用户 App 必然崩溃。应补充可定位的诊断，再作有界复核，
不通过削弱断言、跳过或反复碰运气宣称解决。

真机首声/跳转分布、1.0×与1.5×各30分钟、锁屏/中断/蓝牙、热状态/耗电、
实际手机声音核听仍为 NOT_RUN。短模拟器探针没有证明这些要求通过。
分发材料的独立核对仍待完成。本审查没有新增签名、安装、TestFlight或公开发布。

## 本地独立检查

- 确定性 Xcode 工程生成检查 PASS。
- 重建原创2301482字符GB18030夹具后，`check_source_safety.py --ref HEAD` PASS。
  首次因缺少忽略目录中的夹具而未完成的检查不计为通过；重建后才获得结果。
- 实际旧打包断言 AST 和分段/变调源级探针结果见随附 JSON。
- `git diff --check origin/main...HEAD` 报一个低影响问题：
  `reports/S02B/evidence/files-picker-final-failures.log:18` 末尾新增空行。
  不是本轮主要阻塞项。
- 本执行端为 Linux，没有 Swift/Xcode 或连接的 iPhone；没有重新执行 iOS 测试。

## 返工顺序

先修复设备包检查和两类分段边界；针对新增边界执行真实原生前端/路由回归，
并跑实际设备包入口。随后补齐 iOS26 测试诊断与受影响回归。
代码和包核验通过后，再沿既有授权路径提供可安装的内部测试版本，
收集真机首声、跨窗口长听及后台行为；最后决定发布放行。
不启动训练、不更换候选模型、不修改其他工作线。
