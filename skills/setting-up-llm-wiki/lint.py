#!/usr/bin/env python3
"""Mechanical lint for an LLM wiki. Judgment checks (contradictions, missing pages, gaps) stay with the agent.

Usage (from the wiki root):
    python lint.py [--pages GLOB ...] [--hub GLOB ...] [--stale LEVEL=DAYS ...] [--today YYYY-MM-DD]
                   [--fix] [--index-max N] [--scope] [--lessons GLOB ...] [--full-under N] [--full-due DAYS]

--pages       globs (relative to the wiki root) selecting the wiki pages. Default: wiki/**/*.md
--hub         globs for hub pages (e.g. wiki/overview.md): their links are exempt from one-way and
              count as no inbound link for orphan; they are still checked for broken links and indexing.
--stale       enables the time-staleness check, e.g. --stale fast=90 medium=365 slow=1095
              Pages carry "AS_OF: YYYY-MM-DD" and "VOLATILITY: <level>" in their first 15 lines.
--fix         writes the missing back-link for every one-way pair into the target page's
              "## Related" section (created at the end of the page if absent), reported as [fixed].
--index-max   entry count of the root index.md above which it reports index-load. Default: 150
--scope       prints the judgment-lint scope, read from the newest "lint | full|incremental" entry in log.md:
              full (every page + every --lessons file) when the wiki has fewer than --full-under pages or no
              full lint is logged yet; otherwise incremental (pages modified on or after the last lint
              date, plus every page linking to or linked from them, plus modified --lessons files).
--lessons     globs for the lessons files the judgment scope covers (e.g. lessons/*.md). Default: none
--full-under  page count below which the scope is always full. Default: 50
--full-due    days after the last full lint at which --scope reports "full lint due".

Checks:
  broken      relative link (any .md outside skipped dirs) pointing at a missing file
  unindexed   page not linked from index.md / INDEX.md, or from a _index.md that index.md links
  orphan      page with no inbound link from another page
  one-way     page A links page B, B does not link A (fixed in place with --fix)
  index-load  root index.md holds more than --index-max entries
  stale       AS_OF older than its VOLATILITY threshold
  header      page missing AS_OF / VOLATILITY (only with --stale)

Exit code 1 when any finding exists, 0 when clean. [fixed] and [scope] lines are not findings.
"""
import argparse
import datetime as dt
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote

SKIP_DIRS = {".git", "raw", "progress", "_archive", "node_modules"}
LINK_RE = re.compile(r"!?\[[^\]]*\]\((?:<([^>]+)>|([^)\s]+))(?:\s+\"[^\"]*\")?\)")
FENCE_RE = re.compile(r"```.*?```", re.S)
CODE_RE = re.compile(r"`[^`\n]*`")
ASOF_RE = re.compile(r"AS_OF:\**\s*(\d{4}-\d{2}-\d{2})")
VOL_RE = re.compile(r"VOLATILITY:\**\s*([A-Za-z-]+)")
LINT_LOG_RE = re.compile(r"^## \[(\d{4}-\d{2}-\d{2})\] lint \| (full|incremental)\b", re.M)
HEADING_RE = re.compile(r"^#{1,2} ")


def links_in(path: Path, root: Path) -> set[Path]:
    text = path.read_text(encoding="utf-8", errors="replace")
    text = CODE_RE.sub("", FENCE_RE.sub("", text))
    out = set()
    for angled, bare in LINK_RE.findall(text):
        target = angled or bare
        if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("#"):
            continue  # URL, mailto, in-page anchor
        target = unquote(target.split("#", 1)[0])
        if target:
            out.add((path.parent / target).resolve())
    return out


