# HaoStory

**做一次，讲清楚。**

HaoStory 是一个本地优先、天然双语的 Agent Skill。它把真实的软件开发、产品实验、内容实验和研究过程，沉淀为有证据的文章、视频脚本、社媒短帖与公开开发记录。

> 由 [Howie Wang](https://howie.wang/) / 浩哥 AI 实验室发起

[English](README.md)

## 为什么做 HaoStory

很多项目故事是在工作结束以后凭记忆补写的。这时真正有价值的细节往往已经丢了：失败过什么、为什么改变判断、测试怎样证明结果、前后到底有什么差异。

HaoStory 在工作发生时记录这些节点，结束后建立可编辑的中英文内容结构。CLI 本身不调用 AI 服务；使用 Skill 的 Agent 根据证据分别改写或翻译两种语言。源代码不会上传，内容也不会自动发布。

## 适合谁

HaoStory 不只面向软件开发者。只要你正在与 AI Agent 一起完成一件有价值的事，并希望留下过程中真正有用的部分，就可以使用它：

- 独立开发者与创作者；
- 教师、研究者和内容团队；
- 产品、工作流和创意实验；
- 希望把工作、学习或日常问题沉淀为可复用经验的人。

有代码时，HaoStory 可以记录 Git 证据；没有代码也可以记录判断、草稿、测试、视觉素材、反馈和前后对比。

## 记录什么

- 任务目标和最终结果；
- 经过隐私脱敏的 Git 状态与代码差异；
- 关键检查点里的判断、取舍和经验；
- 用户明确选择的命令输出和视觉证据；
- 用于判断是否值得发布的故事价值评分。

## 分阶段智能采集

HaoStory V2 按 Project → Initiative → Phase → Capture Window → Event 管理本地证据。已启用项目默认使用 `assisted-auto`：Agent 可以为有明确目标的工作开始或恢复本地文本采集、折叠重复事件，但每次开始、暂停、恢复和结束都必须告知用户。敏感工作可用 `manual`，不需要记录时用 `off`。

普通格式调整、依赖安装、简单修复、纯咨询和机械改名不会自动新建故事。高置信事件包括决策、范围变化、失败、恢复、前后对比、里程碑、Demo、指标和脱敏后的外部反馈。

已公开观点保存在本地 `.haostory/story-registry.json`。导出前会区分新观点、新证据、必要背景和重复观点；已发布观点没有新证据时默认归档。视觉素材、品牌与 CTA、故事拆合、登记已发布事实和真实发布始终需要人工确认。

省略 `--session` 时，HaoStory 只会选择唯一的 active/paused 窗口；存在多个候选时明确报错，没有活跃窗口时按 manifest 的 `updated_at` 选择最新 V1 会话。普通 session ID 和 registry 路径不能逃出项目内非符号链接的 `.haostory/`。

## 快速开始

把 `skill/haostory` 复制到你的 Agent Skill 目录，或者让 Agent 直接阅读仓库中的 `SKILL.md`。

```bash
python3 skill/haostory/scripts/haostory.py setup
# assisted-auto 路由（与下面的显式 start 二选一）
python3 skill/haostory/scripts/haostory.py suggest-start \
  --title "实现分阶段采集" \
  --initiative stage-aware-capture-v2 \
  --phase build
# 显式/manual 兼容启动
python3 skill/haostory/scripts/haostory.py start \
  --title "开发第一版主页" \
  --summary "验证一个新的产品方向" \
  --type product
python3 skill/haostory/scripts/haostory.py checkpoint \
  --stage decision \
  --notes "首页从工具导航调整为问题导航" \
  --decision "先展示用户问题，而不是 AI 品牌"
python3 skill/haostory/scripts/haostory.py remember \
  --event failure \
  --notes "同一次验证再次失败" \
  --novelty-key validation-exit-1
python3 skill/haostory/scripts/haostory.py pause --reason "这段不记录"
python3 skill/haostory/scripts/haostory.py resume
python3 skill/haostory/scripts/haostory.py close-phase \
  --result "构建阶段已可进入验证" \
  --handoff
python3 skill/haostory/scripts/haostory.py archive-only \
  --reason "用户明确要求这次不要公开"
python3 skill/haostory/scripts/haostory.py registry do-not-repeat \
  --text "前面不再重复的背景"
python3 skill/haostory/scripts/haostory.py registry check
python3 skill/haostory/scripts/haostory.py story-plan
python3 skill/haostory/scripts/haostory.py finish \
  --outcome "主页完成并通过测试" \
  --lesson "产品定位判断本身也是产品的一部分"
python3 skill/haostory/scripts/haostory.py export
```

HaoStory 不会自动公开素材。分享以前必须查看隐私报告，并人工检查每张图片。

### V1 兼容

已有 `haostory/v1` manifest，以及 `start`、`checkpoint`、`finish`、`audit`、`export` 命令继续可用。V2 只增加可选字段和本地 story registry，不需要破坏性迁移。

## 开源核心

核心工作流以 MIT License 开源；私有系统集成、定制工作流与落地合作可另行提供。最新项目和联系入口见 [howie.wang](https://howie.wang/)。

## 关于浩哥

[Howie Wang](https://howie.wang/) / 浩哥持续探索 AI 怎样帮助人们更好地工作、学习、创造与生活。HaoStory 是这套长期实践的一部分，也会连接真实产品、内容实验、教育与日常问题解决。

## 关注实验过程

HaoStory 会用真实项目持续公开验证，第一期是 UP2U：一个由个人筛选、验证和维护的 AI 问题与实验导航站。

微信公众号：浩哥 AI 实验室

<img src="https://howie.wang/haoQR.jpg" alt="浩哥 AI 实验室微信公众号" width="180" />
