---
name: suzu
description: Cure a past session's status ailments — the standing conditions in the agent's environment that made it go wrong and will again.
disable-model-invocation: true
argument-hint: "[day/topic of the session]"
allowed-tools: "Read, Glob, Grep, Bash, Edit, Write, Skill"
---

The user has asked for a **retrospective** on a past coding session. You are diagnosing the agent's **environment** — steering files, hooks, skills, custom tooling — for the conditions that caused mistakes in that session and would cause them again in the next one. You are not reviewing the code that was written.

## Steps

1. Resolve the session the user specifies to a transcript path. If the user doesn't specify a session, default to the current one.

   The user names a session by day and topic ("yesterday, the one where we debugged the backup"), never by ID, and relative to today rather than by date - the equivalents of "yesterday", "last Saturday", "last week". Run `date` for today's weekday, then list the **single day** the user's phrase lands on with `python filter_transcript.py --day YYYY-MM-DD` from this skill's directory. The listing groups sessions under a dated weekday heading, so the phrase lands on a heading you can read back to the user. It gives local start and end times, duration, the project, the tool-call count, and the opening ask.

   Widen to `--day YYYY-MM-DD..YYYY-MM-DD` only when the day misses. A fortnight of it lists over a hundred sessions on this machine, every one of them paid for out of your own window before a transcript is open, so widen a day at a time.

   Ask the user before opening any transcript whenever two sessions are both plausible — whether they sit on different days or six hours apart on the same day opening with the same slash command. Show them time, duration, project, tool-call count and opening ask, and let them pick.

   The transcripts under `~/.claude/projects/` are the only complete record of what happened. Resolve from the listing.

   [`EPISODE-RESOLUTION.md`](EPISODE-RESOLUTION.md) carries the shapes an **episode** takes across transcripts — **Contiguous**, **Concurrent**, **Duplicate**, **Sequential** — and the touches that masquerade as a fix. Read it when the listing shows a session marked `(cont.)`, sessions whose times overlap the target's, two sessions opening with the same ask, or an earlier session in the same project whose output the target consumed; and again before you mark any candidate already-fixed.

2. Read [`COST-AND-WINDOW.md`](COST-AND-WINDOW.md) before condensing anything. It carries the `--context` triage that names which transcript in the episode is carrying the damage, what a tool call cost the session, and how to spend your own window across the episode — the totals table's sent column is where a rewritten file or a dispatched brief shows up, and an episode of one transcript hides those just as well as an episode of four.

   Then condense the transcript the triage named — `python filter_transcript.py <path> > <file>` from this skill's directory — and read its timeline, opening any row worth it with `--row N`.

   The condensed timeline interleaves the user's turns, the agent's replies, and the tool calls, each row carrying the time elapsed since the row above it, then totals per tool. `USER` rows are the human, including the slash command they typed; `SYS` rows are the harness talking to the agent.

   Read it start to finish, then run `python filter_transcript.py <path> --row N` to print any row untruncated — full tool input, full result. Worth opening: a long gap, a turn where the user corrected the agent, a call that dominates the totals, a run of near-identical calls. A row that wrote or read a whole file runs to tens of KB, so open it as `--row N --tail` when what you need is the error at the end or the head of the input; keep the bare `--row N` for a row you mean to read whole. Transcripts carry non-ASCII text, so any script you write against one needs `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`, as `filter_transcript.py` does. Always redirect a condense to a file and read it in slices; one that comes back inline at 50 KB has already eaten a third of your own pass.

   `--context` reports the usage the API recorded on every assistant entry, so it is **measured**, where the timeline's `~tokens` column is a per-row estimate: it gives the baseline the session opened at, the peak, the row where the window crossed budget and how much work was still queued behind it, and the jumps that took it there. **A task fits in 150,000 tokens** — the user's own bar, hardcoded in the script as `CONTEXT_BUDGET`, rather than a ceiling the harness enforces. Tell the user the bar was self-set and the run passed it; a report that says the user hit a limit says something that did not happen. The budget binds neither a turn nor a session, so find the task boundaries with the tests in **Task boundaries** below and hold it against a task that started from a clean window. When one session holds several tasks back to back, each inherits the bulk of the ones before it — the user's own scheduling rather than a condition of the environment, which step 4 reports as **Git gud!**.

   `--context` is blind to compaction: its peak only climbs, so a session the user compacted reports a `final` well under its `peak` and says nothing about why. Read that gap as a compact the user paid for rather than a window that stayed small, and when the user reports a compact, `grep -c compact` the raw `.jsonl` — that is the only place it is recorded.

   Read the gap column with care:

   - A long gap on a user row is the human away from the keyboard.
   - A long gap on an agent row whose previous row errored, or that repeats the call above it, is the harness blocked — a permission classifier timing out, a prompt waiting. Open the row; the agent did nothing for that time.
   - Every other gap on an agent row is the agent working.

   With the timeline read, check the mtime of every steering file, skill, script and memory directory the episode **read, wrote, or should have had and did not**, against the end of its last transcript. The set is wider than the files the session touched: a skill that steered it wrong and a memory directory that stayed empty are both conditions the session never wrote to. A file modified after the episode ended was probably already fixed in response to it, and the live question becomes whether the fix holds — a retrospective on a problem the user solved a week ago is a report they cannot act on.

