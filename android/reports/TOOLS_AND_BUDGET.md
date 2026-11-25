# 编译环境与预算

用户2026-11-25/26授权：AutoDL必要软件可自主安装，总租用费用不超过10元；
本机不新增工具，最终签名也在AutoDL完成。工作结束核对服务器已关机。

本机已核对PATH、常用安装目录、工具/缓存目录、IDE/JDK注册表和WSL：
已有`E:/java` JDK25、WSL OpenJDK11运行时、便携gh2.104.0；未发现Android SDK、
Gradle、adb、emulator或Kotlin编译器。没有安装本机Android工具。
SSH复用`F:/anaconda3/python.exe`的Paramiko2.8.1/pywin32；加密解包复用cryptography42.0.2。
这些均是已有环境。入口/凭据留在Git忽略目录，密码和传输私钥使用DPAPI CurrentUser。

本次新租AutoDL重庆A区151机：纯CPU32核、120GB内存，按量¥0.88/小时，
系统盘30GB、免费数据盘50GB，没有扩容。控制台已保存2026-11-26 07:30
（Asia/Shanghai）定时关机，设置时估算累计¥6.96，低于10元预算。
已于2026-11-26约01:07主动关机，控制台明确读回“已关机”；没有等待定时器空跑。
¥6.96是原定时上限估算，不是实际账单；未把它当作实付金额。
容器未提供`/dev/kvm`；不能把它称为硬件加速模拟器环境。

云端任务根：`/root/autodl-tmp/ebook_android_20261125`。这是本任务单独新租的容器，
未启动/修改其他研究实例。Temurin17官方GitHub档在该网络下慢且多次断流，
未通过完整哈希的下载未执行、未冒充安装成功。随后使用容器预配置华为镜像的
Ubuntu签名APT仓库安装OpenJDK17.0.21.1+2（`17.0.21.1+2-1~22.04.1`），
仅影响本次新容器；SDK仍保存在任务`toolchain/`。APT验证源签名/包散列。

Android SDK官方来源和验收：

| 组件 | 下载字节 | 官方校验 | 观测SHA256 |
| --- | ---: | --- | --- |
| platform-35_r02.zip | 64273788 | Google仓库XML SHA1 | 0988cacad01b38a18a47bac14a0695f246bc76c1b06c0eeb8eb0dc825ab0c8e0 |
| build-tools_r35_linux.zip | 61958799 | Google仓库XML SHA1 | bd3a4966912eb8b30ed0d00b0cda6b6543b949d5ffe00bea54c04c81e1561d88 |
| platform-tools_r37.0.3-linux.zip | 9571024 | Google仓库XML SHA1 | 214548146cadb2ca3508143d8a1d4be4c59de5bb837253e3ede89ed74cf450d1 |

原始`manifest.json`由bootstrap脚本生成，包含官方URL、SHA1、字节数和SHA256。
不安装Android Studio、Gradle或第三方阅读/语音库。编译用原生Java、aapt2、D8、zipalign；
最终用官方apksigner在AutoDL签名和验证，升级密钥先DPAPI回收核验再清理云端。
5d85816的签名APK已下载并核对SHA256；升级密钥DPAPI往返验证完成，云端
`private-signing/`已删除并通过不存在检查。本机没有下载或运行apksigner JAR。

独立免费标准GitHub `ubuntu-24.04` runner已读回预装SDK35/build-tools35和KVM。
仅新增Android工作流。Android11/API30使用AOSP镜像，Android15/API35使用Google APIs
测试镜像；后者是测试环境属性，应用自身没有GMS依赖或INTERNET权限。
公开CI只留RSA-OAEP/AES-CTR/HMAC认证加密的二进制证据，不公开可安装APK。
每份下载均核对GitHub artifact SHA256、ZIP CRC/路径和包认证后才解包；本机不解出签名工具。

SDK依据：[官方仓库清单](https://dl.google.com/android/repository/repository2-3.xml)、
[SDK许可](https://developer.android.com/studio/terms)、
[免费标准CI规则](https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job)。
实际构建、模拟器和手机验收另记；本文件不是功能测试通过证明。
