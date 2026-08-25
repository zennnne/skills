---
name: updating-plugins
disable-model-invocation: true
description: Updates all installed Claude Code plugins to latest. Discovers plugins dynamically from settings.json — works with any plugin set, no hardcoded names. Uses selective update per plugin source type. Triggers on /update-plugins, /updating-plugins, "อัปเดต plugin", "อัปเดต skill", "update plugins".
allowed-tools: "Bash PowerShell Read"
---

## Step 1 — Discover installed plugins

Enabled plugins come from `settings.json`, but marketplace sources must come from
`~/.claude/plugins/known_marketplaces.json` — that file is authoritative and lists
**all** marketplaces including built-ins like `claude-plugins-official`.
`settings.json`'s `extraKnownMarketplaces` only holds user-added ones, so built-in
marketplaces resolve to `$null` there and their plugins get silently skipped.

```powershell
$s = Get-Content "$env:USERPROFILE\.claude\settings.json" -Raw | ConvertFrom-Json

# All enabled plugins as "pluginId@marketplaceId"
$enabled = $s.enabledPlugins.PSObject.Properties | Where-Object { $_.Value -eq $true }

# Marketplace sources — authoritative list (built-in + user-added)
$markets = Get-Content "$env:USERPROFILE\.claude\plugins\known_marketplaces.json" -Raw | ConvertFrom-Json
```

For each entry in `$enabled`, split on `@` to get `$pluginId` and `$marketplaceId`.

Then look up `$markets.$marketplaceId.source` to get:
- `$srcType` = `.source` field (`"github"` or `"directory"`)
- `$srcPath` = `.path` field (directory type only)
- `$srcRepo` = `.repo` field (github type only)

If `$markets.$marketplaceId` is missing entirely → classify as **unknown** (Step 2).

Sanity-check before moving on: every entry in `$enabled` must land in exactly one
class in Step 2. Report the count so a silent drop is visible.

---

## Step 2 — Classify each marketplace and read installed skills

For each marketplace discovered in Step 1:

### If `$srcType == "github"` → **claude-managed**
No skill list needed — `claude plugin update` handles everything.

### If marketplace entry missing → **unknown**
Do not guess. Report it in Step 4 so it is never silently dropped.

### If `$srcType == "directory"` → check git status

```powershell
git -C $srcPath rev-parse --git-dir 2>&1 | Out-Null
$inGit = ($LASTEXITCODE -eq 0)

# A directory marketplace may sit UNDER a parent git repo (e.g. a backup repo
# wrapping ~/.claude). In that case rev-parse succeeds but the git belongs to the
# parent, not the marketplace — fetching it pulls the wrong remote. Only treat git
# as the marketplace's OWN if the repo toplevel IS this directory.
$hasGit = $false
if ($inGit) {
    $top = git -C $srcPath rev-parse --show-toplevel 2>$null
    if ($top) {
        $hasGit = ((Resolve-Path $top).Path -eq (Resolve-Path $srcPath).Path)
    }
}

$remotes = if ($hasGit) { git -C $srcPath remote } else { @() }
$hasRemote = ($remotes.Count -gt 0)
```

When `$hasGit` is false because git was inherited from a parent repo, the `.clone-source` check below still applies — that is the intended path for these marketplaces.

Then read installed skills from `plugin.json`:

```powershell
$pj = Get-Content "$srcPath\.claude-plugin\plugin.json" -Raw | ConvertFrom-Json
$installedSkills = $pj.skills | ForEach-Object { $_ -replace '^\./',''}
# e.g. ["skills/engineering/diagnose", "skills/productivity/caveman", ...]
```

Classify:
- `$hasGit && $hasRemote` → **git-selective**
- `!$hasGit || !$hasRemote` → check if `"$srcPath\.clone-source"` exists:
  - Exists → **clone-temp**, read URL from that file
  - Not exists → **manual** (skip with warning)

---

## Step 3 — Run updates

### claude-managed plugins

```bash
claude plugin update <pluginId>@<marketplaceId>
```

Run once per plugin in this category. Report success or error.

---

### git-selective plugins

#### 3a. Fetch remote (no merge)
```bash
git -C <srcPath> fetch origin
```

#### 3b. Update installed skills only
For each path in `$installedSkills`:
```bash
git -C <srcPath> checkout FETCH_HEAD -- <skill-path>
```
Do NOT `git pull` — that merges all remote content including new skills.

#### 3c. Discover new skills
List skill dirs from remote (public buckets only — `engineering/`, `productivity/`, `misc/`):
```bash
git -C <srcPath> ls-tree --name-only FETCH_HEAD skills/engineering/ 2>/dev/null
git -C <srcPath> ls-tree --name-only FETCH_HEAD skills/productivity/ 2>/dev/null
git -C <srcPath> ls-tree --name-only FETCH_HEAD skills/misc/ 2>/dev/null
```
Cross-reference with `$installedSkills`. For each skill NOT installed, get last updated date:
```bash
git -C <srcPath> log FETCH_HEAD --format="%cd" --date=short -1 -- <skill-path>
```

