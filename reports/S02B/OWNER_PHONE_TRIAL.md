# Owner手机试用交付

状态：**WAITING_OWNER_FEEDBACK / TESTFLIGHT_AVAILABLE=YES**（2026-11-27）。
可安装版本：**0.1.0（47.1）**。Apple于北京时间11:21:56实际读回VALID、INTERNAL_ONLY、
未过期、既有Owner iPhone组关联及IN_BETA_TESTING。39.1及其关联保留。
手机安装/升级和体验尚待owner反馈，全部NOT_RUN；可安装状态不等于用户已经安装。

- 本次更新包括已批准的本地苏心朗读与速度选择；保留苹果系统语音。
- 已批准的Files选书修复、目录同步、上下/左右阅读、独立书架与书内主题一起进入本次包。
- 本轮只完成交付桥、真实打包/上传/可安装核验和记录，没有追加功能或重复完整App CI。

## 交付身份与范围

- 授权：[唯一任务](../../tasks/S02B_OWNER_PHONE_TRIAL.md)，APPROVED_FOR_OWNER_BETA。
- 固定reader：`6469489062e6b91d743295cc2c08320334dbbf17`；没有修改App/工程/模型/运行库/测试。
- eBOOK任务起点：`97e7a2bb0f395f557bd3b84a6a8249617fe871a1`，PR12，不合并。
- 原桥：`Zhangsfish/lecture-asset` / `codex/ebook-device-installation`；
  起点`0be62cf0a51a5dfc0f8a271b95c2ae9e31c22ded`；[桥PR26](https://github.com/Zhangsfish/lecture-asset/pull/26)仅记录差异，不合并。
- 标准免费公开仓库macos-26 runner；本次实测Xcode26.6（17F113）。本机沿用Python3.11.11、PyYAML6.0.2、Git Bash；无新安装。

桥的reader ref和EBOOK_TESTED_SHA均固定到6469489。无Apple凭据步骤先执行
`prepare_resources.py`、`inspect_runtime.py`，再执行工程`--check`、Bash语法及Swift类型检查。
真实archive在bundle/version/source检查后、任何export/upload前调用reader统一`validate_resources`，
严格核对6模型文件、manifest和2份固定源声明及完整文件集合。未重复完整App CI。

原Secrets引用/team/既有Owner iPhone组保持在同一个步骤，未增加凭据或扩大到准备步骤。
新增两个非秘密operation字段及有限inspect-export/status-only操作；原正式upload仍Internal Only。
JWT/既有组核验与关联POST规则不变；没有创建tester/group/key/account，保留39.1及其关联。
额外GET buildBetaDetails必须确认IN_BETA_TESTING与未过期，才可声明可安装。

## 实际执行记录

| 作业（全为attempt1） | 桥SHA | 操作 / 实际结果 |
| --- | --- | --- |
| [40 /45927979017](https://github.com/Zhangsfish/lecture-asset/actions/runs/45927979017) | `0ca6de5695728618c31e80996241e63f7a52c67c` | 首轮upload：0.1.0（40.1），北京时间10:22:51创建；准备/归档/6+2 PASS，Apple export/upload Invalid Signature，exit70；没有接受事件 |
| [41 /45929985789](https://github.com/Zhangsfish/lecture-asset/actions/runs/45929985789) | `6ee2a4890ae08134ed03d1540b1df30043d19c40` | inspect-export：Apple GET明确40.1不存在；临时41.1导出成功、未上传。签名检查器参数错误，作业FAIL不能作为证书故障证明 |
| [42 /45930428649](https://github.com/Zhangsfish/lecture-asset/actions/runs/45930428649) | `e49554d43931fbcb09ee174f08d5af6bd84d4b7a` | inspect-export：40.1仍不存在；临时42.1未上传。证书链、profile和本地strict签名实际通过；同一参数错误导致作业FAIL |
| [43 /45930880791](https://github.com/Zhangsfish/lecture-asset/actions/runs/45930880791) | `30cf62a5e543d171295d4d574157f3a450044b96` | inspect-export：修正参数后App/ONNX框架strict与Apple anchor均PASS；Apple altool上传前验证实际FAIL，定位ONNXRUNTIME_FRAMEWORK；临时43.1未上传 |
| [44 /45931499589](https://github.com/Zhangsfish/lecture-asset/actions/runs/45931499589) | `962da31da47434b3005fdf2a887dbc46f428238d` | inspect-export：框架为MH_DYLIB，App/框架flags均0x0、team均匹配；Apple实际90035拒绝框架签名（另提取到90725，旧提取器未分离警告/错误）；44.1未上传 |
| [45 /45932244457](https://github.com/Zhangsfish/lecture-asset/actions/runs/45932244457) | `15f56d67dcd74ad7e5f122da1c97effb8ca3d589` | inspect-export：Release符号表未证明静态接口，移除保护主动拦截；没有删除框架，没有导出或上传45.1 |
| [46 /45932641642](https://github.com/Zhangsfish/lecture-asset/actions/runs/45932641642) | `a866cd83c342e3652555080de949ca47ac1349e0` | inspect-export：活跃静态链接映射证明通过，主程序哈希不变；归档6+2、签名/证书/profile及Apple altool预检全部PASS；46.1只在runner临时导出，未上传 |
| [47 /45933165856](https://github.com/Zhangsfish/lecture-asset/actions/runs/45933165856) | `a866cd83c342e3652555080de949ca47ac1349e0` | 正式upload：0.1.0（47.1），真实归档/有界修正/6+2 PASS；北京时间11:19:46上传接受、11:21:56 VALID/INTERNAL_ONLY/未过期/既有组/IN_BETA_TESTING，作业SUCCESS，可安装YES |

各次调整前的真实archive App均93,053,210字节；unsigned执行文件SHA一致：
`f35c58465cc729b41aec172c0a536a7eb7e7be23dd4a84292114cdd6b07ca934`。
6+2核验PASS，模型SHA为`5dbe3500e7d36835e073dad4f3502a579ae497f62c0a6574c736345237e1e7aa`。
没有把41–46的诊断候选当作Apple构建或手机安装。

41/42的`codesign -R`缺少文字要求的`=`前缀，实际被当作文件名；这是桥检查器错误。
43已依[Apple TN3127](https://developer.apple.com/documentation/technotes/tn3127-inside-code-signing-requirements/)
修为`-R '=anchor apple generic'`并真实验证通过。此前“Apple anchor失败”的诊断已撤回，不能据此轮换证书或降低信任检查。

43实证：App及框架均3级Authority、Distribution而非ad-hoc、strict/anchor退出0；
`security verify-cert -p codeSign`退出0，实际leaf存在于profile，team/app identifier对应、get-task-allow=false。
这些本地检查不替代Apple服务器验证；后者仍拒绝框架。只在明确build不存在/被拒绝时做临时导出，
处理中只轮询同一个build，没有为等待处理而重复上传。

## 有证据约束的归档修正

只在桥的临时archive处理`Frameworks/onnxruntime.framework`：先检查路径在RUNNER_TEMP、
产品身份、框架身份、无符号链接、文件只包含Info.plist/框架执行文件/签名封套。
如有未核实资源（包括隐私声明）即拒绝移除。再检查App及其根部dylib均没有任何onnxruntime动态依赖，
并从链接映射的活跃符号/静态archive对象核验`_OrtGetApiBase`实际链接；符号表不够时不能假定通过。
额外生成的私有链接映射不进入App或GitHub，主程序SHA仍须与40–45实际记录完全一致。

46实测移除33,798字节的未使用框架；其执行文件SHA为
`f7f5fd3eb654095732250aa21bc27bd266212dd36d93a4ecc400334a90dbd080`。
App由93,053,210变为93,019,412字节，主程序仍是同一f35c5846…ca934，
运行库已链接的机器码、6模型文件、manifest和2份声明均保留。操作后再次执行统一资源校验。
导出的46.1实际为0个嵌入框架，strict/Apple anchor/Distribution/profile全部PASS，
`altool --validate-app`真实退出0；这是修正有效的证据，不代表已上传或手机已安装。
不声称证书有问题，不轮换证书，不替换运行库，不修改批准的reader源码。

47重新对真实archive完成相同证明/资源校验；同样只移除33,798字节，主程序仍同一f35c5846…ca934。
47中移除框架执行文件SHA为`66c905c734a4b3fa3b0402b5e2d8bd43d77bbd432b59ade45d4e41e9758cd514`；
未把46候选的框架/IPA哈希冒充47。Xcode上传路径没有保留47的本地IPA，因此不填虚构的47 IPA SHA。
精确事件/UTC时间见[evidence](evidence/owner-phone-trial.json)。

## 最终验证与状态

- 本机实际PASS：PyYAML6.0.2解析、两段内嵌Python语法、桥Python编译、Git Bash `-n`、固定源码/Secrets引用与组操作范围比对、`git diff --check`。
- 真实macOS47：准备资源/运行库、工程`--check`、Swift类型检查，Release arm64 archive与6+2校验均PASS；活跃静态链接证明、主程序不变和修正后6+2均PASS；Apple接受/处理/安装状态PASS。
- 55/55各两套完整App测试属于已批准reader6469489的先前真实回归，本轮没有重跑，也没有把桥检查计为新一轮55/55。
- iPhone升级、声音/首声/长听、锁屏/后台、发热/电量与用户认可均NOT_RUN，等待反馈；未用模拟器或本地签名验证替代。
- 不合并PR12/桥PR26，不开展新功能、训练、模型替换、公开分发或泛优化。可安装已交付，停止WAITING_OWNER_FEEDBACK。

## 手机更新与反馈

2026-11-27 owner后续反馈：“语音很好”。这是本次手机语音的定性认可；没有提供设备信息或
升级/首声/p95/长听/热/电量量化结果，不补写这些项目PASS。
owner另明确要求界面文案清理与点按翻页；该有界后续记录在[任务](../../tasks/S02B_OWNER_POLISH.md)，
不改写本报告47.1所打包的源码或实际构建/上传事件。

在已有TestFlight条目更新至**0.1.0（47.1）**，保留原App和书库，不先卸载。
打开原书确认正文/目录/位置；“⋯→字号（阅读设置）→本机朗读→语音”选“苏心”。
原速2–3分钟、1.5×约5分钟，试暂停/继续、跳转、锁屏/后台与发热；
可顺手检查上下/左右及独立书架/书内主题。无需先做完整性能验收才取得包。
真实首声/p95、长听、升级、发热/电量、用户认可均NOT_RUN，不能由模拟器数据替代。

API依据：[buildBetaDetails](https://developer.apple.com/documentation/appstoreconnectapi/get-v1-buildbetadetails)、
[InternalBetaState](https://developer.apple.com/documentation/appstoreconnectapi/internalbetastate)；
签名语义：[Apple TN3161](https://developer.apple.com/documentation/technotes/tn3161-inside-code-signing-certificates/)。
原始日志只在本地忽略目录；IPA/profile/证书/密钥在临时runner处理，不公开上传。
只保留小型脱敏状态；不把内部试用批准扩写为公开分发许可/BOM完成或手机已通过。
