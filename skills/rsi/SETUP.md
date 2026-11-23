# RSI setup (zen present)

Setup turns a feature into a contract the unattended run can trust. Everything that can fail at 2am (a flaky measure, a failing check, a missing worktree) fails here instead, while zen can answer.

## 1. Fit check

RSI needs a metric a command can measure. If the feature has no such number (the goal is "nicer code" or "better UX"), tell zen this is a design task rather than RSI, and end.

Done when: zen agrees the feature has a numeric metric with a direction.

## 2. Interview

Ask one question at a time in plain text, each with your recommended answer drawn from reading the repo, and wait for zen's reply before the next. Cover every contract field in [`SKILL.md`](SKILL.md):

- metric and direction
- measure command (propose one; it must be **tight**)
- check command
- scope and frozen paths
- ceiling: ask for the ideal (hardware limit, theoretical bound) and agree a practical value plus tolerance
- deadline and max iterations (recommend a 30-minute deadline for the first run on a new repo: a tracer run)
- plateau P and on-plateau behaviour (recommend `continue`, so the run uses the time zen gave it)

Done when: every field has an answer zen confirmed.

## 3. Worktree

Confirm the main checkout is clean, then:

```bash
git worktree add ../<repo>-rsi-<feature> -b rsi/<feature>
```

Confirm the path with zen before creating it. All remaining steps run inside the worktree.

Done when: the worktree exists on branch `rsi/<feature>`.

## 4. Baseline in the run environment

Inside the worktree:

1. Run check. It passes on unchanged code; if it fails, fix the command with zen.
2. Run measure N times. Record the median and the noise band.
3. Judge tightness: the noise band is smaller than the gap between baseline and target, and each run parses to one number. If not, tighten the measure with zen (more repetitions inside the command, a fixed input, a warm-up run) and repeat.
4. Compute the target from ceiling and tolerance, and show zen the gap: baseline vs target.

Done when: check passes, N measurements parse, the noise band is narrower than the gap, and zen has seen the numbers.

## 5. Write and commit

Write the contract and the ledger (row 0 = baseline) from the templates in `SKILL.md`, and the advisor file from the shape in [`ADVISOR.md`](ADVISOR.md) with `last ledger row read: 0` and empty sections. Commit all three on the RSI branch.

Done when: `git log -1` on `rsi/<feature>` shows the contract, ledger and advisor file.

## 6. Hand-off

Give zen:

- the machine checklist: plugged in, sleep disabled until the deadline, heavy background jobs (backups, sync) paused if they skew timings
- the permission check: the run session starts in a mode where measure, check, `git commit`, `git restore` and spawning the advisor all run without a prompt (zen's default is `auto`); the first tracer run confirms it
- the exact start lines from the contract's `start` field

Setup ends here. The loop belongs to the fresh session zen starts in the worktree, so its context holds only the contract.
