# skills

Claude Code skills I actually use day to day — some written from scratch, some adapted from other people's work until they fit my hands.

Each skill is a folder containing a `SKILL.md` (frontmatter `name` + `description`, then the steps). Some also ship `reference.md` / `examples.md` / `templates.md`, kept separate so they're only loaded when actually needed.

## Install

Copy just the ones you want into your own skills directory:

```bash
git clone https://github.com/zennnne/skills.git
cp -r skills/skills/deep-research ~/.claude/skills/
```

- **Global** → `~/.claude/skills/<name>/SKILL.md`
- **Per project** → `<project>/.claude/skills/<name>/SKILL.md`

Claude picks a skill up on its own based on its `description`, or you can invoke it directly with `/<skill-name>`.

## Skills

The **Source** column marks skills that are vendored or adapted from someone else's repo. Anything marked "own" I wrote myself.

### Coding

| Skill | What it does | Source |
|---|---|---|
| [`implement-spec`](skills/implement-spec/SKILL.md) | Implement a specification in code. | own |
| [`karpathy-guidelines`](skills/karpathy-guidelines/SKILL.md) | Behavioral guidelines to reduce common LLM coding mistakes. | [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) |
| [`find-standards`](skills/find-standards/SKILL.md) | Find how this problem is already solved: standards we could adopt, and the industry's best practices. | [will-ness-ai/skills](https://github.com/will-ness-ai/skills) |
| [`flashlight`](skills/flashlight/SKILL.md) | Shine a light into a wayfinder map's fog — work one direction now, out of frontier order, or redraw the map itself. | [will-ness-ai/skills](https://github.com/will-ness-ai/skills) |
| [`grilling-frontend-prototyping`](skills/grilling-frontend-prototyping/SKILL.md) | Converge on a frontend look through rounds of prototypes and grilling verdicts. | [will-ness-ai/skills](https://github.com/will-ness-ai/skills) |
| [`using-git-worktrees`](skills/using-git-worktrees/SKILL.md) | Make sure an isolated workspace exists, via native tools or a git worktree fallback — use it when starting feature work that has to stay separate from the current workspace. | [obra/superpowers](https://github.com/obra/superpowers) |
| [`finishing-a-development-branch`](skills/finishing-a-development-branch/SKILL.md) | For when the implementation is done and tests pass, and you have to decide how to merge / PR / clean up. | [obra/superpowers](https://github.com/obra/superpowers) |

### Research & writing

| Skill | What it does | Source |
|---|---|---|
| [`deep-research`](skills/deep-research/SKILL.md) | Multi-pass research: interview first to narrow the scope, then fan out sub-agents to dig into each sub-question in parallel, and finish by synthesizing everything into the knowledge base. | own |
| [`extracting-youtube-transcript`](skills/extracting-youtube-transcript/SKILL.md) | Pull the full transcript of a YouTube video through Playwright MCP (click "Show transcript", then read the panel). | own |
| [`code-story`](skills/code-story/SKILL.md) | Build a wizard-style HTML page that teaches how and why a change works. | [will-ness-ai/skills](https://github.com/will-ness-ai/skills) |
| [`applying-3-act-structure`](skills/applying-3-act-structure/SKILL.md) | Use three-act structure (Setup / Confrontation / Resolution) to plan or diagnose a narrative — fiction, screenplay, content. | own |
| [`report-thai-business`](skills/report-thai-business/SKILL.md) | Turn internal-audit / risk writing from English into Thai that a client executive can accept as-is, with no editing. | own |

### Claude Code housekeeping

These are tied to my personal setup (`~/.claude/session_log/YYYY/MM/`, memory layout, plugin marketplace) — feel free to take them, but fix the paths to match yours first.

| Skill | What it does | Source |
|---|---|---|
| [`auditing-claude-md`](skills/auditing-claude-md/SKILL.md) | Audit an existing CLAUDE.md and sort every block into keep / shrink / move-to-skill / cut. | own |
| [`test-a-skill`](skills/test-a-skill/SKILL.md) | Field-test a skill — run it live in an agent session with no context, then fix whatever it tripped over. | [will-ness-ai/skills](https://github.com/will-ness-ai/skills) |
| [`session-summary`](skills/session-summary/SKILL.md) | Fill the placeholders in the daily session log by reading and summarizing that session's `.jsonl` transcript. | own |
| [`session-index`](skills/session-index/SKILL.md) | Build a monthly table of contents — title / date / status / mistake count for every session that month, as one table. | own |
| [`cleaning-sessions`](skills/cleaning-sessions/SKILL.md) | Delete transcripts (JSONL) and tool-result folders older than N days to reclaim disk space. | own |
| [`updating-plugins`](skills/updating-plugins/SKILL.md) | Update every plugin to the latest version, discovering the plugins itself from `settings.json`. | own |
| [`automating-afk-agent-queues`](skills/automating-afk-agent-queues/SKILL.md) | How to wire an AFK coding agent to a task queue so it works off events instead of spinning in an idle loop. | own |

## Notes

- A few skills ship an `agents/openai.yaml` folder alongside them — that's an export for other agent runners and isn't needed to use them with Claude Code.

## Installed as plugins, not vendored here

Two skill sets I use are installed whole as Claude Code plugins, so they don't live in this repo — install them from their marketplace instead of copying folders:

| Plugin | Skills | Where from |
|---|---|---|
| `9arm-skills` | `debug-mantra`, `post-mortem`, `scrutinize`, `management-talk` | [thananon/9arm-skills](https://github.com/thananon/9arm-skills) |
| `mattpocock-skills` | `writing-for-agents`, `tdd`, `code-review`, `diagnosing-bugs`, `research`, `domain-modeling`, `codebase-design`, `grilling`, `prototype`, `wizard`, `resolving-merge-conflicts` | [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) |
