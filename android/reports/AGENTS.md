# Android交付证据记忆

状态：READY_FOR_AUDIT，等待独立审查和朋友手机验收，不自行合并。
上游：android/AGENTS.md 与 task-handoff/HANDOFF_ANDROID.md。

生产APK源码5d85816e829a05414c1d13b3e4daf5e54586f4a6；61,913字节，0.1.0-android.1。
最终原生测试HEAD dd7333c80ab5379a306e71fee0bb2684838ff2ea，运行45663796803。
两个SHA的android/app树均为bc25683464dd51aa7308dc7d25a0dd255d742496。
云端JVM32/32；API30 AOSP和API35 Google APIs各主21+重启4全部通过。
两套已安装CI程序内容逐项等于最终签名APK。CI临时签名不是升级证书。
物理Mate X3、手机真实声音、真实铰链/长期锁屏/蓝牙/来电/功耗全部NOT_RUN。
受控PCM测试引擎不在交付APK，也不是华为声线音质证明。

文件图：
- TEST_RESULTS.json：规范的机器结果、精确SHA/运行、摘要与全部原始用例/指标。
- TEST_REPORT.zh-CN.md：朋友可读真实报告；INSTALL_GUIDE.zh-CN.md：中文安装使用。
- validation-20261126/：白名单原始JSON、公开签名/包元数据、原创测试书PNG及哈希。
- BUILD_ATTEMPTS.md：失败/取消与修复历史，不将早期失败算通过。
- TOOLS_AND_BUDGET.md、cloud-toolchain-manifest.json：盘点、来源、预算与关机。
- DELIVERY.json：最终本地ZIP和成员校验清单；实际APK/ZIP在忽略的android/delivery/。

本机没有安装新工具或解出签名JAR。SDK/JDK仅在新AutoDL任务容器；无KVM，
模拟器仅用公共仓库免费标准CI。最终密钥由AutoDL生成，已SSH回收为Git忽略目录
.local-test-data/private/ebook-upgrade-signing.dpapi，Windows DPAPI CurrentUser往返核验；
云端private-signing/已清理。约2026-11-26 01:07控制台已确认CPU151“已关机”。
原07:30定时关机估算6.96元低于10元预算，不是实际账单。不要为了报告/测试修改重启云端。

原始加密CI与解密证据在忽略的.local-test-data/ci/<run>/；download_ci.py核对
GitHub SHA256、CRC、HMAC，不提取旧归档的工具。后续工作流已完全移除签名工具传输。
最终签名包与云端32项在.local-test-data/cloud-results/5d85816/。
签名密钥不得放入Git/CI/ZIP；若未来授权升级签名，先恢复原证书，不要生成替代证书。

本轮只改android/和新增Android工作流，另三个原iOS/S01/S02A checkout及既有PR未操作。
