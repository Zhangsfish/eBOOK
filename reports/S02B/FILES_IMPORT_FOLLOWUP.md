# Files 选书修复跟进

用户2026-11-26要求先处理选书失败，再准备手机更新。继续现有PR #12，不合并。
状态：READY_FOR_AUDIT；选书在两系统完整回归中都通过。整体保留BLOCKED_QA：26.5的Apple范围回调失败，干净复核又遇到测试宿主启动崩溃；真机/新TestFlight未执行。

## 已观察的故障及修复点

- 原交付8331b9b的两系统完整回归均41/42，唯一失败为真实Files选择TXT/EPUB。
- 769e04d仅统一DEBUG书架到Application Support并补上不含书名/路径/正文的阶段日志。
  [18.5运行45754799661](https://github.com/Zhangsfish/eBOOK/actions/runs/45754799661)
  仍41/42：选择器创建，但没有selected回调，App解析并未开始；
  [26.5运行45754798939](https://github.com/Zhangsfish/eBOOK/actions/runs/45754798939)
  为42/42，记录了两次selected与books=1/2落盘。不能据此宣布两系统修好，
  也不能确定Apple内部故障原因。两轮真实unsigned arm64 Release归档均通过。
- 当前候选16fe15d：UIDocumentPicker使用asCopy=false取得授权URL，由现有
  security scope→NSFileCoordinator→BookImporter创建App私有副本，不要求选择器
  预先再复制一次。测试明确检查真实Files条目可用，继续实际选择TXT、EPUB并核对书架2本；
  没有注入书架、跳过失败或放宽原断言。

## 最终候选的验证

执行SHA：`16fe15da6bcd7431a8a162fd65ca77ce8da6ff4d`。
Sources树：`6d9339b31da7acd614971037c2e9151e493bdc48`。

| 环境 | CI | 实际结果 |
| --- | --- | --- |
| 免费标准macos-15 / iOS18.5 | [45757099825](https://github.com/Zhangsfish/eBOOK/actions/runs/45757099825) | 超时：部分日志40PASS、1FilesFAIL、1TOC未完成；无最终摘要/归档 |
| 免费标准macos-26 / Xcode26.6(17F113) / iOS26.5 | [45757095612](https://github.com/Zhangsfish/eBOOK/actions/runs/45757095612) | 42PASS/0FAIL/0SKIP；真实导入通过；Release arm64归档通过 |

两轮均尝试完整42项；26.5完成全部方法、真实原生苏心推理/播放、230万字符长篇回归
及unsigned设备归档。18.5的这次运行超时，没有最终测试摘要和归档。
各项PASS/FAIL/未完成、实际Xcode/runtime及资源核验以结果JSON或明确标记的部分日志为准。
独立dc8ad4a运行45756781805因新的完整验证覆盖其范围而取消，不计测试通过。

后续3bfc352旧系统点位修正没有解决问题：
[45761286868](https://github.com/Zhangsfish/eBOOK/actions/runs/45761286868)
完整41PASS/1FilesFAIL/0SKIP；TOC、真实苏心及其他阅读用例通过，实际arm64归档
92,986,336bytes，6项模型资源和2份运行库声明SHA通过。不能把宽标签差异写成已解决根因。

外部源最小检查：6017303运行45764765246在系统Files App启动30秒超时，
尚未编译Reader或执行XCTest。4a5b716运行45765425726为1/2（取消通过），
选择失败发生在导航到外部源之前。记录到真实LocalStorage组存在、标准存储目录缺失，
已在该组下准备原创夹具；系统Files独立启动仍超时。不是模型或正文解析失败。
fba530b修正观测到的18.5导航栏标题/返回按钮定位，
[最小回归45767237191](https://github.com/Zhangsfish/eBOOK/actions/runs/45767237191)
实际2PASS/0FAIL/0SKIP：从外部系统LocalStorage目录单击导入TXT和EPUB，日志两次
selected count=1，分别saved books=1/2；取消通过，真实unsigned arm64设备归档通过，
6项模型资源及2份运行库声明逐SHA核验。App包92,986,336bytes。
该focused范围没有执行苏心推理，不能将它计入原生模型测试。
Stock Files独立启动仍记录30秒超时，但未阻止此轮真实picker选择和导入成功。
App Sources仍为上述6d9339b，不因测试环境调整而改变。

完整检查统一执行7ff918a：
[18.5 /45769244490](https://github.com/Zhangsfish/eBOOK/actions/runs/45769244490)
实际42PASS/0FAIL/0SKIP；
[26.5 /45769249483](https://github.com/Zhangsfish/eBOOK/actions/runs/45769249483)
实际41PASS/1FAIL/0SKIP。两系统Files和全部UI通过、原生苏心12项通过，真实arm64归档
及6项模型资源/2份运行库声明通过。26.5失败是Apple语音完成后缺少range进度事件；
VoiceDB警告在此前通过日志也有，未唯一认定根因。原始失败证据保留。
只追加了一次干净环境复核：565bae0 /[45771793206](https://github.com/Zhangsfish/eBOOK/actions/runs/45771793206)。
实际6项UI均通过，包括TXT/EPUB导入和取消；但EBookTests在XCTest连接前signal abrt。
xcresult摘要为6PASS+1启动错误记录，不能写成7个方法完成或完整42项；单元/原生推理检查与
新设备归档NOT_RUN，未完成Apple回调复核。现有artifact无完整crash stack，未唯一定位根因。
App和测试未变；源码身份见source-identity-d84ceb4.json。不再重跑，保留QA阻碍交审。

## 同版本运行库声明

实际iOS和模拟器二进制均嵌入git-commit-id33ca962。已从二进制发布者的源码fork取得
同一完整提交33ca9628233dc8f002435e868d4c2e9f82766ca1的Microsoft MIT LICENSE
和完整ThirdPartyNotices，按不可变URL/大小/SHA验证。准备脚本将其放入NativeNotices，
归档脚本核对实际随包字节。原ZIP未带声明和旧404记录继续保留，不以另一版本冒充。
本地准备已通过；当前候选26.5的CI设备归档已核验两份实际声明的字节/SHA，
App包92,966,548bytes；18.5后续3bfc352归档也验证两份声明通过。

这只是材料恢复和完整性核验，不是重现编译或独立分发许可批准。
模型、中文字典、采样格式、语速和朗读调度不变；没有新增运行时依赖或本机安装。

## 后续与边界

保留阅读器、目录同步、三种主题和右下角入口。尚无新签名/内部TestFlight，
独立审查后沿用已有安装路径。新苏心版本的真机首声、跳转p95、1.0×/1.5×各30分钟、
锁屏/中断/耳机/蓝牙、内存/发热/耗电仍NOT_RUN，见DEVICE_CHECKLIST.md。
不自行合并，不把模拟器结果说成手机通过。

## 执行环境与费用边界

本机复用既有Python3.11.11/标准库及已安装Pillow，仅作数据校验和原始截图定位；
没有本机新安装。CI限定公开仓库、标准macos-15/macOS-26 runner；
[GitHub官方规则](https://docs.github.com/en/actions/concepts/billing-and-usage)
说明公开仓库标准hosted runner计算免费。只上传小型日志/JSON和有上限的原创夹具UI故障截图；
不上传模型、真实音频、私人小说或密钥，没有云端TTS或付费runner。
