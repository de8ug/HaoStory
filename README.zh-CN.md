# HaoStory Studio

> **采集策略：默认暂停。** 打开 Studio 是一次明确的内容制作任务，并且只读取用户选中的材料。只有浩哥为某个命名项目启用记录，或明确要求一次手动记录时，才会开始持续采集。

**跟浩哥一起，用 AI 讲好自己的故事。**

HaoStory Studio 是一个由智能体调用、本地优先的开源内容导演。选择少量项目说明、图片或近期会话；Studio 负责判断能做什么、缺什么材料、适合什么结构，以及文案、画面、动画、配音、字幕和剪辑怎样配合。具体制作交回当前智能体执行，默认不会扫描整个工程。

> 由 [Howie Wang](https://howie.wang/) / 浩哥 AI 实验室发起

[English](README.md)

## 从选定材料到可编辑成品

在支持的智能体中运行 HaoStory，会打开一个简洁的本地控制台：

```text
选择说明、图片或宿主提供的近期会话
                    ↓
选择文章、视频、小红书图文或多格式组合
                    ↓
查看三个推荐角度和真正有用的材料缺口
                    ↓
按需调研当前平台案例与制作工具
                    ↓
向调用它的智能体提交一份制作方案
                    ↓
验收本地可编辑成品
```

Studio 首先只展示安全的文件名和会话元数据。用户选中后，智能体才读取文件正文或对应聊天。宿主提供会话 API 时可以选择近期会话；其他智能体回退到当前对话或用户导出的材料。

```bash
python3 skill/haostory/scripts/haostory.py studio
```

官方控制台底部会轻量展示浩哥 AI 实验室、微信 `HaoAILab` 和 OneTake。开源 Fork 可以替换或关闭，这些提示绝不会进入用户生成的内容。

HaoStory 本身保持轻量。平台调研与工具编排以带日期的工作流参考维护：优先采用官方规则，把公开案例规律标为假设，并核对 GitHub 工具的许可和维护状态。具体制作可以调用宿主已有的写作、绘图、OneTake、Remotion、FFmpeg、转写、配音和剪辑能力，但安装工具或把材料发送到外部服务前仍需用户授权。

## 安装与调用

Codex 全局使用时，把完整的 Skill 目录复制到 `~/.agents/skills/haostory/`；只在某个项目使用时，放到该项目的 `.agents/skills/haostory/`。替换已有版本后，请新开一个聊天。

最稳定的调用方式是输入 `$haostory`，或在 `/skills` 中选择 HaoStory Studio。自然语言也可以根据 Skill 描述自动匹配，例如：

> 使用 HaoStory，把这个项目选中的说明和图片制作成文章与短视频方案。

显式点名比自动匹配更确定。打开 Studio 只代表同意本次内容任务，不会启用持续采集。完整的本地控制台需要宿主智能体能够运行本地命令，并读取用户批准的本地文件；不具备这些能力的宿主仍可使用内容方法，但不能自行读取本地项目或打开控制台。

可分发包生成在 `dist/haostory.skill`。支持上传 Skill ZIP 的智能体平台可以在完成自身的兼容性与安全检查后导入。上架市场、收费或替其他用户安装始终是独立操作。

## 为什么做 HaoStory Studio

很多项目故事是在工作结束以后凭记忆补写的。这时真正有价值的细节往往已经丢了：失败过什么、为什么改变判断、测试怎样证明结果、前后到底有什么差异。

Studio 可以直接使用用户选中的既有材料。对于希望边做边保存证据的用户，原有分阶段记录能力仍然保留，但它只是可选素材来源并且默认暂停。CLI 本身不调用 AI 服务；不会自动 commit、push、上传或发布。

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

## 可选的分阶段智能采集

HaoStory V2 按 Project → Initiative → Phase → Capture Window → Event 管理证据。一个 Phase 可以是一项有明确结果的开发任务，也可以是路线图里提前规划的阶段。新项目默认 `off`；只有显式执行 `enable`，命名项目才进入 `assisted-auto`。Agent 会告知生命周期变化、折叠重复信息，并且每个阶段通常最多保留 4 个不同事件。

普通格式调整、依赖安装、简单修复、纯咨询和机械改名不会自动新建故事。高置信事件包括决策、范围变化、失败、恢复、前后对比、里程碑、Demo、指标和脱敏后的外部反馈。

已公开观点保存在本地 `.haostory/story-registry.json`。导出前会区分新观点、新证据、必要背景和重复观点；已发布观点没有新证据时默认归档。

在 assisted-auto 工作过程中，Agent 会把关键失败、恢复、前后对比、里程碑和 Demo 的稳定截图直接保存到私有会话 `assets/`。不建立候选清单，也不逐张确认。只有某个重要取舍确实无法判断时，才向用户提出一个简短问题，不做连续访谈。

阶段结束时会生成一份简短的私有阶段材料并报告位置。经过一次阶段级确认后，`share-stage --confirmed` 会更新一份项目进展文档，并把最多三张关键截图放入按日期组织的目录。每张截图都带简短说明和 `real`、`demo` 或 `mixed` 数据标签。对于软件项目，它还会核对 README 是否包含启动方式和运行地址，并返回建议与代码一起提交的文件清单。HaoStory 自身不会改 README、commit、push、上传或发布；制作文章、视频成品仍需单独请求。

省略 `--session` 时，HaoStory 只会选择唯一的 active/paused 窗口；存在多个候选时明确报错，没有活跃窗口时按 manifest 的 `updated_at` 选择最新 V1 会话。普通 session ID 和 registry 路径不能逃出项目内非符号链接的 `.haostory/`。

## 可选采集快速开始

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

HaoStory 也可以针对 WorkBuddy 等智能体市场制作适配版。比较合适的模式是：免费开源 Studio 工作流负责获客和基础创作，可选付费专家持续维护平台调研、个性化模板与制作编排。市场打包、定价、审核、云端运行、隐私条款与结算由目标平台管理，本仓库不会自动完成这些操作。

## 关于浩哥

[Howie Wang](https://howie.wang/) / 浩哥持续探索 AI 怎样帮助人们更好地工作、学习、创造与生活。HaoStory 是这套长期实践的一部分，也会连接真实产品、内容实验、教育与日常问题解决。

## 关注实验过程

HaoStory 会用真实项目持续公开验证，第一期是 UP2U：一个由个人筛选、验证和维护的 AI 问题与实验导航站。

微信公众号：浩哥 AI 实验室

<img src="https://howie.wang/haoQR.jpg" alt="浩哥 AI 实验室微信公众号" width="180" />
