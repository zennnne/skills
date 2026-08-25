---
name: auditing-claude-md
description: >
  Audit an existing CLAUDE.md file and classify each line into: keep, cut, or
  move-to-skill. Applies the minimal-CLAUDE.md principle: only content the agent
  genuinely cannot discover from the codebase itself belongs here. After
  classifying, proposes each change to the user with pros/cons, collects
  approvals, then applies all approved edits in one pass. Use when the user asks
  to review, trim, or evaluate their CLAUDE.md, check for rot, or reduce
  per-request token cost. User must invoke explicitly — never auto-runs.
  Keywords: audit claude.md, review claude.md, trim claude.md, claude.md bloat,
  init cleanup.
disable-model-invocation: true
---

# Auditing CLAUDE.md

Two-phase process: classify all content, then get per-item approval before
touching any files.

## Phase 1 — Classify every block

Read CLAUDE.md and classify each logical block (line or group of related lines)
into one of three buckets.

### Cut — remove entirely

Remove if ANY of the following is true:

- **Discoverable from code** — the agent finds it during the explore phase:
  package.json scripts, architecture readable from folder structure or imports,
  tech stack info visible in config files, patterns already present in the code.
- **Redundant with hooks** — a hook already enforces this deterministically.
- **Meta-commentary** — lines explaining what the file itself is for.
- **Use-case-specific in global scope** — info only relevant to one task type
  (frontend, DB, testing) but costs tokens on every request.

### Move to skill

Move when the block is:

- Steering toward a best practice, preferred library, or coding pattern.
- A how-to procedure only needed during a specific workflow.
- A "always use X, not Y" reminder that applies only to certain task types.

Propose a skill name and a one-line trigger description.

### Keep

Keep ONLY what the agent **cannot discover** through exploration:

- Environment quirks invisible in code (WSL, unusual paths, OS constraints).
- Hard constraints imposed externally (compliance, infra rules).
- Universal behavioral overrides tuned through experience that apply to every
  task type without exception.

### Rot flag

Flag any line containing a specific file path, function name, or version number.
These rot the moment the code changes. Recommend cutting or replacing with a
principle that doesn't reference specifics.

---

## Phase 2 — Per-item approval

After classification, present each non-keep item one at a time using
`AskUserQuestion`. Do NOT edit any file yet.

For each item show:
- The original text
- Proposed action (cut / move to skill `<name>`)
- **Pro:** why doing this improves things (token savings, rot prevention, etc.)
- **Con:** what is lost or risked if this is removed

Options to offer:
- **Apply as proposed** — accept the recommendation
- **Keep it** — leave this block in CLAUDE.md as-is
- **Move to skill instead** (only if action was cut) — extract to a skill
- **Cut instead** (only if action was move) — just delete it

Collect all answers before making any file changes.

---

## Phase 3 — Apply approved changes

After all items are answered, apply in one pass:

1. Edit CLAUDE.md — remove or trim all approved cuts and moves.
2. For each approved "move to skill" — create the skill file at
   `.claude/skills/<name>/SKILL.md` with appropriate frontmatter and body.
3. Report a summary:
   - Lines/blocks removed: N
   - Lines/blocks moved to skill: N (list skill names and paths)
   - Lines/blocks kept: N
   - Estimated token reduction: rough % of original CLAUDE.md removed

---

## Instruction budget reminder

LLMs handle roughly 300–500 instructions per request. Every line in CLAUDE.md
spends from this budget on every request, regardless of relevance. The bar for
keeping something: "the agent cannot function correctly without this, and it
cannot find it on its own during the explore phase."
