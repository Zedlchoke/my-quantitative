# PLAN — DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1

- cycle_id: `DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1`
- asset: `shared` (data/methodology program spanning forex / crypto / stocks)
- plan: this file
- authority: owner directive 2026-09-26 (verbatim scope recorded in §13)
- lifecycle target: ACTIVE_LIGHT → TERMINAL (data-engineering cycle; **budget 0/0
  scored cells — this cycle never computes a strategy outcome**)
- go phrase: none registered (FREE-DATA-FRONTIER-V1 precedent: data-engineering
  cycles with no scored surface carry no GO phrase; nothing in this plan is
  gated on a GO)

## 1. Purpose and non-goals

This is the stepping-stone cycle the owner ordered: consolidate, validate and
price the program's data foundations across FX / crypto / stocks so that the
NEXT research generation can pick frontiers with evidence instead of
discovering data walls mid-cycle (the failure mode that killed STOCKS-NG3 at
its earnings channel, FOREX-NG7 at its financing band, and three separate
generations at broker-cost authority).

**Non-goals (hard):**

- NO strategy scoring, NO PnL computation, NO family proposal, NO S1 opening,
  NO shadow/dashboard modification, NO orders, NO credential use, NO account
  signup, NO purchase, NO licensed raw bytes into Git, NO bulk download
  beyond the probe budget (§8).
- This cycle's verdict can never be read as "a strategy was proven".

## 2. Measured intake facts (2026-09-26, this session)

- Root: `/Users/hoangminhlong/my-quantitative`, branch `main`,
  HEAD `8d549bcf7073b1b62b39d1976bbf418c24f0af49`.
