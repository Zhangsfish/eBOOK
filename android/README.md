# eBOOK Android

华为 Mate X3 / HarmonyOS 4.2 的独立 Android 阅读器。基于 iOS 0.1.0(39.1)
已接受的阅读行为，使用 Android 系统离线 TextToSpeech。实现中，尚未交付 APK。

原生 Java + Android SDK，零第三方运行时依赖。不需要 Gradle、Android Studio、
Kotlin 插件或 Google Play 服务。Java 是为复用现有 JDK/SDK、减少一次性环境体积作出的实现选择。

- `app/src/main/`：应用及资源；`core/` 包可在普通 JVM 独立验证。
- `tests/`：原创数据的 JVM 和 Android 仪器测试。
- `scripts/`：复用现有 SDK 的构建、测试、签名与打包入口。
- `reports/`：工具盘点、真实证据及交付状态。
- 本机 `.local-test-data/`：忽略的构建工具/下载/内部升级签名与包，不进入仓库。

本轮只交本地 ZIP，不自动公开 APK、不自行合并。
