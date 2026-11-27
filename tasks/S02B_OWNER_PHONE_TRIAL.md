# 历史任务：47.1 手机试用交付

后续的文案与点按翻页更新已经交付为 [0.1.0（48.1）](../reports/S02B/owner-polish/PHONE_DELIVERY.md)。最新任务见 [S02B_OWNER_POLISH_PHONE_DELIVERY.md](S02B_OWNER_POLISH_PHONE_DELIVERY.md)。

状态：**WAITING_OWNER_FEEDBACK — 0.1.0（47.1）已可安装，停止开发与上传。**
实际[交付记录](../reports/S02B/OWNER_PHONE_TRIAL.md)：Apple于2026-11-27 11:21:56（北京时间）
读回VALID/INTERNAL_ONLY、既有组及IN_BETA_TESTING。等待owner手机反馈，不重复执行下列已完成步骤。
日期：2026-11-27。依据：[复审及收口决定](../reports/S02B/REVIEW_AND_OWNER_TRIAL_20261127.md)。

## 交付身份

- eBOOK分支/PR：`codex/s02b-suxin-ios-integration` / #12。
- **必须打包的reader源码：`6469489062e6b91d743295cc2c08320334dbbf17`。**
  两套真实CI各55/55；交付ca640cd与它的8项构建输入一致。
- 保留当前苏心、阅读/目录、上下/左右方式与独立主题实现。不要改App、换模型或追加功能。
- 复用已授权的eBOOK专用签名桥：
  `Zhangsfish/lecture-asset` / `codex/ebook-device-installation`，
  起点`0be62cf0a51a5dfc0f8a271b95c2ae9e31c22ded`。
  只改eBOOK桥的必要接线，不改Lecture Asset产品、main或其余项目。

## 立即执行的有限交付工作

1. reader checkout ref和EBOOK_TESTED_SHA两处同时固定到上面的完整SHA，
   保留准确源码一致性门禁，不使用任意branch/latest。
2. 在不带Apple凭据的准备步骤、工程检查之前执行：
   `python3 tools/suxin/scripts/prepare_resources.py`、
   `python3 tools/suxin/scripts/inspect_runtime.py`，
   再 `python3 scripts/generate_xcode_project.py --check`。
3. 在eBOOK archive之后、export/upload之前调用reader的
   `scripts/verify_release_bundle.py:validate_resources`，
   验证真实archive内六项模型文件、模型manifest、两份固定运行库声明及完整集合/摘要。
   保留原bundle/version/源码检查。只验证IPA元数据或仅先前unsigned包不够。
4. 对有限桥接差异做语法/实际prepare检查，核对未改变Secrets作用域、现有内部组、
   日志脱敏和Internal Only。该有限接线及已批准reader的内部上传已获授权，
   无需再次请owner同意同一安装，也不要求合并main或第三轮App审查。
   若需要超出这些范围，给出具体差异和原因，不能顺手扩展产品。
5. 使用已有本地gh/签名执行端触发现有工作流的owner内部upload，分配实际唯一递增build。
   不索取明文密钥，不另建账号/收费服务/外部测试组；模型/IPA/原始签名日志不公开上传。
   保留原39.1内部build供回退，升级保留书库和偏好，不让用户先删除App。
6. 从实际Apple状态读回上传接受、处理VALID/INTERNAL_ONLY和既有Owner iPhone组关联。
   仅可安装后写TESTFLIGHT_AVAILABLE=YES；处理中继续查询同一build，
   不因处理慢重复上传或制造多版本。
7. 直接交付给用户：准确build号、TestFlight更新方式、下方短说明。
   写入 `reports/S02B/OWNER_PHONE_TRIAL.md` 的真实状态，然后
   **停在WAITING_OWNER_FEEDBACK**。不再加功能或无依据继续优化。

既有Apple登录/验证若确需owner操作，只提具体被阻断的一步；先完成所有独立交付工作。
GitHub连接器没有workflow-dispatch能力；可使用现有已登录gh或GitHub Actions页面
触发该工作流。不能把文档更新冒充已启动上传；必须记录实际run和build状态。
如果执行端也缺访问，说明准确缺项；不要以笼统“等审查”结束。

## 用户只做一次约10分钟试用

先从TestFlight更新，打开原有书籍，确认正文/目录/位置正常；
在“⋯→字号（阅读设置）→本机朗读→语音”选“苏心”。

- 原速听2–3分钟，再1.5×听约5分钟，判断声音、读音、卡顿或重复/漏读。
- 试首次播放、暂停继续、跳到未听过位置，判断等待及旧声音是否及时停止。
- 期间锁屏、切后台再回来；确认继续播放、能控制、发热是否明显。
- 可顺手切一次上下/左右阅读，检查原位置附近及书架/书内主题分别生效。

用户反馈足以先决定是否有实际使用障碍，不要求用户做20次计时或诊断。
详细指标由开发侧记录；不能把粗略听感写成p95或各30分钟已通过。

## 收口

本任务只结束于“用户能安装新build”或精确交付阻塞，准备文档/IPA不是终点。
可安装即停止开发等待反馈。用户认可、没有核心故障时结束本轮MVP功能开发，
冻结可用版本；只针对实际反馈修复，不额外增加功能或强行继续版本迭代。
训练PR #11继续独立，不影响本次交付。没有公共发布或自动合并授权。
