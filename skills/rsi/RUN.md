# RSI run (unattended)

Zen is away. You are the **orchestrator**: the hands of the run (edit, check, measure, ratchet). The **advisor** is the run's memory and judgment; it holds every dead end so your context stays clean. You read the contract and the ledger tail; the advisor file is the advisor's to read.

The run has two ways to pause and one way to end:

- **Waiting on the advisor**: when the ASK's tool result already carries the answer, act on it in the same turn. End the turn only while the answer is still pending; its arrival resumes the run.
- **STOP**: a `STOP: <reason>` row as the last ledger line, then the report. This is the only ending.

Every other moment flows straight into the next action in the same turn; a ledger row is a waypoint.

## 0. Load

1. Read the contract in full and the last 5 ledger rows.
2. Verify: cwd is the contract's worktree, branch is `rsi/<feature>`, `git status` is clean. If any of these fails, write `STOP: setup-mismatch` with what you saw, and end.
3. Best = the median of the latest `keep` or `rebaseline` row (row 0 if none).
4. If the advisor file's bottleneck map is empty, profile first: find where the metric's time (or loss) actually goes, using the language's profiler or targeted timing. Keep the findings, and excerpts of the code at the top of the profile, for the first ASK.
5. Spawn the advisor (see [Advisor](#advisor)) with the profile findings and those excerpts as its first ASK, and wait.

## 1. Iterate

Take hypotheses from the front of the **queue** (the advisor's latest answer). Each iteration, in order:

1. **Clock**: run `date`. At or past the deadline, or at max iterations, go to STOP.
2. **Queue**: if empty, ASK for the next queue and wait. To try your own idea, put it in the ASK as a proposal; it runs once the advisor queues it.
3. **Edit** files inside scope to apply the hypothesis.
4. **Scope guard**: every path in `git status --porcelain` (which also lists new untracked files, such as a cache the code wrote) is inside scope or `progress/`. A path outside them gives verdict `out-of-scope`. Run it again after measure, since code can write files while it runs.
5. **Check**: run it. Failure gives verdict `fail-check`.
6. **Measure**: run measure N times; take the median.
7. **Ratchet**:
   - Gain beyond the noise band: append the ledger row, then commit the scope changes plus `progress/` with the hypothesis as the message. Best = this median. Verdict `keep`.
   - Otherwise: `git restore -- <scope paths>`, append the ledger row with the reason in the hypothesis cell, commit `progress/` alone. Verdict `revert`, `fail-check`, or `out-of-scope`.
   Restore only scope paths, so the ledger, contract and advisor file survive every revert.
8. **Ceiling**: best at or beyond target goes to STOP with reason `ceiling`.
9. **Every 10 iterations**: re-measure the committed best N times. If its median has drifted beyond the noise band, write a `rebaseline` row with the new median and band, and use them from here on.
10. Begin the next iteration.

## 2. Plateau: escalate

P consecutive non-keep rows (counted since the last `keep` or `escalate` row) start the escalation ladder, one rung per plateau, each logged as an `escalate` row:

1. **Re-profile**, then ASK with the new profile and the word `plateau`.
2. ASK for **structural** hypotheses only (algorithm, data layout, batching, caching strategy).
3. **Fresh advisor**: respawn it from its file, so new eyes read the whole history, and ASK with `plateau`.

After the third rung, a further plateau follows the contract: `stop` goes to STOP with reason `plateau`; `continue` restarts the ladder at rung 1.

## 3. STOP

1. Append `STOP: <reason>` to the ledger.
2. ASK the advisor for a final write of its file, the three hypotheses it would try next, and its Transferable lessons; wait.
3. Fill the contract's Report section: baseline, best, target, remaining gap in %, kept commits (hash + hypothesis), the advisor's next hypotheses, and its Transferable lessons under a heading "For zen to place in repo docs".
4. Commit `progress/` with the message `rsi(<feature>): run record`. This commit is the permanent record of the run.
5. Clean up: `git rm -r` the contract, the ledger, and the advisor file, then commit `rsi(<feature>): clear run files`. The branch now differs from its base only in scope paths, ready to merge.
6. End with the report as your final message, followed by: the record commit's hash (`git show <hash>:progress/...` reads the run files back), the merge command for `rsi/<feature>`, and `git worktree remove <worktree>` for after the merge.

Done when `git status` is clean, `progress/` holds no file of this run, and the final message carries the report, the record hash, and both commands.

## Advisor

**Spawn** a `general-purpose` subagent with this prompt, using absolute paths:

> You are the advisor for an RSI run. Read `<this skill's folder>/ADVISOR.md` and follow it. Contract: `<path>`. Ledger: `<path>`. Advisor file: `<path>`. First ASK: `<message>`

**ASK** later with `SendMessage` to the same advisor. An ASK carries what the advisor cannot read in the files: the current best, your proposal or question, new profile findings, and **code excerpts**: the functions at the current bottleneck (and any the advisor's last `note` asked for), trimmed to the lines that matter, each headed with its path and line range. The advisor sees only the code you attach. Its answer is a short `queue` / `avoid` / `note` block. Reply with a follow-up question whenever an answer leaves you unsure: a conversation of several turns is normal.

**Respawn** (a new advisor, same prompt, its file as memory) when:
- the advisor is unreachable, or you lost track of it after a compaction;
- ladder rung 3;
- every 50 iterations, to keep its context lean.

Before a planned respawn, ASK the old advisor to write its file first.
