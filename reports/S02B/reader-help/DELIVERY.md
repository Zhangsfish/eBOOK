# 底部阅读控制、教程与反馈

当前 **WAITING_OWNER_FEEDBACK**。两套最终回归各14/14及Release归档已通过；[实际49.1流程](https://github.com/Zhangsfish/lecture-asset/actions/runs/46017595137)已交付 **0.1.0（49.1）**。Apple于北京时间2026-11-27 22:43:46确认既有内部组可安装。[手机交付](PHONE_DELIVERY.md)。Owner明确要求本轮直接内部提测，不再提交网页端审查。不合并PR、不公开发布。

起点 `566a7fa94296633c4078f9b06b7d261a26cc32a7`；实际测试与签名打包固定版本 `1619c200ed7552be5687c4446240daefe676fb4c`。它包含44点透明thumb及PrivacyInfo声明、明确的面板zIndex，以及仅用于专项UI测试的原生滑块几何/触摸计数。Release和普通Debug均使用标准UISlider。文档提交208fd7c与它的八项构建输入相同。初轮a82be00、89c643d、84e49d4及其测试记录保留如下。

## 修改

右下角三个点保留。展开后最下方只有一排返回、喇叭、目录、字号图标，去掉原来的书名标题、大卡片、文字标签与独立关闭行。下方保留进度和收起入口。图标按钮仍有至少44点触控区域；进度圆点可见部分12点，提供44点外层布局和透明thumb，保留系统滑块的触控行为。仅在主题/对比度改变时替换thumb图片，避免拖动过程中重复替换。保留原生UISlider及辅助功能。

颜色跟随书内的明亮、护眼、夜间主题，按钮弱化显示；增强对比度时使用完整前景色。展开/收起不改变正文视口和当前源位置。原有上下滚动、左右点按/滑动、实时目录及字号/行距仍保留。

书架设置新增“新手教程”和“意见反馈”。教程参照Lecture Asset的本地示意动画，依次介绍导入、翻页、底部控制和朗读；首次显示一次，可立即跳过，也可从菜单重看。每页最多播放3秒，离开取消；减少动态效果时显示静态示意。演示不会导入书籍、改设置或播放真实声音。DEBUG测试使用独立启动参数强制演示/静态分支，常规UI测试不自动弹出。

联系沿用Lecture Asset已批准的公开邮箱 `zhangs.taq@gmail.com` 与个人主页。可以点击打开邮件或复制邮箱；只在主动点击后打开系统邮件/网页。自动测试不会发送邮件或访问主页。

苏心模型、中文前处理、音频队列/缓存、语速实现、书籍存储和阅读锚点算法没有改动。没有新增依赖。

首次教程的已看标记使用App自身的UserDefaults。根据[Apple官方用途声明](https://developer.apple.com/documentation/bundleresources/app-privacy-configuration/nsprivacyaccessedapitypes/nsprivacyaccessedapitypereasons?language=objc)，在PrivacyInfo.xcprivacy补充CA92.1；本机解析核对只增加该类别及原因，原有无跟踪/无收集声明不变。最终两套CI均包含这份元数据。

## 真实验证

本机Windows：工程生成一致性、`git diff --check` 和5项打包资源门禁测试通过。本机没有Xcode或已连接iPhone，不能据此宣称原生编译或设备体验通过。

本轮14个方法：5项分页/迁移原生测试、原有4项阅读模式UI、1项苏心语音/语速UI，以及新增的底部布局/拖动/三主题、教程跳过/重看/前后切换、减少动态效果、反馈复制返回，共4项UI。

| 实际运行 | 状态 |
| --- | --- |
| [iOS26.5 / 45999026469，attempt1](https://github.com/Zhangsfish/eBOOK/actions/runs/45999026469/attempts/1) | 13PASS/1FAIL/0SKIP；首次左滑后位置变化等待超时；新增4项UI及其他方法通过。失败后未执行Release归档。 |
| [iOS26.5 / 45999026469，attempt2](https://github.com/Zhangsfish/eBOOK/actions/runs/45999026469/attempts/2) | 13PASS/1FAIL/0SKIP；原有滑动/目录/恢复测试通过；新增布局测试最后一次进度拖动未推进正文。无Release归档。该轮有完整14方法最终结果，不是超时或PASS。 |
| [iOS18.5 / 45999033059](https://github.com/Zhangsfish/eBOOK/actions/runs/45999033059) | 14PASS/0FAIL/0SKIP；Xcode16.4（16F6），iPhone16Pro，unsigned arm64 Release及6+2资源通过。 |
| [89c643d / iOS26.5 / 46005478169](https://github.com/Zhangsfish/eBOOK/actions/runs/46005478169) | 12PASS/2FAIL/0SKIP；默认文本元素左滑未推进；归一化滑块调整前后均为0%，未推进正文。无Release归档。 |
| [89c643d / iOS18.5 / 46005486587](https://github.com/Zhangsfish/eBOOK/actions/runs/46005486587) | 14PASS/0FAIL/0SKIP；unsigned arm64 Release及6+2资源通过。 |
| [84e49d4 / iOS26.5 / 46009570704](https://github.com/Zhangsfish/eBOOK/actions/runs/46009570704) | 12PASS/2FAIL/0SKIP；明确横向拖动已通过；进度仍0%未推进；教程第二次Next后即时断言读到前页标题。无Release归档。 |
| [84e49d4 / iOS18.5 / 46009580484](https://github.com/Zhangsfish/eBOOK/actions/runs/46009580484) | 14PASS/0FAIL/0SKIP；Xcode16.4（16F6），iPhone16Pro；unsigned arm64 Release93,186,443字节，6+2资源通过。 |
| [最终1619c20 / iOS26.5 / 46014013164](https://github.com/Zhangsfish/eBOOK/actions/runs/46014013164) | **14PASS/0FAIL/0SKIP**；Xcode26.6（17F113），iPhone17Pro；unsigned arm64 Release93,182,738字节，6+2资源通过，原设备归档入口实际执行。 |
| [最终1619c20 / iOS18.5 / 46014021341](https://github.com/Zhangsfish/eBOOK/actions/runs/46014021341) | **14PASS/0FAIL/0SKIP**；Xcode16.4（16F6），iPhone16Pro；unsigned arm64 Release93,186,531字节，6+2资源通过。 |

初轮26.5失败发生在原有 `testHorizontalPagesReturnRestoreTOCAndSwitchToVertical` 的第一次左滑，没有观察到新页面位置。此时底部面板尚未展开。分页器/手势代码与48.1完全相同；不据此擅自宣称基础设施或产品根因。保留原记录，仅进行一次同源码完整reading范围复核，没有降低断言、跳过失败或修改App。18.5实际截图已核读三主题底部控制、教程与反馈；截图只含原创夹具。

同源码复核中首次滑动通过，失败转到新增小滑块的拖动。89c643d保留12点可见圆点，增大透明触控thumb并避免每次拖动更新时更换图片，随后对两套系统重新执行完整14方法范围。断言没有放宽，增加了失败时前后位置与滑块数值诊断。两项初轮根因不被推断成已证明的网络/Apple问题。

89c643d的26.5仍出现两次未推进。84e49d4仅把测试输入改为明确的实际手势：横向页面从90%拖到10%（反向相反），进度条从44点透明thumb中心拖到轨道90%处。保留全部位置变化和相邻页一致性断言，不替换成程序设值或Mock，不修改分页器或正式App来迎合测试。默认UI自动化操作失效的唯一根因仍未确定，最终结果需实际观察。

84e49d4的实际横向拖动通过，进度仍未推进。1619c20明确底部面板zIndex为1；专项测试使用真实UISlider子类只读取原生thumbRect转换到窗口的位置、记录super追踪事件和valueChanged次数，测试从该真实位置拖动。不改进度值、不替换触摸结果，Release和普通Debug没有这个子类。教程保留相同标题断言，改为有界等待新标题，而不是点击后立即读可能尚未刷新的快照。

最终两套原生事件记录均为begins=1、accepted=true，18.5有14次continue/16次valueChanged，26.5有13次continue/22次valueChanged；均由真实拖动推进到block3/offset0。26.5实际原生视图高34点，外层布局44点；18.5原生高44点。没有把外层尺寸误写成两套原生控件高度相同。最终实际事件及摘要见[evidence.json](evidence.json)。没有据此宣称某个单一历史失败根因已被唯一证明。

本轮是UI范围回归，不冒充完整55项或新模型音频/真机长听测试。签名上传和Apple可安装状态已实际核验；手机安装/手感、首次教程实际体验及VoiceOver人工检查等待owner反馈。

## 交付

现有eBOOK专用桥ba2c4417f3302f0f8a16c8d7003a167149993dec只更新两个精确源码引用，签名/静态链接/同build双归档摘要/资源校验/既有组及Internal Only约束保留。[实际49.1流程](https://github.com/Zhangsfish/lecture-asset/actions/runs/46017595137)完成；Apple已读回VALID/INTERNAL_ONLY、既有组关联及IN_BETA_TESTING。没有重复上传，48.1和更早包保留。真实归档摘要和可安装事件见[交付证据](phone-delivery-evidence.json)。现在停止开发与上传，等待手机反馈。
