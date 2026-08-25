---
name: automating-afk-agent-queues
description: Guides wiring AFK (away-from-keyboard) coding agents to a task
  queue so they run on events, not an idle loop. Use when the user wants to
  run Claude Code automatically on GitHub issues/PRs, set up a GitHub Actions
  agent, schedule a cloud routine that fixes or reviews code, or decide between
  running agents manually, via subagents, or in CI. Covers the queue-not-loop
  model, label-as-marker vs trigger, why setup-matt-pocock-skills does not
  create the runner, the manual to subagent to CI ladder, fresh-context-per-
  issue to avoid bloat, and the cost model. Triggers on "GitHub Actions agent",
  "run agent AFK", "cloud routine", "ready-for-agent", "agent ตอนนอน",
  "รัน agent อัตโนมัติ", "queue driven agent".
disable-model-invocation: true
---

# Automating AFK Agent Queues

Wire coding agents to a queue so they run when work arrives, never on a
blind timer. The goal is AFK (away-from-keyboard) throughput without context
bloat or wasted token spend.

## Core principle: queue, not loop

Model the work as a **queue of independent tasks**, not a single
`while(true)` loop.

- A time-loop (re-run the same prompt every N seconds) bloats one context
  window across tasks and pays the provider while idle. Avoid it.
- A queue runs a **fresh agent per task**, triggered by an event (a label,
  a webhook, a new issue). It is idle-cheap and context-clean.

Each task starts a **new agent run with its own context** — this is what
prevents the bloat that `/loop /implement` causes.

## Pick the rung (default: start manual)

Choose the lowest rung that meets the need; climb only when it hurts.

1. **Manual — one session per issue** (default). Open a fresh session,
   `/implement <issue>`, review, close. Climb when opening/closing by hand
   becomes the bottleneck.
2. **Subagent fan-out.** A lead session dispatches one subagent per
   independent issue; each subagent holds its own context and returns only a
   summary. Use for parallel work that still runs on the local machine.
3. **CI / cloud (true AFK).** A GitHub Action or scheduled cloud routine runs
   the agent unattended, including while asleep. Use when the machine must be
   free and runs must survive logout.

## What setup-matt-pocock-skills does NOT do

Running `/setup-matt-pocock-skills` scaffolds **config only**: the issue
tracker location, the triage label vocabulary (`needs-triage`, `needs-info`,
`ready-for-agent`, `ready-for-human`, `wontfix`), and the domain-doc layout.

It writes `docs/agents/*.md` and a `CLAUDE.md` block. It creates **no**
`.github/workflows/` file and **no** runner.

The `ready-for-agent` label is a **marker** ("an agent could pick this up"),
not a **trigger**. Nothing acts on it until a runner is built. Confirm this
distinction before promising automation.

## Wire a GitHub Action (rung 3a)

1. In the repo, run `/install-github-app` from Claude Code in the terminal —
   it installs the GitHub app and stores the credential secret. Confirm the
   secret exists in repo Settings before continuing.
2. Add `.github/workflows/agent.yml` that triggers on the marker label:

   ```yaml
   on:
     issues:
       types: [labeled]
   jobs:
     implement:
       if: github.event.label.name == 'ready-for-agent'
       runs-on: ubuntu-latest
       permissions:
         contents: write
         pull-requests: write
         issues: read
       steps:
         - uses: actions/checkout@v4
         - uses: anthropics/claude-code-action
           with:
             anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
             prompt: |
               Implement the issue ${{ github.event.issue.html_url }}.
               Open a pull request when done. Do not merge it.
   ```

   Pin the action to its current major version as shown by
   `/install-github-app`; do not invent a tag.
3. The prompt mode runs headless and opens a PR. Verify the run produced a PR
   that closes the issue, then review it before merge.

## Schedule a cloud routine (rung 3b)

For time-based sweeps (not event-based), use the `/schedule` skill to create
a cron cloud routine — e.g. a daily security pass over one part of the repo.
Keep the cadence matched to real change; a routine that runs while nothing
changed only burns tokens. Confirm the routine appears in the schedule list.

## Cost model

- **GitHub Actions minutes** — public repos: unlimited free. Private repos:
  a monthly free tier, then per-minute billing. Rarely the dominant cost.
- **Token spend** — the dominant cost, and identical wherever the agent runs.
  CI does not make tokens cheaper; it makes runs easier to multiply, so cost
  rises with run frequency and parallelism. Gate the trigger (a label or a
  matched-cadence cron), never an always-on loop.
- **Sandbox/compute** — local Docker is free; remote sandboxes bill compute.

## Keep a review checkpoint

Push human-review checkpoints toward production over time, but do not remove
the last one blindly: review both gates danger and feeds insight back into
the harness. When an agent auto-decides "no review needed", spot-check a
sample of those to keep the auto-decider honest.

## Anti-patterns

- `/loop /implement` in one session — bloats context, the idle-loop trap.
- Expecting `/setup-matt-pocock-skills` to run agents — it only configures.
- Hardcoding a stale action version instead of what `/install-github-app`
  scaffolds.
- A cron routine that runs regardless of whether work exists.
