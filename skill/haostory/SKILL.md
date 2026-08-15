---
name: haostory
description: Capture real software development, product experiments, content production, or research as privacy-reviewed bilingual story assets. Use when an agent should preserve decisions, Git changes, test output, screenshots, lessons, article drafts, build-in-public logs, or video scripts while work is happening, especially when the user asks to document the process, create content from a project, or prepare a public case study.
---

# HaoStory

Turn real work into evidence-backed stories. Capture first, select second, publish only after human review.

## Core rule

Record meaningful changes in judgment, not every mechanical action. Allow two content layers:

1. what was built or learned;
2. how it was built or learned.

Do not recursively create content about routine packaging unless that work reveals a reusable method, failure, or result.

## Workflow

1. Read `references/privacy.md` before the first capture in a repository.
2. Run `scripts/haostory.py setup` when the project has no `.haostory.json`.
3. Run `start` before meaningful work begins.
4. Run `checkpoint` after a decision, failed attempt, implementation milestone, test, or visible before/after result.
5. Run `finish` only after the outcome is known.
6. Run `audit`, then `export`.
7. Improve generated drafts using the evidence package. Rewrite or translate each requested language naturally; do not leave untranslated source text in the other language. Do not invent events, metrics, quotes, or results.
8. Ask for human approval before publishing or copying any raw evidence into a public repository.

Read `references/project-integration.md` when the user wants HaoStory applied automatically across future sessions in a project.

## Commands

From the target project root:

```bash
python3 <skill>/scripts/haostory.py setup
python3 <skill>/scripts/haostory.py start --title "Task title" --summary "Why it matters" --type product
python3 <skill>/scripts/haostory.py checkpoint --stage decision --notes "What changed" --decision "Why"
python3 <skill>/scripts/haostory.py checkpoint --stage tests --notes "What was verified" --run npm test
python3 <skill>/scripts/haostory.py finish --outcome "What happened" --lesson "What changed in our understanding"
python3 <skill>/scripts/haostory.py audit
python3 <skill>/scripts/haostory.py export
```

Use `--asset path/to/file` only for material the user intentionally selected. Treat screenshots as potentially sensitive even when the text audit passes.

## Output policy

Generate Chinese and English drafts by default. Keep raw evidence local under `.haostory/`. Read `references/output-schema.md` when changing the package format.

Generated drafts are scaffolds, not final editorial copy. Strengthen them around one tension, one changed judgment, and verifiable proof. Prefer:

- a specific result over a broad claim;
- a failed attempt over a smooth chronology;
- before/after evidence over adjectives;
- the user's judgment over generic AI narration.

## Story selection

Export every finished session, but recommend publishing only when the story has at least three of these:

- a real conflict or surprise;
- a decision that changed;
- visual or test evidence;
- a lesson useful beyond this project;
- a timely reason to care;
- a result that can be demonstrated.

Read `references/story-shapes.md` when choosing an article or video angle.

## Brand and commercial boundary

Keep public defaults neutral. Apply the user's brand only from `.haostory.json`. Read `references/brand-and-commercial.md` before adding attribution, calls to action, sponsor language, or commercial availability.

## Privacy boundary

Never capture `.env` files, credentials, cookies, private keys, browser profiles, production user data, or private conversations. The text sanitizer reduces risk but does not replace manual review. If the privacy report contains a high-severity finding, do not recommend publication.
