# CEASE_GUARD_STANDARD — explicit cessation guard for volume-crossover chain builders

Round: FUTURES-SIX-ADOPT-PREP-20261004 · Lane ADOPT · 2026-10-04

**Label: PROPOSED STANDARD — pending owner decision D9. This document is input to a ruling; it is
not a ruling, and no standard here is in force until the owner writes one.**

## 1. Consolidated 3-symbol evidence (one law, three independent manifestations)

The k-window volume-crossover roll rule carries a weak IMPLICIT guard: it keeps the old contract
until it has been absent for a FULL k-window of sessions. When a contract CEASES trading before its
trailing-k mean decays below the successor's, the chain silently holds a dead contract and a session
vanishes from the bar-level chain.

| # | Symbol | Session | What happened (measured) | Consequence | Evidence file |
|---|--------|---------|--------------------------|-------------|---------------|
| 1 | **6J** | **2022-09-20** | Exchange OPEN; `6JZ2_2022` traded **125,303 lots** over 1,357 bars; plain k=5 still held **ceased `6JU2_2022`** (stale trailing-5 mean 92,857.8 > Z2's 88,234.0). U2's final session was 2022-09-19 (97 bars, last bar 13:40Z). Switch fired only 2022-09-21. | Session 2022-09-20 silently vanishes from the 1,745-session bar-level held chain; the 09-21 rolled return spans two calendar days off a 97-bar stale U2 close | `FUTURES-SIX-READINESS-20261004/fx_ja/6j_cease_guard_2022.json` (verdict PASS, incl. official corroboration pcal_69 J1U27 first-trade 2022-09-20); baseline cross-check `FUTURES-DEEPRESEARCH-V2-20261003/analysis/6J_cache/held_volume_k5.parquet` (read-only cite) |
| 2 | **6A** | **2024-12-17** | `6AZ4_2024` last bars 2024-12-16 15:09Z; on 12-17 plain k=5 still held dead Z4 while **`6AH5_2025` traded 55,675** (trailing-5 46,490.25 vs 44,502.80 explains the no-switch). Baseline switched 2024-12-18. | 1 vanished session in the baseline bar-level chain | `FUTURES-SIX-READINESS-20261004/fx_ja/6a_roll_measured.json` (`k5_baseline_variant.violation_sessions`, `variant_delta.cease_guard_vanished_session_detail`) |
| 3 | **6A** | **2026-06-16** | `6AM6_2026` last bars 2026-06-15 13:50Z; on 06-16 plain k=5 still held dead M6 while **`6AU6_2026` traded 55,533**. Baseline switched 2026-06-17. | 1 vanished session in the baseline bar-level chain | same file as #2 |
| 4 | **NQ (v2 chain, "NQ-before")** | 2020-03-23..2020-05-29 | `NQH0_2020` bars-cessation 2020-03-20; the v2 chain held it **49 dead sessions** (all 49 closes NaN, all flagged `depleted`), rolling only at the 2020-06-01 dead handoff (dte −73). | Eliminated by the v3 rebuild: 0 violations, roll corrected to the real 2020-03-19 crossover | `FUTURES-SIX-READINESS-20261004/nq/cease_guard_audit.json` (BEFORE: 1 violation, dead_held_sessions 49; v3 plain + cg: 0/0); re-measured by ADOPT in `../cache_v3_hashes.json` |

Explicit-guard check: variants that add the hard cease produce **0 violations** on all three symbols
with **identical roll dates** — the only deltas are the two 6A switches moving **1 session earlier**
(12-18→12-17, 06-17→06-16), i.e. exactly the vanished sessions restored
(`6a_roll_measured.json variant_delta`: "27 rolls BOTH ways … eliminates both vanished sessions";
NQ: cg chain byte/logically identical to plain because NQ's k=5 never hit the pathology).

## 2. Normative algorithm (proposed text)

For any contract chain built by a k-session volume-crossover rule, the builder MUST add an explicit
hard cease guard:

1. **Volume rule (unchanged)**: at each session close, compare trailing-k session mean volumes
   (k=5 unless a cycle's data contract declares otherwise); hold the max-mean contract.
2. **Cessation definition**: `cessation(c)` = the LAST session on which contract `c` printed any bar
   (bars-present derivation, DECLARED — not exchange metadata), cross-checked against the contract
   registry's last-bar field; when an official last-trade date is known (exchange notice / product
   calendar), it takes precedence.
3. **Hard cease**: if the held contract has **no bars on session d**, or **d is past
   `cessation(held)`**, the rule switches IMMEDIATELY to the next quarterly — first candidate with
   data today, else first candidate with any data — regardless of trailing volume.
4. **Switch date = max(volume-crossover date, cease floor)**: a roll may fire earlier than the
   crossover (cease floor binds) but NEVER later; the chain must never hold a contract past its
   cessation.
5. **Audit obligations**: the builder records every guard fire (session, old, new, trigger);
   a chain is INVALID if any held session is past `cessation(held)` or the last held day has no
   bars for the held contract.
6. **Cessation source staleness**: a cessation derived from the session table is full-sample
   information; it is legal HERE because each firing decision uses only time-t facts (see
   `CACHE_V3_PIT_STATEMENT.md` §2, seam 2). Any in-sample strategy use must re-derive cessation
   causally (absence-of-bars-today), which yields identical firing.

### Pseudocode

```python
def build_chain(wide, k=5):
    # wide: session_date x contract VOLUME table, sessions in order
    # cessation(c): last session with any bars for c (bars-present derivation,
    #               declared; official last-trade date overrides when known)
    ces = cessation_by_bars(wide)
    roll = wide.rolling(k, min_periods=1).mean()          # trailing-k means
    state, chain, fires = None, [], []
    for d in wide.index:                                   # sessions, chronological
        row = roll.loc[d].dropna(); row = row[row > 0]
        if state is None:
            state = row.idxmax()                           # initial front
        elif (state not in row) or (d > ces.get(state, d)):  # HARD CEASE
            cands = [c for c in quarterly_after(state) if c in row] \
                 or [c for c in quarterly_after(state) if c in wide.columns and wide.loc[d, c] >= 0]
            fires.append((d, state, cands[0], "cease_guard_no_bars"))
            state = cands[0]                               # immediate, volume-blind
        elif row[state] < row.max():                       # k=5 crossover
            state = row.idxmax()
        chain.append((d, state))                           # never past cessation
    audit(chain, ces, fires)                               # assert 0 dead-held sessions
    return chain, fires
```

## 3. Scope and status

* Scope: all current volume-crossover chains (NQ, 6J, 6A) and any future symbol adopting the same
  chain family. It does NOT touch calendar-rule chains, and it sets no k for symbols that declared
  another window in their own data contract.
* If D9 rules Option B (per-cycle choice), this text becomes the reference implementation each
  future spec must explicitly adopt or deviate from, with the 3-symbol table above as precedent.

— PROPOSED STANDARD, pending owner D9. Not in force.
