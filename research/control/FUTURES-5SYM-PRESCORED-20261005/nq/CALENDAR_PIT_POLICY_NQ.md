# CALENDAR_PIT_POLICY_NQ — NQ session/calendar/PIT policy (DRAFT-PENDING-OWNER; fail-closed everywhere)

- Round **FUTURES-5SYM-PRESCORED-20261005**, lane **NQ**, 2026-10-05. Companion to `SPEC_NQ.md`
  (§3/§4 summarize this file). Worktree HEAD `ffed828f…3940`. Every cell is
  **OBTAINED** (cite + sha256) or **NOT_OBTAINED / NOT_RUN / NOT_TRANSCRIBED** — NOT_OBTAINED is
  **never rule-derived** (standing calendar law; `CYCLE_LAUNCH_DRAFT.md` §2, sha256 `bc2b6488…cb03`).

## 1. Session mask by era (all times America/Chicago unless stated)

| era | sessions | mask law | source |
|---|---|---|---|
| **era-A** | panel start 2010-06-06 → **2015-09-18** | Globex day boundary 17:00 CT; close **16:15 CT**; era-A **Friday early-close class 15:15 CT** (handled per-session by measured last minute, not asserted) | `DATA_READINESS_NQ.md` §4 (sha256 `fc14b69c…c097`); `NQ_K6_GATES.md` §0.2 stat 3 (sha256 `364f0412…2781`) |
| **era-B** | **2015-09-21** (`SESSION_SWITCH_DATE`) → panel end 2026-09-30 (last held session 2026-10-01 partial tail — excluded by coverage law) | day boundary 17:00 CT; close **16:00 CT**; maintenance break **16:00–17:00 CT (5–6 pm ET)**; weekly shape Sun 17:00 CT (6 pm ET) open → Fri 16:00 CT (5 pm ET) close | same cites; the generic "Sun 6pm–Fri 5pm ET + 5–6pm ET maintenance" description matches **era-B only** — the era-correct law binds |

- RTH span for coverage/anatomy: **08:30 CT → era-correct close**; RTH-core coverage = share of
  minutes-with-bar; **< 0.60 ⇒ EXCLUDE session** (deterministic, per-session; the 154
  low-coverage v3 sessions are real market structure — US holidays incl. Juneteenth 2022+,
  Dec-24 half days, era-A Friday early closes, DST-fall-back Sundays, 2026-10-01 partial tail —
  full list in `v3_qc.json`, sha256 `58ec922b…e1d5`).
- Held-contract-only law: all masks, anatomy and any future fill are computed **held-contract-only**
  (mixing contracts inside sessions inflates dispersion — the class-of-defect proven on 6E and
  carried as a cross-symbol construction law).

## 2. DST law (fall-back absolute-24h quirk — PRESERVED AS MEASURED)

- The sessionization libs' comment claims DST-corrected offset arithmetic; the measured baseline
  cache proves **ABSOLUTE 24h semantics**: on fall-back Sundays, post-17:00 Globex-open bars keep
  the SUNDAY `session_date` — **35 (contract, session) rows across 2010–2024** (e.g.
  `NQH0_2020` 2019-11-03, 17 bars 17:00–21:51 CT). The v3 lib reproduces the measured behavior
  with a vectorized equivalent (proven by the 0-rows-lost strict-superset diff).
- **This quirk is LAW for this packet**: preserving it as measured is required for cache_v3
  digest equality; changing the semantics = new chain build + new digests + full before/after
  reconciliation (owner amendment class), never an in-place edit [`DATA_READINESS_NQ.md` §4;
  `CACHE_V3_PIT_STATEMENT.md` §4 seam discussion]. Spring-forward and fall-back weeks are
  **declared evaluation views** (K-V class), never silent resplits.

## 3. Holiday / early-close exclusions — fail-closed, with exact classes, windows and grounds

| # | class | windows / dates | grounds (status of the cell) | disposition |
|---|---|---|---|---|
| H1 | Any held session with RTH-core coverage < 0.60 | per-session list = the 154-row inventory in `v3_qc.json` (holidays incl. Juneteenth-from-2022, Dec-24 half days, era-A Friday 15:15s, DST-fall-back Sundays, 2026-10-01 tail) | MEASURED structure; excluded by the deterministic coverage law, never imputed | **EXCLUDE** (session-level, automatic) |
| H2 | NQ 2026 holiday **product-code** deviations | the entire 10-window 2026 register: **0/10 OBTAINED**; the trading-hours-holiday download route 403-blocked, re-confirmed 2026-10-04 (42-byte body sha `f249b63c…`, byte-identical to round-2's four 403s); committed CDX inventory has **id=146 (NQ) = 0 rows** | NOT_OBTAINED (structural absence + BLOCKED_TRANSPORT) | **EXCLUDE fail-closed** every 2026 deviation-suspect day |
| H3 | NQ 2026 advisory-**class** register | **10/10 windows classified** (`cal_janq` register; the last open cell closed this cycle-family): Good Friday **2026-04-03** — advisory text covers CME FX/Crypto 10:00 am CT + IR 10:00 am CT, **zero product codes, NO Equity-class row** | class-level only ⇒ NQ-specific Globex times still NOT_OBTAINED | **EXCLUDE** 2026-04-03 for NQ (capture `adv_gf_2026_20260913.pdf` sha `a14a3284…b36dc`, `CAL_CLOSE_REPORT.md` §1, sha256 `338cf4e8…a56f`) |
| H4 | NQ early-close times **2011 and 2021–2025** | every holiday-shortened day in those years | NOT_TRANSCRIBED (standing register) | **EXCLUDE until transcribed** (`esnq_hypotheses.json::calendar.nq_early_close_times`) |
| H5 | Expiry-calendar integrity cells | 68/68 quarters OBTAINED; Juneteenth shifts **2026-06-18, 2027-06-17**; **June-2021 NOT shifted** | authority calendar (36 product + 32 family, zero divergence) — dates are never rule-derived | any quarter whose held-chain/expiry pairing cannot be proven ⇒ **EXCLUDE whole quarter** (fail-closed; `nq_cal_coverage.json` sha256 `ad7f4b3a…bf93`) |

2026 named suspect windows visible in this cycle-family's captures (ES/6E rows exist; **no NQ row
exists in any capture — each carries exactly the requested 10-product list, no NQ row**):
MLK 2026-01-19, Good Friday 2026-04-03, July-4 2026-07-03 — all EXCLUDE for NQ under H2/H3.
Owner posture item: **P5-NQ6** (leave fail-closed vs a bounded permitted-route extension — the
D12 posture applied to NQ).

