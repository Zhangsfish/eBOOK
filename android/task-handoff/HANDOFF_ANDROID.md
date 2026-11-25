# 华为版 eBOOK — 新对话直接开工交接

状态：READY。用户2026-11-25明确要求在另一个对话开始实现，最后给朋友一个能安装的
安装包压缩包。本交接不是Android已完成/已适配真机的证明。

## 产品与目标设备

- 用户截图已确认：HUAWEI Mate X3，型号ALT-AL00，HarmonyOS4.2.0。
  这是折叠屏手机，需要覆盖折叠/展开、旋转/尺寸变化和阅读进度保持。
- 用户认可的iOS版本为内部0.1.0(39.1)：沉浸阅读只留右下角“⋯”入口，
  点开才显示返回、目录、字号/行距、主题、朗读、进度；目录跟随当前阅读章。
- 用户要求除朗读平台实现外，其余阅读功能与该版本一致。Android使用手机自带
  系统朗读即可，不在本任务集成Suxin、Matcha、Kokoro或任何云端TTS。
- “沿用同样模型”是本次编码助手配置要求；不要误解为把iOS研究模型移植过来。
  来源会话/创建方不指定新的model/thinking覆盖，沿用用户当前配置，不擅自降级。

## 已准备的工作区与基准

- 新的独立Git checkout：E:\myself\eBOOK-android。
- 当前分支：codex/android-system-tts-reader。不要切换main开发。
- 起始main：83fa0d90fd4cd0dbcd791eeb4a3edd53ba985656，已经合并用户验收的PR#5。
- iOS实际测试/签名源码：7509547a0b62598097ff5f24ca6eb9611455109c。
- PR#5交付源码/文档：3844c1be7a1e058c354f138e6079f6e636899449。
- 仓库：https://github.com/Zhangsfish/eBOOK。新Android模块写在android/，
  不编辑正式iOS代码、原有Tests/Xcode工程/STATUS或既有iOS工作流。
- 检查git status并保留本交接文件；这是来源会话准备的新任务改动，不要清理覆盖。

参考阅读这些基准文件，迁移行为而非把Swift代码假装运行在Android：

1. android/AGENTS.md、本交接；全局工具安装和隐私规则。
2. docs/PRODUCT_SPEC.md、docs/TECHNICAL_PLAN.md、docs/TEST_DATA.md。
   它们原本描述iOS，Android平台的差异以本次用户明确授权和android/AGENTS.md为准。
3. Sources/eBOOK/ReaderView.swift、ReaderTable.swift、LibraryModel.swift、SpeechController.swift。
4. Sources/ReaderCore/：导入/解码/章识别/存储/目录/阅读位置行为。
5. Tests/CoreTests/ReaderCoreTests.swift、Tests/UITests/ReaderUITests.swift。
6. reports/S00/toc-current-chapter/DELIVERY.md、TEST_RESULTS.json及原创书截图；
   reports/S00/device-01/：沉浸入口/三主题历史证据。

现有iOS26 Files-picker UI测试失败仍是iOS历史问题，不得伪造为通过，也不要在
本Android任务修复它。Android要有自己的真实系统选文件导入与测试结果。

## 本次实现与验收

### 阅读与导入

- 原生Android实现，Kotlin优先；选简洁、维护良好且许可可用的界面/EPUB方案。
- 系统文件选择器导入本地EPUB/TXT，无账号/书城/爬书/后台上传。
- UTF-8、UTF-16(LE/BE)、GBK、GB18030；中文不乱码，不静默有损替换。
- 本地书架、书名/进度、打开/移除/恢复；阅读与听书位置分别持久化。
- 长篇TXT必须分块/增量渲染，不可整本放进一个Text或一次性解码所有正文视图。
- TXT章节兼容原S00混合标题，不能把正文每一行数字都当章节。
- 每次打开目录按实际可见阅读位置定位并勾选当前章节，不能仅记住上次点选章。
  清空上次目录搜索；浏览/关闭目录不移动正文；点选章节才跳转。
- 字号、行距、浅色/护眼/深色；沉浸页面不常驻白色按钮、返回或进度条。
  “⋯”对比克制但可发现，点击区域满足Android无障碍要求；正文滑动/轻点不弹控件。
