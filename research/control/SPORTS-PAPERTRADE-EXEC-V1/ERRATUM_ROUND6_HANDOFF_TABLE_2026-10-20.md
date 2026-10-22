# ERRATUM — ROUND-6 HANDOFF TABLE (owner-facing) — 2026-10-20

## 1. What was wrong

The round-6 chat handoff table mislabeled the TEAM PAIRINGS of three WSL
fixtures. The ledger settlement math, chain, and app rendering were never
affected (the app renders `home`/`away` straight from ledger DECISION rows;
no team names are hardcoded anywhere in `apps/paperdesk/renderer/` or
`main/` — grep-verified). The wrong pairings existed ONLY in the handoff
message text, which was written from memory instead of an authoritative
ledger join. This is a reporting error and it is retracted here.

## 2. CORRECTED TABLE (authoritative join, 48-row ledger, by match_id)

| match_id | Fixture (ledger home v away) | Chosen | Result (UMA) | Outcome | P&L |
|---|---|---|---|---|---|
| FD-2026-M36 | **Aston Villa v Liverpool** | HOME | HOME | WIN | +2,769c |
| FD-2026-M37 | Arsenal v Birmingham City | DRAW | DRAW | WIN | +11,253c |
| FD-2026-M38 | Manchester City v Brighton & Hove Albion | HOME | HOME | WIN | +324c |
| FD-2026-M39 | **London City Lionesses v Everton** | AWAY | HOME | LOSE | −1,022c |
| FD-2026-M40 | **Crystal Palace v West Ham United** | HOME | AWAY | LOSE | −1,022c |
| FD-2026-M42 | Charlton Athletic v Manchester United | HOME | AWAY | LOSE | −1,022c |

Net **+11,280c**; equity 102,215c → **113,495c**; ledger 48 rows, chain
verify 0 errors — UNCHANGED by this erratum (no bytes written to the
ledger; this is a text correction only).

(The erroneous table had swapped M36 ↔ M40 fixtures and mislabeled M39.)

## 3. All-six source event→game ID audit (not just M37)

Every settlement was re-audited against a LIVE Gamma fetch of its own
tracked event (payload per event: /tmp copies + committed artifact
`wsl_all_six_identity_audit_2026-10-20.json`):

| match_id | event_id | Gamma event title | HOME/DRAW/AWAY markets found | exactly-one-YES winner | == ledger result |
|---|---|---|---|---|---|
| M36 | 1172241 | **Aston Villa WFC vs. Liverpool LFC** | 5575144/5575145/5575146 | HOME | YES |
| M37 | 1167584 | Arsenal WFC vs. Birmingham City WFC | 5528995/5528996/5528997 | DRAW | YES |
| M38 | 1172253 | Manchester City WFC vs. Brighton and Hove Albion WFC | 5575282/5575283/5575284 | HOME | YES |
| M39 | 1172245 | London City Lionesses vs. Everton FC | 5575190/5575191/5575192 | HOME | YES |
| M40 | 1172232 | Crystal Palace WFC vs. West Ham United WFC | 5575001/5575003/5575005 | AWAY | YES |
| M42 | 1172249 | Charlton Athletic WFC vs. Manchester United WFC | 5575236/5575237/5575238 | AWAY | YES |

Identity law applied: event title contains BOTH ledger team names through
the PINNED WSL crosswalk inversion (`WSL_PM_NAME_TO_FD_NAME`, incl.
'Brighton and Hove' ↔ '&'); per-leg question carries the kickoff date or
the full pairing; exactly-one leg YES==1.0, others 0.0; UMA resolved.
Result of each Gamma resolution equals the ledger SETTLEMENT `result` for
all six; P&L recomputed from each decision's own frozen stake/odds for all
six (matches ledger). Actual PM questions observed (real phrasing incl.
the DRAW variant without a date): see the committed JSON artifact — e.g.
M36: "Will Aston Villa WFC win on 2026-10-18?" / "Will Aston Villa WFC
vs. Liverpool LFC end in a draw?" / "Will Liverpool LFC win on
2026-10-18?".

## 4. Process note

Handoff tables must be generated from an authoritative join (as done here)
— never reconstructed from prior terminal output. The app was already
correct; only the human-readable table was wrong.
