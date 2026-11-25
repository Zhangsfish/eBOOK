# S02B — 苏心原生接入

日期：2026-11-26（Asia/Shanghai）。状态：IN_PROGRESS，尚未请求最终审查。

本线在 `codex/s02b-suxin-ios-integration` 更新 PR #12。阅读基线 main
`83fa0d90fd4cd0dbcd791eeb4a3edd53ba985656`；交接起点
`1eb0eef18e7011feb8034a393f084a91483b9a8e`。冻结 PR #7 与训练 PR #11 不改。

## 当前事实

| 项目 | 状态与边界 |
| --- | --- |
| 原生 Swift 中文前端 | IMPLEMENTED；全量固定字/词数据、最长匹配、数字/年/时间、一不变调、血、PAD |
| 真实作者前端对照 | SIMULATOR_VERIFIED：92条原创文本逐音素/ID一致，三个测试方法3/3，无跳过 |
| App 真实 ONNX、分段播放、缓存、语速、取消 | IMPLEMENTED / SIMULATOR_VERIFIED：两系统原生12方法通过；全套各41/42，Files点击补测中 |
| 真机首声/跳转/30分钟连续播放/发热耗电 | DEVICE_VERIFIED=NOT_RUN；本机 Windows，没有已连接的 iPhone/Xcode |
| 新安装包 | TESTFLIGHT_AVAILABLE=NO；旧39.1仍是原有苹果朗读版本 |
| 全包分发许可 | INCOMPLETE；具体材料缺口见下，不影响独立本地测试 |

