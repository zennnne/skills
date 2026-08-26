# Episode resolution

Reference for step 1 of `esuna`. Two things live here: the shapes an **episode** takes across transcripts, and the touches that masquerade as a fix when you read an mtime.

## Episode shapes

An **episode** — the work the user has in mind — is often more than one transcript, and the opening ask is a weak way to find it. Read the `--day` listing for all three shapes:

- **Contiguous**: a session marked `(cont.)` began moments after the previous one in that project. It is the same episode resumed, so condense every part of it. Its opening ask is an answer to a question asked in the previous transcript ("Option B then, local is fine"), which matches no topic at all — a resumed session is found by its neighbour, never by its ask.
- **Concurrent**: sessions whose times overlap the target's. Two in one project were editing each other's files, so when the target tripped over a file that moved under it, the cause is in the other transcript. Overlapping sessions in *different* projects share one thing anyway — the account's rate limit — and that is how a session comes to sit blocked for two hours in the middle of a task. Run `--context` on each and read the **count** first: three or more heavy sessions at once is the finding, and the peaks are what you quote to size it. Confirm it in the target's own timeline before reporting it — a rate limit announces itself in a `SYS` row naming a reset time, and a long gap with no such row is something else. Step 4 reports what you find under **Git gud!**. Then decide what each one is to the episode: a session that touched the target's repo, files, or branch is **part of it** — condense it in full, because the target's confusion is explained inside it. One that merely ran at the same time is **background** — cite its peak and its ask, and leave it uncondensed.
- **Duplicate**: when two sessions open with the same ask, scan each one's user turns for the first that **redirects** before reading any delta. A slash command run twice under different arguments opens identically and is not the same work; the redirect names what each run actually did, and duration, peak, and whether the agent stopped to ask the user all separate them once you know. The same task genuinely retried later is the cheapest diagnostic available — condense both and read the delta.

- **Sequential**: same project, no overlap, hours or days apart, the later one consuming files the earlier one wrote. Not contiguous, not concurrent, not duplicate, and the commonest shape of all. The one that produced the artifact — a spec, a ticket graph, a lesson plan — is **background**: cite its ask and what it produced, and condense it only when the user's phrase reaches it. What it wrote is on disk, and reading the disk is cheaper than reading how the disk got that way.

## Touches that masquerade as a fix

An mtime says a file changed, never who changed it or why — and the repairs that leave no mtime at all are the ones it cannot see. Four cases read wrong:

- **The session's own writes.** A session that edits its steering files in its closing rows stamps every one of them after its own start. Cross-check each mtime against the Edit and Write rows in the timeline; a file the session wrote itself is evidence about that session, not a repair of it.
- **Incidental touches.** A file stamped today, mid-retrospective, was probably touched by whatever you are running right now. Read the file and see whether the fix is actually in it before marking anything already-fixed.

- **Unattributable touches.** A file stamped recently by neither you nor any transcript in the episode is still a real fix — the user edits these files between sessions. Read it, mark it on what it says rather than on who wrote it, and say the provenance is unknown so the user can correct you.

- **Fixes with no touch anywhere.** Moving a project relocates its `~/.claude/projects/<slug>/` and orphans the memory directory the old slug carried; renaming one does the same. No file changed, so no mtime records it, and a condition that looks live is gone — or a memory directory that looks populated was never the one the session read. `ls ~/.claude/projects/ | grep <project>` finds a second slug when there is one; two slugs for one project means the session ran under a different one than the transcript now sits under.
