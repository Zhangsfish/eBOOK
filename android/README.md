# eBOOK Android

华为 Mate X3 / HarmonyOS 4.2 的独立 Android 阅读器。基于 iOS 0.1.0(39.1)
已接受的阅读行为，使用 Android 系统离线 TextToSpeech。内部测试版0.1.0-android.1，
已真实构建并签名；华为真机尚未连接，不能当作真机兼容性验收。

原生 Java + Android SDK，零第三方运行时依赖。不需要 Gradle、Android Studio、
Kotlin 插件或 Google Play 服务。Java 是为复用现有 JDK/SDK、减少一次性环境体积作出的实现选择。

- `app/src/main/`：应用及资源；`core/` 包可在普通 JVM 独立验证。
- `tests/`：原创数据的 JVM 和 Android 仪器测试。
- `scripts/`：复用现有 SDK 的构建、测试、签名与打包入口。
- `reports/`：工具盘点、真实证据及交付状态。
- 本机 `.local-test-data/`：忽略的原始证据、下载和DPAPI保护的升级密钥，不进入仓库。
- `delivery/`：忽略的本地交付ZIP，含已签名APK、中文说明、SHA256和真实测试报告。

生产编译源码为5d85816；后续测试/报告提交不改变应用内容。最终测试HEAD、
安装程序内容一致性和完整结果见 `reports/TEST_RESULTS.json`，使用边界见
`reports/TEST_REPORT.zh-CN.md`，朋友按 `reports/INSTALL_GUIDE.zh-CN.md` 安装即可。

开发复现：已有Python与JDK时运行 `python scripts/build.py --core-only --test`；
已有SDK35/build-tools35时运行 `python scripts/build.py --test --instrumentation`。
从仓库根目录执行时在脚本前加 `android/`。签名按本次授权仅在AutoDL执行；
不在朋友手机或本机安装开发环境。原生模拟器入口为独立Android工作流。

本轮只交本地 ZIP，不自动公开 APK、不自行合并。
