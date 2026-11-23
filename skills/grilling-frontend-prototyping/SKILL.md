---
name: grilling-frontend-prototyping
description: Converge on a frontend look through rounds of prototypes and grilling verdicts. Use when the user wants to iterate on UI/visual taste against concrete variants, or a wayfinder prototype ticket names this skill.
disable-model-invocation: true
---

Run a `/grilling` session, using the `/prototype` skill — each question is asked with prototypes, not words:

- Each round, build 5 radically different prototypes of the current design
  question into one live mocked app: one standalone HTML file in the
  scratchpad, updated in place each round. `/prototype` will reach for the
  Artifact tool; this machine denies it, so the local file is the artifact.
  Keep one path all session. In round 1, open it in the user's browser
  yourself (`Start-Process <path>`); don't hand them a command to run. They
  refresh that tab every round after.
- A floating bottom-right draggable picker names each design; ←/→ arrows
  switch between them, restyling the mocked app live. When the design has
  meaningful states (an inbox: full vs empty), add picker buttons that toggle
  the mock between them.
- The grilling walks down the visual design tree, each verdict zooming in
  one level: the overall design, then component groups, then individual
  components — until the user has designed the entire feature in detail.

The user's eyes are the review loop — a round ends on their verdict, not on
your own look at the page. To see it yourself, serve the directory with
`python -m http.server 8765` and open `http://localhost:8765/<file>`;
playwright cannot load `file://`. Read back only the frames you changed.