- 保留折叠/展开与重启后的章/段落位置；界面重排不丢书、不从开头重置。

### 系统朗读

- 使用android.speech.tts.TextToSpeech，查询实际安装引擎/中文离线声音。
  不依赖Google Play服务、Google语音包、账号或收费SDK；不承诺手机未验证的声线。
- 播放、暂停/继续、停止、语速、章节/段落导航、进度保存与恢复。
  用实际回调维护听书位置，避免关闭面板就停止或无限重复当前段。
- 按句/段分块，符合引擎输入限制；后台/锁屏、通知/媒体按钮、音频焦点/耳机事件
  依据官方Android API实现并记录真实验证，注意华为后台限制。
- 缺少中文离线声音时明确提示，并通过用户主动操作打开系统TTS设置。
  阅读必须仍可使用，不暗中改云端，也不让用户提供API Key。

### 真实验证与交付

- 复用scripts/generate_long_gb18030_fixture.py生成原创2,301,482字符测试书，
  验证导入、中文/混合标题、长距离滚动、目录自动定位、内存与重启进度恢复。
- 实际编译APK并校验签名/包信息/安装可用性；自动化单测与可用的模拟器测试分开记录。
- 目前没有通过ADB连接这台Mate X3；朋友未安装前，华为真机/发热/电量/锁屏结论
  必须NOT_RUN，不能把桌面、JVM或模拟器结果写成这台手机实测。
- 最后交付一个本地ZIP：已签名可安装APK、中文安装/使用说明、SHA256、版本与源码SHA、
  测试结果及已知问题。内部测试签名可用但必须明示，并安全保留签名密钥以便后续覆盖升级。
  不交付仅AAB或未签名APK，不要求朋友安装Android Studio/ADB/编译环境。
- 模型/音频/私人书、签名私钥/设备唯一标识不进入源码、CI公开产物或交付ZIP。
  APK/ZIP本轮本地交付，不自动上传公开Release/应用商店；不自行合并任何PR。

## 工具盘点与停止边界

来源会话只做了初查：PATH能找到java/javac；未在PATH发现Gradle/adb/sdkmanager/
emulator，默认C:\Users\Zhang S\AppData\Local\Android\Sdk未发现。**这不是全面盘点**；
新对话仍需检查现成IDE/SDK/JDK/WSL/其他已安装环境，以及免费标准CI的既有Android工具。
尚未安装Android工具，也未承诺构建已可用。缺新工具/依赖时按全局规则集中说明并请求
必要免费安装授权，项目隔离，不能自行全局安装或接受商业/发布协议。

可以开始实现、测试、准备内部签名与本地安装包。不能改动iOS/S01/S02A研究，
不能发布商店、用付费CI/云端TTS或把系统设置/安装步骤伪装为已在用户手机完成。
完成后READY_FOR_AUDIT，给用户APK ZIP的完整本地路径和准确测试/源码版本。

## 已有工作必须保留

- E:\myself\eBOOK（S01）：3bfb4429fe7a42e50df62f4857bcb9909bf00ab3。
- E:\myself\eBOOK-device-validation：3844c1be7a1e058c354f138e6079f6e636899449；PR#5已合并。
- E:\myself\eBOOK-s02a：eeee1443c1aac561035cf30590ff323c30ccab8a；PR#7未合并，READY_FOR_AUDIT。
  用户对Suxin的试听偏好已确认，但此Android任务不接本地AI，不继续S02B。
- 本新目录没有模型、WAV、私人小说、截图或密钥。

## 官方依据（交接时已读，后续API/构建版本仍查最新官方资料）

- 华为HarmonyOS4.2安装包安装说明：
  https://consumer.huawei.com/cn/support/content/zh-cn01089223/
- Android系统TTS：
  https://developer.android.com/reference/android/speech/tts/TextToSpeech
- 离线voice能力查询：
  https://developer.android.com/reference/android/speech/tts/Voice#isNetworkConnectionRequired()

只保留手机型号/系统事实；不得复制来源截图或序列号、IMEI、MEID、设备自定义名称。
