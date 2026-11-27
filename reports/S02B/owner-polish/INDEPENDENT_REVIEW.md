# 文案与点按翻页：独立审查

2026-11-27（Asia/Shanghai）。结论 **APPROVED_FOR_OWNER_BETA**。
本轮App改动未发现阻止owner手机试用的缺陷。冻结App，下一步只交付内部TestFlight更新，随后等待实际使用反馈。

## 身份和证据

- 基线452d1671e9f4500cd2edece8553c212da9cf5244，其八项构建输入与47.1已批准源码6469489一致。
- 实测源码 **`03fe0237462f0af0595d47c455c7e5756d6cbd97`**。
- 审查交付2d3be5e57116c388ff77ea0b4e7b12514bb49157；独立Git对比确认Sources、Tests、scripts、tools/suxin、workflows、Xcode工程、gitattributes、gitignore八项与实测源码一致。
- 实际获取两套CI的job日志和附件，核对原始XCTest方法、xcresult导出摘要、归档与资源元数据，并校验ZIP SHA256和CRC。没有为本次审查重跑完整CI。

| 实际CI | XCTest | 实际归档 |
| --- | --- | --- |
| [18.5 /45941580059](https://github.com/Zhangsfish/eBOOK/actions/runs/45941580059)，job140316875714 | 5分页单测、5UI，10PASS/0FAIL/0SKIP | unsigned Release arm64，6模型资源+2运行库声明通过 |
| [26.5 /45941580359](https://github.com/Zhangsfish/eBOOK/actions/runs/45941580359)，job140317087900 | 同上，10PASS/0FAIL/0SKIP | 原设备入口实际执行，unsigned Release arm64，6+2通过 |

附件15172923435：2,260,533字节，SHA256 `8bbfb7cdb51b84b4efb1cb989ab735ce7395b9e7a4f056495934bf127787dbbe`。
附件15173820177：2,335,662字节，SHA256 `fcb089970b74b1d1875e5a71d580efdf9ecea55dadf115fe3444462ecf2de7ab`。
独立查看18.5/26.5设置图及26.5点按后正文图，图像摘要与交付元数据一致。

## 代码审查

1. 文案清理保留导入、路径、解码、存储失败和语音回退的原判断。逐条重放scope.json九组字符串替换，确认这些文件的其余字节一致；模型、前端、NativeTTS、资源和偏好结构保持一致。
2. 点按共用原分页器和位置回报，只响应左右三分之一。单击等待双击失败，保留原选择识别器；选区存在时让出手势，VoiceOver运行时禁用新增普通点按；滑动过渡期间阻止并发点按。原无障碍翻页动作保留。
3. 实际测试覆盖点按/滑动相邻页一致、首尾边界、中心/双击、控制入口、重启恢复、目录和主题。初轮EOF失败及中间取消仍保留；最终按真实源结束位置判断书尾，未删除边界断言。
4. 独立运行工程生成`--check`、差异空白检查、两份Python语法及改动范围核验，均通过。

10项是本轮相关范围；55项完整测试和音频图执行属于上一版历史依据。本版iPhone选字、VoiceOver及连点手感仍待更新后体验，不宣称真机已通过；这不要求继续推迟给owner可安装包。

## 交付与停止

当前可安装版本仍为 **0.1.0（47.1）**、源码6469489。独立核对[正式run45933165856](https://github.com/Zhangsfish/lecture-asset/actions/runs/45933165856)的原始安全标记：上传接受、VALID、INTERNAL_ONLY、既有组和TESTFLIGHT_AVAILABLE均针对47.1，它不含本轮改动。

桥HEAD af7f4d0cfdc6464064ea1e123da1cc93457bf86f仍固定6469489，`ebook_prepare_archive.py`还断言旧执行文件摘要f35c5846…ca934。直接重跑会打旧版，仅改pin也不足以交付新版。唯一READY任务为[S02B_OWNER_POLISH_PHONE_DELIVERY.md](../../../tasks/S02B_OWNER_POLISH_PHONE_DELIVERY.md)：同步新源码和真实归档身份，保留静态链接、主程序不变与6+2检查，沿既有内部上传路径读回实际可安装状态。

**停止App迭代。** 新build可安装后给准确版本和3–5分钟试用说明，停 **WAITING_OWNER_FEEDBACK**。满意且无核心故障就结束本轮MVP实现，只针对实际反馈重开修复。不合并、不公开发布，训练线独立。
