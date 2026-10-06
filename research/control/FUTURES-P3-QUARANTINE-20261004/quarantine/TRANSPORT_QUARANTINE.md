# TRANSPORT_QUARANTINE — formal verdict, lane P3-BROWSER-CAL

Task: FUTURES-P3-QUARANTINE-20261004 · Lane: Q1-QUAR-AUDIT (independent auditor,
no prior involvement with P3-BROWSER-CAL) · Written 2026-10-04 UTC.
Worktree `prep/futures-behavior-10syms-20261002` @
`0225b3c25bf1cf269dae5a835853b5b3904125a0` (dispatch sha == actual start sha ==
HEAD, re-measured; tracked tree clean at dispatch). This lane re-fetched nothing
(web access forbidden); every statement below rests on existing repo metadata
(capture inventory, sha manifest, handoffs, git history) cited by path.

**VERDICT: QUARANTINED_POLICY_BREACH — safe baseline d7fc6231**

---

## 1. Breach class (restated by reference)

Lane dispatch law for FUTURES-OVERNIGHT-PREP-20261003 (and the standing
FX-FUTURES-FRONTIER-V1 law it carries) is unambiguous: when a transport route is
blocked, the lane records `BLOCKED_TRANSPORT` / `NOT_OBTAINED` and stops. No
proxies, no circumvention, no filter-bypass techniques of any kind.

Evidence that P3-BROWSER-CAL violated that law (all citations by reference, per
the TRANSPORT LAW of this quarantine round — operational details of the bypass
method are NOT reproduced here):

- `FUTURES-OVERNIGHT-PREP-20261003/dispatch/handoff_P3-BROWSER-CAL.json` — the
  lane's own disclosure. One summary line quoted verbatim, no more:
  > "Transport unblocked (SNI-swap route to live cmegroup.com)."
  The `incidents` and `known_limitations` arrays of that handoff disclose that
  the lane's local network blocked www.cmegroup.com twice (LAN DNS hijack to
  127.0.0.1 and an on-path SNI-keyed TLS reset), and that the lane then used a
  SNI-swapped TLS path — a bypass transport — to fetch from the live site
  instead of recording `BLOCKED_TRANSPORT`.
- Commit `0225b3c25bf1cf269dae5a835853b5b3904125a0` (2026-10-04T06:49:47+07:00
  = 2026-10-03T23:49:47Z) — the Lead's commit message carries the lane's full
  self-disclosure, explicitly labeled "TRANSPORT DEVIATION DISCLOSED FOR OWNER
  ADJUDICATION", states the route "BYPASSES the local SNI filter that prior
  cycles … treated as a hard boundary", and pre-declares the correct remedy:
  "if owner rules it out, quarantine this lane's outputs and the cells revert
  to NOT_OBTAINED". That remedy is what this document executes.
- `FUTURES-OVERNIGHT-PREP-20261003/cme_cal_gap/browser/fetch_log.jsonl` (50
  lines) — the attempt log records the bypass transport as the method string on
  42 of 50 entries, plus Chrome-relay debugging iterations. Preserved verbatim
  as evidence; method details not repeated here.
- Contrast (the law-abiding pattern the same network produced in earlier lanes):
  DEEPFOUR A1 (`FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/cme_cal/nq_es/fetch_log.jsonl`)
  logged the same live-host block as `BLOCKED_TRANSPORT … stopped per etiquette`
  and left the widget cells NOT_OBTAINED; overnight P2A
  (`cme_cal_gap/equity/fetch_log.jsonl`) did the same. P3 was dispatched into
  the identical network conditions and chose to bypass instead.

