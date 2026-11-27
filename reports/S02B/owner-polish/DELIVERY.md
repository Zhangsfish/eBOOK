# 界面文案与点按翻页

当前 **APPROVED_FOR_OWNER_BETA**；[独立审查](INDEPENDENT_REVIEW.md)通过。仅执行[手机交付任务](../../../tasks/S02B_OWNER_POLISH_PHONE_DELIVERY.md)，随后等待反馈。以下保留实现交付事实。

实现交付时状态 **READY_FOR_AUDIT**。当前 TestFlight 为 **0.1.0（47.1）**。
本轮实际测试源码 `03fe0237462f0af0595d47c455c7e5756d6cbd97`，起点 `452d1671e9f4500cd2edece8553c212da9cf5244`。
交付提交只更新文档与证据，八项构建输入与实际测试源码一致。[任务](../../../tasks/S02B_OWNER_POLISH.md) · [PR #12](https://github.com/Zhangsfish/eBOOK/pull/12)

## 修改

删除书架的本地保存/导入版权提醒、阅读设置的手机合成/正文不上传说明、TXT目录推测免责声明。
空书架、无目录和准备状态缩短；苏心显示为“苏心”，语音不再附工程语言代码。
自动使用系统语音时只显示“本段使用系统语音”；失败信息及移除书籍后清除进度的必要后果简短保留。
清理文字，不改实际文件保护、版权/隐私工程约束、模型/前端/音频队列/缓存/语速或自动回退逻辑。

横向页面左、右各三分之一分别接受上一页和下一页的单击。中间区域留给正文操作。
单击和滑动共用分页器与进度保存。单击让位于双击和文字选择，VoiceOver 使用原有的翻页动作。
右下角“⋯”和控制面板照常操作。
参照[Apple UITapGestureRecognizer](https://developer.apple.com/documentation/uikit/uitapgesturerecognizer)、
[手势失败依赖](https://developer.apple.com/documentation/uikit/uigesturerecognizer/require(tofail:))。

## 验证

| 实际环境 | XCTest | Release arm64 归档 |
| --- | --- | --- |
| Xcode 16.4（16F6），iOS 18.5 / iPhone 16 Pro | 10 通过，0 失败，0 跳过 | 93,057,256 字节，资源 6+2 校验通过，[CI](https://github.com/Zhangsfish/eBOOK/actions/runs/45941580059) |
| Xcode 26.6（17F113），iOS 26.5 / iPhone 17 Pro | 10 通过，0 失败，0 跳过 | 原设备归档入口通过，93,053,775 字节，资源 6+2 校验通过，[CI](https://github.com/Zhangsfish/eBOOK/actions/runs/45941580359) |

每套实际执行 5 项分页和迁移测试、4 项阅读模式 UI 测试，以及 1 项语音和语速设置 UI 测试。覆盖点按与滑动的相邻页一致性、首尾边界、中间和双击不翻页、控制面板、重启恢复、实时目录及独立主题。已查看两套模拟器的设置和正文截图，确认说明删去、操作控件与右下角入口可见。双击测试验证了页面位置，真实文字选择与 VoiceOver 手感仍待设备体验。

本机工程生成检查、Python 语法检查、`git diff --check` 及改动范围核对通过。两套归档的执行文件和模型摘要、实际测试方法、截图元数据均已记录。[构建和测试证据](evidence.json) · [源码范围](scope.json)

本轮范围是阅读与设置。整套 55 项回归和音频生成沿用上一版的历史记录。本版 iPhone、VoiceOver、签名和 TestFlight 状态为 `NOT_RUN`，进入独立审查。

## 保留初轮失败与中间取消

`124640205d7d67198ab72f22482f65f44e8aa3a1`：
[18.5/45939771262](https://github.com/Zhangsfish/eBOOK/actions/runs/45939771262)与
[26.5/45939771381](https://github.com/Zhangsfish/eBOOK/actions/runs/45939771381)均为
**9PASS/1FAIL/0SKIP，10个实际执行方法**。唯一失败为新EOF测试；原生5项、语音/语速UI、
点按与滑动相邻页、双击/中心/控制/重启、原阅读方式和独立主题测试均通过。
这两次没有成功后的arm64归档，不将其写成完整PASS。

18.5实证：从`block1874/offset0`右点确实到`offset263`；旧测试把最后一个源块开头当成最后一页，
属于错误前提。26.5则在设置100%滑条后未等到预设的精确源地址，实际落点没有记录，不能自行归因。
最终测试沿已验证的目录入口选第625章，逐页检查DEBUG测试元数据的真实结束地址1875/0，再验证EOF右点不前进、左/右可返回同页及当前目录。
没有删掉边界断言或把超时接受为通过；只纠正了不精确的测试定位方法。DEBUG字段不出现在发布版UI。

`f7b42093999df8b559aaa807885db5d9f2cf1e80`的中间
[45941322897](https://github.com/Zhangsfish/eBOOK/actions/runs/45941322897)与
[45941322947](https://github.com/Zhangsfish/eBOOK/actions/runs/45941322947)均实际CANCELLED，
被最终精确目录方案替代，没有完成结果，不计PASS。
另外e4deaa3只清理剩余“S00/手动选编码/无损替换”错误提示，未改解析/解码判断。
