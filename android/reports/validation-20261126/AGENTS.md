# Android本次交付证据

用途：本轮内部APK的可审查、可哈希验证证据。上游为android/AGENTS.md与交接。
原始材料是官方CI下载后核对GitHub SHA256、ZIP CRC、HMAC并解密的本机归档，
以及AutoDL已签名产物的公开元数据。仅复制白名单文件，不含APK、测试引擎、
工具、密钥、凭据、私人书或手机唯一标识。

core-cloud.json是5d85816真实JDK17执行结果。api*-main/resume.json保留原始
UTF8字节；对应最终运行编号和测试HEAD见上一层TEST_RESULTS.json。
version-and-source.json、签名与包信息是已回收云端官方工具输出，不手工改写。
PNG只展示原创测试书；人工检查的运行2a942ac与最终生产应用树一致，
截图来源/哈希和具体复核项见visual-review.json。SHA256SUMS.txt逐文件核对。
本证据全部来自JVM/模拟器；Huawei Mate X3真机、声线、功耗仍NOT_RUN。
