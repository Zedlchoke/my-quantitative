# FOREX-FREE-V3 — A7 TERMINAL AUDIT (V3 closeout)

- Audit: `A7-TERMINAL-FOREX-FREE-V3`, measured 2026-09-04T21:58:36Z
- Auditor role: independent terminal check of the C1..C8 chain; audit-only, no repairs
- Audited HEAD: `6dca6db9dd29ab9d02be9260d0dca817f47fe315`
  (`orca/forex-free-v3-r-a7-terminal`, porcelain empty at audit start)
- Authority: PLAN_forex_v3.md sections 11-13, 15
- Prior authorization: prelaunch pass 3 `FOREX_FREE_V3_S0_LAUNCH_AUTHORIZED` @ `193b169`

## Facts audited and verdicts

| Check | Verdict | Evidence |
|---|---|---|
| C1 pin chain | **PASS** | `cafd78e` (wave) -> `236dcda` (selection) -> `9d96110` (W3) -> `2d4c883` (W3B) -> `331a389` (W3C) -> `b9de1cb` (scored) -> `6dca6db` (HEAD); every link strictly ancestral (merge-base). Twins detached at `331a389`, tracked-clean. 7/7 W3C code hashes equal to `w3_freeze.json` in both the freeze tree and this audit tree — zero post-freeze drift. |
| C2 ledger digest | **PASS** | Canonical ledger sha256 `6329cabc…f173` byte-identical in this tree, e-exec-1, r-reproduce. 6 records, all `scored=true published=true real_pnl=true`. Authorization file carries `FOREX_FREE_V3_W3C` (integrated copy cmp-identical to twin); `publish_cell` enforces token equality, 6/6 `published_now=1`. Spot recompute of **family2:anchor** in THIS worktree against e-exec-1 data with freeze token set: record_id match, **39/39 booked fields identical, 0 diffs**. Data: 156-entry staged manifest replays 156/156 sha256 in both twins, twin-vs-twin 156/156 identical. |
| C3 gates recomputed | **PASS** | All 6 cells: recomputed verdict AND reasons equal stored (`stage_a_gates` from freeze-pinned source + independent per-threshold re-derivation). **family2 anchor: PASS** (exp +23.9215 fin-adj / +5.5282 price-only, PF 1.3307, alpha +12.3204, BE +4.264 bps, MDD 1829.95, fold share 0.418, max pair 0.2184, USD corr −0.116 @ 88d, dropout 8/8, stress 580.47/422.97/265.47 distinct+declining+positive+PF≥1.0, financing no inversion). **family2 neighbour: PASS** (+18.6118 / +11.7774, PF 1.3850, BE +7.389, USD +0.027 @ 220d, dropout 8/8, stress distinct+declining). family1 anchor/neighbour/control FAIL with exactly the 8 stored reasons; family2 control FAIL as designed. |
| C4 trade reconciliation | **PASS** | 6/6: kept == n_trades; fold sums + purged == kept (F1a 263+8=271, F1n 256+7=263, F1c 127+11=138, F2a 105+8=113, F2n 276+13=289, F2c 111+8=119); purge/force-flat semantics consistent. |
| C5 control coherence | **PASS** | family1 control −33.3015 far worse than anchor −4.5924; family2 control −7.2224 negative, PF 0.914 < 1.10, does not reproduce; family2 mechanism sanity PASS; no financing-manufactured edge (price-only sign agrees on both anchors). |
| C6 denominators / prior ledgers | **PASS** | 12 historical (V1 6 + V2 6) + V3 6 observed = 6 published = **18 total**. V1 ledger `066db433…` and V2 ledger `1be279ef…` re-hashed: equal to their recorded values; zero V3-cycle commits touched them. |
| C7 boundaries | **PASS** | No S1 access (`SEALED_UNTOUCHED` in state + run contract); no paper/live/order/credential artifact created in the V3 cycle (tracked `live*` files predate V3; V3 diff adds only data_fusion/proposals/forex_free_v3 assets+tests+control+audits). `git ls-files` data_raw matches: **0**. Workers zero at audit time. Twins tracked-clean; 3 untracked run outputs each, cmp-identical to integrated control-plane copies; exec/repro reports identical except elapsed_s. |
| C8 terminal label | **PASS** | Label `FOREX_FREE_V3_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1` certified: family2 anchor AND neighbour pass every applicable frozen gate under independent recomputation AND reproduction ALL_MATCH (byte-identical, 0 field diffs). Survivor **family2 (FXFV3-A6-P1)** locked for a FUTURE owner-approved S1 plan only — nothing opened this cycle. |

## Terminal label certified

```
FOREX_FREE_V3_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1
```

Program statement update: observed 12 + 6 = 18; published 12 + 6 = 18; survivors 1 family
(family2 anchor + supporting neighbour). family1 (FXFV3-A5-P1) rejected wholesale.
A correct positive here does not reopen anything: the label locks the survivor for a
future owner-approved S1 plan; V3 opened no S1, no paper, no live.

## Findings (0 critical / 0 high / 0 medium / 1 low / 3 info)

- **T3-INFO-1** — “156 price files” shorthand is imprecise: the 156-entry staged manifest =
  152 price files (117 H1 + 7 D1 + 28 H4) + 4 V1 control artifacts. Replay itself exact.
- **T3-INFO-2** — `w3_freeze.json` twins prose still names `9d9611` (superseded by W3C
  re-point; actual twin HEADs verified `331a389`). Inherited INFO N1; fix at next manifest touch.
- **T3-INFO-3** — runner constant `FREEZE_TOKEN="FOREX_FREE_V3_W3"` is the base name; the
  operative scored token `FOREX_FREE_V3_W3C` is CLI-supplied and equality-enforced at
  publication. Families accept-and-ignore the token string.
- **T3-LOW-1** — untracked scratch fixture ledgers under `data_raw/forex_free_v1/dryrun/`
  in both twins; gitignored, outside the staged manifest, not runner-consumable; no effect
  on scored artifacts. Optional cleanup at cycle close.

## Blockers

None.

## Evidence files

- `_a7_spot_recompute.py` / `_a7_spot_recompute_out.json` — end-to-end recompute of family2:anchor
- `_a7_gate_recompute.py` / `_a7_gate_recompute_out.json` — full 6-cell gate/trade/mechanism recompute

Attestation: audit-only, no repairs. Every number independently recomputed from file bytes;
the only scoring executed was the single authorized spot recompute of the decisive cell.