## 4. FOMC event PIT

- **Standing-outside law**: every base-FOMC statement day is EXCLUDED at day level —
  **132 statements 2011–2026, incl. 40 untimed 2011–2015** (day-level exclusion is time-safe;
  untimed statements are excluded by DAY, never by inferred time). FOMCIN-class arms use the
  inverse include set. [`SPEC_PB1_ES.md` §3 precedent carried; `CYCLE_LAUNCH_DRAFT.md` §2.]
- **Vintage table pointer (primary source + release-time proof)**: statement archive
  (`fed/statements/monetary*.html`, 147 files) with 'For release at 2:00 p.m. ET' proof lines —
  anatomy pinned in `FUTURES-DEEPRESEARCH-V2-20261003/analysis/NQ_a4_events.json` (sha256
  `5a09aff9…66d`, cited at `NQ_K6_GATES.md` header); on cache_v3 the timed-14:00 set reproduces at
  **n = 85** (v3 admits exactly one additional event, **2020-04-29**, whose held session
  NQM0_2020 has coverage 1.0 post-repair) [`NQ_K6_GATES.md` §1; `m1_fomc_anatomy_v3.json`
  sha256 `78c094aa…7fdf`].
- Minute anatomy 2011–2015: **NOT_RUN** (statements carry no release-time line; day-level only) —
  standing committed NOT_RUN, respected, never inferred.

## 5. BLS vintage law (CPI / NFP-EMPSIT, the 08:30 ET / 07:30 CT clock)

- **First-published vintage rule**: calendars are keyed to the **vintage as-of the decision date**
  (`available_time = vintage(decision_date)`); **current-calendar inference FORBIDDEN** everywhere
  (standing ruling). CPI **204** + EMPSIT **204** scheduled dates 2010–2026, all 08:30 ET
  (07:30 CT), per-year wayback snapshot verifiers [`esnq_hypotheses.json::bls_pit`, sha256
  `68e21c56…6605`; machine table `bls_dates.json` sha `ad41d2a7…` recorded at
  `NQ_K6_GATES.md` header].
- **Lapse anomalies carried as law (canceled-and-rescheduled days are separate strata, never
  pooled into release cells)**: 2025 — CPI Oct-ref Nov-13 and EMPSIT Oct-ref Nov-7 **CANCELED**;
  CPI Sep-ref Oct-15→24, Nov-ref Dec-10→18; EMPSIT Sep-ref Oct-3→Nov-20, Nov-ref Dec-5→16; recurs
  2026 — CPI Jan-26 ref Feb-11→**13**; EMPSIT Feb-6→11. Canceled-but-expected days measured
  control-level (no print ⇒ no spike) — the vintage-law falsifier direction, descriptive only
  [`NQ_K6_GATES.md` §5 release cells].
- **D5 pin (SIX-GATE cal_close)**: CPI January-2026 released **Friday 2026-02-13, embargo 08:30
  a.m. ET** — two independent official BLS artifacts agree (pre-release schedule snapshot Wayback
  `20260207070202` sha `9d3db688…` + release document `cpi_02132026.htm` sha `fdb36ea5…`, USDL-26-0186)
  [`CAL_CLOSE_REPORT.md` §1/§6-T4].
- Surprise/consensus content and actual-publish latency: **NOT_RUN** (no PIT consensus archive) —
  no NQ family may condition on them.

## 6. NQ 2026 deviations — status register (post cal_close)

| cell class | before this cycle-family | after | source |
|---|---|---|---|
| 2026 product-code holiday deviations | 0/10 | **0/10** — absence re-proven from committed CDX (id=146 = 0 rows) + content level; only routes BLOCKED_TRANSPORT | `CAL_CLOSE_REPORT.md` §2/§3 |
| 2026 advisory-class windows | 9/10 (Good Friday pending) | **10/10** — Good Friday closed at CLASS level only | `CAL_CLOSE_REPORT.md` §1/§3 |
| Consequence for any NQ freeze | — | every 2026 early-close-suspect day stays **EXCLUDE fail-closed** unless a per-session measured coverage proves ordinary structure (H1 path) | this file §3 |

— End CALENDAR_PIT_POLICY_NQ. Fail-closed everywhere; nothing derived where evidence is absent.
