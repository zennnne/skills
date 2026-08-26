---
name: auditing-claude-md
description: >
  Audit an existing CLAUDE.md file and classify each block into: keep, shrink,
  move-to-skill, or cut. Applies the minimal-CLAUDE.md principle: only content
  the agent genuinely cannot discover for itself belongs here, and reference
  that is wanted but bulky moves down behind a pointer rather than out. Surveys
  hooks, existing skills, and inbound references first, then proposes each
  change with pros/cons, collects approvals, and applies them in one pass. Use
  when the user asks to review, trim, or evaluate their CLAUDE.md, check for
  rot, or reduce per-request token cost. User must invoke explicitly — never
  auto-runs.
  Keywords: audit claude.md, review claude.md, trim claude.md, claude.md bloat,
  init cleanup.
disable-model-invocation: true
---

# Auditing CLAUDE.md

Call the Skill tool with `writing-for-agents` before Phase 1 (it lives in the
`mattpocock-skills` plugin; if the bare name does not resolve, try
`mattpocock-skills:writing-for-agents`). Three of its levers do the work here:

- **Context load** — every kept line is paid on every turn, whether it fires or not.
- **Progressive disclosure** — reference belongs behind a pointer, not inline.
  This is what the **Shrink** bucket exists to apply.
- **Pruning** — duplication, caches of the environment, and no-ops come out.

Four phases: survey, classify all content, get per-item approval, then apply.

## Phase 0 — Survey before classifying

Two of the cut criteria below are undecidable from CLAUDE.md alone, and a cut
made without the surrounding facts silently breaks other files. Gather first.

1. **Pick the file and its scope.** Audit the path given as an argument;
   with no argument, audit `CLAUDE.md` in the working directory. A file under
   `~/.claude/` is **global scope** — its skills dir is `~/.claude/skills/`. A
   file at a project root is **project scope** — `.claude/skills/`. Record which.
2. **Back up.** Copy the file to `CLAUDE.md.bak` beside it. The target is often
   hand-curated and often not in git.
3. **Measure the baseline.** Record `wc -l` and `wc -m` (characters). Report
   characters, not bytes — `wc -c` inflates the reduction on any non-Latin file,
   because cut material skews more ASCII than kept material.
4. **Read the environment the audit judges against:** `settings.json` /
   `settings.local.json` for hooks, every `SKILL.md` frontmatter in the scope's
   skills dir, the directory layout, and any memory index loaded each session.
5. **Grep the repo for inbound references to each section** — by name and by
   ordinal. A rule cited elsewhere as "rule 3" is load-bearing: cutting any
   earlier item in that list renumbers it and breaks the citation silently.

**Done when** scope, backup, baseline numbers, the hook list, the existing skill
list, and the inbound-reference map are all in hand.

## Phase 1 — Classify every block

Classify each logical block (line or group of related lines) into one of four
buckets. Structural lines — blank lines, `---` rules, a heading whose section
survives — count with the block they enclose; a heading whose content all leaves
goes with it.

Done when **every block of CLAUDE.md is in exactly one bucket**.

On top of its bucket, a block earns a **rot flag** if it names a specific file
path, function name, count, or version number — these go stale the moment the
code changes, so a rot-flagged block leans toward cut, or toward **Shrink** as a
principle that references no specifics.

### Cut — remove entirely

Remove if ANY of the following is true:

- **Discoverable from code** — a cache of what the environment already states:
  package.json scripts, architecture readable from folder structure or imports,
  tech stack in config files, patterns already present in the code. In a project
  with no code, the equivalent sources are the spec file that owns the detail,
  the directory listing, and the dated decision record.
- **Redundant with hooks** — duplication of what a hook already enforces
  deterministically. Decide this against the hook list from Phase 0.
- **Already owned by a skill** — an existing `SKILL.md` states this. Moving it
  would create a third copy; cut it and let the skill own it.
- **Meta-commentary** — lines explaining what the file itself is for.
- **Use-case-specific in global scope** — one task type's material (frontend,
  DB, testing) paying context load on every request.

A block with an inbound reference is not cut until the referring file is fixed
in the same pass, or the block is shrunk instead.

### Shrink — keep the meaning, disclose the detail

Shrink when the block is wanted but its detail belongs one rung down: the
authoritative version lives in another file, or could, and CLAUDE.md needs only
enough to fire the pointer. This is the disposition for a rot-flagged block
worth keeping — rewrite it as a principle naming no specifics.

State the replacement text. Front-load the leading word, name the condition that
should send the agent to the target, and drop identity the target already carries.

### Move to skill

Move when the block is:

- Steering toward a best practice, preferred library, or coding pattern.
- A how-to procedure only needed during a specific workflow.
- A "always use X, not Y" reminder that applies only to certain task types.

Propose a skill name and a one-line trigger description.

### Keep

Keep what the agent **cannot discover** through exploration:

- Environment quirks invisible in code (WSL, unusual paths, OS constraints).
- Hard constraints imposed externally (compliance, infra rules).
- Universal behavioral overrides tuned through experience that apply to every
  task type without exception.

Keep two further classes even though a fuller copy exists elsewhere:

- **Context pointers** — a line whose job is to name out-of-context material and
  encode when to reach it. Its value is in its wording, not its content.
- **Deliberate duplication where failure is expensive** — a rule the user
  identifies as non-negotiable earns its always-loaded cost.

---

## Phase 2 — Per-item approval

Present every non-keep item as one numbered list in a single message, then wait
for the user's picks in a single reply. Use the `AskUserQuestion` tool only if it
is both present **and** permitted — on many setups it exists but sits in
`permissions.deny`, so text is the working path, not the fallback.

For each item show:
- The original text
- Proposed action (cut / shrink to `<new text>` / move to skill `<name>`)
- **Pro:** why doing this improves things (token savings, rot prevention, etc.)
- **Con:** what is lost or risked if this is removed, including any inbound
  reference found in Phase 0

Options to offer — the proposed action, plus every other bucket that applies:
- **Apply as proposed**
- **Keep it** — leave this block in CLAUDE.md as-is
- **Shrink instead** — keep the meaning, disclose the detail
- **Move to skill instead** — extract to a skill
- **Cut instead** — just delete it

Collect all answers before making any file changes.

---

## Phase 3 — Apply approved changes

After all items are answered, apply in one pass:

1. Edit CLAUDE.md — remove approved cuts, replace approved shrinks with their
   new text, and remove moved blocks.
2. Fix every inbound reference the change breaks: repoint files that named a
   moved block, and renumber citations to any numbered list that lost an item.
3. For each approved "move to skill" — create `<skills-dir>/<name>/SKILL.md`,
   where `<skills-dir>` is the one recorded in Phase 0. The directory name and
   the frontmatter `name:` must match. Write it **model-invoked** — omit
   `disable-model-invocation` and give it a description carrying its trigger
   branches — so the agent reaches it on its own when that task type comes up.
   Prune it against `writing-for-agents` and give each step a completion
   criterion.
4. Report a summary:
   - Blocks cut: N (M lines)
   - Blocks shrunk: N (M lines to K lines)
   - Blocks moved to skill: N (list skill names and paths)
   - Blocks kept: N
   - Inbound references repaired: N (list the files)
   - Size reduction: the Phase 0 baseline and the new `wc -l` / `wc -m`, with
     the percentage and the unit named.

---

## Instruction budget reminder

Every line in CLAUDE.md spends from a finite instruction budget on every
request, whether or not it is relevant to that request. The bar for the Keep
bucket: the agent cannot function correctly without this and cannot find it on
its own — or the line is a pointer whose whole job is to send the agent
somewhere else.
