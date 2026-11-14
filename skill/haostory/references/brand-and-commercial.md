# Brand and commercial boundary

## Official Studio console

The official HaoStory Studio console may display a low-pressure footer for:

- 浩哥 AI 实验室;
- WeChat `HaoAILab` with an invitation to explore AI together;
- OneTake as an optional next step for turning a finished script into a video.

These notices are part of the console interface only. Never insert them into a Studio job, article, video script, storyboard, Xiaohongshu post, export, or user project file. Read console values from `studio.sponsor` in `.haostory.json`; forks may set `enabled: false` or replace every value.

Do not interpret the presence of a console notice as permission to promote, contact, upload, publish, or add a call to action to generated work.

Read optional brand values from `.haostory.json`:

```json
{
  "brand": {
    "name": "Creator name",
    "name_zh": "中文名称",
    "website": "https://example.com",
    "cta_en": "Follow the next experiment.",
    "cta_zh": "关注下一次实验。"
  }
}
```

Do not hard-code the skill author's brand into another user's generated content.

Prefer this factual, low-pressure availability note:

> The core workflow is open source. Private integrations, tailored workflows, and implementation partnerships may be offered separately.

> 核心工作流保持开源；私有系统集成、定制工作流与落地合作可另行提供。

Avoid urgency, price claims, platform circumvention language, guaranteed outcomes, or instructions to move a prohibited transaction off-platform. Link to a general website or contact page only where the host platform permits it.