def title_of(path: Path) -> str:
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def add_backlinks(page: Path, sources: list[Path]) -> None:
    raw = page.read_bytes().decode("utf-8", errors="replace")
    eol = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.splitlines()
    entries = [f"- [{title_of(s)}]({Path(os.path.relpath(s, page.parent)).as_posix()})" for s in sources]
    idx = next((i for i, l in enumerate(lines) if l.strip().lower() == "## related"), None)
    if idx is None:
        while lines and not lines[-1].strip():
            lines.pop()
        lines += ["", "## Related", ""] + entries
    else:
        end = next((j for j in range(idx + 1, len(lines)) if HEADING_RE.match(lines[j])), len(lines))
        ins = end
        while ins > idx + 1 and not lines[ins - 1].strip():
            ins -= 1
        lines[ins:ins] = entries
    page.write_bytes((eol.join(lines) + eol).encode("utf-8"))


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", nargs="+", default=["wiki/**/*.md"])
    ap.add_argument("--hub", nargs="*", default=[])
    ap.add_argument("--stale", nargs="*", default=None)
    ap.add_argument("--today", default=None)
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--index-max", type=int, default=150)
    ap.add_argument("--scope", action="store_true")
    ap.add_argument("--lessons", nargs="*", default=[])
    ap.add_argument("--full-under", type=int, default=50)
    ap.add_argument("--full-due", type=int, default=None)
    a = ap.parse_args()

    root = Path.cwd().resolve()
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    thresholds = {}
    for item in a.stale or []:
        level, days = item.split("=")
        thresholds[level.strip().lower()] = int(days)

    def kept(p: Path) -> bool:
        return p.is_file() and not SKIP_DIRS.intersection(p.relative_to(root).parts[:-1])

    all_md = [p.resolve() for p in root.rglob("*.md") if kept(p)]
    pages = sorted({p.resolve() for g in a.pages for p in root.glob(g) if kept(p) and p.name != "_index.md"})
    hubs = {p.resolve() for g in a.hub for p in root.glob(g) if kept(p)}
    page_set = set(pages)
    linked = page_set - hubs  # pages subject to orphan / one-way
    index = next((root / n for n in ("index.md", "INDEX.md") if (root / n).exists()), None)

    rel = lambda p: p.relative_to(root).as_posix() if p.is_relative_to(root) else str(p)
    findings: dict[str, list[str]] = {}
    add = lambda kind, msg: findings.setdefault(kind, []).append(msg)
    fixed: list[str] = []

    out_links = {p: links_in(p, root) for p in all_md}

    for src, targets in out_links.items():
        for t in sorted(targets):
            if not t.exists():
                add("broken", f"{rel(src)} -> {rel(t)}")

    # one-way pairs first, so --fix repairs them before orphan / one-way are judged
    missing_back: dict[Path, list[Path]] = {}
    for p in pages:
        if p in hubs:
            continue
        for t in sorted(out_links.get(p, set()) & linked):
            if t != p and p not in out_links.get(t, set()):
                missing_back.setdefault(t, []).append(p)
    if a.fix:
        for t, sources in missing_back.items():
            add_backlinks(t, sources)
            out_links[t] |= set(sources)
            fixed += [f"{rel(t)} <- {rel(s)}" for s in sources]
        missing_back = {}
    for t, sources in missing_back.items():
        for s in sources:
            add("one-way", f"{rel(s)} -> {rel(t)} (no link back)")

    indexed: set[Path] = set()
    if index:
        top = out_links.get(index.resolve(), set())
        indexed = set(top)
        for sub in top:
            if sub.name == "_index.md":
                indexed |= out_links.get(sub, set())
        lines = index.read_text(encoding="utf-8", errors="replace").splitlines()
        entries = sum(1 for l in lines if LINK_RE.search(l))
        if entries > a.index_max:
            add("index-load", f"{rel(index)} has {entries} entries > {a.index_max}")
    for p in pages:
        if index and p not in indexed:
            add("unindexed", rel(p))
        if p in hubs:
            continue
        inbound = [s for s in linked if s != p and p in out_links.get(s, set())]
        if not inbound:
            add("orphan", rel(p))

    if a.stale is not None:
        for p in pages:
            head = "\n".join(p.read_text(encoding="utf-8", errors="replace").splitlines()[:15])
            asof, vol = ASOF_RE.search(head), VOL_RE.search(head)
            if not asof or not vol:
                add("header", f"{rel(p)} missing {'AS_OF' if not asof else 'VOLATILITY'}")
                continue
            level = vol.group(1).lower()
            if level not in thresholds:
                add("header", f"{rel(p)} unknown VOLATILITY '{level}'")
                continue
            age = (today - dt.date.fromisoformat(asof.group(1))).days
            if age > thresholds[level]:
                add("stale", f"{rel(p)} AS_OF {asof.group(1)} ({level}, {age}d > {thresholds[level]}d)")

    if not index:
        add("unindexed", "no index.md / INDEX.md at wiki root")

    total = sum(len(v) for v in findings.values())
    print(f"lint: {len(pages)} pages, {total} findings")
    for kind in ("broken", "unindexed", "orphan", "one-way", "index-load", "header", "stale"):
        for msg in findings.get(kind, []):
            print(f"  [{kind}] {msg}")
    for msg in fixed:
        print(f"  [fixed] {msg}")

    if a.scope:
        log = root / "log.md"
        runs = LINT_LOG_RE.findall(log.read_text(encoding="utf-8", errors="replace")) if log.exists() else []
        last_any = max((d for d, _ in runs), default=None)
        last_full = max((d for d, k in runs if k == "full"), default=None)
        lessons = sorted({p.resolve() for g in a.lessons for p in root.glob(g) if p.is_file()})
        if len(pages) < a.full_under or not last_full:
            mode, scope, scope_lessons = "full", set(pages), lessons
            why = f"{len(pages)} pages < {a.full_under}" if len(pages) < a.full_under else "no full lint logged"
        else:
            since = dt.date.fromisoformat(last_any)
            fresh = lambda p: dt.date.fromtimestamp(p.stat().st_mtime) >= since
            changed = {p for p in pages if fresh(p)}
            scope = set(changed)
            for p in changed:
                scope |= out_links.get(p, set()) & page_set
            scope |= {s for s in pages if out_links.get(s, set()) & changed}
            scope_lessons = [p for p in lessons if fresh(p)]
            mode, why = "incremental", f"changed since {last_any} + linked"
        print(f"scope: {mode} — {len(scope)} of {len(pages)} pages, {len(scope_lessons)} lessons files ({why})")
        if last_full:
            age = (today - dt.date.fromisoformat(last_full)).days
            due = a.full_due is not None and mode == "incremental" and age >= a.full_due
            print(f"last full lint: {last_full} ({age}d ago){' — full lint due' if due else ''}")
        for p in sorted(scope) + scope_lessons:
            print(f"  [scope] {rel(p)}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