首轮前端测试 HEAD `e3573b7b7ed56f844fbb0dcfa8647d97466c12f1`：
[真实 macOS CI](https://github.com/Zhangsfish/eBOOK/actions/runs/45648983455)。
Xcode16.4(16F6)、iOS18.5、ARM64虚拟Mac、iPhone16Pro模拟器；没有模型合成。
不要把这次3/3或旧 PR #7 预计算 ID 后端结果当作本次完整 TTS 通过。

首轮真实原生图/播放 HEAD `ab0eb5421e308e29177f8fa50aef9616bf2ce4ca`：
[CI 45650400148](https://github.com/Zhangsfish/eBOOK/actions/runs/45650400148)，11方法9PASS/2FAIL，
0跳过。编译与真实PCM合成/播放已发生，但不得写整套通过。
失败为：原队列文本实际只产生2块却断言>2；WAV写入器尚未关闭就重开读取，帧数为0。
修正先关闭写入器使头部落盘，并延长原创队列文本。旧失败JSON保留于evidence目录，
其WAV SHA不算已完成WAV文件验收。旧软件探针RTF/首样本仅是失败运行中的诊断数据。

## 实际完整回归与性能

完整回归执行HEAD：`31951f256c9610ca02b4d41077c64b03d3ecfbdc`。
两次都为真实ARM64 iOS模拟器，不是桌面Python/ONNX输出，也不是预计算音素后端。
完整Swift文字前端→实际ORT→真实PCM/WAV→原生队列/混音器；没有神经推理Mock。

| 环境 | CI | 实际结果 |
| --- | --- | --- |
| 免费macos-15，Xcode16.4(16F6)，iOS18.5 / iPhone16Pro Simulator | [45653198977](https://github.com/Zhangsfish/eBOOK/actions/runs/45653198977) | 42方法41PASS/1FAIL/0SKIP；失败为Files选书UI |
| 免费macos-26，Xcode26.6(17F113)，iOS26.5 / iPhone17Pro Simulator | [45653195410](https://github.com/Zhangsfish/eBOOK/actions/runs/45653195410) | 同样41PASS/1FAIL/0SKIP；失败为Files选书UI |

两台均报告Apple M1(Virtual)、3逻辑CPU，模型CPU4 intra/1 inter线程。
通过项包括原生前端92条逐ID对照、真实模型1.0×/1.5×、WAV关闭后重开帧数校验、
真实PCM三块队列及暂停/继续、准备期取消与迟到事件、缓存版本/损坏/上限、偏好迁移、
真实阅读器控制器播放→跳章→新听书位置落盘、原目录/长篇/主题/位置回归、音色及语速UI保存。
混读回退路由通过记录型系统Provider验证；真实Apple回调是另一项原有测试，不能互相冒充。
取消测试在准备阶段发出取消，没有单独证明每次命中正在运行的ORT Run。

| 短文本软件探针 | iOS18.5 | iOS26.5 |
| --- | ---: | ---: |
| 新Session模型创建，秒 | 1.718077 | 1.688972 |
| 未缓存原文→整段WAV墙钟，秒 | 2.118098 | 2.388901 |
| 1.0×推理耗时，秒 | 0.183389 | 0.416506 |
| 1.0×音频长度，秒 | 3.448163 | 3.448163 |
| 1.0× RTF（n=1） | 0.053185 | 0.120791 |
| 1.5×同文音频长度，秒 | 2.380045 | 2.380045 |
| 1.5×同文RTF（n=1） | 0.059216 | 0.033295 |
| 另3块队列RTF范围 | 0.061143–0.196066 | 0.044326–0.068447 |
| 首次排入播放器，秒 | 2.870482 | 2.041507 |
| 首个非零混音器样本，秒 | 2.986295 | 2.153828 |
| 队列最高缓冲数 / 回调欠载 | 3 / 0 | 3 / 0 |
| 探针处进程生命周期峰值RSS，bytes | 448020480 | 530825216 |

RSS约427.3/506.2MiB，是整个测试宿主进程的lifetime峰值，不是模型增量内存。
队列测试1.5×，包含主动暂停500ms；计时起点之前已激活AVAudioSession，
所以非零混音器时间不是包含全部初始化的真实手机首声。WAV墙钟不含播放。
没有足够样本计算有意义的首声/跳转p95，也没有30分钟吞吐、热状态或电量结果。
不能用这些短块数据与旧Windows/长混读文本直接比较优化倍数。

两系统实际WAV帧数76032，SHA256均为
`4f02c4cb2ec727fbfae4f5645c8024c2136bed93059454ae4c34fef6244a2c88`。
WAV仅在CI测试沙箱生成/重开，不上传音频或App；公开证据只含哈希/参数/计时。

## Files补测与设备归档

上述唯一失败在真实Files面板，选择TXT后仍未进入书架；测试没有绕过失败。
正式导入实现与Info.plist未改。根据两系统AX日志，将预览图/整行点击改为可见文件名
点击，并在未导入且文件名仍可见时限一次双击重试，仍由真实系统选择器导入TXT/EPUB。
测试/驱动修正HEAD：`958a927d6a278283fb435850f8ab1bcc6217f3a4`。
补测仍失败，两系统均1方法0PASS/1FAIL/0SKIP；没有以改断言/跳过/注入书架换取通过。
[iOS18.5补测](https://github.com/Zhangsfish/eBOOK/actions/runs/45657320975)、
[iOS26.5补测](https://github.com/Zhangsfish/eBOOK/actions/runs/45657318415)。
文件名单双击都未得到导入结果；根因未解决，不能断言只是自动化问题，也不能宣称系统入口通过。
保留为 **BLOCKED_QA / Files E2E unresolved**。新建独立问题前可直接用本PR的日志定位。

两次仍实际完成设备Release arm64 archive，6项模型资源逐SHA核对通过；
App包分别92,637,960 / 92,634,564bytes，未签名、无新TestFlight，包不上传公开artifact。
测试失败与archive成功分别保留，workflow整体仍FAIL。

App Sources树在完整回归与补测之间均为
`61148da270588df0d74306421ee46e5861cdb5f4`；测试变更只涉及Files激活方式，
没有改正式App来迎合自动化。

随后发现长窗口开头的空行/分隔符可能变成独立纯空白神经请求；在
`7c1dba22db6e05e7d49a84e3dc37d36ca8b853fd` 将它们并入相邻文字，保留全部原文与UTF16范围，
且纯标点/空白整个窗口在推理前明确回退。真实队列用前导空行原创文本重跑，
状态单测覆盖首部空行、省略号和中间分隔行。该苏心修正的Sources树为
`602aae66b90dcad8b16dea38dbe0eb02b22dd4f4`。
准备期取消用例已更名以准确反映覆盖范围，不再暗示确定命中每次ORT Run。

### 最新苏心原生回归：7c1dba2

- [iOS18.5：45658774211](https://github.com/Zhangsfish/eBOOK/actions/runs/45658774211)：12PASS/0FAIL/0SKIP。
- [iOS26.5：45658772525](https://github.com/Zhangsfish/eBOOK/actions/runs/45658772525)：12PASS/0FAIL/0SKIP。
- 以上为前端、真实图/PCM/控制器和状态缓存的12项，**不是完整42项重跑**。
  两次另外都完成真实设备arm64 Release archive及6项资源哈希校验；整个workflow成功。

| 最新短探针 | iOS18.5 | iOS26.5 |
| --- | ---: | ---: |
| 模型创建，秒 | 1.892470 | 2.151580 |
| 冷原文→完整WAV墙钟，秒 | 2.413153 | 2.654273 |
| 1.0× RTF（n=1） | 0.067205 | 0.052279 |
| 1.5×同文RTF（n=1） | 0.165551 | 0.080684 |
| 另3块队列RTF范围 | 0.051709–0.115733 | 0.057327–0.092423 |
| 首次排队，秒 | 3.048328 | 3.286088 |
| 首个非零混音器样本，秒 | 3.351578 | 3.598104 |
| 最大队列 / 回调欠载 | 3 / 0 | 3 / 0 |
| 探针处进程lifetime峰值RSS，bytes | 427425792 | 513867776 |
| unsigned Release App bytes | 92638096 | 92634692 |

此队列包含前导空行与主动暂停500ms，音频会话已在计时前激活；最新首样本数字超过3秒，
不能用旧较快样本宣称冷启动目标已通过。RSS约407.6/490.1MiB；完整套件历史峰值仍保留
530825216bytes，不能把scope不同造成的数值变化归为内存优化。WAV SHA仍为上述4f02…2c88。
真实iPhone首声/p95/30分钟/热/电量目标均未执行。

Files进一步验证HEAD `3633d421dcf6484b993c3962ab17a84baf473f72`：
用`UIDocumentPicker`的保留delegate显式桥接同一个系统Files界面，单文件/asCopy导入；
库解析、编码、协调读取与持久化不变。真实选择与取消两个用例正在补测，不提前宣布修复。

## 实现及边界

- Swift前端消费全量41,923单字、47,111词组和1,559通用音节转换条目。
  测试oracle由原装作者代码和pypinyin0.55.0实际计算，未人工填音素；另有训练外
  新文本验证。字典与模型通过版本/大小/SHA256校验；Python/Piper/eSpeak不进App。
- 仅原生中文。含英文、未知字符或分块后不支持的内容，在播放前验证整个有界窗口，
  提示后整窗口使用Apple语音，不静默丢字。苏心失败不自动假装另一音色成功。
  混读回退不是原生英文G2P；不同窗口可能有明确提示的音色变化。
- 直接ORT CPU推理：4 intra/1 inter线程、一个后台actor/session；RunOptions支持取消。
  不在主线程加载模型/词典或推理，不启用CoreML，不带历史sherpa/Kokoro/Matcha包。
- 首块约18字符，后续约36字符，优先标点，保留原始UTF16地址与数字单位。
  最多3个PCM缓冲、一个下一窗口的2个预取子块；禁止整章/整书音频预生成。
  硬切长句仍可能影响边界多音词/变调，需长听核验，不能用92条前端一致性替代音质验收。
- 64MiB缓存保存在App私有Caches并排除备份；身份包括资源清单指纹、文本摘要、
  声音、语速和格式版本；PCM负载哈希验证，损坏失效，容量LRU淘汰。不记录正文。
  缓存不按书籍建索引；移除一本书后其旧派生音频可能保留到淘汰/系统清缓存或删除App数据。
- 音色选择保留苹果语音，苏心0.5–2.0×；旧偏好文件迁移不丢阅读/苹果语音设置。
  暂停不让迟到合成开始播放；跳转/切声/切书取消推理与队列，代际身份挡住迟到事件。
  隐藏面板继续播放；原有目录实时定位、主题和右下角入口保留。
- 听书位置只在短块实际播放回调后推进，重启可重读当前短块；不是逐词/逐帧持久化。
  队列回调欠载统计是软件探针，不能当作手机听感无中断证明；跨外层窗口仍需长听检查。

## 资源及分发核对

固定模型revision `5ee2da546f3635da263602842d238d8624cb7a81`；INT8图67,260,202bytes，
SHA256 `5dbe3500e7d36835e073dad4f3502a579ae497f62c0a6574c736345237e1e7aa`。
6项模型/字典/声明总69,551,510bytes；完整清单由准备脚本确定性生成，权重/音频不入Git。
ORT SPM `8ebc5ebf92190903c274a7621ba4c96a732335ec`，iOS ZIP33,821,118bytes，
SHA256 `2c2299acbb461d26d4bac4bc85985d40e7c7177ed6072703ae0846d88b0b4599`。
实际Info.plist含设备arm64、模拟器arm64/x86_64；原包没有license/notices。
对应Microsoft v1.28.2 tag及LICENSE/ThirdPartyNotices读取404，尚未核验精确源码与静态依赖BOM。

作者根MIT和pypinyin MIT完整随模型准备；作者也明确列出Piper VITS GPL、eSpeak/Piper
GPL、教师模型与语料链。原生App没有Piper/eSpeak运行库，不等于权重/数据分发链已清。
见 [NOTICE](../tools/suxin/NOTICE.md)。不能以另一源码版本的MIT文本冒充已完成整包核对。

## 真实命令及边界

```text
Windows / Python3.11.11 / existing approved environments:
scripts/generate_long_gb18030_fixture.py
E:/myself/eBOOK-s02a/.local-test-data/s02a2/s02a3/runtime/venv/Scripts/python.exe -X utf8 tools/suxin/scripts/export_author_reference.py --author-dir E:/myself/eBOOK-s02a/.local-test-data/s02a2/assets/suxin-full-v1
tools/suxin/scripts/prepare_resources.py --source-dir E:/myself/eBOOK-s02a/.local-test-data/s02a2/assets/suxin-full-v1 --pypinyin-wheel E:/myself/eBOOK-s02a/.local-test-data/s02a2/s02a3/runtime/wheels/pypinyin-0.55.0-py2.py3-none-any.whl
tools/suxin/scripts/inspect_runtime.py
scripts/generate_xcode_project.py --check
scripts/check_source_safety.py --output <ignored-local-evidence>

Free macOS runner / installed Xcode:
python3 tools/suxin/scripts/prepare_resources.py
python3 tools/suxin/scripts/inspect_runtime.py
python3 scripts/generate_long_gb18030_fixture.py
python3 scripts/generate_xcode_project.py --check
python3 tools/suxin/scripts/ci_integration.py --scope all
python3 tools/suxin/scripts/ci_integration.py --scope picker
python3 tools/suxin/scripts/ci_integration.py --scope integration
```

生成器一致性、2301482字符GB18030原创夹具、固定资源准备、基础源内容安全检查已通过。
初次安全检查误把main已有TOC PNG按普通文件200KB上限拒绝；只放行两个已批准截图目录，
对TOC PNG另外逐字节比较main83fa基线，未放宽新音频/模型/正文检查。
本次误运行旧S01入口 `python -m unittest discover -s tools/tts-lab/tests` 得ImportError：
该模块属于未合入的PR #4，本分支不存在；未安装依赖或移植其代码，不计入S02B测试通过数。

## 待审查与未完成

真机首声p95/未缓存跳转、1.0×与1.5×各30分钟、峰值内存/发热/电量、锁屏/电话/蓝牙
都为NOT_RUN。没有可用的本机Xcode/连接iPhone；另见 [真机清单](S02B/DEVICE_CHECKLIST.md)。
完整运行库/权重分发材料仍INCOMPLETE，独立审查和现有签名路径之后才可提供新内部测试。
没有上传新TestFlight，没有公共App Store发布，不自行合并、训练或寻找其他模型。
