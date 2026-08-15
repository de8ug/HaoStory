# HaoStory

**做一次，讲清楚。**

HaoStory 是一个本地优先、天然双语的 Agent Skill。它把真实的软件开发、产品实验、内容实验和研究过程，沉淀为有证据的文章、视频脚本、社媒短帖与公开开发记录。

> 由 [Howie Wang](https://howie.wang/) / 浩哥 AI 实验室发起

[English](README.md)

## 为什么做 HaoStory

很多项目故事是在工作结束以后凭记忆补写的。这时真正有价值的细节往往已经丢了：失败过什么、为什么改变判断、测试怎样证明结果、前后到底有什么差异。

HaoStory 在工作发生时记录这些节点，结束后建立可编辑的中英文内容结构。CLI 本身不调用 AI 服务；使用 Skill 的 Agent 根据证据分别改写或翻译两种语言。源代码不会上传，内容也不会自动发布。

## 记录什么

- 任务目标和最终结果；
- 经过隐私脱敏的 Git 状态与代码差异；
- 关键检查点里的判断、取舍和经验；
- 用户明确选择的命令输出和视觉证据；
- 用于判断是否值得发布的故事价值评分。

## 快速开始

把 `skill/haostory` 复制到你的 Agent Skill 目录，或者让 Agent 直接阅读仓库中的 `SKILL.md`。

```bash
python3 skill/haostory/scripts/haostory.py setup
python3 skill/haostory/scripts/haostory.py start \
  --title "开发第一版主页" \
  --summary "验证一个新的产品方向" \
  --type product
python3 skill/haostory/scripts/haostory.py checkpoint \
  --stage decision \
  --notes "首页从工具导航调整为问题导航" \
  --decision "先展示用户问题，而不是 AI 品牌"
python3 skill/haostory/scripts/haostory.py finish \
  --outcome "主页完成并通过测试" \
  --lesson "产品定位判断本身也是产品的一部分"
python3 skill/haostory/scripts/haostory.py export
```

HaoStory 不会自动公开素材。分享以前必须查看隐私报告，并人工检查每张图片。

## 开源核心

核心工作流以 MIT License 开源；私有系统集成、定制工作流与落地合作可另行提供。最新项目和联系入口见 [howie.wang](https://howie.wang/)。

## 关注实验过程

HaoStory 会用真实项目持续公开验证，第一期是 UP2U：一个由个人筛选、验证和维护的 AI 问题与实验导航站。

微信公众号：浩哥 AI 实验室

<img src="https://howie.wang/haoQR.jpg" alt="浩哥 AI 实验室微信公众号" width="180" />
