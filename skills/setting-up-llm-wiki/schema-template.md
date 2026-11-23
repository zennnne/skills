# {{Wiki name}} — schema

{{One sentence: what this wiki is for and what questions it answers.}}
LLM-wiki pattern: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f.
The LLM writes and maintains every file under `wiki/`, `index.md`, and `log.md`; zen curates sources, asks questions, and reviews.

## Layers

| Layer | Where | Rule |
|---|---|---|
| Sources | `raw/` | Immutable. Read, never edit. {{How sources arrive.}} |
| Wiki | `wiki/` | LLM-owned. Rewrite freely as new evidence lands. |
| [module: overview] Overview | `wiki/overview.md` | The current big picture of the whole wiki: main threads, how they connect, open questions. Synthesis, not a list; the list is `index.md`. |
| [module: lessons] Lessons | `lessons/<craft>.md` | How to do the domain's recurring work well: rules learned from zen's corrections. Outside `wiki/` because it is knowledge about doing the work, not about the domain. |
| Index | `index.md` | One line per page (link + one-line summary), grouped by page type. Read first on every query. |
| Log | `log.md` | Append-only timeline of operations. |
| Lint script | `lint.py` | Mechanical checks. Run it; edit it only to fix a bug in it. |

## Page types

{{One subsection per page type, e.g.:}}

### {{Type}} — `wiki/{{type}}/<slug>.md`

{{What one page of this type covers, and the sections it always has.}}

## Page conventions

Every wiki page:

- [module: time staleness] Opens with `AS_OF: YYYY-MM-DD` and `VOLATILITY: {{levels}}`, where {{level → stale-after threshold, one per line}}.
- [module: status staleness] Tags each page or section with a status: {{statuses, e.g. canon / ⏳ past-era (still true for its era; state what is true now) / open / retconned → moved to `_archive/`}}.
- Cites the `raw/` source (or URL) for each claim.
- Links with standard markdown links whose path is relative to the linking file: `[text](../{{type}}/<slug>.md)`. Every link then opens directly with Read and parses in `lint.py`.
- Ends with `## Related`. Links are two-way: when A links B, B links A.

## Operations

### Ingest

1. Read the new source in `raw/`.{{ If supervised: Discuss the key takeaways with zen before writing.}} For a source with images (web snapshot, PDF, slides), read the text first, then open each image the text refers to, one at a time; reading a file returns its text only.
2. Write or update every page the source touches: summary page, plus entity/concept pages it adds to or contradicts. Where it contradicts an existing claim, keep both with sources and flag it.
3. [module: overview] When the source extends or contradicts the big picture, revise `wiki/overview.md`.
4. Update `## Related` links (both directions) and `index.md`.
5. Append to `log.md`.

Done when every touched page is updated, linked both ways, indexed, and logged, and `python lint.py {{lint args}}` reports no `broken`, `unindexed`, or `one-way` findings.

### Query

1. Read `index.md`, then the relevant pages; open `raw/` only to check a citation. [module: overview] Read `wiki/overview.md` right after `index.md`.
2. Answer with citations to the pages used.
3. **File back** an answer worth keeping (comparison, analysis, new connection) as a page or a section of one; update index and log.

### Lessons [module: lessons]

A **lesson** is a rule for doing a recurring piece of work in this domain ({{crafts, e.g. writing image prompts, designing a scene}}), learned from a correction.

**Before** doing that work, read `lessons/<craft>.md` and apply every rule in it.

**When zen corrects** how a piece of work was done, route the correction by what it is about:

| Correction about | Where it goes |
|---|---|
| A fact on a wiki page | Fix the page itself. The fixed page is the record; no lesson. |
| How to do one of this domain's crafts | A lesson in `lessons/<craft>.md`, plus a `lesson` log entry. |
| How to maintain this wiki | An edit to this file, plus a `schema` log entry. |
| How to work with zen in every project | Global feedback memory, outside this wiki. |