#### 3d. Refresh plugin cache
```bash
claude plugin update <pluginId>@<marketplaceId>
```
If fails → note "restart Claude Code เพื่อ apply"

---

### clone-temp plugins

#### 3a. Read upstream URL
```powershell
$upstreamUrl = (Get-Content "$srcPath\.clone-source" -Raw).Trim()
$tempDir = "$env:TEMP\plugin-update-$(Get-Random)"
```

#### 3b. Clone to temp
```bash
git clone --depth 1 <upstreamUrl> <tempDir>
```
Verify `<tempDir>/skills/` exists. If not → abort, warn "repo structure อาจเปลี่ยน ต้อง update manual"

#### 3c. Selective copy — installed skills only
For each path in `$installedSkills`:
```powershell
$src = "$tempDir\<skill-path>"
$dst = "$srcPath\<skill-path>"
if (Test-Path $src) {
    $dstParent = Split-Path $dst -Parent
    if (-not (Test-Path $dstParent)) { New-Item -ItemType Directory -Force $dstParent | Out-Null }
    Copy-Item -Recurse -Force $src $dstParent
}
```
Do NOT copy `.claude-plugin/` from temp — ใช้ metadata เดิมที่ $srcPath

#### 3d. Discover new skills
List skill dirs in `$tempDir/skills/engineering/`, `$tempDir/skills/productivity/` (และ buckets อื่นถ้ามี).
Cross-reference with `$installedSkills`. For each new skill, get last commit date:
```bash
git -C <tempDir> log --format="%cd" --date=short -1 -- <skill-path>
```

#### 3e. Cleanup temp
```powershell
Remove-Item -Recurse -Force $tempDir
```

#### 3f. Refresh plugin cache
```bash
claude plugin update <pluginId>@<marketplaceId>
```
If fails → note "restart Claude Code เพื่อ apply"

---

### manual plugins (no git, no .clone-source)

Report: `⚠️ <pluginId>@<marketplaceId> — ข้าม (ไม่มี git remote และไม่มี .clone-source) ต้อง update manual`

---

### unknown plugins (marketplace ไม่อยู่ใน known_marketplaces.json)

Report: `❌ <pluginId>@<marketplaceId> — หา marketplace source ไม่เจอ ตรวจ known_marketplaces.json`

---

## Step 4 — Final report

```
Plugin update summary
─────────────────────────────────────────
✅ <pluginId>@<marketplaceId>  — updated   [claude-managed]
✅ <pluginId>@<marketplaceId>  — N skills updated   [git-selective]
   🆕 New (not installed):
      - <skill-name>  last updated YYYY-MM-DD
✅ <pluginId>@<marketplaceId>  — N skills updated   [clone-temp]
   🆕 New (not installed):
      - <skill-name>  last updated YYYY-MM-DD
⚠️  <pluginId>@<marketplaceId>  — ข้าม ต้อง update manual
❌ <pluginId>@<marketplaceId>  — marketplace source ไม่เจอ

Coverage: N/N enabled plugins  (ต้องเท่ากันเสมอ)
⚠️  Restart Claude Code เพื่อให้ plugin update มีผล
```

If no new skills for a plugin → รายงาน "ไม่มี skill ใหม่" แทนการข้าม section นั้น

---

## Anti-patterns

- ❌ Hardcode plugin names หรือ skill lists ใน skill — ให้อ่านจาก `settings.json` และ `plugin.json` เสมอ
- ❌ `git pull` ตรงๆ ใน git-selective repos — จะ merge new skills เข้า plugin.json โดยไม่ตั้งใจ
- ❌ Copy `.claude-plugin/` จาก temp หรือ remote — metadata เดิมต้องคงไว้
- ❌ นับ `skills/personal/`, `skills/in-progress/`, `skills/deprecated/` ว่าเป็น "new" — buckets พวกนี้ไม่ expose
- ❌ ข้าม new-skills report ถ้าไม่มี new skills — ให้บอก "ไม่มี skill ใหม่" แทน
- ❌ อ่าน marketplace sources จาก `settings.json` → `extraKnownMarketplaces` — มีแค่ marketplace ที่ user เพิ่มเอง ตัว built-in (`claude-plugins-official`) จะไม่อยู่ในนั้น ทำให้ plugin ของมันหลุด flow เงียบๆ ใช้ `plugins\known_marketplaces.json` เสมอ
- ❌ ปล่อยให้ enabled plugin ตัวไหนไม่ตกอยู่ใน class ไหนเลย — ต้องมี unknown branch รับ และรายงาน coverage N/N
- ❌ เชื่อ `rev-parse --git-dir` ตรงๆ ว่า marketplace มี git ของตัวเอง — ต้องเช็ค `--show-toplevel == $srcPath` ด้วย ไม่งั้น marketplace ที่อยู่ใต้ backup repo (`~/.claude/.git`) จะถูก fetch จาก remote ผิด แทนที่จะใช้ `.clone-source`
