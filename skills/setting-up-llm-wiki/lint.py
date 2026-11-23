#!/usr/bin/env python3
"""Mechanical lint for an LLM wiki. Judgment checks (contradictions, missing pages, gaps) stay with the agent.

Usage (from the wiki root):
    python lint.py [--pages GLOB ...] [--hub GLOB ...] [--stale LEVEL=DAYS ...] [--today YYYY-MM-DD]

--pages   globs (relative to the wiki root) selecting the wiki pages. Default: wiki/**/*.md
--hub     globs for hub pages (e.g. wiki/overview.md): their links are exempt from one-way and
          count as no inbound link for orphan; they are still checked for broken links and indexing.
--stale   enables the time-staleness check, e.g. --stale fast=90 medium=365 slow=1095
          Pages carry "AS_OF: YYYY-MM-DD" and "VOLATILITY: <level>" in their first 15 lines.

Checks:
  broken     relative link (any .md outside skipped dirs) pointing at a missing file
  unindexed  page not linked from index.md / INDEX.md
  orphan     page with no inbound link from another page
  one-way    page A links page B, B does not link A
  stale      AS_OF older than its VOLATILITY threshold
  header     page missing AS_OF / VOLATILITY (only with --stale)

Exit code 1 when any finding exists, 0 when clean.
"""
import argparse
import datetime as dt
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


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", nargs="+", default=["wiki/**/*.md"])
    ap.add_argument("--hub", nargs="*", default=[])
    ap.add_argument("--stale", nargs="*", default=None)
    ap.add_argument("--today", default=None)
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
    pages = sorted({p.resolve() for g in a.pages for p in root.glob(g) if kept(p)})
    hubs = {p.resolve() for g in a.hub for p in root.glob(g) if kept(p)}
    page_set = set(pages)
    linked = page_set - hubs  # pages subject to orphan / one-way
    index = next((root / n for n in ("index.md", "INDEX.md") if (root / n).exists()), None)

    rel = lambda p: p.relative_to(root).as_posix() if p.is_relative_to(root) else str(p)
    findings: dict[str, list[str]] = {}
    add = lambda kind, msg: findings.setdefault(kind, []).append(msg)

    out_links = {p: links_in(p, root) for p in all_md}

    for src, targets in out_links.items():
        for t in sorted(targets):
            if not t.exists():
                add("broken", f"{rel(src)} -> {rel(t)}")

    indexed = out_links.get(index.resolve(), set()) if index else set()
    for p in pages:
        if index and p not in indexed:
            add("unindexed", rel(p))
        if p in hubs:
            continue
        inbound = [s for s in linked if s != p and p in out_links.get(s, set())]
        if not inbound:
            add("orphan", rel(p))
        for t in sorted(out_links.get(p, set()) & linked):
            if t != p and p not in out_links.get(t, set()):
                add("one-way", f"{rel(p)} -> {rel(t)} (no link back)")

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
    for kind in ("broken", "unindexed", "orphan", "one-way", "header", "stale"):
        for msg in findings.get(kind, []):
            print(f"  [{kind}] {msg}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
