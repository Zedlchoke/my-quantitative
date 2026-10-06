# CAL_CLOSE_REPORT — bounded permitted-route calendar closure (D12 residual + D5 pin + ES/NQ 2026 holiday deviations)

Round FUTURES-SIX-SCORED-GATE-PREP-20261004 · lane CAL-CLOSE · generated 2026-10-04.
Worktree `/Users/hoangminhlong/.worktrees/futures-six-gate/prep` (absolute:
`/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-gate/prep`), branch `prep/futures-six-gate-20261004`.
actual_start_sha (measured once, bare 40-hex): `893db28cd1b3299c914369ec08cb33f68bf5798a` == dispatch base. commit_sha: null (lane writes files only).
Pre-fetch enumeration: `RESIDUAL_INVENTORY.md` (written before any network attempt). Machine mirror: `calendar_close_delta.json`.

## 1. What was attempted, obtained, blocked

19/30 fetch attempts used (all logged in `fetch_log.jsonl`, incl. 2 retro-logged manual attempts).
Permitted routes only: web.archive.org (CDX + `id_` replays), bls.gov direct. No live cmegroup.com,
no proxies/SNI tricks/UA spoofing/logins.

### Obtained (FACT = capture + sha256 + fetch-log line)

| cell | value (verbatim basis) | provenance |
|---|---|---|
| **NQ 2026 Good-Friday advisory window (2026-04-01)** — was the only NOT_OBTAINED window in cal_janq's 10-window register ("Pending" at only archived vintage) | Advisory FILLED at newest vintage: "Good Friday 4/3/2026 Settlement Times — Friday, April 3, 2026 — CME Group FX and Cryptocurrency Products 10:00 am CT — CME Group Interest Rate Products 10:00 am CT"; BLS March Employment Situation note (settlements derived on trade date April 3rd) | `captures/adv_gf_2026_20260913.pdf` sha256 `a14a3284…b36dc`, Wayback `20260913074752`, official URL `cmegroup.com/tools-information/holiday-calendar/files/2026/good-friday-holiday-settlement-times-2026.pdf`; text extraction at `captures/adv_gf_2026_20260913.txt`. **Class-level only** (FX/Crypto + IR; zero product codes; no Equity-class row) |
| **ES 2026 holiday deviations — FACT grade in THIS worktree ×3 windows** (MLK 01-18, Good Friday 04-01, July-4 07-02), ES id=133 rows transcribed verbatim in `calendar_close_delta.json` | e.g. ES 2026-04-03 `[08:15 closed]` (Good Friday early close), ES 2026-07-03 `[12:00 closed]`, ES 2026-01-19 `[12:00 preopen, 17:00 open]` | `captures/svc_20260118_20260812185118.json` (wire sha `5184b760…`), `captures/svc_20260401_20260722114222.json` (`cdba0a65…`), `captures/svc_20260702_20260129012310.json` (`6fbf2904…`) — Wayback `id_` replays of archived `trading-hours-by-product` 2026-window URLs read from committed round-2 CDX inventory. Gunzip shas of two captures are BYTE-IDENTICAL to round-1's independently verified files (`61603abf…`, `d97339fb…`) |
| **Recovery: `svc_20260401_20260722114222.json`** — listed MISSING-from-disk in round-1's ES independent verification | First local verification of that capture; served gunzip sha `d1c4048f…` does **not** match round-1's recorded claimed sha `0700f57c…` → round-1's claimed-hash row for this ts remains UNVERIFIED (source bytes under P3 quarantine, inaccessible to this lane); the ES Good-Friday cell rests on this lane's own chain | same capture as above; disclosed as a correction |
| **6E 2026 holiday windows ×3 corroboration** (id=58 rows in the same captures) | 6E 2026-01-19 `[12:00 preopen, 17:00 open]`; 2026-04-03 `[10:15 closed]`; 2026-07-03 `[12:00 closed]` | same three captures |
| **D5 — BLS CPI January 2026 announcement pin** | Schedule row: "January 2026 — Feb. 13, 2026 — 08:30 AM"; release document embargo line: "Transmission of material in this release is embargoed until 8:30 a.m. (ET) Friday, February 13, 2026" (USDL-26-0186) | Schedule snapshot `captures/bls_cpi_sched_20260207.html` sha `9d3db688…` (Wayback `20260207070202` of `bls.gov/schedule/news_release/cpi.htm`, PRE-release) + release document `captures/bls_cpi_jan2026_release.html` sha `fdb36ea5…` (Wayback `20260913074752` of `bls.gov/news.release/archives/cpi_02132026.htm`). Two independent official BLS artifacts agree |

