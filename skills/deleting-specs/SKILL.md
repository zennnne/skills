---
name: deleting-specs
description: Delete a finished feature's spec (from /to-spec) and tickets (from /to-tickets) once the build has landed.
disable-model-invocation: true
---

# Deleting Specs

A spec and its tickets are **scaffolding**: a projection of the decisions made during grilling, built to carry them into `/implement`, and taken down once the building stands. The decisions themselves live on in `GLOSSARY.md`, ADRs, the code, and its tests. Left standing, scaffolding goes stale and an agent reading it later trusts it over the code.

Scope is exactly the scaffolding: the spec and its tickets. Everything else stays: `GLOSSARY.md`, ADRs, `prototype/*` branches, code, tests.

The argument names the feature: a `.scratch/<feature-slug>` path, a slug, or the spec's issue number. With no argument, list the candidate features and ask which.

## 1. Locate the tracker

Read `docs/agents/issue-tracker.md` (written by `/setup-matt-pocock-skills`). If it is missing but `.scratch/` exists, treat the tracker as local markdown; otherwise ask.

_Done when_ you know whether this is local markdown or a real tracker (GitHub, GitLab, …).

## 2. Inventory the scaffolding

- **Local** → `.scratch/<feature-slug>/spec.md` and every file under `.scratch/<feature-slug>/issues/`.
- **Real tracker** → the spec issue, plus every ticket that names it as parent, is its sub-issue, or links back to it. Walk the blocking edges too: a ticket reachable only through another ticket's "Blocked by" still belongs to the feature.

Record each item's state (`Status:` line locally, open/closed on a tracker).

_Done when_ every ticket of the feature is on the list with its state, and none is guessed.

## 3. Gate on the build

Scaffolding comes down only after the building stands. Every ticket must be done: `Status:` resolved/done locally, closed on a tracker. If any ticket is still open, stop and report which ones; the user decides whether they are abandoned (delete anyway) or still live (abort).

_Done when_ every ticket is done, or the user has explicitly cleared each open one.

## 4. Harvest stray decisions

The spec is a projection, but a decision can reach it without ever landing in `GLOSSARY.md` or an ADR (e.g. the idea was sharpened with `/grill-me`, which keeps no paper trail). Read the spec's **Implementation Decisions** and each ticket's comments. For each decision that is hard to reverse, check whether an ADR, the glossary, or the code itself already carries it.

List every **orphan** (a decision carried by nothing but the scaffolding) and offer to record each one through `/domain-modeling` before deleting. The user may decline.

_Done when_ every hard-to-reverse decision is either carried elsewhere or explicitly waived by the user.

## 5. Find dangling pointers

Grep the repo (excluding the scaffolding itself) for the spec path, the feature slug, and each issue number: `CLAUDE.md`/`AGENTS.md`, ADRs, code comments, other tickets. Each hit becomes a dangling pointer after deletion.

_Done when_ every hit is listed with a proposed fix (rewrite to point at the ADR/code, or remove the line).

## 6. Confirm, then delete

Show the user one list: the scaffolding to delete, the pointers to fix. Wait for approval.

- **Local** → fix the pointers, then `git rm -r .scratch/<feature-slug>/` if tracked, or remove the directory if untracked.
- **Real tracker** → fix the pointers, then close the spec issue and any still-open tickets with a comment pointing at the ADRs/code that now carry the decisions. Closing keeps the history; reach for permanent deletion (`gh issue delete`) only when the user asks for it by name.

Leave the change uncommitted for the user to review.

_Done when_ `.scratch/<feature-slug>/` is gone (or every issue is closed), the repo holds zero references to it, and you have reported what was deleted, which pointers changed, and which orphan decisions were recorded or waived.
