# S02A.3 — Suxin-Light 真实合成与 Matcha 同文试听

日期：2026-11-25（Asia/Shanghai）。Issue #10，原分支与 PR #7。
状态：READY_FOR_AUDIT — 真实桌面合成和iOS模拟器后端验证已交付；完整原生前端/真机/分发门槛待完成。

## 产品决定与本次结果

已用固定作者代码的真实中文/英文前端和 INT8 ONNX 图完成 Suxin 五段中文及混读
WAV（22,050Hz、单声道、16-bit PCM），没有手写音素、Mock、测试音、预录样本或其他模型替代。
与原 Matcha 五段音频使用完全相同的原创文本，已交付离线 HTML 和含10条 WAV 的 ZIP。

用户在本轮实际试听后明确回复：**“更喜欢 Suxin-Light”**。
据此把 **Suxin-Light 作为优先音色候选，Matcha 保留备用，Kokoro 暂停**。
这是短样本的主观偏好确认，不是十分钟耐听、iPhone 性能或产品分发放行。
没有填写虚构的自然度、柔和度、情绪或发音评分。完整原生文字前端尚未实现。

## 可直接打开的本地材料

新版页面把 Suxin 放在前面，Matcha 仍可逐段比较；没有修改音频或之前的试听材料。

```text
HTML:
E:\myself\eBOOK-s02a\.local-test-data\s02a2\s02a3\listening\matcha-suxin-a748670b89de4ea490939d42ffdf0c09\index.html

含实际 WAV 的 ZIP（解压后打开 index.html）:
E:\myself\eBOOK-s02a\.local-test-data\s02a2\s02a3\listening\matcha-suxin-a748670b89de4ea490939d42ffdf0c09.zip

Suxin 原始五段音频、流式样本与实测 JSON:
E:\myself\eBOOK-s02a\.local-test-data\s02a2\s02a3\outputs\suxin-b7d23f31649f4d1da5433fcda07de49e\
```

最终 ZIP：2,648,067 bytes，SHA256
`4b379a6e89ef17e35320cf8d83281af8f6dcaf87a45710189e617a788840906f`。
10个 WAV 的原始哈希、ZIP成员哈希与CRC核对通过，FFmpeg全文件解码10/10通过。
Chrome157.0.8103.79 + 已有 Playwright1.63.0 逐条实际解码并静音播放10/10通过，
评分初始为空、同时只有一个播放器播放、无JS错误/外网请求，375px无横向溢出。
浏览器静音播放不证明扬声器声学输出；音色偏好来自用户真实试听。
页面、截图、音频、评分和 ZIP 均只在 Git 忽略目录，不提供公开托管。

## 精确版本与来源

- 接手前历史交付：`7d2d1a4d68dcbe4402c367fa0060b95ac44ceb3d`。
- 检查干净工作区后安全 fast-forward 至任务文件基线
  `30569e8519297b195c328f57a0d980250778d66b`；未清理、覆盖或重做旧模型/音频。
- Suxin 五段及作者流式样本实测源码：
  `a7b073d572fe7e4862679678dc872f0887a5e19d`，执行开始时工作区干净。
- Suxin 补充前端/预热混读探针：`9713f7596c9f9a3b9565cfb61dd836b1b3602b5b`。
- Matcha 直接复用 `f015d3dcef870381bc7f7f19fc32bcf8dee5f4e0` 的五条原始输出及
  实测元数据，逐 WAV SHA 核对；没有把新日期写成新一次推理。
- 作者固定 revision：`5ee2da546f3635da263602842d238d8624cb7a81`。
  Suxin图 SHA256：`5dbe3500e7d36835e073dad4f3502a579ae497f62c0a6574c736345237e1e7aa`。
  作者 synthesizer / mixed_frontend 两文件分别保持原 SHA
  `3231440ceaf809465373235d9526b7437906c0b18d8892e74822d6684603b769` /
  `6bbf508c0e7fb6a887da787631d23a09d8e712d5d231e08b8d3a33325cbd333e`。
- 原创语料文件 SHA256：`b03fec6c0ced39735b81fb4793187581603e5f37b2e0d8dae2692eb98c6eaf5c`；
  每段 UTF-8 文字SHA和每个WAV的SHA、帧数、时长均在公开小JSON证据中。
- 最终交付 HEAD 单独列在 PR；不把报告提交SHA冒充上述实际执行版本。

## Windows：真实文字到语音