- Dirty tree: `plans/ACTIVE_CYCLES.json` modified (benign projection
  regeneration from the PWS-CX-BNBUSDT-C1 session's registry write —
  classified AUTHORIZED_HANDOFF-derived, NOT swept into this cycle's commits);
  untracked control dirs of other cycles (OWNER_CHANGE / evidence of other
  sessions — preserved); `plan_at.md`, `.zcode/` (owner/tool — untouched).
- Disk: **7.5 GiB free of 228 GiB (97% used) — the binding resource
  constraint.** `.worktrees` 23G; `~/.my-quantitative-data` 3.6G;
  `~/staging_backups` 617M (P-13 archives); `.git` 644M.
- Heavy lock: FREE_PROVEN at intake (no holder, no flock).
- 10 cycles ACTIVE_LIGHT (incl. PROSPECTIVE-SHADOW-V1 E-worker, LIVE-DATA-
  GATEWAY-V1 worker, PWS-CX-BNBUSDT-C1 GO-1 in flight). **This cycle must not
  touch any of their surfaces, workers or data dirs in write mode.**
- S1 SEALED everywhere. ERP1 sealed holdouts (2026-H1 AUDUSD/USDCAD) are
  UNREAD program assets — **no lane may read holdout/sealed file content**
  (inventory-level metadata only: name/size/sha).
- Standing environment constraint (L-FXFF-1): broker/exchange estates
  (*.dukascopy.com, *.cmegroup.com) are SNI-filtered on this network path —
  measured, committed evidence; no circumvention ever.

## 3. Prior data-authority rulings this cycle inherits (do not re-litigate)

| Source | Ruling | Evidence cycle |
|---|---|---|
| Binance Vision + keyless public endpoints | authorized internal research, keyless | many (S4 frozen set) |
| Dukascopy public M1 BID/ASK | owner-delegated source choice 2026-09-23, TCU_RISK_DISCLOSED; corpus on disk | EURUSD-OPEN-SEARCH-V1/V2, FX-MAJORS-SEARCH-V1 |
| *.dukascopy.com / *.cmegroup.com transport | BLOCKED_TRANSPORT (SNI filter) | FIBV1, FXF-F |
| Dukascopy fresh TCU (any-service preamble, no-database, personal-non-commercial) | worsened; re-acquisition needs owner license capture | EURUSD-DATA-QUALIFICATION-V1 |
| TrueFX / OANDA v20 practice | owner license/account decision pending | EDQ1 owner packet |
| TD (Twelve Data) | vendor OHLC-only; NO cost authority (F4 class) | FOREX-NG6/NG7 |
| EODHD "All World" | owner entitlement; EOD + some channels OK; earnings-history channel 403 | STOCKS-NG3 |
| FINRA consolidated NMS short-sale | ToU INCOMPATIBLE with research use — terminal | STOCKS-NG4 (P-25) |
| SEC EDGAR (FTD/N-PORT/Form-4/4A) | entitled, declared UA; PIT = acceptance timestamps; FTD ≥17d guard | FDF-V1/V1R1, DEU-V1 |
| OFR | official endpoints 200; RETRIEVAL_TIME_ONLY | FDF-V1R1 |
| NY Fed reference rates | entitled; revisionIndicator machine-served | FDF-V1 |
| Broker cost authority (FX majors) | zero account-bound bytes in 3 independent censuses; IBKR gateway probe timed out unauthenticated | DATA-EDGE-UNLOCK-V1 Lane F |
| CFTC CoT / Treasury / CBOE / FRED(owner key) / BIS / ECB | entitled official, per prior cycles | RATES/COMMODITIES/NG cycles |
| Coinbase/Kraken/Deribit keyless WS | collectors exist; PROSPECTIVE-only history | DEU-V1 Lane C |
| Binance OI/liquidation/L2 history | liquidationSnapshot 404; multi-year PIT OI/L2 none | BTC-H4-TWO-REGIME-V1, bear-recon |

## 4. Cycle structure (lanes)

A1 (this session) is the sole integrator. Lanes are dispatched with packets
(full packets committed under `research/control/DATA-FOUNDATION-FX-CRYPTO-
STOCKS-V1/dispatch/`), each in its own worktree + branch, each ending with a
structured handoff JSON (`zcode_orch_v3_handoff@1`) at the packet's
`handoff_path`. Survey lanes run in parallel; **no lane may run a heavy job**
(everything is manifest reads, hashing, small parses; if a lane estimates
>10 min CPU or >1 GB temp it stops and reports instead).

| Lane | Branch / worktree | Scope (allowed write paths) | Deliverable |
|---|---|---|---|
| L-FX | `orca/dfv1-lane-fx` | `research/control/DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1/fx/` | FX inventory rows + validation + gap input |
| L-CX | `orca/dfv1-lane-cx` | `.../cx/` | Crypto inventory rows + validation + gap input |
| L-ST | `orca/dfv1-lane-st` | `.../stocks/` | Stocks inventory rows + validation + gap input |
| L-PIT | `orca/dfv1-lane-pit` | `.../pit_license/` | Cross-asset authority-row schema instantiation, license ruling consolidation (§3 table verified against artifacts), pipeline + fixture contracts draft |
| L-COST | `orca/dfv1-lane-cost` | `.../cost_execution/` | Cost/execution authority consolidation (census #4), measurable-vs-owner-action split per asset |
| L-A7 | `orca/dfv1-lane-a7` | `.../audits/` | Independent plan review (pre-execution) AND terminal audit |
| A1 | `orca/data-foundation-v1-integration` | `.../` (integration root) | All §6 deliverables |

Forbidden for every lane: `plans/` (except reading), `research/wayfinder/`,
other cycles' control dirs, `~/.env`, credentials, holdout/sealed content,
any write outside its allowed paths, push/merge/history ops.

## 5. Authority-row schema (every dataset gets one row; no inferred PASS)

```json
{
  "dataset_id": "string (stable, snake_case)",
  "asset_class": "forex|crypto|stocks|rates|vol|commodities|shared",
  "source": {"provider": "", "channel": "exact endpoint/bundle/product",
              "terms_url": "", "license_ruling": "cite §3 row or new ruling"},
  "local_presence": {"paths": [], "bytes": 0, "manifest_path": "",
                      "manifest_verify": "ALL_MATCH|MISMATCH|NO_MANIFEST|NOT_RUN"},
  "coverage": {"instruments": [], "start": "", "end": "",
                "resolution": "", "measured_from": "bytes|metadata|stated"},
  "timing": {"event_time": "present|absent|approx", "available_at": "...",
              "ingested_at": "...", "revision_policy": "..."},
  "timezone": {"declared": "", "dst_evidence": ""},
  "quality": {"missingness": "", "gaps": "", "duplicates": "",
               "cross_source_check": ""},
  "economics": {"hypotheses_opened": [], "prior_kill_fixed": "",
                 "falsifying_control": ""},
  "costs": {"acquisition": "", "storage_bytes": 0, "api_limits": "",
             "reproducible": "yes|partial|no"},
  "status": "AVAILABLE_VALIDATED|AVAILABLE_UNVALIDATED|BLOCKED_LICENSE|BLOCKED_ACCOUNT|BLOCKED_COST|BLOCKED_STORAGE|BLOCKED_TRANSPORT|NOT_RUN",
  "status_evidence": "command or artifact backing the status"
}
```

Rules: `AVAILABLE_VALIDATED` requires a re-measured coverage/checksum check
from bytes THIS cycle (manifest ALL_MATCH + first/last/row-count census);
file existence alone never implies it. `BLOCKED_*` rows must name the exact
owner action that unblocks (feeds D3).

## 6. Mandatory deliverables (owner's list, verbatim mapping)

1. **DATA_INVENTORY** (`DATA_INVENTORY.md` + `data_inventory.jsonl`) — every
   existing dataset, FX/Crypto/Stocks sections, authority status per §5.
2. **DATA_GAP_MATRIX** (`DATA_GAP_MATRIX.md`) — per missing dataset: why
   needed, which hypothesis class it opens, which recorded kill it would have
   prevented, priority, cost/volume estimate; "need-now" vs "only-with-
   mechanism" split.
3. **OWNER_ACQUISITION_RUNBOOK** (`OWNER_ACQUISITION_RUNBOOK.md`) — per
   blocked source: official doc links, account/subscription type, safe export
   procedure, what must never enter chat/Git; no passwords/API secrets.
4. **PIT_AND_COST_CONTRACTS** (`PIT_AND_COST_CONTRACTS.md`) — schema,
   quality thresholds, test battery, and the evidence standard for
   "backtestable after costs" per asset.
5. **NEXT_RESEARCH_FRONTIER** — ≤3 frontiers genuinely enabled by
   AVAILABLE_VALIDATED data; any frontier lacking data stays BLOCKED and is
   excluded from any scored cycle.
6. **A7 audit + handoffs + gate table + final owner report** (simple
   language) — under `audits/` and `FINAL_REPORT.md`.

Additional required artifact: **OUTCOME_EXPOSURE_MAP.md** — which data
windows/instruments have been outcome-exposed (S0-exposed research data:
every dev/holdout window the ledger shows was read) vs which remain unopened
(sealed S1, ERP1 2026-H1 AUDUSD/USDCAD holdouts, untouched future windows);
rules for keeping confirmation data unopened.

## 7. Pipeline design contract (deliverable, not implementation)

L-PIT drafts, A1 freezes:

```text
raw immutable (write-once, sha256-manifested, machine-local, NEVER in Git)
  → normalized + provenance (source_id, normalizer_version, row-level lineage)
  → PIT/quality gate layer (fixtures below; fail-closed)
  → cost book (per-asset measured spreads/fees/financing with stress tiers)
  → query/replay read-only layer (deterministic point-in-time reads)
```

Fixture battery (each gets a named synthetic test design; existing battery
inventoried first — many already exist from EURUSD/CHR3F cycles): future
leak (truncation replay), revision/restatement detection, DST boundary,
symbol/identity change, duplicate/missing bar, quote crossed/stale, source
disagreement, stamp-scale migration (L-TRACKB1-1: assert last-stamp within
one bar of declared end), spread non-positive minute rejection.

Research-vs-confirmation separation: every dataset tagged
`OUTCOME_EXPOSED` / `UNOPENED` in the inventory; unopened windows are only
readable by a future owner-authorized confirmation plan.

## 8. Probe budget and rules (the only network/ingest allowed)

- Disk: **≤2.0 GB total new bytes this cycle; hard floor — stop all
  acquisition if free disk <5.0 GB (BLOCKED_STORAGE).**
- Network: keyless + license-screened (§3) sources only; ≤300 light requests
  per probe set, rate-limited, no retries hammering; no credential ever.
- Candidate probes (run ONLY if the gap matrix shows they change a status):
  Binance Vision catalog/exchangeInfo reachability + one monthly-file sha
  check; ECB SDMX / BIS / Treasury reachability HEAD; SEC EDGAR bulk
  directory census; NY Fed/OFR endpoint liveness re-check. Anything touching
  a new source not in §3 requires the L-PIT license screen FIRST (P-25 law:
  authority gate runs before bulk retrieval).
- No probe writes outside `~/.my-quantitative-data/data-foundation-v1/` and
  the cycle control dir; manifests mandatory for every fetched byte.

## 9. Stop conditions (owner's, verbatim intent)

Stop when: inventory + gap matrix cover all three asset classes; every
in-disk source of consequence is validated within budget; every remaining
gate has a concrete owner-action runbook entry. Do NOT extend the cycle to
"get more data". Terminal labels (preregistered):
`FOUNDATION_READY_FOR_NARROW_RESEARCH` or
`BLOCKED_WITH_ACQUISITION_RUNBOOK` (both may co-occur per asset). Either is a
valid close; neither is a profitability claim.

## 10. Incident & hygiene laws carried

P-8/P-9/P-10 (atomic pathspec commits; never sweep foreign projection),
P-13 (archive-before-delete; inherited pins), P-17 (one live Lead session —
this cycle's session is the only writer here), P-19 (verification-gated
sequences; shas measured never typed; cwd re-anchored per command), P-25
(license before retrieval), L-FIBV1-1/L-FXFF-1 (transport vs license
blockers; standing SNI filter — G0 reachability probe before any lane burns
on those estates), Q-8 (measured beats stated), Q-9 (seal criteria not just
data), P-18/ERP1 (truncation-proof standard for PIT claims).

## 11. Gates for this cycle

| Gate | Check | Evidence |
|---|---|---|
| G0 | intake re-measured; this plan committed; A7 plan review AUTHORIZED | audit file |
| G1 | lanes dispatched with packets; worktrees verified (HEAD/branch/porcelain) | dispatch/ + registry |
| G2 | per-asset inventory complete (every known dataset has a §5 row or explicit NOT_RUN reason) | data_inventory.jsonl |
| G3 | validation re-measurements executed within budget; no inferred PASS | validation logs |
| G4 | gap matrix + runbook + contracts + exposure map drafted | artifacts |
| G5 | probes (if any) within §8 budgets; manifests ALL_MATCH | probe logs |
| G6 | A7 terminal audit 0 HIGH/CRITICAL blocking | audits/ |
| G7 | two-half close (registry TERMINAL, ledger row, MAP bullet, LESSONS if any) | registry + root files |

## 12. Budget

Scored cells: 0/0 (never). Probe budget per §8. Agent lanes: ≤6 + A7.
Compute: no heavy-lock jobs expected; if a validation sweep needs the heavy
lock it serializes via `researchctl` and yields to foreign cycles.

## 13. Owner directive (verbatim scope anchor, 2026-09-26)

"orchestrate một chương trình DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1 làm bước
đệm cho việc tìm strategy có bằng chứng tốt hơn. Đây là cycle dữ liệu và
phương pháp, không phải cycle săn PnL…" (full text preserved in
`research/control/DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1/OWNER_DIRECTIVE.md`).
**The ENTIRE OWNER_DIRECTIVE.md is binding** — including the per-asset
priority lists (Forex / Crypto / Stocks), the crypto prohibition on inferring
order book or forced flow from candles, and the no-credentials/no-accounts
rules — not only the deliverables and stop conditions. Every relevant lane
packet restates its per-asset priority list verbatim; PIT_AND_COST_CONTRACTS
encodes the crypto no-candle-inference prohibition as an explicit contract
clause + fixture requirement.

## 14. Amendment r1 — A7 plan review remediation (binding, 2026-09-26)

A7 verdict `AUTHORIZED_WITH_FINDINGS` (0 CRITICAL / 1 HIGH / 5 MEDIUM / 5 LOW;
`audits/A7_PLAN_REVIEW_r1.md`). All findings remediated as follows before G1:

- **F1 (HIGH) — disk accounting:** the ≤2.0 GB budget is a **total new-disk
  footprint cap covering worktree checkouts + probes + artifacts together**;
  the 5.0 GiB free floor applies to ALL new-byte creation including
  `git worktree add`. Measured: tracked checkout = 148 MB per worktree; ≤7
  worktrees ≈ 1.04 GB, leaving ≤0.9 GB for probes. `df` is re-measured and
  recorded immediately before each `git worktree add` (abort below 6.0 GiB
  free); per-worktree `du -sh` recorded in G1 evidence; worktrees are lean
  (no data copies, no venv duplication).
- **F2 — probe budget machine-readable:** frozen probe-set list (the five in
  §8); cycle-wide request counter in `probe_ledger.json` — cap 600 requests
  TOTAL, ≤300 per set, ≤2 sets by default; G5 verifies the counter, not just
  manifests. A new source outside §3 requires a new A7-screened amendment
  before any request.
- **F3 — "of consequence" defined:** every dataset with a §3 ruling row;
  every dataset cited by any §6 deliverable; every dataset ≥50 MB on disk;
  every dataset referenced by any registry terminal phase. Any validation
  skip carries an explicit NOT_RUN + the rule applied.
- **F4 — registration order:** the cycle is registered via `researchctl`
  (lifecycle ACTIVE_LIGHT) BEFORE the first lane dispatch; the registry row
  is G1 evidence alongside the packets.
- **F5 — no racing reads on live-owned data:** datasets owned by an
  ACTIVE_LIGHT cycle with workers>0 or heartbeat <24h are censused
  metadata-only; `manifest_verify` = `INHERITED_NOT_REHASHED_LIVE_OWNER`
  using that cycle's committed manifests; a MISMATCH verdict is never
  written from a possibly mid-write file.
- **F6 — directive scope:** closed by the §13 rewrite above.
- **F7 — neighbor count:** the ACTIVE_LIGHT neighbor list is re-measured at
  G1 from the live registry (grep-window caveat noted); §2's "10" is not
  relied upon.
- **F8 — sealed bytes:** sealed/holdout inventory uses inherited manifest
  SHAs (P-13 resolution); byte-level re-hash of sealed files requires
  explicit owner authorization, else NOT_RUN.
- **F9 — owner-facing taxonomy:** DATA_INVENTORY.md carries a mapping note:
  BLOCKED_TRANSPORT ≡ BLOCKED (cause = transport; standing environment
  constraint per L-FXFF-1) within the owner's 7-state view.
- **F10 — measured, not estimated:** lanes run their first work chunk under
  `/usr/bin/time` and abort if projected >10 min CPU or >1 GB temp; A1
  spot-checks one lane's measurement at G3.
- **F11 — A7 reproduction charter:** the terminal A7 packet explicitly
  requires recounting key numbers from committed artifacts, re-deriving ≥5
  authority-row statuses from their evidence fields, re-hashing ≥3 datasets,
  and re-measuring ≥2 coverage claims independently.
