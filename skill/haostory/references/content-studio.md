# HaoStory Studio production guide

Read this reference after the user submits a Studio job.

## Production contract

The job request is the complete permission boundary for this run:

- `selected_paths`: project-relative files that may be opened;
- `conversation_refs`: host conversations the user selected and that may now be retrieved;
- `formats`: `article`, `video`, `xiaohongshu`, or a combination;
- `angle`: the chosen narrative structure;
- `goal`, `audience`, and `supplements`: user direction;
- `generate_with_current_material`: proceed without requiring every suggested supplement.
- `research_current_examples`: permission to research current public platform rules and examples without sending private project material.

Do not read adjacent files or conversations to make the job “more complete.” Ask one focused question only when the missing answer would materially change factual accuracy, privacy, or the core position. Otherwise state any uncertainty and create the first editable version.

## Shared evidence brief

Before drafting multiple formats, privately distill the selected material into:

1. the audience's problem or curiosity;
2. the concrete project or creation;
3. the strongest tension, failure, surprise, or changed judgment;
4. the result and its evidence;
5. the lesson that transfers beyond this project;
6. approved visuals and what each proves;
7. facts or claims that remain uncertain.

Adapt every format from this brief. Do not copy the same prose into each channel. Before execution, use the production blueprint in [platform-research.md](platform-research.md) to decide which parts need writing, illustration, screen capture, animation, voice, captions, editing, or a platform-specific export. Hand those parts back to the invoking agent and its available tools.

## Article structures

### Failure and recovery

Hook with the assumption that failed, show the observed problem, explain the changed decision, prove the result, and close with the reusable lesson.

### Decision story

State the decision and stakes, present the alternatives, explain the evidence behind the choice, show what happened, and identify when the decision would not apply.

### Project case study

Problem → constraints → first approach → turning point → result → evidence → practical lessons → open questions.

### Practical guide

Promise a specific outcome, establish the real context, give a small number of tested steps, call out failure modes, and end with a usable checklist.

## Video structures

### 60-second story

- 0–3 seconds: a concrete result, tension, or surprising statement;
- 3–15 seconds: the real problem and stakes;
- 15–38 seconds: the failed assumption or changed decision;
- 38–52 seconds: visible proof and result;
- 52–60 seconds: one transferable takeaway and a natural close.

Provide spoken script, shot or screen direction, on-screen text, and material source for every beat.

### Three-minute case study

Use a cold open, compact context, two or three meaningful beats, result demonstration, limitations, and closing lesson. Mark where a talking head, screen recording, screenshot, diagram, or generated visual is appropriate.

### Screen walkthrough

Organize around what the viewer should notice, not every click. Each scene needs a purpose, narration, visual source, and transition.

## Xiaohongshu structures

### Before/after carousel

Deliver a cover title, one-sentence promise, 5–8 cards, image guidance per card, body copy, and honest topic tags. Use before/after only when both states are evidenced.

### Experience and pitfalls

Open with the real situation, name the failed attempt without exaggeration, present the adjustment, result, and 3–5 practical takeaways. Avoid fake controversy and guaranteed outcomes.

### Step cards

Use a specific cover result, a brief context card, 4–7 actionable cards, a pitfalls card, result/evidence card, and closing question. Keep card text scannable.

## Quality gate

- Every factual statement traces to approved material or is clearly framed as a suggestion.
- No private path, secret, account detail, unpublished business fact, or identifiable third-party material leaks into output.
- Images have a clear editorial purpose and do not imply evidence they do not show.
- The opening promises something the draft actually delivers.
- The output includes limitations when the evidence is incomplete.
- Console sponsor copy, Hao AI Lab, `HaoAILab`, and OneTake are absent unless the user explicitly asks to discuss them as subject matter.
