# 手机内部测试版准备

## 当前决定：APPROVED_FOR_OWNER_BETA（2026-11-27）

独立复审已通过，批准reader源码6469489062e6b91d743295cc2c08320334dbbf17。
立即执行 [唯一交付任务](../../tasks/S02B_OWNER_PHONE_TRIAL.md)：更新旧桥双重reader pin、
无Apple凭据资源准备、archive后统一包校验，再签名上传到既有owner内部组并读回可安装状态。
当前新build仍未上传/可安装；此批准不等于TESTFLIGHT_AVAILABLE。
此次只批准同一源码的有限交付接线，不再等待一轮App功能审查或追加开发。
可安装后给用户短说明，停WAITING_OWNER_FEEDBACK；下方准备记录保留为旧桥的准确起点。

## 既有准备记录（历史事实）

状态：PREPARATION_ONLY。新版本尚未签名/上传，不是可安装包或用户手机测试结果。

只读核对了现有eBOOK专用签名桥：
E:/myself/lecture_asset-ebook-device，codex/ebook-device-installation，
HEAD 0be62cf0a51a5dfc0f8a271b95c2ae9e31c22ded；工作区干净，未改动该分支或Lecture Asset产品。
其手动s00-testflight.yml仍双重固定旧reader SHA 7509547a0b62598097ff5f24ca6eb9611455109c，
对应已记录39.1苹果语音版。不能直接再次启动来冒充新苏心版本。

## 复审后必须落实的最小变更

1. 工作流环境EBOOK_TESTED_SHA及reader checkout ref同时固定到独立复审通过的准确SHA。
   源码一致性门禁保留，不能改成任意分支或latest。
2. 在无Apple凭据的检查阶段运行prepare_resources.py和inspect_runtime.py，
   然后generate_xcode_project.py --check；当前老桥没有这两项资源准备。
3. archive后、export/upload前调用scripts/verify_release_bundle.py的统一校验函数，
   核对六项资源/两份固定声明及对应摘要，记录准确源码、资源身份和唯一递增build。
4. 保持既有Secrets使用、日志脱敏、Internal Only及现有owner组关系；模型/IPA/原始签名日志
   不作为公开artifact。无需新账号、密钥、收费服务、外部测试组或先合并main。
5. 上传接受、Apple处理VALID/INTERNAL_ONLY、现有owner组关联和可安装状态分别读回。
   只有真实可安装后才写TESTFLIGHT_AVAILABLE=YES；不能用归档或作业创建代替。

本轮在eBOOK分支准备了统一资源校验与原设备入口的实际验证；签名桥变更及上传须在
当前代码独立复审/内部试用必要资源核对后进行。现阶段没有访问凭据内容或触发Apple账户操作。
修复复审通过即沿已有授权提供手机测试包，不以完成全部真机指标为安装前置条件。

## 给用户的短试用说明（待实际build后填写）

在TestFlight直接点更新，随后核对原书库和位置保留。在书架选择翻页方式与书架外观；
书内主题仍在“⋯ → 字号（阅读设置）”单独调整，检查两处颜色互不改变。
在“字号（阅读设置）→ 本机朗读 → 语音”选苏心，先1.0×听2–3分钟，再1.5×听约5分钟，
中间试暂停/继续、未听过的位置跳转、锁屏/后台。反馈声音、等待、卡顿、锁屏和发热即可。
再从书架切换一次上下/左右阅读，确认回到同一段附近；目录每次打开都指向当前章。
实际build号/准确源码SHA/可安装状态在真正上传处理后补充，当前NOT_RUN。
