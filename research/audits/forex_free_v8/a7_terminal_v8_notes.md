# A7 Terminal Audit Notes — FOREX-FREE-V8 (fresh context)

Auditor: A7 (independent, fresh-context terminal). Head audited: `07de93c`.
Full machine verdict: `research/audits/forex_free_v8/a7_terminal_v8_verdict.json`
(schema `forex_free_v8_a7_terminal_v1`).

## Verdict

**CONFIRM_FOREX_FREE_V8_REJECT_ALL** — 0 unresolved HIGH/CRITICAL
(4 LOW + 1 INFO, all verdict-impact none).

## What was recomputed from bytes

1. **Ledger arithmetic** — every gate margin re-derived from row values with the
   comparator-directed formula. Gate 2 anchor: `1.0531109111-1.10 = -0.0468890889`
   exact (the recorded sign follows the `>=` comparator; the brief's literal
   subtraction `1.10-1.0531` is +0.0469 — same magnitude). Gate 3: 2 positive of
   3 populated folds, margin 0.0, strict pass rule ⇒ FAIL. Gate 5:
   `1.5-6.3458737732 = -4.8458737732` exact. Fail sets from
   `artifacts/margins_to_fail.jsonl`: anchor {2,3,5,10}, neighbour {3,5,10},
   control {3,5,10} — matches the verdict exactly.
2. **Row-internal recompute** — fold-weighted expectancy and fold-sum PnL equal
   the row fields exactly; break-even = (price-only/trades)/2 per side
   (≤2.7e-11 rounding); concentration, dual books, LOPO (all 21 drop-one PnLs
   positive), stress tier 2.0, fold populations ≥ 25 all verified.
3. **Independent scored rerun** (single run, authorized terminal reproduction) —
   copied gitignored `staged_vintaged/` + `data_raw/forex_free_v1/` into this
   worktree (never committed), ran `exec_driver_v8.py scored`: exit 0; the 3
   fresh ledger rows are **canon-JSON identical** to the committed rows; **14/14
   artifacts byte-identical** to HEAD. Tree restored to HEAD bytes afterwards.
4. **Twin r-reproduce-1 (detached 720decb)** — 14/14 artifacts byte-match; twin
   rows 3:6 canon-match committed rows. Seeded-prefix observation: does **not**
   undermine anything — the driver recomputes from sha256-pinned bytes and only
   appends; decisively, the A7 rerun was *unseeded* (appended onto exactly the 3
   committed rows) and reproduced everything. Observation: the twin scratch
   ledger now holds 9 rows (a second, post-terminal emission, canon-identical;
   consistent with the V9-bootstrap precondition runner) — LOW, no impact.
5. **Falsification** — independent ratio **19.7700614189/4.9281797948 = 4.0116x,
   same sign** (terminal claims 4.01x). R1 (≥0.5x) FIRES; R2 neighbour/anchor
   = 1.8340 ≥ 1.0x FIRES; R3/R4 do not fire — all matching the D1
   preregistration (`d1/a5-axis3/proposal-1.json`) verbatim.
6. **F2 boundary** — anchor landed exactly at 2/3; owner option-1 strict ruling
   (margin 0.0 fails) was recorded pre-GO **by git chronology** (prelaunch
   01:53:56Z < GO commit 02:06:10Z < scored 02:16:28Z). Neutrality confirmed:
   even if gate 3 passed, gates 2/5/10 + R1 + R2 kill the family independently.
7. **DSR** — recomputed from `artifacts/per_period_series.jsonl` (4920 rows)
   via `research/dsr.py`: 0.34069405314711143 / 0.40584145546448613 /
   0.5396817836770421 and sr0 0.014025205891650681 — bit-exact match. PBO
   NOT_RUN fail-closed correct (3 < 8).
8. **Bookkeeping** — budget 3/6, 3 slots never reassigned; S1 SEALED_UNTOUCHED
   (no S1 path anywhere in cycle code); registry verify PASS 56 entries/0
   errors; no survivors; terminal commit on **no** remote and **not** in local
   main (no push/merge).

## Refutation hunt (all failed to refute)

- (a) No gate claimed failed actually passes; claimed passes verified true.
- (b) Control out-earns anchor on **every** book/tier: fin-adj 3.85x, price-only
  1.66x (6624.43 vs 3985.21), stress tier 1.0 exp 22.77 vs 7.93 — the primary
  book's 4.01x is the conservative ratio.
- (c) Control not disadvantaged by construction: configs identical except the
  preregistered driver/window/direction-map; same warmup 252, same clock, same
  cost ladder, same universe, same 1640-clock grid; digests recompute-match.
- (d) DSR consistent with the reject (no deflated edge anywhere, control 0.54 ≪
  significance).

## Findings (graded)

| ID | Severity | Summary |
|----|----------|---------|
| F1 | LOW | `owner_fresh_go.json recorded_at_utc` 02:40Z post-dates its own commit (02:06:10Z) — typo; git chronology proves pre-GO legality |
| F2 | LOW | terminal `measured_at_utc` 02:35Z pre-dates the twin runs it reports; commit (04:33:26Z) post-dates all reported content — label imprecise only |
| F3 | LOW | twin scratch ledger now 9 rows (second post-terminal emission, canon-identical, untracked) — execution-accounting observation |
| F4 | LOW | FAMILY_FAILURES row prose nits (`terminal_sha` null disclosed; duplicated failure code; DSR row labeled DIAGNOSTIC_CONTRACT_GAP) — numbers all verified |
| F5 | INFO | gate-10 `bool(None)` mechanical fail on non-control arms = verbatim V7 precedent; gate-5 `<=` direction = adjudicated F-A7-T-1 owner debt; both verdict-neutral (reject stands on G2+R1+R2) |

Nothing was repaired; the tree ends clean (porcelain = 0).