新环境：`.local-test-data/s02a2/s02a3/runtime/venv/Scripts/python.exe`，
Python3.11.11、NumPy1.26.4、ORT1.20.1、pypinyin0.55.0、piper-tts1.8.0、
pathvalidate3.3.1。只使用 CPUExecutionProvider、4线程、原速1.0。
原装 `SuxinTTS.from_pretrained` + `synthesize_long`，作者推荐 noise_scale/noise_w=0、
group PAD、无语言标签、normalize_audio=false；没有修改作者前处理或声码器代码。

Suxin本轮：模型初始化 **8.418s**，另有Python模块导入 **1.546s**；
加载完成到第一段完整WAV准备好 **1.162s**，两者相加 **9.580s**。
这不是受控冷盘启动或真实首声，不能声称手机5秒内出声已达标。

| 同一原创段落 | Suxin生成s | Suxin音频s | Suxin RTF | 历史Matcha生成s | 历史Matcha音频s | Matcha RTF |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| narration | 1.161679 | 7.306213 | 0.158999 | 0.744199 | 8.034921 | 0.092621 |
| dialogue | 0.515332 | 5.505850 | 0.093597 | 0.683161 | 6.287120 | 0.108660 |
| numbers | 0.593129 | 9.229025 | 0.064268 | 0.853039 | 9.801950 | 0.087027 |
| polyphones | 0.472913 | 6.526168 | 0.072464 | 0.565664 | 7.210068 | 0.078455 |
| mixed | 5.753676 | 5.483084 | 1.049350 | 0.447336 | 4.805125 | 0.093096 |

Suxin 加权RTF **0.249534**、5-case最近秩p95 **1.049350**，进程累计峰值RSS
**265,641,984 bytes**。历史Matcha初始化5.903s、加权RTF0.091131、p95=0.108660、
峰值RSS254,324,736 bytes。两次均为Windows桌面；Matcha先做过独立预热，Suxin
首轮含前端首次使用开销，且执行时间不同，不称严格同温/同负载速度排名。

首次mixed慢不能隐去，也不能直接视为持续生成速度。单独有界补测保留两次真实
原速mixed WAV：前端首次/第二次prepare **0.598478 /0.006162s**；
前端准备后两次完整合成 **0.238670 /0.240547s**、RTF **0.043528 /0.043871**。
两次补测mixed WAV均与首轮mixed原始WAV哈希完全相同。
补测模型初始化5.380s、峰值RSS255,922,176 bytes；不同进程/缓存状态，
不能把首轮5.754s的原因全部归于单一前端步骤或承诺每次都能达到补测速度。

作者 `synthesize_stream_from_tokens` 也实际运行：输入即时提供同一原创叙述全文，
预热后的第一块在 **0.158410s**产出，3块、总耗时0.565165s、音频6.998s。
没有LLM/网络、没有播放探针；这里只证明作者分块接口实际输出，不等于首声或连续听书。

## 中文发音与中英混读

五段作者前端的 `missing_phonemes` 均为空，说明这五段未遇到音素表OOV，
不证明字音/韵律全部准确。保留了作者真实音素及ID用于诊断，没有人工改音素。

复用已安装的本地 faster-whisper1.2.1 / CTranslate2 4.8.2 / large-v3 CUDA，
完全离线转写两模型各五段，仅作待核听线索：

- Suxin转写出现“小宁/小明”“合上/和尚”“银行/野航”和1024/1724等差异；
  mixed中的英文词转写不稳定。可能包含ASR自身识别错误，不能直接标为模型确诊读错，
  更不能换算成人工准确率或声音质量分。
- Matcha的mixed转写缺少原文英文词，符合单中文模型的已知限制；原输入未删除英文。
  其余转写也有个别差异，未自动称为发音全对。
- 用户已明确更喜欢Suxin短样音色；仍建议后续真机检查数字、专名、多音字和混读。
  本阶段不修补作者词典或擅自淘汰模型。

完整机器稿与原始WAV哈希在两份 `*-offline-asr-review.json`；均明确不是人工评分。

## iOS 原生后端：PASS_BACKEND_ONLY

