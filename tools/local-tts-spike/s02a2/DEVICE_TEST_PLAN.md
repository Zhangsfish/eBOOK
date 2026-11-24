# 已有签名环境的最小真机复现计划

状态：**DEVICE_NOT_RUN / BLOCKED_ENV**。以下是待执行步骤，不是安装或测试成功记录。
Windows 当前仅识别到 iPhone 蓝牙音频接口，没有已连接且获信任的 Xcode 部署设备。
既有 device-validation 工作流只制作无签名准备包，不能把它当作真机运行。
本轮没有读取、导出或复制 Apple 凭据、UDID、证书，也未创建账户或描述文件。
Kokoro 的一次 CoreML 机会已结束，不再启动 Kokoro 真机或调参任务。

若独立审查后仍明确授权 Matcha 真机复核，使用已有 Mac/Xcode、已授权开发者团队
和现有有效签名。没有这条路径时停止并保持 DEVICE_NOT_RUN；不创建新签名资源。

1. 在该 Mac 检出报告中的精确实现版本，使用已有 Python 3 和 Xcode 16.4 或记录实际版本。
   通过 `model_assets.py --model matcha --download --directory .local-test-data/s02a2/assets/matcha`
   取回完整固定资源，然后运行：

   ```text
   python3 tools/local-tts-spike/s02a2/scripts/stage_device.py --model-dir .local-test-data/s02a2/assets/matcha
   ```

   此步骤只复制到新的 Git 忽略目录，不签名、不安装、不运行模型。保留输出目录内
   `s02a2-context.json` 中的源码/脚本/语料哈希。不要将含模型的目录上传到 GitHub。

2. 连接、信任 iPhone，并在 Xcode 中确认现有团队和有效开发签名。进入上一步打印的
   package 目录。通过 Xcode 本机界面选择该设备；若使用终端，下述占位值只在本机填写：

   ```text
   xcodebuild -scheme LocalTTSSpike -destination 'platform=iOS,id=LOCAL_DEVICE_ID' -derivedDataPath ../DeviceDerivedData -clonedSourcePackagesDirPath ../DeviceSourcePackages -parallel-testing-enabled NO DEVELOPMENT_TEAM=EXISTING_TEAM CODE_SIGN_STYLE=Automatic -only-testing:LocalTTSSpikeTests/MobileCandidateTests/testMatchaThreads4 test
   ```

   不加 `-allowProvisioningUpdates`，不把设备 ID/团队凭据写入报告或 Git。缺少现成签名
   时记录完整本地错误并停止。核对实际 checkout 仍为 sherpa `38016c6e0622e90bf417c35e8b47e0eb805af417`
   和 ORT 包装仓库 `8ebc5ebf92190903c274a7621ba4c96a732335ec`，以及二进制固定 SHA。
   先运行一个四线程短测；不要自动扩大为线程/设备矩阵。必要时用相同设备上的二线程
   测试解释实际失败，必须另记原因、环境和结果。

3. 日志必须明确出现 `IOS_PHYSICAL_DEVICE`。记录 iPhone 型号/SoC/iOS、Xcode、Debug
   配置、模型加载/预热、五段各自耗时/RTF、加权与 p95、非零混音输出时间、进程峰值 RSS。
   模型哈希和 WAV 哈希是完整性证据，不能证明人工音质。现有探针在整段合成后启动
   AVAudioEngine；首 callback 不能替代首次播放，也没有扬声器回录或麦克风物理出声测量。

4. **本仓库尚未实现或运行 10–15 分钟真机播放/热量/电量/锁屏验证工具。** 短测不能
   替代它。只有短测达到门槛且用户认可音色后，才可另行审查是否值得继续。后续真机
   会话需固定音量/路由、充电状态、屏幕状态及环境温度，记录起止电量、thermalState、
   Instruments 内存/能耗曲线、锁屏/来电/暂停恢复及断音；不得用生成 600 秒 WAV 冒充。
   当前所有这些验收项仍为 NOT_RUN，不授权 S02B 或正式 App 变更。
