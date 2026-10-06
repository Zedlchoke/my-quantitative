# GAPS_AND_DECISIONS_NQ — three buckets (workable-now / owner decisions / post-approval only)

- Round **FUTURES-5SYM-PRESCORED-20261005**, lane **NQ**, 2026-10-05. DRAFT-PENDING-OWNER.
- New decision IDs carry the **`P5-` prefix** (round decision-namespace law,
  `dispatch/DISPATCH_MANIFEST.json`). Prior decisions are cited by their full original IDs
  (ADOPT-D8/D9/D12, D1–D12) and are **never renumbered, never re-litigated, never re-opened**.
- Standing law restated: missing evidence = `NOT_RUN`, never inferred `PASS`. Everything in this
  packet is DRAFT-pending-owner; nothing is self-ratified.

## (a) Workable NOW (done by this lane; PREP-legal, 0 scored runs)

| item | state | evidence |
|---|---|---|
| cache_v3 integrity re-verification | **DONE** — 10/10 sha256+bytes match `adopt/cache_v3_hashes.json`; row counts re-measured (panel 6,780,608; sessions 11,715; held/cg 4,219; rolls 66) | `FREEZE_BUILDER_SPEC_NQ.md` §1; lock state `FREE_PROVEN`, light reads only |
| Full PRE-SCORED packet drafted | **DONE** — SPEC, identity budget (+JSON), cost contract, calendar/PIT policy, freeze-builder spec, runner-compat spec (7 files, this directory) | `SPEC_NQ.md` … `RUNNER_COMPAT_NQ.md` |
| Family PREP-gate inventory | **DONE (measured in prior rounds, carried)** — NQ-F1 K6 PASS (2.230×/0.686×, n=85); NQ-F2 K6 PASS (4.51× scoring era); NQ-F3 rebuild precondition DONE-descriptive (ret-series max diff 0.0); EXPWITCH-NQ leg DEAD-AT-GATE recorded | `NQ_K6_GATES.md` (sha256 `364f0412…2781`); `SYNTHESIS_K6.md` |
| Fee A7 | **DONE (prior round)** — AUTHORIZED_WITH_FINDINGS, 0 HIGH/0 CRITICAL | `fee_a7/A7_FEE_REAUDIT.md` (sha256 `2c1095d6…11ad`) |
| What remains workable-now for OTHER lanes | runner implementation against `RUNNER_COMPAT_NQ.md` acceptance checks; wave-2 verification — both PREP-legal, zero scored runs | `RUNNER_COMPAT_NQ.md` §RC-7 |

**Nothing else is workable-now for NQ.** Every remaining item below is owner-side or
post-approval-side; a lane attempting any of it would violate the standing gates.

## (b) Owner decisions (P5-* new items mapped to prior decision IDs; settled law never re-opened)

