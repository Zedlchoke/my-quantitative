# FREEZE — DAILY-EXPLORATORY-V1 preparation (2026-10-01)

## Scope (owner election verbatim: "ĐI TIẾP KHÔNG CÓ SAO KÊ")

EXPLORATORY-ONLY cycle under DECLARED costs; OI-2 NOT_RUN (Access Denied);
commission/swap/slippage/execution-spread = DECLARED or NOT_RUN, never
MEASURED; **no after-cost PASS ever**; PnL published only as exploratory
under frozen ×1.0/1.5/2.0 stress; **no edge claim from the 2020–2026
exposed folds**; validation surface = post-registration prospective
accumulation only (≥6×26w, earliest honest ≈ 2029-09).

## Frozen decisions

1. **OI-1**: IBKR HMDS D1 panel-of-record for NZD/CHF/XAU/XAG;
   LAG_DECLARED_BY_OWNER; closed bars from next business day; σ tripwire
   1σ/5σ/0.5σ frozen (NZD 64.64 / CHF 49.62 / XAU 112.18 bps — G3_G4
   file); never loosened.
2. **G5**: no PnL trim; raw BID/ASK open/close; async two-sided open =
   BAR-SIDE DIFFERENCE ≠ executable spread; O-FOLDS untrimmed =
   pessimistic-exploratory scenario; C-FULL = control; execution cost
   MEASURED only with simultaneous quotes (none exist today → all
   DECLARED). Band cells D1BAND-* frozen per G5_G6 file.
3. **G6**: AUD/CAD D1 2026-07-01→09-30 pulled (16/16 sha, 66/66
   weekdays, 0 gaps; forming bar excluded). Spread-envelope FAIL stands
   recorded; adjudicated (b) — the failing leg (absolute p90 < 8 pips)
   was never lawful for this observable (all-weekday HMDS close prints
   vs C1's Friday-20:00 Dukascopy panel). Corrected envelope law
   HMDS-D1-CLOSE-ENVELOPE@1 frozen per G6_ADJUDICATION.md (midweek-only
   magnitude gate; Friday tail disclosed-never-gated). Venue seam on the
   June overlap: p50 0.35 pips (coherent).
4. **G9 engine** (commit 09fb1b74): quote-CCY book (identity 1e-9 +
   par-replay cross-check), journal_row@1 writer (leak-law built in),
   DECLARED cost kernel (tiers ×1.0/1.5/2.0, bar-side-difference law);
   13/13 tests green; leak-clean (A1 firsthand). Synthetic fixtures only
   — no PnL computed on any real panel.
5. **Slate**: DS-03 + DS-05 only (5 parked per owner law; see
   PLAN_DAILY_SUCCESSOR_DRAFT §0b). Budget: ≤10 identities / ≤83 rows.
6. **Calendar**: EXPLORATORY folds 2020-10-02→2026-09-24 (8×26w);
   prospective = post-registration accumulation; S1 SEALED; PC12A
   exposed folds never relabeled.

## Registration gate status

| prereg gate | status |
|---|---|
| G1/G2 (statement) | NOT_RUN — owner elected exploratory-only |
| G3 (VIX) | PASS |
| G4 (σ tripwire) | computed, frozen |
| G5 (spreads) | computed, frozen |
| G6 (AUD/CAD D1) | pulled + adjudicated, frozen |
| G7 (PARAM-GAP) | complete |
| G8 (selection) | this document |
| G9 (engine) | built + tested, leak-clean |
| G10 (prospective law) | complete |
| G11 | AT registration |
| G12 (A7) | POST-registration |

All prereg gates resolved. Registration authorized by owner election.
