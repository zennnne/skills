---
name: setting-up-llm-wiki
disable-model-invocation: true
description: Scaffold a Karpathy-style LLM wiki (schema + index + log) in a new project and co-design its schema with zen.
---

# Setting up an LLM wiki

Pattern source: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f. Live instance to borrow from: `C:/Users/User/research/CLAUDE.md`.

The pattern in one paragraph: the LLM **compiles** knowledge once into a persistent, interlinked set of markdown pages and keeps it current, instead of re-deriving it from raw files on every question. Three layers: **sources** (immutable inputs the LLM reads), **wiki** (pages the LLM owns and rewrites), **schema** (the `CLAUDE.md` / `AGENTS.md` that makes the LLM a disciplined maintainer). Three operations: **ingest**, **query** (with **file-back** of good answers), **lint**. Two navigation files: `index.md` (catalog, read first) and `log.md` (append-only timeline). Lint splits into a **mechanical** pass (`lint.py`, shipped with this skill) and a **judgment** pass (the agent).

That core is the fixed part. Everything else in `schema-template.md` (page types, overview, staleness model, lessons, web capture, search, `progress/`) is a **module**: include it only when an interview answer calls for it, so each wiki carries only what its domain uses.

## 1. Fit check

The pattern fits a domain where knowledge **accumulates from outside sources**: research, a course, a book, a hobby, a game, personal tracking, a team's meeting notes.

In a code repo the code is the source of truth, so a wiki over it goes stale with every commit. There, point zen to the lighter set: `CONTEXT.md` (glossary), `docs/adr/` (decisions), `progress/<feature>.md` (in-flight state, deleted when the feature lands). Set up a wiki in a code repo only for knowledge that lives outside the code (domain research, specs from clients, competitor notes), and scope it to its own folder.

Done when zen confirms this domain is a fit, or picks the code-repo alternative (then stop here).

## 2. Interview

Ask zen, one question at a time, offering a recommended answer each time:

1. **Domain and purpose**: what questions should this wiki answer in three months?
2. **Sources**: what goes in (web articles, PDFs, transcripts, chat logs, own notes) and how they arrive (zen drops files, agent fetches URLs, another skill writes them). Web articles among them → include the `web capture` module.
3. **Page types**: which entity/concept/topic pages the domain needs (e.g. characters + themes for a book; methods + tools for research).
4. **One picture?**: do the pages form one connected body of knowledge (a fictional world, one course, one research thesis)? Yes → include the `overview` module. Unrelated topics side by side → leave it out.
5. **Staleness**: what makes a page out of date here. Either **time** (real-world facts age: `AS_OF` + `VOLATILITY` thresholds per page class) or **status** (fiction, canon, specs: each page or section tagged with a status such as canon / past-era / open / retconned, and lint hunts contradictions instead of age).
6. **Crafts**: does this domain have recurring work whose know-how should build up from zen's corrections (image prompts, scene writing, experiment setup)? Yes → include the `lessons` module, one `lessons/<craft>.md` per craft named.
7. **Supervision**: ingest one source at a time with zen reviewing, or batch-ingest.
8. **Long tasks**: will any operation outlive one context window (batch ingest, large refresh, multi-session retcon)? Yes → include the `progress/` module. No → leave it out; add it later if a long task appears.
9. **Scale**: expected size in a year. Hundreds of pages or more → include the `search` module now; otherwise leave it out and let lint flag when `index.md` stops being enough.
10. **Location**: wiki root path, and whether it is its own git repo.

Done when every question has an answer zen has accepted.

## 3. Scaffold

At the wiki root create:

```
CLAUDE.md     schema, filled from schema-template.md with the interview answers
index.md      "# Index" + one empty "## <category>" heading per page type
log.md        "# Log" + a first entry: ## [YYYY-MM-DD] schema | wiki created
raw/          sources (immutable)
wiki/         LLM-owned pages; with the overview module, wiki/overview.md holding "# Overview" only
lint.py       copied from this skill's lint.py, unchanged
lessons/      only with the lessons module: one "# Lessons — <craft>" file per craft, linked from index.md
progress/     only with the progress module (add .gitkeep)
```

Fill [`schema-template.md`](schema-template.md): every `{{placeholder}}` replaced with an interview answer; every `[module: …]` part kept or deleted per the interview, with its tag removed. A tag covers a whole `##` section when it sits in the heading, otherwise the text after it up to the end of its sentence, bullet, or table row. Fill `{{lint args}}` with the `--pages` globs matching the page types, plus `--hub wiki/overview.md` with the overview module (a hub links everywhere by design, so it must not demand back-links), plus `--stale <level>=<days> …` with the time-staleness module.

If the wiki root sits inside a repo that already has a `CLAUDE.md`, put the schema at `<wiki-root>/CLAUDE.md` and add one line to the repo's `CLAUDE.md` pointing at it, worded as the trigger: "Read `<wiki-root>/CLAUDE.md` before answering questions about <domain> or editing files under `<wiki-root>/`."

Done when the files exist, `CLAUDE.md` contains no `{{` and no `[module`, and `python lint.py <lint args>` runs from the wiki root and prints its summary line.

## 4. Tracer ingest

If zen has a first source at hand, run one **ingest** end to end following the new schema, with zen watching. Adjust the schema where the run exposed a gap (a missing page type, a convention that felt wrong), and log the change as a `schema` entry.

Done when one source is ingested, `index.md` lists its pages, `log.md` has the `ingest` entry, and zen is satisfied with the schema. With no source at hand, report the scaffold and tell zen to run the first ingest by dropping a file in `raw/` and asking for it.