### Blocked (honest statuses)

| target | route | status |
|---|---|---|
| NQ/6J/6A holiday deviations at PRODUCT-CODE level (all windows) | Wayback replay of `cmegroup.com/services/trading-hours-holiday-download` @20250829195952 | **BLOCKED_TRANSPORT** — 403, 42-byte body sha `f249b63c…` byte-identical to round-2's four 403s. Standing block re-confirmed 2026-10-04. 1 attempt this lane. |
| D5 BLS pin, DIRECT route | `bls.gov/schedule/news_release/cpi.htm` (×2 = cap) + `bls.gov/schedule/2026/01_sched.htm` (×1) | **BLOCKED_TRANSPORT** — 403 "Access Denied" Akamai bot-block on every plain-curl attempt (site-wide). Pin taken via web.archive.org replays of the official pages instead (within the dispatch permitted set "official domains + web.archive.org"; archive-of-official is not a bypass of an access control — same route class used for CME). |
| Post-release schedule snapshot @20260213183647 | Wayback `id_` replay | FAILED 500 ×2 (cap reached) — not needed; the release document supersedes. |
| Wayback transients | CDX probes | 503 ×2 — each retried successfully within cap. |

### Transport-discipline violation (disclosed)

One (url,method) pair exceeded the ≤2 cap: the good-friday-advisory CDX URL got a 3rd attempt
(503 → 200 → manual 200 re-run to tee the body to disk). Same idempotent GET, no bypass technique.
Both manual attempts are retro-logged in `fetch_log.jsonl` with the violation marked. 19 attempts
total; budget 30.

## 2. Local absence re-verification (no fetch; from committed evidence)

Exact id-token parse of the committed 709-row trading-hours CDX inventory
(`FUTURES-SIX-ADOPT-PREP-20261004/cal_eb/captures/cdx_th_full.txt`, 80 distinct capture timestamps):
id=42 (6B) **0 rows**; id=69 (6J) **0 rows**; id=37 (6A) **0 rows**; id=146 (NQ) **0 rows**;
anchors id=58 (6E) 685 rows, id=133 (ES) 688 rows. This (a) confirms the 6B/6J/6A holiday
structural-absence proofs, (b) re-derives cal_janq's NQ absence claim (whose own in-log probe had
failed curl rc=3) from committed bytes, and (c) is corroborated at content level by this lane's three
captures (each carries exactly the requested 10-product list, no NQ row).

## 3. Per-symbol coverage after this lane

| symbol / dimension | before (after round 2) | after (this lane) |
|---|---|---|
| 6E expiry (68-cell grid) | 66/68 | **66/68** — ECU26/ECZ26 upgraded to CLOSED_PROVEN_ABSENT (documented exclusion; no fetchable route; future re-crawls would be needed) |
| 6B expiry | 62/68 | **62/68** — BPH23..BPM24 (6) CLOSED_PROVEN_ABSENT |
| 6J expiry | 62/68 | **62/68** — 2023 ×4 CLOSED_PROVEN_ABSENT; **2 cells remain NOT_RUN (identity undeterminable without forbidden derivation; flagged to owner)** |
| 6A expiry | 66/68 | **66/68** — 2023Q1/Q2 CLOSED_PROVEN_ABSENT |
| **FX 4-code grid** | **256/272** | **256/272** (no new cells; classification upgraded: 14 documented exclusions + 2 flagged) |
| 6E holidays | 34/42 + 8 INCONCLUSIVE_AGED_OUT | unchanged; ×3 of the 34 windows corroborated at FACT grade in this worktree |
| 6B holidays | 0/42 structural absence | 0/42 — re-verified locally (id=42 = 0 rows) |
| 6J holidays | 0/42 product-code level | 0/42 — re-verified locally (id=69 = 0 rows) |
| 6A holidays | 0/42 product-code level | 0/42 — re-verified locally (id=37 = 0 rows) |
| ES 2026 holidays | 11 windows / 23 cells OBTAINED (round-1 verified; OBSERVED here) | **OBTAINED, 3 windows now FACT-grade in this worktree** (2 byte-identical + 1 recovered capture with disclosed claimed-hash mismatch); ES 2011-2025 product-level times remain NOT_TRANSCRIBED (round-1 register; fail-closed) |
| ES expiry | 68/68 (round-1 recheck) | unchanged |
| NQ 2026 holidays — product-code level | 0/10 | **0/10** — absence re-proven from committed CDX + content level; only routes (holiday-download, live) BLOCKED_TRANSPORT |
| NQ 2026 holidays — advisory class level | 9/10 (1 NOT_OBTAINED: Good Friday) | **10/10** — Good Friday window closed at class level (4 normal_or_closure_only + 6 class_level) |
| D5 BLS CPI Jan-2026 pin | NOT_OBTAINED | **OBTAINED — Friday 2026-02-13, embargo 08:30 a.m. ET** |

