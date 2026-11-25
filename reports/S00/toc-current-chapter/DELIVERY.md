# 目录跟随当前阅读章节

状态：READY_FOR_AUDIT — 两套 iOS 专项通过；手机内部版已可更新。
日期：2026-11-25（Asia/Shanghai）。PR #5，未合并。

用户反馈：目录从头打开，长书需要向下翻找正在阅读的章节。
现在每次打开目录都会重新按屏幕上的阅读位置定位并勾选当前章，清空旧搜索词；
浏览或关闭目录不移动正文，只有点选章节才跳转。搜索入口保持可见。
阅读、书籍和听书进度的保存格式不变，无需卸载或重新导入。

## 精确版本与修改范围

- 开始基线：`4f9175ed6326b95902aceaccf47258771281eac1`。
- 最终实现及签名 checkout：`7509547a0b62598097ff5f24ca6eb9611455109c`。
- 最终文档交付 HEAD 另列 PR；实现后不再修改 Sources/Tests/脚本/工作流/工程。
- `BookDocument.tocEntry(atBlock:)` 根据最近的前置目录目标定位正文中段，
  支持 EPUB 目录顺序与正文不同、同目标的嵌套项、无目录/前言/越界位置。
- `ReaderView` 使用稳定目录 ID 自动滚动、选中标记和 VoiceOver selected/value；
  新打开时清空搜索，搜索栏始终可见。正文渲染器、解码器、存储字段、语音引擎未改。
- S01 PR #4、S02A PR #7 和各自工作区保持原 SHA；未开始 S02B。
  原始长书/字号/重启测试保留在 full-suite 模式，专项测试独立验证新行为。

## 真实 Xcode 验证

最终专项严格运行2个命名方法，断言总数2、无跳过：

1. Core：章节正文/边界、嵌套与乱序 EPUB、无目录和前言。
2. UI：真实导入230万字符原创 TXT，目录跳到500章，实际手动阅读跨过章节边界；
   目录必须定位到最新阅读章，而非最后点选章。再跳到624章，重开目录检查旧搜索清空、
   当前条目自动可见且选中；终止/重启后仍正确；每次开关目录正文 anchor 不变。

| 实际运行 | 源码 | 真实结果 |
| --- | --- | --- |
| [最终 Xcode26 / iOS26.5](https://github.com/Zhangsfish/eBOOK/actions/runs/45548099346) | 7509547 | **2/2 PASS，0失败/0跳过**；iPhone17 Pro ARM64模拟器；iPhone Release archive、Debug测试构建、Release模拟器构建通过 |
| [最终 Xcode16.4 / iOS18.5](https://github.com/Zhangsfish/eBOOK/actions/runs/45548105689) | 7509547 | attempt1：1/2，通过Core；UI在打开书籍前获取AX快照超时。**[attempt2](https://github.com/Zhangsfish/eBOOK/actions/runs/45548105689/attempts/2)：同源2/2 PASS，0失败/0跳过**；Intel iPhone16 Pro模拟器；Debug/Release构建通过 |
| [首轮完整26.5](https://github.com/Zhangsfish/eBOOK/actions/runs/45542499967) | ebd9232 | 25/27 PASS，2失败，0跳过：已知Files导入UI失败；新测试未处理显示数字千分位逗号 |
| [首轮完整18.5](https://github.com/Zhangsfish/eBOOK/actions/runs/45542537329) | ebd9232 | 26/27 PASS，1失败，0跳过：同一千分位脚本错误；其他用例通过 |
| [修正脚本后26.5专项](https://github.com/Zhangsfish/eBOOK/actions/runs/45545433809) | 34d5289 | 2/2 PASS，0跳过，实际624章/字号/重启及渲染检查通过 |
| [修正脚本后18.5专项](https://github.com/Zhangsfish/eBOOK/actions/runs/45545438020) | 34d5289 | 1/2 PASS，0跳过：深处目录滚动会折叠系统搜索栏，后续在7509547改为始终显示 |

千分位解析修正沿用原有断言的数字过滤，未放宽章节/进度检查。
18.5 的自动折叠问题通过真实运行及 Apple
[搜索栏 displayMode 文档](https://developer.apple.com/documentation/swiftui/searchfieldplacement/navigationbardrawer(displaymode:))
定位；保留搜索可见性检查，没有删掉断言换取通过。
7509547 的首次 AX 快照超时发生在书架查询阶段，原因未唯一定位；
不修改代码/断言的第二次运行通过全部专项检查，首次失败仍保留，不称已证明根因。

最终26.5渲染观测：2个进程会话、最多2个可见正文cell、12个窗口块、
单正文组件最多1599 UTF16、最远block1869；进程累计峰值RSS414,154,752 bytes。
最终18.5的104次采样同样为2会话、最多2可见cell/12窗口块/1599 UTF16、
最远block1869；峰值RSS280,694,784 bytes。以上都是模拟器数据，不是真机内存/长期稳定性验证。
三个[原始模拟器截图](evidence/)展示手动读过章节后、624章、重启恢复的目录；
均已视觉核读，为未修改的原创测试书截图，来源和SHA见 PROVENANCE.json。

所有已下载 CI ZIP 均按 GitHub digest、CRC 和安全路径核对；
实际计数/环境/失败历史保留在 TEST_RESULTS.json。未把失败或未运行改写成通过。
本机 Windows 无 Xcode；本地工程生成一致性、Git Bash脚本语法、差异检查通过，
原生结果全部来自标准免费公开 GitHub macOS runner。

## 手机内部更新：0.1.0（39.1）

- [上传45550231458](https://github.com/Zhangsfish/lecture-asset/actions/runs/45550231458)。
- 隔离安装桥分支 `codex/ebook-device-installation`，
  helper SHA `0be62cf0a51a5dfc0f8a271b95c2ae9e31c22ded`，固定 reader7509547。
- 真实 archive / Swift helper检查通过。Apple接受上传：2026-11-25 05:00:45 UTC；
  05:02:25 UTC 读回 **VALID**，并验证现有 Owner 内部手动测试组的 build relationship。
  helper在关联前实际检查 `INTERNAL_ONLY` audience、internal/manual group及禁用public link。
- 这证明新版在既有内部测试组可用；用户是否已更新、手机上的实际目录效果仍待答复。
- 复用已有加密Actions凭据，没有读取/复制密钥到 eBOOK 或聊天、没有新增测试员/组，
  没有App Review、公开发布或Lecture Asset App重传/运行时代码变更。
- Xcode直接上传未保留最终签名IPA，未声称具有签名IPA的独立hash/CDHash/profile核验。

当前手机检查：在原TestFlight App直接更新39.1，读到后面的章节再打开目录，
关闭重开一次。不要卸载。真正的 owner-phone 结果单独记录，不用模拟器结果代替。

## 审查边界

原有 iOS26.5 Files 原生导入UI失败仍未解决，PR #5保持draft，交给独立审查；
本次未修改或弱化它。专项2/2不能冒称一次完整28项全绿回归。
不自行合并，不启动S02B，不引入AI模型或云端TTS。

全部验证只用原创测试文本。没有读取、提交、上传私人小说正文、音频、密钥或模型。
真实书籍和阅读位置仍在用户设备本地。源码、真实验证及内部更新证据交付完成，
停止在 READY_FOR_AUDIT，等待独立审查及用户手机反馈。
