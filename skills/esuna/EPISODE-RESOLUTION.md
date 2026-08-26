# Episode resolution

Reference for step 1 of `esuna`. Two things live here: the shapes an **episode** takes across transcripts, and the touches that masquerade as a fix when you read an mtime.

## Episode shapes

An **episode** — the work the user has in mind — is often more than one transcript, and the opening ask is a weak way to find it. Read the `--day` listing for all three shapes:

- **Contiguous**: a session marked `(cont.)` began moments after the previous one in that project. It is the same episode resumed, so condense every part of it. Its opening ask is an answer to a question asked in the previous transcript (the Thai for "Option B then, local is fine"), which matches no topic at all — a resumed session is found by its neighbour, never by its ask.
- **Concurrent**: sessions whose times overlap the target's. Two in one project were editing each other's files, so when the target tripped over a file that moved under it, the cause is in the other transcript. Overlapping sessions in *different* projects share one thing anyway — the account's rate limit — and that is how a session comes to sit blocked for two hours in the middle of a task. Run `--context` on each overlapping session and hold the peaks against each other; step 4 reports what you find there under **Git gud!**. Then decide what each one is to the episode: a session that touched the target's repo, files, or branch is **part of it** — condense it in full, because the target's confusion is explained inside it. One that merely ran at the same time is **background** — cite its peak and its ask, and leave it uncondensed.
- **Duplicate**: when two sessions open with the same ask, discriminate on duration and on whether the agent stopped to ask the user something. Before reading any delta, scan each one's user turns for the first that redirects: a slash command run twice on different arguments (`teach lesson 22`, then `teach lesson 21B` six minutes in) opens identically and is not the same work, and every discriminator above fires on it. The same task genuinely retried later is the cheapest diagnostic available — condense both and read the delta.

## Touches that masquerade as a fix

An mtime says a file changed, never who changed it or why. Two kinds of touch read as a repair and are not:

- **The session's own writes.** A session that edits its steering files in its closing rows stamps every one of them after its own start. Cross-check each mtime against the Edit and Write rows in the timeline; a file the session wrote itself is evidence about that session, not a repair of it.
- **Incidental touches.** A file stamped today, mid-retrospective, was probably touched by whatever you are running right now. Read the file and see whether the fix is actually in it before marking anything already-fixed.
