# Cost and window

Reference for step 2 of `esuna`. Two things live here: how to spend your own context window across an episode, and what a tool call cost the session under diagnosis.

## Spending your own window

Condensing is cheap; the run around it is not. A whole measured run of this skill - listing, condensing, reading, and the report - costs 90,000-115,000 tokens of *your own window*, which is not the size of anything the script prints. It scales with the number of transcripts rather than with the difficulty of the diagnosis, so an episode of three or more transcripts does not fit alongside a full read of each. Read the numbers as room you have rather than room you have spent:

- Triage first: run `--context` on every part of the episode before reading any timeline in full. It is cheap, and it tells you which transcript carries the damage.
- Read in full the transcript that carries the ask and the one that crossed budget. Skim the rest for the rows their `--context` reports named.
- Keep `--row` for rows you can name a reason for. Rationing it down to one is how a diagnosis ends up resting on inference.

## What a call cost

A call's cost is what it **sent** plus what came **back**, and the totals table splits the two. Read the sent column first: a `Write` pays for the file it writes, a `Bash` for the heredoc it carries, an `Agent` for the brief it dispatches, and a session that rewrites one prototype seven times pays for that file seven times over while every tool result in the file stays small. A tool heavy on sent is streamlined by writing less — an edit in place of a rewrite, a file on disk in place of a paste — where one heavy on back is streamlined by asking for less.

Costs are estimates in tokens rather than characters, because an image arrives as base64 and by character count a screenshot outweighs the entire rest of the session. An image is priced at 1,600 whether or not the harness announced its size, because every image that did announce one hit that ceiling - so a session shot through with full-viewport screenshots is at the ceiling, not below it, and the totals are a floor for it.