固定原生测试源码：`9713f7596c9f9a3b9565cfb61dd836b1b3602b5b`。
[免费ARM macos-15任务45584309079](https://github.com/Zhangsfish/eBOOK/actions/runs/45584309079)
**实际通过**：50项Python预检、固定原生库/模型核验、Xcode构建、1个真实XCTest
执行五次ONNX图推理和WAV写出；未跳过测试。Xcode16.4(16F6)、iOS18.5(22F77)、
iPhone16 Pro ARM64模拟器，Apple M1(Virtual)，CPU EP、4线程、ORT1.28.2。

图session初始化 **3.358246s**，加权RTF **0.598536**，5-case最近秩p95
**1.210590**；累计峰值RSS **255,180,800 bytes（243.36MiB）**。

| 原创段落 | 模拟器图生成s | 模拟器WAV音频s | RTF |
| --- | ---: | ---: | ---: |
| narration | 5.883332 | 7.558095 | 0.778415 |
| dialogue | 7.350726 | 6.072018 | 1.210590 |
| numbers | 4.711498 | 9.299592 | 0.506635 |
| polyphones | 1.753008 | 6.791837 | 0.258105 |
| mixed | 1.572302 | 5.816599 | 0.270313 |

首段从图合成请求到实际主混音器非零样本 **11.273218s**，不含上述图初始化和
离线Python前处理；不是物理扬声器测量，**5秒目标未通过**。一段RTF超过1，
不能把平均值小于1写成任意段落均能连续跟上播放或长期无中断。
没有继续做CoreML/Kokoro优化，也没有把此结果当成真实iPhone。

使用已有C++ ORT桥和作者 `MixedFrontend.prepare(原文)` 实际输出的完整ID序列，
文件SHA `f07ac7e64ad94dcef10e1504dcd89a72a70a5b646705eb148293b1dc406c474e`。
明确标记 **AUTHOR_PYTHON_FRONTEND_PRECOMPUTED_IDS / end_to_end_native_text=false**；
后端执行已成功，中文前处理仍不在iOS运行。桌面试听使用作者分句/拼接，
本次原生诊断每段以完整预计算ID单次送图，因而两边WAV时长/哈希并不相同；
没有宣称跨平台音频等价、完整原生TTS或让用户把桌面试听误当模拟器录音。
模拟器五个WAV只存在runner临时忽略路径，均有帧数/RMS/SHA，未上传或下载音频。
取回的是3,257-byte小JSON ZIP，GitHub digest/CRC/成员SHA/源码一致性核验通过，
0模型/音频/profile/编译产物。实际元数据见 `suxin-ios-backend-9713f75.json`。

历史Matcha的ARM模拟器4线程加权RTF0.5759及完整首块混音9.815s仍有效，
本轮没有重跑。它使用真实原生文字前端；Suxin这次排除了G2P，不能拿两者数字
宣称完整iOS Suxin比Matcha快或慢。用户确认的音色来自桌面同文试听，不是模拟器音频验收。

首次CI [45583501783](https://github.com/Zhangsfish/eBOOK/actions/runs/45583501783)，
源码bcb6a383e4649e122cffffa28204dd1111ae50e8，预检50项中1项报错：Git自动把
作者Windows导出的CRLF改成LF，严格SHA检查拒绝了变更。未进入原生编译/模型执行，
不是Suxin语音失败。保留原始ID字节并对该单一文件设置 -text / cr-at-eol，
强制重新录入索引；核对Git对象与作者原导出SHA完全一致后才重新dispatch。
没有关闭SHA检查、改音素或放宽端到端标记。

## 完整 Swift 中文前处理：NOT_IMPLEMENTED

现有ONNX已包含SuxinVoc，Windows真实图执行无需移植独立声码器；
原生图证明也不需要重新写一套推理引擎。尚缺的是真实文字前端：

1. 对齐pypinyin的词组正向最大匹配、单字/词组字典、声母/带调韵母转换；
   已安装版两个JSON分别788,780 /2,545,585 bytes，不可用单字拼音替代词组行为。
2. 移植作者的数字/年份/时间、标点、语言分段、一/不变调、特殊字和PAD规则，
   用真实作者前端做逐ID回归，包括生僻字、专名、长句及当前机器稿差异。
3. 混合英文仍需eSpeak等价原生路径及数据/构建/许可证核验，不能手填几段英文ID
   冒充任意用户导入文本可用。中文路径与混读路径需分别验收。

工程估计而非已实测工时：中文等价原型及基础回归约3–5工作日；
混读原生库、设备调试和分发义务需另行确认，当前不承诺完整工期。
本轮没有实施完整前端或正式App接入，保留到后续获授权的任务。

## 依赖与资源：试听实验和产品分发分开

依照Issue10明确授权，新建venv，不使用system-site-packages。
13个必要PyPI wheels先按官方版本JSON核对文件名/大小/SHA，再仅从本地wheel目录
`--no-index --no-deps --require-hashes`安装；`pip check`通过。
依赖锁、声明许可证、许可证/notice文件SHA见 `s02a3/manifests/installed-frontend.json`。
13 wheel共 **69,802,834 bytes**；venv实测269,486,350 bytes，不含共享基础Python；
这些是Windows实验体积，不是iOS App下载/安装包大小。

| 项目 | 实读证据 | 尚未放行的范围 |
| --- | --- | --- |
| Suxin图/代码/配置 | 固定11文件67,430,162 bytes，图67,260,202 bytes；逐SHA通过；作者LICENSE声明MIT | 作者同时列Piper VITS GPL架构、eSpeak GPL及教师来源；模型/数据/声音完整分发链仍需核验 |
| pypinyin0.55.0 / pathvalidate3.3.1 | 官方wheel及MIT声明/许可成员已核对 | 声音/词典数据及最终App整包不能由Python包根MIT自动推定放行 |
| piper-tts1.8.0 / eSpeak | 官方wheel声明GPL-3.0-or-later，相关COPYING成员有哈希；eSpeak数据实测19,088,498 bytes | 原生分发方式、完整对应源码/notices及App分发条件未清关，不能写成纯MIT |
| ORT及其余传递依赖 | 版本/哈希/声明许可证已记录；MIT、BSD、Apache等；没有自建/升级通用环境 | Python wheel审核不替代iOS XCFramework及全部第三方数据清单 |
| Matcha及Vocos/词典/FST | 保留原完整模型资源和S02A.2许可证据；未删文件或把代码许可套给权重 | 精确权重/训练数据/导出及词典通知仍有缺口；免费App不自动取得分发权 |

上述未解决的分发问题没有阻止本次私人本地试听；也未据此宣称公开分发已合法放行。
官方依据：[Suxin固定LICENSE](https://huggingface.co/TEQUILA123/suxin-light/blob/5ee2da546f3635da263602842d238d8624cb7a81/LICENSE)、
[Piper1.8 COPYING](https://github.com/OHF-Voice/piper1-gpl/blob/v1.8.0/COPYING)、
[PyPI Piper1.8](https://pypi.org/project/piper-tts/1.8.0/)、
[pypinyin0.55](https://pypi.org/project/pypinyin/0.55.0/)、
[Matcha固定模型卡](https://huggingface.co/csukuangfj/matcha-icefall-zh-baker/blob/6ccce73a41f1f4be966c485c75bcbf9d13df4819/README.md)。

## 复现、检查与下一步边界

```text
python tools/local-tts-spike/s02a3/scripts/prepare_suxin_env.py resolve
# 查看wheel-audit.json后，在新建项目环境安装：
python tools/local-tts-spike/s02a3/scripts/prepare_suxin_env.py install
PROJECT_VENV/python tools/local-tts-spike/s02a3/scripts/benchmark_suxin.py --model-dir .local-test-data/s02a2/assets/suxin-full-v1 --threads 4
PROJECT_VENV/python tools/local-tts-spike/s02a3/scripts/probe_frontend.py --model-dir .local-test-data/s02a2/assets/suxin-full-v1
python -m unittest discover -s tools/local-tts-spike/Tests -v
python scripts/generate_xcode_project.py --check
python tools/local-tts-spike/scripts/check_delivery.py --desktop-metrics tools/local-tts-spike/evidence/desktop-metrics.json
```

本地Python元数据/范围安全单测50/50通过；它们不代替真实模型合成或iOS推理。
正式阅读器Sources/Tests/工程/STATUS及S01工作区没有改动。用户先前验收的PR #5
在本轮开始时按明确指示合并，merge83fa0d90fd4cd0dbcd791eeb4a3edd53ba985656，
不属于本轮TTS实现。PR #7不会自行合并。

真机推理、完整原生文字前端、连续10–15分钟、锁屏/蓝牙/中断、发热和电量仍为NOT_RUN。
用户已选音色后，后续方案是小段预生成+有界缓存+分段播放、模型常驻/显式预热和真机测量；
本轮只提出方案，没有在正式App实现，也不因几秒完整首段等待再次淘汰候选。
Apple系统朗读保留兜底，不新增模型/供应商、云端请求、收费、后端或发布动作。

所有公开提交和CI产物只允许小源码/JSON/报告；模型、真实音频、私人书、页面和密钥
没有上传。停止在READY_FOR_AUDIT，交给独立审查，不启动S02B或正式发布。
