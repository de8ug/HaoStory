# Platform and production research

Use this reference when a Studio job requests current public research or when choosing a production toolchain. Platform behavior changes; treat fixed numbers and trend claims as dated evidence, not permanent rules.

## Research boundary

- Browse only when `research_current_examples` is true or the user separately asks for current research.
- Search with generic topic and format descriptions. Never paste private project text, unpublished names, personal data, or selected conversation content into an external service.
- Prefer official platform rules, creator guidance, original works, tool documentation, and source repositories.
- Separate stable principles from current patterns. Record source URL and retrieval date for time-sensitive findings.
- Study a small, diverse sample. Do not present one viral work as a formula or promise that an output will become popular.
- When public official guidance is unavailable, say so and treat observed examples as hypotheses.

## Production blueprint

Before executing tools, produce a compact internal blueprint:

1. destination platform and audience behavior;
2. content thesis and chosen narrative structure;
3. required material table: available, missing, optional, and how to obtain it;
4. deliverables: copy, script, storyboard, cards, cover, voice, captions, animation, music, and export variants;
5. tool routing with a reason and fallback for every nontrivial step;
6. review gates for factual accuracy, privacy, visual quality, audio, and platform compliance.

Then hand each production step to the invoking agent and its available tools. HaoStory coordinates; it does not need to bundle every renderer, voice system, editor, or platform connector.

## Tool-routing examples

Select by actual job and available capabilities rather than requiring every tool.

| Need | Preferred class | Useful options |
|---|---|---|
| Story research and factual checks | Browser/search with sources | host web tools; official platform pages; primary sources |
| Article and platform copy | Current language model | produce from the approved evidence brief, then editorial review |
| Covers and illustration | Image generation or design tool | host image tool; user-provided brand assets |
| Editable talking-head or whiteboard project | Structured video project generator | OneTake workflow when available |
| Programmatic motion graphics | Code-driven video | Remotion and its maintained Agent Skills |
| Assembly, trim, audio mix, subtitles, transcode | Media pipeline | FFmpeg |
| Local speech-to-text and subtitle timing | Local ASR | whisper.cpp or an approved host transcription tool |
| Voiceover | User-approved TTS or recorded voice | preserve pronunciation notes and require audio review |
| Final editorial changes | User's preferred editor | keep source project and intermediate assets editable |

Never install a tool, send material to a service, synthesize a person's voice, or incur cost without the authorization required by the host and user.

## Verified baseline, 2026-11-15

These are starting points, not an evergreen platform formula.

### X

Official X guidance recommends a real, conversational, concise voice, media that helps a post stand out, and no more than one or two hashtags when hashtags are used. Older X/Twitter business video guidance emphasizes early attention, strong visuals, captions for sound-off viewing, and short copy. Because part of that evidence concerns paid advertising and older platform behavior, validate it against current organic examples before applying it broadly.

- https://business.x.com/en/basics/get-your-business-started-with-x
- https://business.x.com/content/dam/business-twitter/resources/x-downloadable-guides/build-your-presence-on-x-one-sheet.pdf
- https://business.x.com/content/dam/business-twitter/en/resources/downloadables/objective-playbooks/video-views-playbook.pdf

### Xiaohongshu

Official rules emphasize real experience, useful information, original expression, accurate and complete claims, authorized material, and avoiding false or exaggerated results. A production plan should therefore request firsthand context, evidence for before/after claims, clean original visuals, source attribution, and important limitations rather than optimizing only for a sensational title.

- https://school.xiaohongshu.com/rule/detail/157/119982
- https://school.xiaohongshu.com/rule/detail/109/2565
- https://pgy.xiaohongshu.com/faq

### WeChat Channels / 视频号

No stable, sufficiently detailed public official creator guide was found through ordinary web discovery on 2026-11-15. Do not hard-code dimensions, length, or “viral” formulas from secondary posts. When a job targets 视频号, use current official account/creator surfaces available to the user, recent first-party examples, or user-provided performance data, and label any inferred pattern as a hypothesis.

### Open-source production tools

Remotion provides maintained Agent Skills and a React-based workflow for programmatic video, including animation, audio, captions, effects, and rendering. FFmpeg remains a general assembly and transformation layer. whisper.cpp provides local speech recognition and subtitle-oriented examples. Check each tool's current license, dependencies, maintenance state, and fit before recommending installation.

- https://github.com/remotion-dev/remotion
- https://github.com/remotion-dev/skills
- https://ffmpeg.org/ffmpeg-filters.html
- https://github.com/ggml-org/whisper.cpp