3. Call the Skill tool with `mattpocock-skills:writing-for-agents` before hunting a single candidate. It is the reference for every document an agent consumes, which is what all of these categories propose to change, and it decides **what a candidate may propose** — so it belongs before the hunt rather than after it. Take three things from it: the **lever** each candidate pulls, since one that cannot name a lever is a wish rather than an edit; its **no-op** test and its **sediment**, which turn "this file is bloated" into a candidate that deletes; and its **two loads**, which price a candidate on the same arithmetic as step 4's severity order. It stays loaded from here on, and governs the diff you draft once they pick.

   Then look for candidates in these categories.

   - **Navigation**: how easy was it for the agent to find the right files? Are there hidden dependencies between files? Would a **navigation pointer** make it easier? _Use when_ the session took a long time to find a piece of information.
   - **Automated checks**: are there automated checks that could catch errors the agent made? Linting, typing, tests, filesystem linters? A `PreToolUse` hook in `settings.json` is the check available in a workspace that has no build to hang one on, and it is the category's answer to a mistake a written rule has already failed to stop. _Use when_ the agent made a mistake that could have been caught by an automated check, or repeated one a steering file already forbids.

   - **Skills that steered wrong**: did a skill the session invoked send it down a path this machine does not support, or leave out the branch the session actually needed? _Use when_ the agent improvised around a step, silently skipped one, or stopped to ask the user something the skill could have branched on. The edit lands in the skill file, and one that names a tool sitting in `settings.json`'s `deny` list is describing a machine that no longer exists.
   - **Coding standards**: the **reviewer agent** is `mattpocock-skills:code-review`, which reads `CODING_STANDARDS.md` or `CONTRIBUTING.md` when a repo has one and otherwise falls back to its built-in smell baseline. Should it be given a new rule to enforce? Should an existing rule be removed or clarified? _Use when_ the reviewer agent failed to catch a mistake — or when review never ran at all, or ran against a repo with no standards file, since work merged unreviewed is itself the candidate. A rule that belongs to review rather than implementation is a reason to create that file in the repo it applies to — propose it, and let the user decide.
   - **Global CLAUDE.md**: are there any steering instructions that should be moved to coding standards, automated checks, or memory instead? _Use when_ a `CLAUDE.md` is particularly large — in the project OR the user's global scope.
   - **Tool economy**: did the agent make expensive tool calls that could be streamlined? Is there any custom tooling (CLI's, MCP's) that is particularly token-inefficient? _Use when_ the agent made an expensive tool call, or tool results dominate the biggest jumps in the context report.
   - **No-ops**: look for instructions in steering files that don't modify the agent's behaviour. _Use when_ the steering files are large and unwieldy. The memory files recalled during the session are steering files too: they arrive as `SYS` rows in the timeline, and one the agent recalled and then worked against, or that names a file no longer on disk, is a no-op paid for on every session that recalls it. Also `ls` the project's memory directory: a file that never appears in the timeline at all is being paid for by no one, and an empty directory means every session in that project starts cold.
   - **Information access**: look for opportunities to increase the agent's access to information. Teeing dev server logs, readonly access to third-party services. _Use when_ a crucial piece of information was not available to the agent.

   The session decides which categories are live. A session that produced no code — teaching, research, planning — retires **Coding standards**; skip it.

