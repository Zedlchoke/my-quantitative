# CAL_COST_REPORT — LANE-CALCOST, round FUTURES-5SYM-PRESCORED-20261005 (PREP-only)

Generated 2026-10-05. Relaunch of this lane: the prior attempt died to infrastructure rate-limiting
BEFORE writing anything — this lane started fresh (no prior artifacts existed; `cal_cost/` was empty
at start). Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-5sym-prescored/prep`,
branch `prep/futures-5sym-prescored-20261005`. HEAD at lane start: `b051d61e3a8d061412e1837bfc046a419e16dd10`.

Scope: NQ, 6E, 6B, 6J, 6A — inventory then lawful closure of residual calendar cells + cost-state
verification. **Fetch budget: 18 / 40 attempts used** (all logged in `fetch_log.jsonl`; 9× HTTP 200).

## 0. Transport-law compliance statement

Permitted routes only: plain curl to web.archive.org (CDX + `id_` replays), plain curl to official
domains (federalreserve.gov, boj.or.jp, bankofengland.co.uk, rba.gov.au), WebFetch (1 blocked
attempt, logged). MAX 2 attempts per URL honored (two URLs reached the cap and were abandoned:
the two syntax-400 CDX forms replaced by corrected distinct URLs; the `trading-hours*` family
wildcard 503'd twice and was replaced by narrower per-service URLs). No live cmegroup.com content
obtained (egress sinkhole — see §2). No proxies/SNI tricks/UA spoofing/logins. No P3-quarantined
content accessed (the `.worktrees/futures-behavior` tree was never opened; every capture in this
lane is this lane's own fresh capture). Captures under `captures/` (13 files, incl. failure
evidence), hashed in `SHA256SUMS_calcost.txt`.

## 1. Cells CLOSED this lane (with captures)

| cell | value | provenance |
|---|---|---|
| **EV-1 BoE MPC 2026** (6B event calendar) | Full 2026 confirmed announcement dates: Thu 5 Feb, 19 Mar, 30 Apr, 18 Jun, 30 Jul, 17 Sep, **5 Nov, 17 Dec**; page states "Next due: 5 November 2026", Bank Rate 3.75%. Remaining-2026 = **2026-11-05, 2026-12-17** | `captures/boe_mpc_live.html` sha `2464e218…`, bankofengland.co.uk/monetary-policy/upcoming-mpc-dates, 200, log line 15 |
| **EV-2 BoJ MPM remaining-2026** (6J event calendar; DATES ONLY — intraday stamps stay NOT_IN_CORPUS) | Remaining-2026 meetings: **Oct 29–30, Dec 17–18, 2026** (verbatim table: "Oct. 29 (Thurs.), 30 (Fri.)", "Dec. 17 (Thurs.), 18 (Fri.)" with their release dates) | `captures/boj_mpm_live.html` sha `a6a7958a…`, boj.or.jp/en/mopo/mpmsche_minu/index.htm, 200, log line 14 |
| **EV-4 FOMC remaining-2026** (NQ/ES-relevant event calendar) | Remaining-2026 decision meetings: **October 27–28, December 8–9** (Dec starred = SEP meeting); full 2026 set Jan 27-28 … Dec 8-9 (8 meetings) | `captures/fomc_calendars_live.html` sha `362f22e3…`, federalreserve.gov/monetarypolicy/fomccalendars.htm, 200, log line 13; year-section parse verified against header anchors |
| **EV-3 RBA 2026 — PARTIAL** (6A contingency) | 2026 decisions to date: 3 Feb, 17 Mar, 5 May, 16 Jun, 11 Aug, **29 Sep** 2026. Forward Nov/Dec dates **NOT_OBTAINED** (see §2) | `captures/rba_decisions_live.html` sha `fea5ba99…`, 200, log line 16 |

These are NEW event-calendar register cells opened by this round's dispatch (decision-time-knowable
schedules); they do not alter the 68-cell FX expiry grids or holiday registers. The BoE capture also
upgrades the corpus-assembled 6B_DEEP_v2 MPC dates (provenance class "assembled") to
official-capture grade for 2026.

## 2. Cells STILL OPEN, with honest grounds (nothing forced)

| cells | state | grounds (fresh, 2026-10-05) |
|---|---|---|
| **NQ 2026 holiday-deviation, product-code level (id=146), 10 windows** | NOT_OBTAINED 0/10 (unchanged) | Fresh complete no-collapse CDX of `services/trading-hours-by-product` (709 rows / 83 timestamps — byte-set identical to committed round-2 inventory; zero new crawls): `id=146` = **0 rows**. `holiday-download`: only 2 archived captures exist (2025-04-22, 2025-08-29), both 403 error bodies — replayed this lane, 42-byte sha `f249b63c…` byte-identical across three rounds. Holiday-calendar HTML page: **zero** 200 captures archived (all 301/302). Live cmegroup.com: ECONNREFUSED 127.0.0.1:443 at egress — re-confirmed through the WebFetch tool (prior evidence was curl-only). Advisory class-level register (10/10, cal_close) remains the operative evidence. |
| **6B holidays ×42; 6J holidays ×42; 6A holidays ×42** (product-code level) | PROVEN_ABSENT, structural (re-confirmed fresh) | Same fresh 709-row CDX: `id=42` = 0 rows, `id=69` = 0 rows, `id=37` = 0 rows across every capture of the family; anchors id=58/id=133 present. Holiday-download dead (above). Advisory/settlement PDF families carry no product codes (committed family inspections). |
| **6B expiry 2023Q1–2024Q2 (BPH23, BPM23, BPU23, BPZ23, BPH24, BPM24)** | PROVEN_ABSENT (re-confirmed fresh; dispatch's earlier-vintage hunt EXHAUSTED) | Fresh no-collapse `CmeWS/mvc/ProductCalendar*` CDX (450 rows, 440×200): `Download.xls?productId=42` = exactly 4 captures, ALL ≥ 2024-09-03 (20240903 ×2, 20241006, 20241108) — **no earlier vintage exists anywhere in the archive**; Future/42 pre-span (2017-06..2018-04); Options/42 pre-span (2018) and an options surface regardless; live route blocked. The two committed vintages' expired-contract drop proof stands. |
| **6J expiry 2023 ×4 (J1H23/M23/U23/Z23); 6A expiry 2023Q1/Q2 (ADH23, ADM23)** | PROVEN_ABSENT (unchanged) | Same fresh CDX: `productId=69` = 2 captures, both post-expiry (2024-09-04, 2025-11-04); `productId=37` = **ZERO** captures; Future/69 pre-span only; Future/37 post-expiry from 2023-09-16. |
| **6J expiry — 2 cells, identity undetermined** | NOT_RUN, flagged to owner (carried) | Identity not determinable without forbidden derivation (IMM/grid arithmetic). Not re-derived. |
| **6E holidays — 8 windows** (2022-12-31, 2023-01-15, 2023-02-19, 2023-04-06, 2023-05-28, 2023-06-18, 2023-07-03, 2025-01-05) | INCONCLUSIVE_AGED_OUT (unchanged; never counted) | Fresh CDX re-check: each window still carries exactly ONE out-of-bracket capture (fromEventDate set enumerated in `CALENDAR_DELTA.json`); no forward-horizon captures; the one route that could serve them (live per-product service) is egress-blocked. Per standing law these are never counted. |
| **EV-3 RBA forward 2026 dates (Nov/Dec)** | NOT_OBTAINED (partial cell) | int-rate-decisions page lists released decisions only; monetary-policy landing page carries no forward schedule; `/about-rba/calendar/` = 404 (kept as evidence). No further permitted surface identified without URL-guessing. |

## 3. Fail-closed exclusion impact (which research windows stay excluded)

- **NQ**: 2026 holiday-deviation windows remain usable ONLY at advisory-class level; any
  NQ-specific holiday session-time consumption (product level) stays **EXCLUDED** while the
  10 product-level cells are NOT_OBTAINED. NQ quarterly expiry 4/4 closed (unaffected).
- **6B**: research windows touching 2023Q1–2024Q2 quarterly roll/expiry dates remain **EXCLUDED**
  (6 cells proven-absent at archive level; earlier-vintage hunt exhausted). 2026 event-calendar
  layer now has official MPC dates (newly closed, positive evidence — no exclusion needed for BoE days).
- **6J**: 2023 quarterly expiry windows excluded (4 proven-absent + 2 identity-flagged);
  BoJ MPM dates now officially pinned for remaining-2026 (dates only).
- **6A**: 2023Q1/Q2 expiry windows excluded; era-2-only cost models still may not back-cast into
  2020 windows (standing law); RBA contingency has decisions-to-date only — forward Nov/Dec RBA
  days are NOT covered by official capture (contingency consumers must fail closed on those dates).
- **6E**: 8 aged-out holiday windows remain INCONCLUSIVE (never counted; standing exclusion).
  2026 holiday windows remain 10/10 documented (3 at FACT grade in this worktree, cal_close).

## 4. COST side (no network; see COST_STATE_VERIFY.md)

- 3 key A7 files re-hashed: `A7_FEE_REAUDIT.md` MATCH vs this round's authority-matrix record
  (`2c1095d6…`, 2 occurrences); `a7_fee_digest.json` = `fa697c69…` (no external comparator existed —
  baseline recorded here; internal-integrity spot-checks 4/4 MATCH incl. validator script
  `fdead766…`); `a7_validator_report.json` = `a9078769…` (byte-comparator absent; **content
  comparator reproduced: 37/37 statuses identical** to the committed p0 validator report).
- Dual-variant cost-freeze law restated citation-only: stale 21.006/33.506/46.006 prints never
  consumable; Variant A 2.25/side (NFA 0.02) vs Variant B 2.24/side (0.01 offset), delta
  0.01/side = 0.02/RT; **e.1–e.4 remain UNRULED (owner slot)**.
- Per-symbol modeled RT floors restated with verified citations: 6J $67.42 = 8.4499 bp T1 (sha
  `6ca0baeb…` re-verified); 6A era law $104.92 / $54.92; 6E 3.6–6.3 bp; 6B 6.3–11.2 bp.
- No fee numbers changed; language law (MODELED COST / VERIFIED_VS_ACCOUNT=NOT_RUN) untouched.

## 5. Decision items for owner/controller (namespaced P5-CALC-*; no collisions)

- **P5-CALC-NQ-HOLPROD**: NQ 2026 holiday product-level (id=146) — every permitted route exhausted
  with fresh enumeration; adjudicate whether the advisory class-level register (10/10) is accepted
  as operative for NQ with product-level documented-exclusion, or whether cells stay open pending
  unblocked live/archive access. (Also applies mutatis mutandis to 6B/6J/6A holiday registers,
  which are stronger: structural absence.)
- **P5-CALC-6J-IDENT**: the 2 identity-undetermined 6J expiry cells remain flagged (carried from
  cal_janq/cal_close); resolution requires an owner-defined identity source (derivation forbidden).
- **P5-CALC-RBA-FWD**: RBA forward 2026 decision dates (Nov/Dec) NOT_OBTAINED — decide whether the
  6A contingency requires them before any consumption, or whether fail-closed exclusion on those
  dates stands.
- **P5-CALC-FEE-E14**: e.1–e.4 (fee variant selection + sub-rulings) remain UNRULED — owner slot;
  any downstream cost freeze must wait for the ruling or keep both variants dual-tracked.

## 6. Incidents

- Prior lane attempt (same lane id) died to infrastructure rate-limiting before writing anything —
  relaunch performed; nothing was inherited (cal_cost/ was empty). This lane paced its fetches
  (18/40; sleeps between calls) and completed all deliverables.
- Blocked routes recorded (not bypassed): live cmegroup.com egress sinkhole (WebFetch + curl);
  holiday-download archived replays 403 ×2; wayback CDX transients 503×2/504×1 (retried within cap
  on corrected URLs); RBA `/about-rba/calendar/` 404 (wrong-surface guess, kept as evidence);
  2 CDX syntax-400s (corrected URL forms used; both abandoned URLs left at cap).

## 7. Artifacts

`RESIDUAL_BASELINE.md` (pre-fetch) · `CALENDAR_DELTA.json` (machine delta) · `COST_STATE_VERIFY.md` ·
this report · `fetch_log.jsonl` (18 lines) · `fetch_lane.py` (deterministic fetch/log tool) ·
`captures/` (13 files) · `SHA256SUMS_calcost.txt` (captures + deliverables) ·
`../dispatch/handoff_CALCOST.json`. No commits; no writes outside `cal_cost/**` +
`dispatch/handoff_CALCOST.json`.
