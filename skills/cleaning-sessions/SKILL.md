---
name: cleaning-sessions
description: Deletes Claude Code session transcript files (JSONL) and their tool-result spill directories older than a user-chosen number of days, freeing disk space. Use when accumulated sessions are taking up disk, or during periodic housekeeping. User must invoke explicitly — never auto-runs. Triggers on "clean sessions", "delete old sessions", "clear session history", "purge old conversations", "remove old transcripts", "ล้าง session", "ลบ session เก่า", "เคลียร์ session".
disable-model-invocation: true
argument-hint: "[days]"
allowed-tools: "PowerShell AskUserQuestion"
---

# Cleaning Sessions

Removes Claude Code session JSONL files **and their matching tool-result spill directories** older than **N days** from the Claude config directory. Frees disk space without touching memory files, skills, or settings.

## What gets deleted

- `~/.claude/projects/<project-dir>/<session-uuid>.jsonl` — session transcripts
- `~/.claude/projects/<project-dir>/<session-uuid>/` — the matching **spill directory** (holds `tool-results/` overflow files). These are the bulk of on-disk weight and become dead weight once the transcript is gone.
- **Orphaned** spill directories — a `<session-uuid>/` dir whose `.jsonl` transcript no longer exists (already cleaned in a prior run), older than N days.
- All filtered by `LastWriteTime` older than N days.

## What is preserved

- `memory/` subdirectories and all `.md` files — **never** matched, because deletion targets only directories whose name is a valid session UUID.
- `settings.json`, `CLAUDE.md`, skills, `history.jsonl`, `file-history/` snapshots.

---

## Workflow

### Step 1 — Resolve N days

If `$days` argument was passed, use it. Otherwise ask the user how many days (suggest **30** — keeps ~1 month of history while reclaiming older storage).

### Step 2 — Scan (dry run)

```powershell
$claudeDir  = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { "$env:USERPROFILE\.claude" }
$projectsDir = Join-Path $claudeDir "projects"
$cutoff = (Get-Date).AddDays(-[int]$days)
$uuid = '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'

# 1. Old transcript files
$jsonl = Get-ChildItem -Path "$projectsDir\*\*.jsonl" -File -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -lt $cutoff }

# 2. Spill directories — ONLY those whose name is a session UUID (protects memory/ etc.)
$dirs = Get-ChildItem -Path "$projectsDir\*\*" -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match $uuid -and $_.LastWriteTime -lt $cutoff }

# Size of a spill dir = sum of its files, recursively
$dirBytes = ($dirs | ForEach-Object {
    (Get-ChildItem $_.FullName -Recurse -File -ErrorAction SilentlyContinue |
        Measure-Object -Property Length -Sum).Sum
} | Measure-Object -Sum).Sum

$jsonlBytes = ($jsonl | Measure-Object -Property Length -Sum).Sum
$totalKB = [math]::Round(($jsonlBytes + $dirBytes) / 1KB, 1)

Write-Output "Transcripts to delete : $($jsonl.Count) files"
Write-Output "Spill dirs to delete  : $($dirs.Count) dirs"
Write-Output "Total to free         : $totalKB KB"
```

Report the counts and size. If both counts = 0, tell the user nothing to delete and stop.

### Step 3 — Confirm

Ask the user to confirm deletion of **$($jsonl.Count) transcript(s) + $($dirs.Count) spill dir(s)** ($totalKB KB). Stop if they cancel.

### Step 4 — Delete

```powershell
$jsonl | Remove-Item -Force -ErrorAction SilentlyContinue
$dirs  | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Output "Deleted $($jsonl.Count) transcript(s) and $($dirs.Count) spill dir(s) — $totalKB KB freed"
```

---

## Platform paths

| OS | Default path |
|----|-------------|
| Windows | `$env:USERPROFILE/.claude/projects/` |
| macOS | `~/Library/Application Support/Claude/projects/` |
| Linux | `~/.config/claude-desktop/projects/` |

Override with `$CLAUDE_CONFIG_DIR` env var if set.

---

## Notes

- Never delete sessions while Claude Code is actively running in another terminal — the active session's transcript and spill dir are being written to.
- The UUID filter on directory deletion is the key safety guard: it means only `<uuid>/` dirs are ever removed, so sibling folders like `memory/` inside a project dir are structurally impossible to touch.
- Do not clean `history.jsonl` or `file-history/` snapshots — they are not session transcripts.
