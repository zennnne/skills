# Cost and window

Reference for step 2 of `esuna`. Two things live here: how to spend your own context window across an episode, and what a tool call cost the session under diagnosis.

## Spending your own window

Condensing is cheap; the run around it is not. A whole measured run of this skill - listing, condensing, reading, and the report - costs 90,000-115,000 tokens of *your own window*, which is not the size of anything the script prints. Three cold runs on three different episodes measured 93k, 100k and 105k, so treat the range as real rather than as a caution.

You cannot see your own usage, so budget by proxy instead: **two transcripts read in full is the run's ceiling.** It scales with the number of transcripts rather than with the difficulty of the diagnosis, so an episode of three or more does not fit alongside a full read of each. Read the numbers as room you have rather than room you have spent:

- Triage first: run `--context` on every part of the episode before reading any timeline in full. It is cheap, and it tells you which transcript carries the damage.
- Read in full the transcript that carries the ask and the one that crossed budget. Skim the rest for the rows their `--context` reports named.
- Keep `--row` for rows you can name a reason for. Rationing it down to one is how a diagnosis ends up resting on inference.

## What a call cost

A call's cost is what it **sent** plus what came **back**, and the totals table splits the two. Read the sent column first: a `Write` pays for the file it writes, a `Bash` for the heredoc it carries, an `Agent` for the brief it dispatches, and a session that rewrites one prototype seven times pays for that file seven times over while every tool result in the file stays small. A tool heavy on sent is streamlined by writing less — an edit in place of a rewrite, a file on disk in place of a paste — where one heavy on back is streamlined by asking for less.

Costs are estimates in tokens rather than characters, because an image arrives as base64 and by character count a screenshot outweighs the entire rest of the session. An image whose displayed size the harness announced is priced from that size and can land well under the cap - 613 and 669 both appear in real totals - while the nine in ten that announce nothing are priced at the 1,600 cap. So an image column mixing small numbers with 1,600s is reporting measurement next to default, and a session shot through with full-viewport screenshots reads as a floor rather than a total.
