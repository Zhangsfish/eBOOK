# 文案与点按翻页的手机更新

状态 **WAITING_OWNER_FEEDBACK**，`TESTFLIGHT_AVAILABLE=YES`。新版本 **0.1.0（48.1）** 于 2026-11-27 19:38:08（北京时间）确认可安装。39.1 和 47.1 的测试组关联保留。

- eBOOK 审查提交 `03b527ced4a94ea4b8cd7a3632ce63787d42a40d`。实际打包源码固定为 `03fe0237462f0af0595d47c455c7e5756d6cbd97`。八项构建输入与审查前的实测源码一致。[独立审查](INDEPENDENT_REVIEW.md)
- 现有签名桥 PR #26 的本轮基线 `af7f4d0cfdc6464064ea1e123da1cc93457bf86f`，执行代码 `e0a122b499ef417fba032e58cb1181594634a08a`。[签名桥](https://github.com/Zhangsfish/lecture-asset/pull/26)
- 正式上传作业 run 48 / attempt 1 交付 **0.1.0（48.1）**，job `140478918532`。标准 macOS runner，Xcode 26.6（17F113）。[作业 45991125943](https://github.com/Zhangsfish/lecture-asset/actions/runs/45991125943)

## 归档核对

签名桥的 checkout ref 和源码门禁同时固定到 03fe023。无 Apple 凭据的步骤依次准备资源、核对运行库并验证工程。Release 归档使用同一 runner、源码、项目、构建号和 DerivedData。先关闭映射生成建立基线，再开启生成并检查映射存在。比较两份实际归档内的主程序摘要、App 身份和 6+2 资源。两次摘要一致才可进入原有框架检查。根据活跃的静态链接和无 ONNX 动态依赖的证据，仅移除匹配原有身份、路径和文件集合的多余框架。移除后复核主程序及 6+2 资源，继续现有 Internal Only 上传和 Owner iPhone 关联。

本机 YAML、Bash 和 Python 语法及归档顺序核验通过。确认现有 Secrets 引用、权限、组、runner 和发布方式。先前两套真实 iOS 模拟器各 10/10，归档通过，本轮沿用其测试证据。[测试记录](DELIVERY.md)

## 实际上传与状态

| 北京时间（2026-11-27） | 实际状态 |
| --- | --- |
| 19:33:22 / 19:33:50 | 关闭、开启链接映射的两份 Release 设备归档通过。App 标识、版本、构建号及 6+2 资源通过。 |
| 19:33:55 | 两份归档的主程序摘要一致。活跃链接映射确认 `_OrtGetApiBase` 已静态链接，主程序及根部动态库无需该 ONNX 框架。移除多余的 33,798 字节后，主程序与 6+2 资源复验通过。 |
| 19:35:53 | Xcode 上报 Apple 接受 48.1 的内部上传。 |
| 19:38:08 | App Store Connect 实际读回 48.1 为 `VALID`、`INTERNAL_ONLY`、未过期、现有 Owner iPhone 关联通过、`IN_BETA_TESTING`。 |

本次归档主程序 SHA-256 为 `89605d8567d02a50a29352d1d303934487364ac429de00fad3ce10c537b538f1`。开启映射及整理框架前后均相同。App 从 93,053,274 变为 93,019,476 字节。模型 SHA-256 为 `5dbe3500e7d36835e073dad4f3502a579ae497f62c0a6574c736345237e1e7aa`。Xcode 上传路径无留存 IPA。[事件证据](phone-delivery-evidence.json)

本轮完成签名桥和内部交付。两套各 10/10 属于已审查的 03fe023 模拟器结果。48.1 的真机更新、点按、选字和 VoiceOver 仍待手机反馈。本轮停止在 `WAITING_OWNER_FEEDBACK`。

## 更新说明

在 TestFlight 的 eBOOK 条目点“更新”到 **0.1.0（48.1）**，保留原 App 和书库。在书架右上角选左右翻页模式，再打开原来在读的书。点左侧上一页、点右侧下一页，滑动也能翻页。开关设置和目录，再退出重开看位置。顺手试双击和长按选字、连续点按，并继续听苏心。体验 3–5 分钟即可反馈。
