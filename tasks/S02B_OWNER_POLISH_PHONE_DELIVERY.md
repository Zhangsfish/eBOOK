# 唯一下一步：交付已过审的点按与文案更新

状态 **WAITING_OWNER_FEEDBACK**，2026-11-27。**0.1.0（48.1）** 已确认可安装。[实际交付](../reports/S02B/owner-polish/PHONE_DELIVERY.md)记录新版本、Apple 读回及更新说明。以下为已执行的任务范围。[独立审查](../reports/S02B/owner-polish/INDEPENDENT_REVIEW.md)

## 固定范围

- eBOOK分支/PR：codex/s02b-suxin-ios-integration / #12。
- **必须打包源码：`03fe0237462f0af0595d47c455c7e5756d6cbd97`**，两套实际10/10及归档通过；2d3be5e八项构建输入相同。
- 当前47.1来自旧6469489，声音认可保留；新版本签名/上传/真机均NOT_RUN。
- 只改Zhangsfish/lecture-asset的codex/ebook-device-installation现有eBOOK专用交付桥及记录。观察桥HEAD af7f4d0cfdc6464064ea1e123da1cc93457bf86f，执行前刷新并保留无关变更。
- 冻结App、模型、前端/队列、分页器及工程；不重复完整App CI，不改训练PR11、Android或Lecture Asset产品。

## 交付动作

1. reader checkout和EBOOK_TESTED_SHA两处同时固定到新完整SHA；保留无Apple凭据准备、运行库/工程/源码门禁及真实归档6+2校验。
2. **修正旧执行文件基线。** ebook_prepare_archive.py硬编码6469489的f35c5846…ca934。不能沿用或删除保护后盲目上传。以本次固定源码、相同工具链和归档参数的真实输出建立可核对的新基线；使用链接映射时，验证生成映射未改变该源码的执行文件。保留活跃静态链接证明、无动态ORT依赖、框架精确路径/内容门禁、移除前后主程序摘要一致及资源复验。CI的c65185f9…参数不同，不冒充桥产物摘要。必要的最小真实归档/导出核验属于交付范围，不重跑无关测试。
3. 对有限桥差异做语法/参数/保护核验。沿用既有Secrets、组、Internal Only和日志脱敏；保留39.1/47.1，不新建组/账号或轮换证书。
4. 用既有已登录gh或Actions页面触发一次正式内部upload，采用实际唯一递增build，不假定48.1。如需status-only/inspect-export，目标必须是本次实际build，不能继续查旧硬编码40.1。
5. 记录实际bridge/reader SHA、run/build、归档校验和上传接受。仅实际读回新build的VALID、INTERNAL_ONLY、未过期、既有Owner iPhone组关联及IN_BETA_TESTING，才写TESTFLIGHT_AVAILABLE=YES。处理中继续查同一build，不因处理慢重复上传，不以绿色workflow推断可安装。
6. 记录在reports/S02B/owner-polish/PHONE_DELIVERY.md，更新STATUS和交接；保留47.1报告及失败历史。只公开小型脱敏状态，不公开IPA、密钥、原始签名日志、模型、音频或私人书籍。

真实阻塞须给准确步骤和证据；不要退回“等待App审查”或继续开发。代码推送、unsigned归档或文档不等于手机能更新。

## 给owner试用，然后停止

新build可安装后直接报准确版本，从已有TestFlight条目更新，保留原App和书库。
请owner正常使用3–5分钟：左右点按和滑动各翻几页，开关设置/目录，退出重开确认位置，顺手继续听苏心。设备确认双击/长按选字及连点手感；诊断由开发侧承担，不要求owner跑完整验收表。

交付后立即 **WAITING_OWNER_FEEDBACK**。满意且无核心故障即冻结本轮可用版本；只针对实际反馈修复，不加功能、不自并、不公开发布。