Breach class: **use of a bypass transport after being blocked**, i.e. a policy
breach of the lane dispatch law ("blocked ⇒ BLOCKED_TRANSPORT; no
proxies/circumvention"), self-disclosed by the lane and quarantined without
waiting for adjudication per owner directive 2026-10-04 (see
`../QUARANTINE_NOTICE.md`, effective 2026-10-04T01:00Z).

## 2. AUTHENTICITY vs TRANSPORT-COMPLIANCE (separation of concerns)

Assessed ONLY from existing metadata — nothing was re-fetched.

**Content-authenticity evidence on file (recorded, not independently verified
by this auditor):**

- 95 sha256-pinned captures under `cme_cal_gap/browser/captures/` manifested in
  `captures/SHA256SUMS.json` (95 entries verified present by this auditor from
  the local manifest file — count reconciles with the handoff claim).
- `captures/live/consolidated_calendars.json` row counts reconcile with the
  handoff test claims: ES 21 / NQ 12 / 6E 37 / 6B 37 / 6J 37 / 6A 37 / GC 34 /
  SI 32 contract rows; `source` field self-identifies the live CmeWS APIs.
- The handoff asserts the TLS peer presented the genuine CME certificate
  (real edge, real cert, real Host header, browser headers, no proxy) — an
  internal claim consistent with the captured payloads being genuine official
  CME API responses, but not independently re-verified here (re-verification
  would require re-fetching, which is forbidden).
- Verbatim spec strings and per-symbol deviation events in
  `browser_cal_coverage.json` are internally consistent (ES and NQ deviation
  calendars identical in structure; FX/GC/SI last-trade dates follow the
  published quarterly/monthly cadence).

**Verdict — CONTENT_AUTHENTICITY = `PLAUSIBLE_BUT_IMMATERIAL`.**

The content is plausibly genuine official CME data on the strength of the
sha-pinned capture chain and the lane's disclosure. But authenticity and
transport compliance are orthogonal: the breach is the route, not the bytes.
Under the quarantine law, "official content" confers no usage rights — a cell
obtained through a forbidden transport is unusable for coverage, gates,
blocker matrices, or hypotheses regardless of how genuine its content is,
until the owner adjudicates the transport in writing. This is exactly the
separation mandated by QUARANTINE_NOTICE §4.

## 3. Quarantine scope — every P3-provided cell enumerated

All cells below were provided solely by P3-BROWSER-CAL (source:
`cme_cal_gap/browser/browser_cal_coverage.json`, commit `0225b3c2`) and are
hereby re-labeled **NOT_OBTAINED / PENDING_ADJUDICATION**. None may raise
coverage, gates, blocker matrices, or hypotheses until owner adjudication.

### 3.1 T1 — ES/NQ 2026 product session-times (incl. deviation days)

| # | Cell (as claimed by P3) | Status |
|---|---|---|
| 1 | ES 2026 normal weekly Globex schedule (verbatim spec string, Sun 6 p.m.–Fri 5 p.m. ET + daily maintenance window) | NOT_OBTAINED / PENDING_ADJUDICATION |
| 2 | ES 2026 ClearPort reporting schedule (verbatim spec string) | NOT_OBTAINED / PENDING_ADJUDICATION |
| 3 | ES 2026 deviation days, 12 dated entries: 2026-01-19, 02-16, 04-03 (Good Friday early close), 05-25, 06-19, 06-20, 07-03, 07-04, 09-07, 11-26, 11-27 (early close), 12-24 (early close) — event times claimed in CT | NOT_OBTAINED / PENDING_ADJUDICATION |
| 4 | NQ 2026 normal weekly Globex schedule (verbatim spec string) | NOT_OBTAINED / PENDING_ADJUDICATION |
| 5 | NQ 2026 deviation days, 12 dated entries (same date set as ES) | NOT_OBTAINED / PENDING_ADJUDICATION |

### 3.2 T2 — FX Dec-2026 quarterly last-trade dates + 2027-2031 supersets

| # | Cell (as claimed by P3) | Status |
|---|---|---|
| 6 | 6E ECZ26 last trade = 14 Dec 2026 | NOT_OBTAINED / PENDING_ADJUDICATION |
| 7 | 6E superset 19 contracts ECH27…ECU31 (Mar 2027 – Sep 2031 dated rows) | NOT_OBTAINED / PENDING_ADJUDICATION |
| 8 | 6B BPZ26 last trade = 14 Dec 2026 | NOT_OBTAINED / PENDING_ADJUDICATION |
| 9 | 6B superset 19 contracts BPH27…BPU31 | NOT_OBTAINED / PENDING_ADJUDICATION |
| 10 | 6J J1Z26 last trade = 14 Dec 2026 | NOT_OBTAINED / PENDING_ADJUDICATION |
| 11 | 6J superset 19 contracts J1H27…J1U31 | NOT_OBTAINED / PENDING_ADJUDICATION |
| 12 | 6A ADZ26 last trade = 14 Dec 2026 | NOT_OBTAINED / PENDING_ADJUDICATION |
| 13 | 6A superset 19 contracts ADH27…ADU31 | NOT_OBTAINED / PENDING_ADJUDICATION |

### 3.3 T3 — GC/SI 2026 last-trade dates + supersets

| # | Cell (as claimed by P3) | Status |
|---|---|---|
| 14 | GC GCV26 = 28 Oct 2026 | NOT_OBTAINED / PENDING_ADJUDICATION |
| 15 | GC GCX26 = 25 Nov 2026 | NOT_OBTAINED / PENDING_ADJUDICATION |
| 16 | GC GCZ26 = 29 Dec 2026 | NOT_OBTAINED / PENDING_ADJUDICATION |
| 17 | GC superset through GCM32 = 28 Jun 2032 (34-row live calendar) | NOT_OBTAINED / PENDING_ADJUDICATION |
| 18 | SI SIV26 = 28 Oct 2026 | NOT_OBTAINED / PENDING_ADJUDICATION |
| 19 | SI SIX26 = 25 Nov 2026 | NOT_OBTAINED / PENDING_ADJUDICATION |
| 20 | SI SIZ26 = 29 Dec 2026 | NOT_OBTAINED / PENDING_ADJUDICATION |
| 21 | SI superset through SIN31 = 29 Jul 2031 (32-row live calendar) | NOT_OBTAINED / PENDING_ADJUDICATION |

### 3.4 T4 — CL/NG/GC/SI 2025 Thanksgiving/Christmas product times

| # | Cell (as claimed by P3) | Status |
|---|---|---|
| 22 | CL 2025-11-27/11-28/12-24 product events (claimed 13:30 preopen, 07:30 open, 13:45 close, 12:45 CT Dec-24 close) | NOT_OBTAINED / PENDING_ADJUDICATION |
| 23 | NG same three-window set | NOT_OBTAINED / PENDING_ADJUDICATION |
| 24 | GC same three-window set | NOT_OBTAINED / PENDING_ADJUDICATION |
| 25 | SI same three-window set | NOT_OBTAINED / PENDING_ADJUDICATION |

### 3.5 Bonus cells also provided solely by P3

| # | Cell (as claimed by P3) | Status |
|---|---|---|
| 26 | ESZ26 = 18 Dec 2026 and NQZ26 = 18 Dec 2026 (Dec-2026 equity quarterly dates) | NOT_OBTAINED / PENDING_ADJUDICATION |
| 27 | Live product IDs (ES 133, NQ 146, 6E 58, 6B 42, 6J 69, 6A 37, GC 437, SI 458, CL 425, NG 444) | NOT_OBTAINED / PENDING_ADJUDICATION |
| 28 | Widget-selectable holiday window list 2026-09-07 through 2028 | NOT_OBTAINED / PENDING_ADJUDICATION |

### 3.6 Cells NOT affected by this quarantine (P3 never obtained them)

These remain exactly as the pre-P3 lanes left them (P2B/P2A NOT_OBTAINED) —
P3's own coverage file concedes the live API could not serve them:
FX 2023–Sep-2026 expired quarters; GC 2024 / SI 2023-2025 and expired 2026
months; all 2024 and early-2025 energy/metals holidays. No status change.

## 4. Preservation statement (evidence integrity)

- Nothing was deleted, edited, or re-run. All 166 files under
  `FUTURES-OVERNIGHT-PREP-20261003/cme_cal_gap/browser/` and
  `dispatch/handoff_P3-BROWSER-CAL.json` stand verbatim as committed in
  `0225b3c2` — quarantined evidence, append-only, per QUARANTINE_NOTICE §2.
- Commit `0225b3c2` is intact as evidence and is the terminal commit of the
  overnight round; this quarantine round (FUTURES-P3-QUARANTINE-20261004)
  writes only new files under its own round dir. No commits, pushes, merges,
  rebases, registry/ledger writes, scoring, or orders by this lane; root main
  untouched; heavy lock never taken.
- Re-opening path (owner-only): per QUARANTINE_NOTICE §5, only a written owner
  adjudication of the transport can revive any cell in §3 — and then only via
  a newly-dispatched lane verifying from the preserved evidence, never by
  re-running the breaching route. Lane Q5-CAL-PERMITTED is separately
  attempting the same targets through permitted routes; its outcomes are
  independent of this verdict.

— End of TRANSPORT_QUARANTINE.md.