Each lesson: `## <n>. <short title>`, then **Rule** (the target behaviour, phrased as what to do), **Why** (the failure it prevents), and an example when the rule alone is ambiguous. When a new lesson overlaps an old one, merge them into one rule. Done when the rule sits under the right craft, merged with any overlapping lesson, and logged.

### Lint

Run when zen asks, or at session start when the newest `lint` log entry is over {{N}} days old. Two passes:

**Mechanical**: run `python lint.py {{lint args, e.g. --pages "wiki/**/*.md" --hub wiki/overview.md --stale fast=90 medium=365 slow=1095}}` from the wiki root. It reports `broken` (link to a missing file), `unindexed`, `orphan`, `one-way` (hub pages given by `--hub` are exempt from these two), and with time staleness `header` (missing AS_OF/VOLATILITY) and `stale`. Fix every `broken`, `unindexed`, `one-way`, and `header` finding, then rerun until those kinds are gone.

**Judgment**: read every page for:

- **Contradictions** — two pages disagreeing on a fact. [module: status staleness] Two `canon` statements that cannot both hold are the top finding.
- **Missing pages** — a concept mentioned on 2+ pages with no page of its own. Create them.
- **Orphans** — for each `orphan` the script reported, link it from the pages it belongs with, or report it if nothing fits.
- **Gaps** — questions the wiki cannot answer yet; suggest sources or questions to fill them.
- [module: lessons] **Lesson sediment** — lessons that overlap (merge them), contradict (ask zen which holds), or guard against something that no longer happens (propose deleting).
- [module: overview] **Overview drift** — `wiki/overview.md` no longer matching the pages.
- **Index load** — without the search module: `index.md` past a few hundred entries → propose adding it.

Report stale pages, contradictions, unresolved orphans, and gaps to zen as a list. Done when the script's fixable kinds are gone, every judgment check has run on every page, and the log has a `lint` entry naming each finding.

## Web capture [module: web capture]

Web sources enter `raw/` as markdown snapshots, never as bare URLs, so a dead link cannot erase a source. One file per source: `raw/<yyyy-mm-dd>-<slug>.md`, headed with the URL and capture date, body converted to clean markdown (nav, ads, and comments stripped). Images the content depends on go to `raw/assets/` and are linked locally by relative path (ingest step 1 covers reading them). {{Capture tool: agent fetch-and-convert, or a clipper zen uses in the browser.}}

## Search [module: search]

`index.md` is the entry point while it stays readable in one pass. Once it stops being enough (roughly a few hundred pages, or queries that keep missing pages that exist), query the wiki through {{search tool, e.g. qmd — local hybrid BM25/vector search with CLI + MCP, https://github.com/tobi/qmd}} first, then open the hits. Keep `index.md` maintained either way; search finds pages, the index shows the wiki's shape.

## In-flight work [module: progress]

`log.md` records operations that finished; `progress/<task>.md` holds the state of one that hasn't. Open a progress file when an operation will outlive one context window: a batch ingest, a lint that fixes many pages, a refresh of stale pages, a multi-session synthesis.

- Name it after the task (`progress/batch-ingest-2026-11.md`). One file per task.
- Keep it current at every milestone, so a fresh context (after compact or a new session) resumes from it alone: **goal** and done-criterion, **done so far**, **tried and failed** (with why), **next step**.
- At session start, read every file in `progress/` before taking on new work.
- When the task is done: file back any knowledge worth keeping into the wiki (and, with the lessons module, each dead end that taught a reusable rule into `lessons/`), append the `log.md` entry, then delete the progress file. `progress/` is empty whenever nothing is in flight.

## Log format

```
## [YYYY-MM-DD] ingest | <source title>
## [YYYY-MM-DD] file-back | <page> — <what was added>
## [YYYY-MM-DD] lint | <n> findings — <short list>
## [YYYY-MM-DD] lesson | <craft> #<n> — <short title>
## [YYYY-MM-DD] schema | <what changed in this file>
```

`grep "^## \[" log.md | tail -5` shows recent activity.
