---
name: rsi
disable-model-invocation: true
description: Run an RSI optimisation loop on one feature. First call sets up a contract with zen; a fresh session in the worktree then ratchets the metric toward the ceiling unattended.
---

# RSI: ratchet one metric toward its ceiling

RSI here is **one task looped**: a single feature, a single metric, iterated in one long session until a stop condition.

## Pick the branch

Look for `progress/rsi-*.md` in the current repo.

- **No contract**, or zen names a new feature: read [`SETUP.md`](SETUP.md) and follow it. Setup runs with zen present and ends at hand-off.
- **A contract exists** and the cwd is its worktree: read [`RUN.md`](RUN.md) and follow it. The run is unattended.
- A contract exists but the cwd is elsewhere: print the worktree path and the start command from the contract, then end.

## Leading words

- **ceiling**: the practical best value for the metric. The **target** is the ceiling plus the tolerance zen accepts (e.g. "within 3% of practical").
- **baseline**: the metric measured N times before any change. Its median is the first **best**.
- **noise band**: max minus min of the N baseline runs. A change counts as a gain only when it beats best by more than the noise band.
- **tight**: the measure command prints one number on its last line, finishes in seconds to a few minutes, and gives the same result on unchanged code.
- **check**: the correctness gate (tests or a golden-output diff). Every candidate passes check before it is measured.
- **scope**: the paths the loop edits. **frozen**: the paths it reads but leaves untouched (the measure script, benchmark inputs, check's tests). Anything outside scope is frozen by default.
- **bottleneck**: the part that dominates the metric, found by profiling. Hypotheses aim at the current bottleneck (Amdahl).
- **ratchet**: a candidate that passes check and gains beyond the noise band is committed; every other candidate is reverted. Best only ever improves.
- **ledger**: the append-only record of every iteration, dead ends included.
- **dead end**: a hypothesis that was tried and reverted, with the reason. Dead ends are never retried in the same form.
- **plateau**: P consecutive iterations with no kept change.
- **orchestrator**: the run session; it edits, checks, measures, ratchets, and writes the ledger.
- **advisor**: a subagent the orchestrator converses with; it owns the run's memory (dead ends, what worked, the bottleneck map) and answers with a queue. Its role lives in [`ADVISOR.md`](ADVISOR.md).
- **queue**: the up-to-three ranked hypotheses in the advisor's latest answer. The orchestrator runs only queued hypotheses.

## Files

All three live in the worktree under `progress/` and are committed on the RSI branch while the run lasts (use `git add -f` if `progress/` is gitignored). Only the contract sits at the top of `progress/`: the post-compaction re-read of `progress/*.md` loads the small contract alone, while the ledger and advisor file sit in subfolders. After STOP, a clean-up commit removes all three (RUN.md, STOP), so a merge of the branch carries only scope changes.

### Contract: `progress/rsi-<feature>.md`

Small, re-read in full after every compaction.

```markdown
# RSI contract: <feature>

- metric: <name> (<unit>), <lower|higher> is better
- measure: `<command>`  (runs: N=<5>)
- check: `<command>`
- scope: <paths>
- frozen: <paths>
- ceiling: <practical value>  (from: <ideal value / reasoning>)
- tolerance: <3%>  → target: <number>
- baseline: median <x>, noise band <y>  (measured <date>)
- deadline: <YYYY-MM-DD HH:MM local>
- max iterations: <n>
- plateau: P=<5>; on plateau after escalation: <continue|stop>
- worktree: <absolute path>, branch rsi/<feature>
- start: `cd <worktree>` then `claude`, then `/rsi`

## Report
<!-- written at STOP -->
```

### Ledger: `progress/ledger/rsi-<feature>.md`

Append one row per iteration; read only its tail.

```markdown
| # | time | hypothesis | check | median | Δ vs best | verdict |
|---|------|------------|-------|--------|-----------|---------|
| 0 | <time> | baseline | pass | <x> | 0 | baseline |
```

Verdicts: `keep`, `revert` (no gain beyond noise), `fail-check`, `out-of-scope`, `rebaseline`, `escalate`, and the final row `STOP: <ceiling|deadline|max-iterations|plateau|setup-mismatch>`.

### Advisor file: `progress/advisor/rsi-<feature>.md`

The advisor's memory, written only by the advisor; its shape lives in `ADVISOR.md`. The orchestrator reaches its contents through the advisor's answers.