4. Present these candidates to the user inline in your reply rather than in a file the user has to open — this report is the one part of the run the user reads. Filenames, flags, row numbers and quoted lines stay verbatim in whatever language they are written in on disk.

   Order them by severity, each under a number they can cite. Severity is how much the problem cost the user: a candidate that misled the user outranks one that merely burned tokens. Two candidates that are one cost counted twice — the layout that created the conflicts and the step that decided whose window paid for them — rank upstream first, and say in the body that fixing either alone leaves the other. Where the user asked a question, answer it in a line above the list; severity order and the order that answers the user are rarely the same order, and the list keeps severity. Say what you found and skip the categories that had nothing in them: those categories are broad enough to furnish a plausible candidate for any session on earth, and a padded list costs them more than a short one, because they act on it.

   An environment with nothing wrong in it is a real result, and a session can run far over budget while producing none. When the cost traces to how the user drove the session — several tasks sharing one window, parallel sessions competing for one budget, an ask that arrived in pieces — report it under a heading of its own, **Git gud!**: the measured peak, what it was spent on, and the cut the user should have made. Name the row the cut belonged at and which shape in **Task boundaries** it was — a cut that names a row is one the user can act on, where "split your tasks" is one the user cannot. It is a finding about the user rather than a candidate for an edit, so it carries no number and no live/already-fixed mark, and when the environment was clean it stands alone.

   Mark each one:

   - **live** — the condition is still on disk and the next session meets it unchanged.
   - **already-fixed** — repaired since, whether by the user or by the session itself in its closing rows. It still belongs on the list: the user is asking because the fix is in doubt, so open the replacement and say whether it holds.
   - **regression-risk** — the symptom is gone but nothing stops it returning, because what fixed it was a one-off act rather than a standing rule. A file deleted by hand that the next run recreates, a mistake the agent happened to avoid the second time. Say which rule would make it stick; that rule is the edit. A standing rule that the session's own record shows failing more than once has already earned this mark: prose that lost three times loses a fourth, and the edit is a check that fires rather than a sentence that asks.

   The marks are per-candidate, so one condition repaired in one file and still live in another is **two candidates**, split and marked separately. Fudging a single mark across both hides the half they can still act on.

   Only **live** and **regression-risk** are worth an edit.

   Then ask which ones to act on. The user answers with numbers. For each one the user picks, show the diff, wait for the user's go-ahead, apply it, and move to the next.

   A candidate that edits **global** scope — `~/.claude/CLAUDE.md`, or the memory directory of the project the user works out of most, `C--Users-User` — reaches every future session, so say so when you present it. One session is thin evidence for a global rule, so find the repeat before proposing one: `grep -l` the symptom's own string — the error text, the flag, the filename — across `~/.claude/projects/*/*.jsonl`, which costs one call and names every session that hit it. Cite those sessions, or mark the candidate project-scoped instead.

## Reference

### Task boundaries

A **task** is one thing the user wanted done, running from their ask to the deliverable. Three tests find its edge, sharpest first:

- **Context reset**: could the window be cleared at this row without losing anything the rows after it need? The budget measures what has to be carried together rather than how much work was done, so this is the test it answers to.
- **Dependency**: does the new ask consume the previous deliverable? `grill-me`, then `to-spec`, then `to-ticket` is one task across many turns, not three — each step eats the one before it, where an "oh, another thing" ask eats nothing.
- **Deliverable**: count the artifacts the user wanted, not the turns spent reaching them. Eight tickets written in one pass are one deliverable.

Two shapes cross the budget, and they earn different advice:

- **Several tasks in one window**: the later task opened carrying the earlier one. The cut belongs at the row where the context-reset test passes.
- **One task too big for a window**: it started clean and crossed anyway. The deliverable itself needed splitting, so the cut belongs upstream in whatever scoped the work — and since the work is already closed by the time this skill runs, it is advice for the next one rather than an edit.

### Files

These are the steering files on this machine, in the order a candidate should prefer them:

- `<project>/CLAUDE.md`: pushed to the context window of any agent working in that project. Use incredibly sparingly, usually only for **navigation pointers** to other files.
- Any file the project's workflow opens unconditionally, whatever it is called — a `NOTES.md` read in full at the top of every session carries `CLAUDE.md`'s cost while escaping its discipline. Hold it to the same bar, and split the part every session needs from the part reached by a pointer.
- `<project>/CODING_STANDARDS.md`: read by the review agent, which receives a diff and carries the least **context pressure**, where the implementation agent carries the most — so a **Coding standards** candidate lands here rather than in a steering file the implementation agent pays for on every session. Add **navigation pointers** to docs folders if it grows past 1,000 lines.
- Docs in the project: reference files reached by a **navigation pointer** from another file, so they cost nothing until something points at them. Look for an existing doc to extend before writing a new one.
- `~/.claude/CLAUDE.md`: the same, for every project at once. The bar is higher in proportion.
- `~/.claude/projects/<project>/memory/`: one fact per file, indexed by `MEMORY.md`, loaded by relevance rather than always. Prefer it over global `CLAUDE.md` for anything that only some sessions need. Each project directory carries its own; write to the one belonging to the project the session ran in, which the `--day` listing names. `C--Users-User` is the user's home directory, so its memory reaches most sessions.
- `~/.claude/skills/`: use skills for docs (since their description goes into the agent's context window), or for user-invoked commands. Follow the advice in the `writing-for-agents` skill.
- `~/.claude/settings.json`: hooks, permissions, environment. The **automated checks** category usually lands here, as a `PreToolUse` matcher that denies the shape of the mistake and names the tool to use instead. Its `deny` list is also where a **skills that steered wrong** candidate gets confirmed: a skill naming a tool that sits in `deny` describes a machine the user no longer has.
- `~/.claude/hooks/`: the scripts `settings.json` fires. A hook that writes something the agent later reads belongs to **Information access**, and the bug is usually in the script rather than in the settings entry.