| ID | decision | maps to / status of the prior ID | fail-closed default if unanswered |
|---|---|---|---|
| **P5-NQ1** | Adopt D9 **Option A** for the NQ lane: explicit cease-guard standing law + ratify NQ cache_v3 as canonical chain of record | **ADOPT-D9** (open, unratified — `D8_D9_DECISION_SHEET.md`, sha256 `b1d6079f…f8ae`). This item does NOT re-open D9; it sequences it first for NQ | cache_v3 stays canonical-CANDIDATE; freeze builder hard-refuses; packet stays NOT_RUN |
| **P5-NQ2** | Sign the **NQ identity ceiling** (option NQ-A 22 / NQ-B 29 / NQ-C 36) AND name the **clock-shadow reading (a)/(b)** | Implements `IDENTITY_TABLES.md` §4 requirement ("owner NQ ceiling REQUIRED first", sha256 `750858ab…f6e6`); NQ-D (43) is not signable in this packet (dead leg, P5-NQ5) | no registration on NQ is lawful; no ceiling is invented by any lane |
| **P5-NQ3** | Rule the **D3 regulatory basis** as applied to NQ: Variant A (2.25/side, NFA timeline) vs B (2.24/side, IBKR offset); delta $0.02/RT | **D3** (open; the fee A7 execution half is DISCHARGED — AUTHORIZED_WITH_FINDINGS; the ruling half rides the D3 signature, `COST_FREEZE_ERRATUM.md` §3.3, sha256 `cf83bc2d…9ae8`) | Variant A binds basis-only; A≡B inside 2014-10-01→2017-12-31 |
| **P5-NQ4** | Adjudicate the `DATA_READINESS_NQ.md` §1 pointer-line defect ("NQ tick 0.25 pt / **$2.50**") as an annotation-only erratum (correct identity: tick 0.25 pt = **$5.00**, mult 20 — consistent with the committed S6 spread census and the entire cost ladder) | New, annotation-only; **zero packet numbers consume $2.50**; the committed file is never edited in place (append-only erratum law) | runners treat $2.50 configs as refuse-worthy (RC-1.1) |
| **P5-NQ5** | Confirm the **EXPWITCH-NQ leg disposition**: accept DEAD-AT-GATE as standing (the pre-declared F5-K6 consequence), or commission a vendor-granularity data-plane fix for the 2013–2021 15-min RTH gaps (era-wide, 35/66 expiry Fridays AND 46/80 ordinary Fridays — a data-plane decision, never a re-tunable parameter) | Implements the recorded interpretation slot of `NQ_K6_GATES.md` §2 (lane changed nothing); anti-cherry-pick law untouched | leg stays DEAD-AT-GATE; excluded from every slate; no EXPWITCH-NQ identity may be minted |
| **P5-NQ6** | Rule the **NQ 2026 calendar residual posture**: leave fail-closed (all 2026 deviation-suspect days excluded) vs authorize a bounded permitted-route extension (Wayback/official only, ≤2 attempts/URL) | Applies the **D12** posture to NQ specifically (`CYCLE_LAUNCH_DRAFT.md` §8 D12 row); prior D12 stays open | fail-closed exclusions stand (`CALENDAR_PIT_POLICY_NQ.md` §3 H2/H3/H4) |
| (standing slot) | **Placebo budget**: single-seed/single-delay stands by default; any ≥100-seed expansion is a separate owner ruling | `IDENTITY_TABLES.md` §7.3 (slot EMPTY — carried unchanged) | single-seed publication law binds every signed option |

Settled law this packet does NOT re-open (restated for the record): ES cap 24 FROZEN (D4, ES-only);
PB2 HOLD (6E/6B); PB3 PARK (6A); ADOPT-D8 (6A tick era — 6A-specific, never applied to NQ);
v2-cache deprecation; the fee erratum chain (1.386 retired); BLS/FOMC vintage law;
`data-ready ≠ scored-authorized`.

## (c) Post-approval ONLY (registration / gates / GO — nothing here may start from a lane)

Ordered, two-key law (`CYCLE_LAUNCH_DRAFT.md` §6/§7 carried verbatim in effect):

1. **Registration** at the cycle's own gate, ROOT checkout, owner-run or explicitly owner-delegated:
   freeze set sha-pinned (cycle spec sha + exclude-list sha + identity-table sha + §1 chain digests
   + cost-table digest + calendar provenance manifest). Re-hash at freeze; drift ⇒ BLOCKED.
2. **Prelaunch A7 — key 1 of 2**: fresh-context audit (identity enumeration vs frozen table, cost
   arithmetic vs pinned table, PIT/exclude coverage, budget accounting, freeze integrity, language
   scan); verdict required 0 HIGH/CRITICAL unresolved.
3. **Exact-arm dry-run**: single-shot rehearsal under ×1.0; byte-exact enumeration + cost
   recomputation; counters untouched; output quarantined descriptive-only.
4. **Owner typed GO — key 2 of 2**: `GO <REGISTERED-CYCLE-ID> SCORED EXECUTION`, exact match,
   recorded `auth/GO_RECORDED.json`. Prior "cho agent làm đi"-class directives ratify nothing.
5. **Scored run under heavy lock** (`locks inspect`; held ⇒ `NOT_RUN_RESOURCE_CONFLICT`).
6. **Reproduction twin (G8)**: byte/logical match; chain digests == pinned.
7. **Terminal A7 + two-half close**; terminal outcomes pre-decided (`*_REJECT_ALL` /
   `*_NO_ELIGIBLE_IDENTITY` / `*_SURVIVOR_PENDING_S1` / `*_BLOCKED_<reason>`).

No promotion / paper / live / order / S1 access anywhere in this chain.

— End GAPS_AND_DECISIONS_NQ. Buckets are exhaustive: anything not in (a) is (b) or (c) or does not
exist lawfully.