## 4. Corrections to prior rounds (evidence-first)

1. cal_janq's "Good-Friday advisory Pending at the only archived vintage" was **incomplete**: the
   no-collapse CDX lists 3 timestamps (20251013214632, 20260422061020, 20260913074752); the Sep-2026
   vintage is filled. Window closed at class level. (cal_janq's collapse=urlkey CDX row hid later
   vintages.)
2. Round-1 ES verification's 8 missing-from-disk captures included
   `svc_20260401_20260722114222.json`; recovered this lane; served bytes ≠ round-1's claimed sha
   (`0700f57c…` vs `d1c4048f…`). Round-1's claimed-hash row stays unverified; verdict
   VERIFIED_WITH_RESIDUALS stands with this residual now documented at content level.
3. cal_janq's id-list absence probe (69|37|146) failed in its own log (curl rc=3) while its delta
   recorded "0 rows" — conclusion re-derived here from committed bytes (see §2). Conclusion stands;
   provenance repaired.

## 5. Fail-closed register (unprovable cells ⇒ documented exclusion at future freeze)

- FX expiry residuals 6E×2, 6B×6, 6J×4, 6A×2 = 14 cells: EXCLUDED (documented absence; only a future
  Wayback crawl or unblocking of live access could change this).
- 6J ×2 cells: identity undetermined — EXCLUDED + flagged to owner (no derivation performed).
- 6E 8 aged-out holiday windows: INCONCLUSIVE, not counted (documented exclusion).
- 6B/6J/6A holidays (42+42+42) and NQ 2026 product-code level (10): structurally absent from the
  archive; EXCLUDED at product-code level (advisory-class registers recorded where obtainable).
- ES 2011-2025 product-level early-close times: NOT_TRANSCRIBED (round-1 register carried forward).

## 6. Validations

- T1: every consumed capture hashed (`SHA256SUMS_lane.txt`, 10 files); fetch-log wire shas match disk.
- T2: gzip decode determinism — gunzipped shas of 2 captures equal round-1's recorded hashes
  (byte-identity across rounds); third capture's mismatch documented, not papered over.
- T3: capture parse — ES/6E id-token rows extracted from all three svc captures; event lists
  transcribed verbatim (eventDate, eventTime, marketEventType, tradingDate) in
  `calendar_close_delta.json`; no interpretation beyond the service's own fields; no rule derivation.
- T4: D5 pin — two independent BLS artifacts (schedule snapshot 6 days pre-release; release document)
  agree on date 2026-02-13 and 08:30 a.m. ET embargo.
- T5: absence re-verification — id-token counts on committed CDX (§2).
- Zero violations of: no-S1, no-scoring, no registry/ledger writes, no P3-quarantine access
  (quarantine path never opened), one `git rev-parse HEAD` at start, no staging/commit/push.

## 7. Artifacts

`RESIDUAL_INVENTORY.md` · `CAL_CLOSE_REPORT.md` (this file) · `calendar_close_delta.json` ·
`fetch_log.jsonl` (19 lines) · `fetch_lane.py` · `plan_wave*.json` (fetch plans) · `captures/` (8 raw
captures + 2 derived text extractions) · `SHA256SUMS_lane.txt` · `../dispatch/handoff_CAL-CLOSE.json`.
