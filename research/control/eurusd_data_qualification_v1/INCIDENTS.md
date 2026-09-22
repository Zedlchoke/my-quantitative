# EURUSD-DATA-QUALIFICATION-V1 — incident log (append-only)

## INC-EDQ1-1 — A1 dispatch-packet sha typo (F3 of A7 audit), 2026-09-22

The A7 dispatch packet typed the audited HEAD by hand as
`e49c23cff682ab15507651078f399dd48e9260d` (39 hex; char 34 'e' vs measured
'5'). The auditor caught it, measured the real HEAD
`e49c23cff682ab15507651078f399dd485e9260d` via git rev-parse, and used the
measured value throughout. Correction note (post-commit, same day): the
first commit of this file mistakenly repeated the malformed 39-hex string
in the "real HEAD" slot above; the correct 40-hex measured value is
`e49c23cff682ab15507651078f399dd485e9260d` — verified against
`git rev-parse` at integration. No artifact carries the malformed sha. Lesson
re-learned (CLAUDE.md §4.1): never hand-type SHAs; always git rev-parse.
