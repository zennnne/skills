---
name: deep-research
disable-model-invocation: true
description: Conducts thorough multi-pass research on a broad topic by first narrowing scope through an interactive interview, then dispatching parallel sub-agents to investigate sub-questions, and synthesizing findings into a cited Markdown report saved per-topic for later knowledge harvesting. Use when the user asks to deeply research, study in depth, or "เจาะลึก/ศึกษาเชิงลึก" a general subject (e.g. "deep research เรื่อง skincare", "deep-research อุตสาหกรรมอนิเมะ", "research hormone therapy for men"), wants a scoped-down overview of an unfamiliar field, or wants reusable research notes. NOT for single-fact lookups or already-narrow questions answerable by one web search. Keywords: deep research, deep-research, วิจัย, ศึกษาเชิงลึก, เจาะลึก, research report, literature review, รวบรวมข้อมูลเชิงลึก.
allowed-tools: "Read Write WebSearch WebFetch AskUserQuestion Agent"
---

# Deep Research

Narrows a broad topic to a crisp research question, investigates it with
parallel sub-agents, and synthesizes a cited report. Output is plain Markdown
per topic under `C:/Users/User/research/` — that folder is the knowledge base;
answer later questions by reading `synthesis.md` files from it, not from memory.

Set `AS_OF` = today's date at run start; pass it to every sub-agent so they can
date-stamp claims and flag stale sources.

## Phase 1: Scope down (interactive)

The topic arrives broad. Do NOT start researching yet — narrow it first.

**Default (deep) path:** Run a focused interview, 1–3 questions per round via
`AskUserQuestion`, until scope is unambiguous. Clarify:

- **Angle** — which facet matters (mechanism / outcomes / safety / how-to /
  market / comparison …)
- **Depth & length** — quick overview vs comprehensive
- **Audience & purpose** — own learning? a decision? background for writing?
- **Boundaries** — what is out of scope; time window if relevant
- **Project** — which project/category this research belongs to. Default:
  use the current working directory's project name (kebab-cased) as
  `<project-slug>` — e.g. "Cuteness consultant" → `cuteness-consultant`.
  If not in a named project, check `C:/Users/User/research/INDEX.md` for
  existing slugs to reuse; fall back to `general` only if neither applies.
  State the derived slug to the user and let them correct it — do NOT ask
  from scratch when the working directory already implies a clear project.

Keep asking until a one-sentence research question can be stated. State it back
and get explicit confirmation before Phase 2.

**Fast path:** If the user signals urgency ("เร็วๆ", "ไม่ต้องถามมาก", "just go"),
collapse to ONE round: state a best-guess scope (angle + depth) as explicit
assumptions, ask a single yes/no confirm, then proceed unless corrected. Never
zero rounds on a broad topic; never more than one round when speed is asked.

## Phase 2: Decompose & confirm plan

Break the confirmed question into 3–5 non-overlapping sub-questions, each a
self-contained investigation. Present the list via `AskUserQuestion` (Approve /
Edit / Add or drop one). Wait for approval.

Derive `<project-slug>` and `<topic-slug>` = lowercase-hyphenated short names.
Create folder `C:/Users/User/research/<project-slug>/<topic-slug>/`.

## Phase 3: Parallel investigation (sub-agents)

First Read `reference.md` for the sub-agent prompt template.

Spawn one sub-agent per sub-question using the Agent tool
(`subagent_type: general-purpose`), all in a single message so they run in
parallel. Cap fan-out at 5; if more sub-questions exist, run in batches. Fill
each prompt with: the sub-question, `AS_OF`, and the notes path
`C:/Users/User/research/<project-slug>/<topic-slug>/notes/<sub-slug>.md`.

Each sub-agent must search and fetch real sources, write its notes file, and
return ONLY a distilled summary (key findings + citations) — never raw search
dumps. This keeps the main context clean.

If a sub-agent errors, relaunch it once; if it fails again, note the gap and
continue with the rest.

## Phase 4: Synthesize

Read `reference.md` for the synthesis structure, then read all notes files.
Write `C:/Users/User/research/<project-slug>/<topic-slug>/synthesis.md`:
executive summary,
thematic findings with inline citations `[n]`, a confidence marker
(High/Medium/Low) per major claim, contradictions / open debates, limitations,
and a numbered source list.

Cite only sources that appear in the notes. Never invent URLs. Flag any claim
where sources disagree or are stale relative to `AS_OF`.

## Phase 4.5: Verify (spot-check)

Pick the 3–5 highest-impact claims in the synthesis (the ones the user would
act on). For each, trace it back to its notes file and confirm the cited source
actually supports it; WebFetch the source itself if the note is ambiguous. Fix
or downgrade-confidence any claim that fails. Do not skip this for health,
finance, or safety topics.

## Phase 5: Handoff & index

1. Update `C:/Users/User/research/INDEX.md` (create with a `# Research Index`
   heading if missing). Entries are grouped under one `## <project-slug>`
   heading per project — add the heading if this project is new, then append:
   `- [<topic>](<project-slug>/<topic-slug>/synthesis.md) — <one-line scope>
   (AS_OF <date>)`
2. Ensure a memory pointer exists: if
   `C:/Users/User/.claude/projects/C--Users-User/memory/reference_research_library.md`
   is missing, create it (type `reference`, pointing at the research folder +
   INDEX.md) and add its line to `MEMORY.md`. If it exists, leave it alone.
3. Report to the user: synthesis path, notes folder, source count, and 3–5
   headline takeaways (so they sit in conversation context).
4. Optionally suggest `/harvest-insights` — only for transferable insights from
   the session (preferences, workflow learnings), not to copy report content
   into memory; the files are the knowledge base.
