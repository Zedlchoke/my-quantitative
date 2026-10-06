# SOURCE_INVENTORY — FUTURES-TEN-HYPO-PREP-20261004 (controller aggregate)

Every network-obtained fact this round rests on is a capture in a lane
`captures/` dir with a sha256 row in that lane's `SHA256SUMS_lane.txt`.
Hash re-verification by the controller at synthesis time (wave-1 commit
`b7f274a4` + SUMS normalization): **comm_energy 33/33 OK** (9 lane captures
+ 24 baseline/root/home rows), **comm_metal 14/14 OK**, **fx_eb 4/4 OK**,
**fx_ja 2/2 OK**, es_nq 0 captures (5 attempts, all BLOCKED_TRANSPORT,
0 bytes). Cross lane: zero-network.

## 1. New captures this round (29 files; provenance = URL + fetch ts in each lane's fetch_log.jsonl)

| Lane | Capture | Source domain | Class |
|---|---|---|---|
| comm_energy (9) | cftc_cot_release_schedule.html · eia_ng_futures_dnav.html · eia_steo_main.html · eia_wngsr_schedule.html · eia_wpsr_schedule.html · eia_wti_spot_dnav.html · noaa_cpc_610day.html · opec_home.html · webarchive_cmegroup_cl_20260723.html | cftc.gov · eia.gov · noaa.gov · opec.org · web.archive.org/cmegroup | OFFICIAL (CFTC/EIA/NOAA/OPEC) + ARCHIVED_OFFICIAL (CME) |
| comm_metal (14) | cot_* (5: landing, schedule probe, explanatory notes, disagg explanatory, deacmxsf current, f_disagg current.txt) · lbma_prices_page.html · lbma_silver_page.html · nt_gold_specs_archive.html · cme_gold_markets_page_20260917.html · cme_voi_page_20240229.html · treasury_real_yield_2026.html · wgc_research_landing.html · silver_institute_landing.html | cftc.gov · lbma.org.uk · web.archive.gov (treasury) · web.archive.org (CME/NT) · gold.org · silverinstitute.org | OFFICIAL + ARCHIVED_OFFICIAL + INDUSTRY_PUBLIC |
| fx_eb (4) | cme_specs_6E_archive20210301.html · cme_specs_6B_archive20210301.html · ecb_accounts_20261004.html · ons_releasecalendar_20261004.html | web.archive.org/cmegroup · ecb.europa.eu · ons.gov.uk | ARCHIVED_OFFICIAL + OFFICIAL |
| fx_ja (2) | mof_jgb_auction_en.html · rba_board_minutes.html | mof.go.jp · rba.gov.au | OFFICIAL |

## 2. Baseline re-verification (before any fetch; no re-fetch of held evidence)

- comm_energy: 24 register rows re-verified byte-identical against
  committed in-worktree copies (baseline register
  `FUTURES-OVERNIGHT-PREP-20261003/hypo/comm/captures/source_sha256.tsv`).
  CONTROLLER CORRECTION (disclosed in the SUMS file header): the
  register's original path column names the now-P3-quarantined worktree;
  the P3 worktree was NOT accessed — verification ran against the
  byte-identical copies committed inside the verified base `a4a88265`;
  SUMS paths rewritten to the in-worktree copies, hashes unchanged.
- comm_metal: same 24-row baseline register re-verified (lane report);
  SUMS normalized by controller to `captures/`-relative paths so
  `shasum -c` runs from the lane dir (format fix only).

## 3. P3-quarantine boundary statement (for verify)

P3-quarantined material = the live worktree
`.worktrees/futures-behavior/prep` (@ b583c33a) and its
`FUTURES-P3-QUARANTINE-20261004` control dir. Content already committed
inside the verified base `a4a88265` (including
`FUTURES-BEHAVIOR-10SYMS-PREP-20261002/**` dossiers referenced by the
baseline register) is the verified base itself and remains citable; it
predates and passed round-2 verification. No lane read the live P3
worktree; the only P3 strings in round outputs are (a) the disclosed
SUMS-transcription correction above and (b) explicit "never accessed"
declarations.

## 4. Fetch-budget compliance

Per-lane attempts (all logged): es_nq 5 · fx_eb 11 · fx_ja 5 ·
comm_energy 20 · comm_metal 28 — each ≤ 30; blocked routes recorded
BLOCKED_TRANSPORT, zero bypass; zero paywall/login/credential attempts.
**VERIFY-R3 finding M3 (controller correction applied 2026-10-04)**:
es_nq logged 3 GET attempts on one (url,method) pair (cboe probe) —
a violation of the ≤2/(url,method) rule by 1 attempt on an
already-BLOCKED_TRANSPORT route (0 bytes, 0 captures, no content
consumed). The lane's own fetch_log discloses all 3 lines; no other lane
breached the cap. Verified counts: 5/11/5/20/28, all ≤30 total.


— End SOURCE_INVENTORY.md.
