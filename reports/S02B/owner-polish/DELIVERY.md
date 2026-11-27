# 界面文案与点按翻页

状态：IN_PROGRESS。起点452d1671e9f4500cd2edece8553c212da9cf5244，任务tasks/S02B_OWNER_POLISH.md。
47.1是现有可安装版；本轮新源码没有签名/上传，不复用6469489的旧批准。

## 修改

删除书架的本地保存/导入版权提醒、阅读设置的手机合成/正文不上传说明、TXT目录推测免责声明。
空书架、无目录和准备状态缩短；苏心显示为“苏心”，语音不再附工程语言代码。
自动使用系统语音时只显示“本段使用系统语音”；失败信息及移除书籍后清除进度的必要后果简短保留。
清理文字，不改实际文件保护、版权/隐私工程约束、模型/前端/音频队列/缓存/语速或自动回退逻辑。

横向页面左/右三分之一单击分别上一页/下一页，中间不翻页，沿用现有分页器和位置回调。
单击等待双击失败，选择文字时让出手势；VoiceOver关闭本次普通点按处理，原自定义翻页动作保留。
滑动转场期间不接受程序翻页。没有透明覆盖按钮；安静入口、浮层、上下滚动、目录/重启恢复保留。
参照[Apple UITapGestureRecognizer](https://developer.apple.com/documentation/uikit/uitapgesturerecognizer)、
[手势失败依赖](https://developer.apple.com/documentation/uikit/uigesturerecognizer/require(tofail:))。

## 验证

- 本机现有Python3.11.11：工程`--check`、CI包装Python语法、`git diff --check`已通过；没有Xcode，不声称本机iOS运行。
- 新增真实UI路径：左/右点与滑动相邻页一致、首尾边界、中间/双击/控制面板不跳页、点按位置重启恢复及实时目录。
- 同一reading范围纳入既有语音/独立速度保存UI测试，保护更名后的苏心选择和设置功能；5项原生有界分页/迁移测试保留。
- 真实iOS18.5/26.5结果、精确测试SHA、CI链接及unsigned arm64包证据：待执行。
- 这版的iPhone点按/实际VoiceOver手势、签名/TestFlight：NOT_RUN。用户已有“语音很好”反馈仅属于上次47.1体验。

最终提交PR12，READY_FOR_AUDIT；不自行合并或上传，不增加第三项功能。
