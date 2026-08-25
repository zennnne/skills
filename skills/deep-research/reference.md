# Deep Research — Reference

## Contents
- Sub-agent prompt template (Phase 3)
- Synthesis structure (Phase 4)
- Memory pointer template (Phase 5)

## Sub-agent prompt template

Fill `{SUB_QUESTION}`, `{AS_OF}`, `{NOTES_PATH}` and pass as the Agent prompt:

```
You are researching ONE focused sub-question for a larger report. Today's date
(AS_OF) is {AS_OF}.

Sub-question: {SUB_QUESTION}

Do this:
1. Run web searches and WebFetch the most credible sources (official bodies,
   peer-reviewed, reputable journalism, primary data). Prefer 5+ distinct
   domains. Do not spend searches on stable textbook basics — summarize those
   briefly and spend the search budget on what is recent, contested, numeric,
   or specific to this sub-question.
2. For every factual claim, record the source URL and its publication date.
   Flag anything older than ~3 years (research) or ~6 months (fast-moving /
   news) relative to AS_OF as possibly stale.
3. Write your findings to {NOTES_PATH} as Markdown: bullet findings, each with
   an inline source link and date; a short "open questions / disagreements"
   section; a numbered source list at the end.
4. Return to me ONLY a distilled summary — the key findings and their
   citations. Do NOT paste raw search results or full page text.
```

## Synthesis structure

Write `synthesis.md` in this order:

1. **Research question** — the one-sentence scope confirmed in Phase 1.
2. **Executive summary** — 150–300 words, prose.
3. **Findings** — grouped by theme, not by sub-agent. Inline citations `[n]`.
   Tag each major claim `(Confidence: High/Medium/Low)`.
4. **Contradictions & open debates** — where sources disagree, say so.
5. **Limitations** — gaps, stale sources, what wasn't covered.
6. **Sources** — numbered list `[n] Title — URL (date)`, matching inline marks.

Keep it ≥80% prose; bullets only for genuinely list-like content.

## Memory pointer template

Content for `reference_research_library.md` (create once, Phase 5 step 2):

```markdown
---
name: research-library
description: คลัง deep-research reports อยู่ที่ C:/Users/User/research/ — เช็ค INDEX.md ก่อนตอบคำถามเชิงลึกที่อาจ research ไว้แล้ว
metadata:
  type: reference
---

Deep-research reports live in
`C:/Users/User/research/<project-slug>/<topic-slug>/synthesis.md`, grouped by
project, with an index at `C:/Users/User/research/INDEX.md`.

**How to apply:** when the user asks an in-depth question, check INDEX.md first
— if the topic was researched, Read its synthesis.md and answer from it (with
its citations) instead of re-searching from scratch.
```

MEMORY.md index line:
`- [Research library](reference_research_library.md) — คลัง deep-research อยู่ที่ C:/Users/User/research/ เช็ค INDEX.md ก่อนตอบคำถามเชิงลึก`
