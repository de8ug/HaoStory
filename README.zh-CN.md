# HaoStory

> **本地运行策略：默认暂停。** 只有浩哥明确为某个命名项目启用 HaoStory，或明确要求进行一次手动记录时才运行。`setup` 只初始化配置，不代表项目已经选择加入。

**做一次，讲清楚。**

HaoStory 是一个本地优先、天然双语的 Agent Skill。它把真实的软件开发、产品实验、内容实验和研究过程，沉淀为有证据的文章、视频脚本、社媒短帖与公开开发记录。

> 由 [Howie Wang](https://howie.wang/) / 浩哥 AI 实验室发起

[English](README.md)

## 为什么做 HaoStory

很多项目故事是在工作结束以后凭记忆补写的。这时真正有价值的细节往往已经丢了：失败过什么、为什么改变判断、测试怎样证明结果、前后到底有什么差异。

HaoStory 在工作发生时只保留少量关键节点，为后续文章或视频准备材料。CLI 本身不调用 AI 服务；不会自动 commit、push、上传、制作成品或发布。

## 适合谁

HaoStory 不只面向软件开发者。只要你正在与 AI Agent 一起完成一件有价值的事，并希望留下过程中真正有用的部分，就可以使用它：

- 独立开发者与创作者；
- 教师、研究者和内容团队；
- 产品、工作流和创意实验；
- 希望把工作、学习或日常问题沉淀为可复用经验的人。

有代码时，HaoStory 可以记录 Git 证据；没有代码也可以记录判断、草稿、测试、视觉素材、反馈和前后对比。

## 记录什么

- 阶段目标和最终结果；
- 经过隐私脱敏的 Git 状态与代码差异；
- 关键检查点里的判断、取舍和经验；
- 选定的命令输出，以及自动沉淀的关键视觉证据；
- 用于判断是否值得发布的故事价值评分。

## 分阶段智能采集

HaoStory V2 按 Project → Initiative → Phase → Capture Window → Event 管理证据。一个 Phase 可以是一项有明确结果的开发任务，也可以是路线图里提前规划的阶段。新项目默认 `off`；只有显式执行 `enable`，命名项目才进入 `assisted-auto`。Agent 会告知生命周期变化、折叠重复信息，并且每个阶段通常最多保留 4 个不同事件。

普通格式调整、依赖安装、简单修复、纯咨询和机械改名不会自动新建故事。高置信事件包括决策、范围变化、失败、恢复、前后对比、里程碑、Demo、指标和脱敏后的外部反馈。

已公开观点保存在本地 `.haostory/story-registry.json`。导出前会区分新观点、新证据、必要背景和重复观点；已发布观点没有新证据时默认归档。

在 assisted-auto 工作过程中，Agent 会把关键失败、恢复、前后对比、里程碑和 Demo 的稳定截图直接保存到私有会话 `assets/`。不建立候选清单，也不逐张确认。只有某个重要取舍确实无法判断时，才向用户提出一个简短问题，不做连续访谈。

阶段结束时会生成一份简短的私有阶段材料并报告位置。经过一次阶段级确认后，`share-stage --confirmed` 会更新一份项目进展文档，并把最多三张关键截图放入按日期组织的目录。每张截图都带简短说明和 `real`、`demo` 或 `mixed` 数据标签。对于软件项目，它还会核对 README 是否包含启动方式和运行地址，并返回建议与代码一起提交的文件清单。HaoStory 自身不会改 README、commit、push、上传或发布；制作文章、视频成品仍需单独请求。

省略 `--session` 时，HaoStory 只会选择唯一的 active/paused 窗口；存在多个候选时明确报错，没有活跃窗口时按 manifest 的 `updated_at` 选择最新 V1 会话。普通 session ID 和 registry 路径不能逃出项目内非符号链接的 `.haostory/`。

## 快速开始

私有原始记录保存在 Git 忽略的 `.haostory/`；经过阶段级确认的精简材料默认更新到 `docs/progress.md` 和 `docs/screenshots/YYYY-MM-DD/`。建议和它所说明的代码改动放在同一次提交中，但是否提交或同步仍由用户另行决定。

把 `skill/haostory` 复制到你的 Agent Skill 目录，或者让 Agent 直接阅读仓库中的 `SKILL.md`。

```bash
python3 skill/haostory/scripts/haostory.py setup
python3 skill/haostory/scripts/haostory.py enable \
  --progress-file docs/progress.md \
  --screenshots-dir docs/screenshots
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
  --event demo \
  --notes "稳定后的桌面端结果" \
  --novelty-key stable-demo \
  --asset /tmp/stable-demo.png \
  --data-kind demo
python3 skill/haostory/scripts/haostory.py pause --reason "这段不记录"
python3 skill/haostory/scripts/haostory.py resume
python3 skill/haostory/scripts/haostory.py close-phase \
  --result "构建阶段已可进入验证" \
  --todo "使用真实数据验证移动端流程" \
  --handoff
python3 skill/haostory/scripts/haostory.py share-stage \
  --confirmed
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
python3 skill/haostory/scripts/haostory.py disable
```

阶段结束不会自动生成内容、改变 Git 历史、上传文件或发布。下一步操作前必须查看隐私报告、阶段记录，并验收最终视频或文章。

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
