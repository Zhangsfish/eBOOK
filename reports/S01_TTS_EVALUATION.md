# S01 Mandarin TTS Voice Lab 评测与交付记录

状态：**READY_FOR_AUDIT**，等待独立审查。日期：2026-11-24，Asia/Shanghai。
范围：Issue [#3](https://github.com/Zhangsfish/eBOOK/issues/3)，分支
`codex/s01-tts-voice-lab`，仅 S01。

## 版本与证据边界

- 开始提交：`be5306c0ee1ea2625f22e3045e9346d98efeb95b`。
- 已合并的 S00/main 基线：`adc9f340a2ff427b30cddce33ad8a4d9efdac55a`。
- 精确交付 HEAD、该 HEAD 的最终 CI 链接和实际 Xcode 回归结果记录于本次 PR
  正文。报告与实现一同提交；审查应使用 PR 的完整 HEAD。
- 本机检查发生在 Windows 10.0.26200，Python 3.11.11。没有本机 Xcode、Swift
  或 xcrun。GitHub 公共仓库的标准免费 macOS runner 用于实际 iOS 回归。
- 本报告中的价格是官方文档快照下的**计算估算**；Mock 测试音不是供应商音频。
  **真实供应商请求 0，付费使用 0，真实声线试听 0，人工评分 0。**

## 已交付的工作台

`tools/tts-lab/` 使用 Python 标准库，包含四个独立 REST Adapter、统一请求和
音频约定、Mock Transport、保守的成本预检、缓存、本地匿名播放器和评分模板。
无需 SDK、账户、API Key 或新安装的软件包。iOS Sources、原有 Tests、Xcode 工程
和播放实现保持不变。

六段原创文本共 **930 Unicode scalars、2,643 UTF-8 bytes、931 UTF-16 units**，
包含一处补充平面汉字。统一 NFC/LF 规范化后分为 **12 个共享文本块**，每块最多
120 scalars。覆盖平静旁白、对话、克制情绪、中英数字单位、跨块长句与段落、
原创姓名地名和多音字。没有商业小说摘录，也没有导入用户书籍的 CLI 入口。

共同输出为 **24 kHz、16-bit、单声道 PCM WAV**。解析器核对音频头和完整帧，
不通过更改扩展名或无声重采样来掩盖差异。两个本地 `<audio>` 控件提供 A/B
比较和暂停全部播放；匿名标签在不同片段之间保持一致。供应商映射只在独立
的本地 `private-mapping.json` 中，页面不读取该文件。

## 四家协议与未执行项目

官方资料于 2026-11-23–24 复核。完整接口来源、字段、风格映射及限制见
[API contract notes](../docs/TTS_PROVIDER_API_CONTRACTS.md)。下表的 PASS 仅表示
本地序列化/Mock 解析测试通过，不表示供应商已接受真实请求。

| 供应商 / 模型 | Adapter Mock | 声线 / 柔和风格处理 | 真实服务与听感 |
|---|---|---|---|
| MiniMax Speech 2.8 HD / Turbo | PASS | 男女声槽位待选择；gentle 映射官方 calm，neutral 不强制情绪 | NOT_RUN |
| Fish S2.1 Pro / Free | PASS | 需选择已有 reference_id；不使用 references/克隆；等价 gentle 未配置，明确 UNSUPPORTED | NOT_RUN |
| Eleven v4 / Multilingual v2 | PASS | 声线槽位待选择；v2 不发送不支持的 language_code；不把 style 数值当作 gentle | NOT_RUN |
| Azure Neural / Chinese DragonHD Flash | PASS | 使用有官方来源的中文语法示例，地区访问待核验；HD 不发送不支持的 prosody rate | NOT_RUN |

没有调用供应商声线目录接口，也没有根据样例 ID 猜测普通话质量、可用权限或性别。
Azure 示例同样不代表实际资源已经开通。男女声是待完成的对照槽位；本阶段没有
宣称已完成男女声试听。ElevenLabs 旧默认声线存在迁移/到期规则，因此不将旧
默认 ID 当作新账户可用的声线选择。

## 计费单位与本地估算

以下是默认整套**假设未来配置完成并执行**的文本费用估算，不含税、套餐折扣、
可能的声线费用或实际规范化差异。MiniMax/Azure 每模型包含两声线 × 两风格；
Fish/ElevenLabs 只有两声线 × neutral，因此这些总价不能直接作音质或性价比排名。

| 模型 / 家族 | 计划块请求 | 单位估算 | 文档单价 | 假设执行的估算 USD |
|---|---:|---:|---|---:|
| MiniMax speech-2.8-hd | 48 | 3,720 字符 scalars | $100 / M characters | 0.37200 |
| MiniMax speech-2.8-turbo | 48 | 3,720 字符 scalars | $60 / M characters | 0.22320 |
| Fish s2.1-pro | 24 | 5,286 UTF-8 bytes | $15 / M bytes | 0.07929 |
| Fish s2.1-pro-free | 24 | 5,286 UTF-8 bytes | 文档标示 $0 | 0（非实测账单） |
| Eleven eleven_v4 | 24 | 1,860 字符 scalars | $0.08 / 1,000 characters | 0.14880 |
| Eleven eleven_multilingual_v2 | 24 | 1,860 字符 scalars | $0.08 / 1,000 characters | 0.14880 |
| Azure neural | 48 | 8,040 Azure 计费字符估算 | 地区 / SKU 未定 | UNKNOWN |
| Azure dragon-hd-flash | 48 | 7,956 Azure 计费字符估算 | 地区 / SKU 未定 | UNKNOWN |

价格来源：[MiniMax](https://platform.minimax.io/docs/pricing/overview.md)、
[Fish](https://docs.fish.audio/developer-guide/models-pricing/pricing-and-rate-limits.md)、
[ElevenLabs](https://elevenlabs.io/pricing/api)。该 ElevenLabs 快照已更新初始清单中
较早的价格假设。Azure 按[官方计费定义](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech#pricing-note)
将汉字计两次，并计入 speak/voice 外的内部 SSML；转义实体采用保守的序列化计数。
MiniMax/Eleven 的 scalar 数为估算，后续实际 usage/账单仍需核对。

已知价小计为 **$0.97209**，整批总价因 Azure 未知而保持 **UNKNOWN**，不是零。
当前实际支出始终为零。未知价格、非正/非有限支出上限和超出上限的批次被拒绝。
S01 的实时入口还有阶段硬锁：即使显式给出 `--execute-live`、正数上限并预先设置
环境变量，也在读取凭据、发起请求前拒绝。

## 缓存与敏感信息

缓存键覆盖 provider、model、voice、精确文本 SHA-256、风格、速度、地区、
音频约定和协议版本；mock/live 分开，测试音不能成为未来真实合成的缓存命中。
成功记录按字节哈希校验。pending、失败、损坏或并发占用的记录阻止自动请求，
不因含糊超时自动重试。状态记录保留非密钥请求身份和时间，供后续本地核查。

凭据仅在未来获授权的 transport 内临时绑定到 wire headers。Dry Run/Mock 不读取
供应商密钥，不加载 `.env`。`.env.example` 仅列变量名称；服务返回的错误正文
不会进入异常文本、JSON、缓存或日志。未来 transport 只允许已审阅 HTTPS 地址、
禁止重定向和自动重试，并把单次请求与非空批次报价绑定。它仍是待授权扩展点，
不是已经完成生产验收的计费系统。

音频、缓存、映射、HTML、评分、浏览器截图和测试输出全部位于被忽略的
`.local-test-data/tts-auditions/`。仓库仅保存源码、原创语料、说明和本摘要。
CI 将 Dry Run stdout 留在该本地忽略目录，不上传试听输出。

## 实际检查

本机的 Windows `python3` 指向未配置的 WindowsApps 别名，实际复用既有
`C:\conda_envs\myenv\python.exe` 执行同一命令，没有安装工具：

```powershell
& 'C:\conda_envs\myenv\python.exe' -m unittest discover -s tools/tts-lab/tests
& 'C:\conda_envs\myenv\python.exe' tools/tts-lab/run.py --dry-run --provider all
& 'C:\conda_envs\myenv\python.exe' scripts/generate_xcode_project.py --check
```

| 检查 | 实际结果 / 范围 |
|---|---|
| 离线 unittest | PASS，38 项；所有测试禁止 socket/DNS/普通 HTTP opener |
| 四家 Adapter 和全部模型 / 家族 | PASS，Mock 请求和音频解析、HTTP/应用错误、非法字段和格式 |
| 文本与成本 | PASS，字节/scalar/UTF-16 区分、汉字/SSML 计数、Free 与 UNKNOWN 区分、支出边界 |
| 缓存 | PASS，键隔离、成功复用、损坏/并发/pending/超时后不自动重新请求 |
| CLI 默认 / 显式 Dry Run | PASS，无凭据、无网络、8 模型/家族、32 条件、288 个假设块请求 |
| Mock 完整流程 | PASS，首次 288 次 Mock 调用、144 个本地测试音拼接片段；重跑 0 次新调用、288 次缓存命中 |
| 匿名页面与评分 | PASS，单独映射、HTML 转义、远程音频路径拒绝、CSV 分数全空、固定七项权重 |
| 本地浏览器 | PASS，Chrome 157.0.8103.79 / Playwright 1.62.1 / Node 24.15.0；无新安装 |
| 浏览器交互 | PASS，1280/390/320 px 无横向溢出、无映射泄露、Mock WAV 解码、A/B 互斥及暂停、0 HTTP 请求 |
| Xcode 工程生成校验 | PASS，`Xcode project is current.` |
| iOS 实际回归 | 使用原有免费 macOS 流程；本次完整 HEAD 的实际构建/测试结果见 PR 和其 CI 链接 |

浏览器仅播放了测试信号，没有试听供应商声线。局部界面截图和机器输出均留在
本地忽略目录，没有作为供应商评测结果上传。S00 的历史基线曾通过 26/26 模拟器
测试和 Debug/Release 构建；本次回归结果应按 PR 中的当前 HEAD 核验。

## NOT_RUN 与结论

- **NOT_RUN：**实际合成/声线目录调用、供应商格式/权限/限额实测、实际价格账单、
  TTFA/延迟/失败率、人工音质与长时间疲劳评分、地区资源访问、商业权利/保留训练
  政策完整审查。未申请账户、未克隆声音、未请求或收集 API Key。
- **尚无音质胜者。**自然度、柔和程度、耐听程度、发音和分段一致性均未取得真实
  听感证据。四家候选名单保持开放，`docs/S01_PROVIDER_DECISION.md` 仍为 OPEN。
- 同一速率数值与 WAV 格式不保证供应商的响度、停顿或感知语速相同。Fish/Eleven
  的 gentle 条件未执行；Azure HD 当前只准备有文档来源的中文 Flash 配置。
- 实时 CLI 激活、批次费用核验及声线/地区选择需要后续明确授权的修改与审查。
  现有 Adapter、格式验证、缓存和本地播放器可复用；S01 不开启该入口。
- S00 的真机安装、锁屏/后台耐久、电话/蓝牙和手动辅助功能验证仍为历史未完成项。
  本阶段没有把云端 TTS 接入 App，没有部署后端、发布 App 或开始 S02。

交付停在 **READY_FOR_AUDIT**。建议先独立审查协议、离线边界、成本单位和缓存
行为；真实试听与供应商选择等待后续单独授权。不得自行合并 PR。
