# G7_G8_G10_FREEZE_DRAFTS — freeze-ready declarations computed WITHOUT the statement (A1, 2026-10-01)

Statement-free by construction: nothing here requires OI-2; each item is
a DRAFT that becomes FROZEN at registration (G-rows re-run and locked;
never loosened).

## G7 — vehicle/PARAM-GAP declaration set (COMPLETE for the operative slate)

| leg | vehicle (sha-pinned basis) | PARAM-GAPs declared (frozen defaults) |
|---|---|---|
| DS-03 | USDJPY FX-spot; D1 closes from the PC12A M1 panel via the DECLARED D1-close aggregation law (panel sha per data_freeze; conId identity from the probe) | Brent-flat gate = corpus-mandatory (2× in S65); grid G1 nodes B (3%, default) / C (5%), A = reported null-control only; EIA serving lag 1bd declared (OI-5); no other free parameters |
| DS-05 | EURUSD FX-spot; D1 closes same aggregation law; inputs AUD/CAD D1 (G6) + 5 majors D1 | 20d rank window (corpus); entry rank 1–2 (corpus); 2-week consistency = entry law (corpus); exit top-3 (corpus); stop 2×ATR with ATR-14 DECLARED convention; AUD/CAD input end = G6 outcome |

Parked legs frozen AS PARKED with their named un-park conditions
(DS-01-a/b, DS-02-a, DS-04-b calendar source, DS-06-a source, DS-07
stop decision) — owner-level, each ONE action.

## G8 — selection-freeze manifest (draft; the freeze ACT happens at registration)

Frozen-content list: operative slate {DS-03, DS-05} + parked table +
excluded table; calendar §2 (EXPLORATORY 8×26w, 2020-10-02→2026-09-24 +
prospective law); budget §3 rescope (10 identities / 64–83 rows); grids
G1 (2 selectable nodes); cost kernel cells (G5 output) + DECLARED bands
with PROVISIONAL labels; OI-1 labels + σ tripwire (G4 output); journal
schema (journal_row@1 + quote-CCY rows); PASS_BARS_V2 + P-MW/P-FA scoped
to the prospective surface. The manifest file itself is written at
registration time by the cycle's freeze ceremony — this draft lists its
complete contents.

## G10 — prospective-calendar + ongoing-collection law (draft)

1. **Prospective validation surface**: ≥6×26w folds of daily bars
   accumulated AFTER the registration timestamp; warmup served from
   never-scored pre-registration bars (the 2020–2026 panel provides
   warmup + EXPLORATORY battery data only). Earliest honest evaluation ≈
   2029-09 for a 2026-10 registration (156w).
2. **Ongoing-collection law per consumed input**:
   - Majors + USDJPY/EURUSD D1: derived from the live collectors
     (FX-RANGEFADE / fx-majors panels accumulate via their lawful
     channels; SIXSOURCE ibkr_fx streaming as the read-only 7497
     corroboration) — weekly integrity check + sha manifest; any gap
     typed, never interpolated.
   - AUD/CAD/NZD/CHF D1: scheduled HMDS D1 pulls through the existing
     read-only 7497 session precedent (bounded, paced, sha-pinned) —
     PROPOSAL, executes only inside the registered cycle.
   - XAU: pinned archive frozen for the EXPLORATORY window; prospective
     accumulation from the OI-1 panel-of-record channel (HMDS D1).
   - EIA dailies: the data lane's dual-channel retrieval cadence
     (FRED + EIA official), serving lag 1bd declared.
3. **No unseal, no inference**: S1 tail stays SEALED; PC12A-exposed
   panels never relabel as untouched; nothing here scores.

## Gate status after this session's independent work

| gate | needs OI-2? | status after this session |
|---|---|---|
| G1 statement | YES | **NOT_RUN — Access-Denied blocker (owner-measured 13:45 ICT)** |
| G2 component upgrade | YES (G1) | NOT_RUN |
| G3 VIX re-verify | no | computed (G3_G4 file) — freeze-time re-run stands |
| G4 σ tripwire | no | computed incl. XAU (G3_G4 file) — freeze-time re-run stands |
| G5 daily spreads | no | computed MEASURED-DERIVED (G5_G6 file) |
| G6 AUD/CAD D1 | no | options computed; needs owner/lane pick or typed truncation |
| G7 vehicle/PARAM-GAP | no | **COMPLETE (this file)** — frozen at registration |
| G8 selection freeze | no | manifest draft COMPLETE (this file) — freeze ACT at registration |
| G9 quote-CCY engine | no | SPEC complete (plan §7b + journal law); engine build = registered-cycle work |
| G10 prospective law | no | draft COMPLETE (this file) |
| G11 GO phrase | registration act | NOT_RUN |
| G12 A7 prelaunch | post-registration | NOT_RUN |

Fail-closed unchanged: registration/scored/GO/S1 blocked until G1–G12
ALL PASS; OI-2 remains the only OWNER-FILE dependency (G1/G2) — G6's
extension pull is the one owner/lane ACTION dependency that does not
involve the statement.

## Co-owner decisions 2026-10-01 (packet 9db7f7f1) — recorded

- **G6**: HMDS D1 pull for AUDUSD/USDCAD via TWS 127.0.0.1:7497
  READ-ONLY **authorized and dispatched** (contract/pacing/sha/coverage/
  gaps/PIT verification per lane; on failure → typed NOT_RUN_INPUT_END +
  force-flat, NEVER gap-filling). Result pending in g6_pull/.
- **G5**: no PnL trim; O/C kept raw; open-side = bar-side difference not
  executable spread; O-FOLDS pessimistic-exploratory scenario, C-FULL
  control; execution cost MEASURED only with simultaneous quotes.
- **G9**: engine build/test lawful at preparation WITHOUT PnL exposure.
- **Gate order corrected**: preregistration = G1–G8 + G10; at
  registration = G11; post-registration = G12. The earlier "ALL G1–G12
  before registration" framing was circular — corrected.
- **OI-2**: G1/G2 NOT_RUN (Access Denied) ⇒ no scored/after-cost PASS;
  an EXPLORATORY-ONLY amendment is DRAFTED (below) and NOT dispatched.
