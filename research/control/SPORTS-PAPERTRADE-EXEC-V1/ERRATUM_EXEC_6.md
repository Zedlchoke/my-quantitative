# ERRATUM EXEC-6 — GO-state reconciliation + cutover phrase registration (controller, 2026-10-10T03:45Z; owner round-10 audit authorized)

## 1. GO-state forensics (resolves the RUN ALL contradiction)

Timeline proven from bytes:
- 2026-10-07T08:48:33Z — cycle registered, phrase RUN ALL REGISTERED_NOT_CONSUMED.
- 2026-10-07T11:08:47Z — **owner typed `GO SPORTS PAPERTRADE EXEC V1 RUN ALL`
  verbatim in a new message** (journal phase event; transcribed to
  GO_TOKEN.json).
- 2026-10-07T11:09:54Z — ledger GENESIS (wallet 100,000¢, key fingerprint
  2f08a3d2a61b).
- 2026-10-07T11:19:08Z — journal: "consumed root+mirror per ERRATUM_EXEC_1
  D-1"; commit b250bfb1 "GO CONSUMED (P-8)".
- Ledger head now 53449ef5…, 19 rows, chain walk OK.

**Conclusion: RUN ALL was CONSUMED and is spent (P-8).** The
`go_phrase_state: REGISTERED_NOT_CONSUMED` readings in recent reports were
the stale bookkeeping field documented in ERRATUM_EXEC_5 D-4 (researchctl
does not expose it) — controller round-9 mis-presented that stale field as
the live gate state in AMENDMENT_SOURCE_SWITCH_POLYMARKET and the round-9
packet; both are corrected by reference per house convention.

## 2. CAS fix applied (this erratum is the public record)

Root registry row CAS-saved (save sha 8daa51c2…): go_phrase →
**`GO SPORTS PAPERTRADE EXEC V1 POLYMARKET CUTOVER`** (new scope per
AMENDMENT_SOURCE_SWITCH_POLYMARKET), go_phrase_state → REGISTERED_NOT_
CONSUMED with the consumed-history inline; phase carried forward untouched
(including the B1R_RESEAL text from the parallel session). History of the
consumed RUN ALL remains proven by GO_TOKEN.json + journal + ledger genesis
+ b250bfb1 — nothing deleted or rewritten.

## 3. Settlement verification (owner round-10 item 2)

Match **401918299** (WNBA): FORECAST (B1-WNBA) → MARKET_QUOTE (AWAY 2.34 /
HOME 1.61, Pinnacle) → DECISION BET_PAPER AWAY stake 500¢ (EV_net 0.271768
≥ 0.05, ops journal 2026-10-08T17:24:01Z) → SETTLEMENT 2026-10-10T02:30:31Z:
ESPN scoreboard FINAL **NY 83 — ATL 85** (completed=true) ⇒ chosen AWAY
WINS, **pnl = 500 × (2.34 − 1) = +670¢ exactly**, equity_after 101,470¢,
row_sha256 53449ef5…, chain walk 19/19 OK. Matches 401918297 (+395¢) and
401918298 (+405¢) previously audited; **401918300 remains OPEN** (500¢
exposure). Dashboard /api/state (03:42:23Z) reconciles exactly: equity
101,470¢, settled 3, open 1, chain ok, mode REAL — no refresh fix needed.

## 4. Cutover re-probe (owner round-10 item 4)

Polymarket read-only probe 2026-10-10T03:44:02Z (2,100 open events):
NBA 0/82, WNBA 0/15, SOCCER-UNL 0/2, WSL 0/147 — **NOT_RUN_NO_MARKET stands
for all 246 fixtures.** No production source change; no fallback; no
duplicate decisions. WSL gates unchanged: FIRST BATCH (forecast-only) and
BET_PAPER (this cycle's new phrase + the WSL cycle's own split phrase) —
both REGISTERED_NOT_CONSUMED.

## 5. Lawful next GO (IF and WHEN the owner decides)

`GO SPORTS PAPERTRADE EXEC V1 POLYMARKET CUTOVER` — activates the frozen
source switch for leagues READY at that moment. Today that set is empty
(READY_LEAGUES_NONE); typing it now would be a lawful no-op activation
waiting for listings. The WSL BET_PAPER phrase additionally requires its
own conditions (market listing + live-quote A7) per
DECISION_PACKET_BET_PAPER_GATE.md.
