# FREEZE_BUILDER_SPEC_IMPL — implemented builder vs the real (NOT_RUN) manifests

- Round **FUTURES-5SYM-PRESCORED-20261005**, wave 3, lane **FREEZE-WIRING**, 2026-10-05.
- Implementation: `freeze_wiring/freeze_builder.py` (stdlib-only, deterministic).
- **This round consumes SYNTHETIC manifests ONLY.** Every bundle this builder
  emits is stamped `SYNTHETIC-SANDBOX` and is NOT a research result, NOT a
  freeze, and NOT consumable by any real run. The builder hard-refuses on
  GATE-0 authority absence, so no synthetic bundle can exist without the
  caller forging owner artifacts **inside sandbox temp dirs only** (fake
  authority in sandbox = lawful for machinery proofs; it is not authority).

## 1. What is implemented (and proven by freeze_wiring/tests)

| capability | law source | status |
|---|---|---|
| GATE-0 authority matrix per symbol (NQ: d9+ceiling; 6E/6B: pb2+ceiling; 6A: pb3+d8+d9+ceiling; 6J: 6j_ceiling+ceiling) | `nq/FREEZE_BUILDER_SPEC_NQ.md` §0 · `fx_eb/GAPS_AND_DECISIONS_6E_6B.md` P5-OD1 · `fx_ja/GAPS_AND_DECISIONS_6J_6A.md` P5-D1/P5-D5 · meas_nq REFUSED_D9_UNSIGNED refusal law | IMPLEMENTED + TESTED (refusal demos, distinct exit codes) |
| `d9_ratification@1` validation: schema + `typed_by_owner` + `decision == "ADOPT-D9-OptionA"` | meas_nq refusal law (`meas_nq/m2_f3_rebuild_harness`, exit 20 class) mirrored | IMPLEMENTED + TESTED |
| `d8_ratification@1`: decision ADOPT-D8-OptionA (measured 2020-11-20/23 boundary) | P5-D5 chain | IMPLEMENTED + TESTED |
| `pb2_lift@1` / `pb3_lift@1` presence gates | P5-OD1 / P5-D5 | IMPLEMENTED + TESTED |
| `6j_ceiling@1`: option ∈ {J-A, J-B, J-C} AND `clock_shadow_reading` ∈ {a, b} | P5-D1 (IDENTITY_BUDGET_6J §"signing law") | IMPLEMENTED + TESTED |
| `ceiling@1` identity-table binding: option name + positive ceiling int + `{name, sha256}` identity table reference | owner ceiling law (any symbol) | IMPLEMENTED + TESTED |
| GATE-1 input re-hash (path + sha256 + bytes; drift/missing refuse, never silent reuse) | FREEZE_BUILDER_SPEC_NQ §1 GATE-1 law | IMPLEMENTED + TESTED |
| Bundle emit: `freeze_manifest_<SYM>.json` (input digests + params + `builder_code_sha256` + `content_stamp_sha256` content-derived + `generated_at == --epoch`), `frozen_identity_table_<SYM>.json`, `frozen_exclusion_calendar_<SYM>.json` | FREEZE_BUILDER_SPEC_NQ §4 manifest shape, adapted to sandbox scope | IMPLEMENTED + TESTED |
| Determinism: byte-identical bundles for identical manifest+artifacts+epoch; wallclock NEVER read (`--epoch` REQUIRED) | task A determinism law | IMPLEMENTED + TESTED |
| FINAL status artifact ALWAYS written (even on refusal), bundle dir NEVER created on refusal | "writes nothing" law (SPEC_NQ §0) + task A FINAL-artifact law | IMPLEMENTED + TESTED |
| `cease_guard_chain()` — synthetic cease-guard chain resolver: guard variant diverges from naive EXACTLY at the guarded date | CEASE_GUARD_STANDARD §2 shape (D9-contingent law carrier) | IMPLEMENTED + TESTED (6A-style violation-day proof) |

## 2. Exit codes (GATE-0 refusals, each its own)

```
0   FREEZE_BUNDLE_COMPLETE
2   REFUSED_BAD_ARGS
21  REFUSED_GATE0_NQ_D9_UNSIGNED            (NQ: no valid d9_ratification@1)
22  REFUSED_GATE0_CEILING_UNSIGNED          (any symbol: no valid ceiling@1)
23  REFUSED_GATE0_PB2_UNSIGNED              (6E/6B: no valid pb2_lift@1)
24  REFUSED_GATE0_PB3_UNSIGNED              (6A: no valid pb3_lift@1)
25  REFUSED_GATE0_D8_UNSIGNED               (6A: no valid d8_ratification@1)
26  REFUSED_GATE0_6J_CEILING_UNSIGNED       (6J: no valid 6j_ceiling@1)
27  REFUSED_INPUT_DRIFT                     (GATE-1 re-hash mismatch)
29  REFUSED_GATE0_ARTIFACT_INVALID          (present but wrong schema/decision/signature)
30  REFUSED_INPUT_MISSING                   (GATE-1: manifest input absent)
31  REFUSED_MANIFEST_INVALID                (schema/cycle/symbol/roles malformed)
```

## 3. Sandbox input-manifest schema (`futures_5sym_prescored/freeze_input_manifest@1`)

```json
{"schema": "futures_5sym_prescored/freeze_input_manifest@1",
 "cycle_id": "FUTURES-5SYM-PRESCORED-20261005",
 "symbol": "NQ",
 "inputs": [{"role": "panel|chain|calendar|exclusion_table|cost_manifest|
                    spec_packet|identity_table|ceiling_table",
             "path": "<relative or absolute>", "sha256": "<64hex>",
             "bytes": 123}],
 "params": {"...symbol law params..."}}
```
Required roles: `panel, chain, calendar, exclusion_table, cost_manifest,
identity_table`. Every entry re-hashed at GATE-1.

## 4. REAL manifests — SPECIFIED, NOT RUN (NOT_RUN this round)

The real freeze manifests and their invocation are owned by the per-symbol
dossiers and remain **NOT_RUN** here; this lane wired the machinery, nothing
real:

| symbol | real spec (authority for the real invocation) | why NOT_RUN |
|---|---|---|
| NQ | `nq/FREEZE_BUILDER_SPEC_NQ.md` (§1 10-file cache_v3 digest table, §2 k=5 + cease-guard params, §3 alias rule, §5 reproduction twin) | ADOPT-D9 unsigned (P5-NQ1); ceiling unsigned (P5-NQ2) — GATE-0 would refuse; no real invocation attempted |
| 6E / 6B | `fx_eb/FREEZE_BUILDER_SPEC_6E_6B.md` | PB2 HOLD (P5-OD1) — no FX scored cell can exist; GATE-0 would refuse |
| 6J | `fx_ja/FREEZE_BUILDER_SPEC_6J_6A.md` (§125 owner 6J ceiling signature requirement) | no 6J ceiling anywhere (P5-D1) — GATE-0 would refuse |
| 6A | `fx_ja/FREEZE_BUILDER_SPEC_6J_6A.md` + `fx_ja/SPEC_6A_CONTINGENCY.md` | PB3 PARK + ADOPT-D8 unratified (P5-D5 chain) — GATE-0 would refuse |

Per the dispatch measurement_law, these are recorded NOT_RUN with grounds —
never forced.

## 6. WAVE-4 APPENDIX — the REAL intent-execution seam (LANE-WIRING-FIX)

Wave 4 added the production execution path under this builder's wiring
package; this section only POINTS to it (authority unchanged, nothing here
ratifies a freeze):

- `wiring/intent_executor.py` + `futures_5sym_prescored/intent_packet@1`:
  every wired intent executes as ITS OWN trade (per-intent direction,
  signal/decision/entry/exit timestamps and declared fills preserved,
  ordering preserved) through `exec/scored_runner_v2.py`'s intent-mode
  engine — same authority/twin/ledger/publication law. Contract, SPEC→
  execution law mapping, accounting-reuse proof and owner-gated remainder:
  **`wiring/INTENT_SEAM_SPEC.md`**.
- The positional compiler (`wiring/spec_compiler.py`) is relabeled
  `POSITIONAL_ACCOUNTING_TEST_ONLY` and REFUSES multi-intent /
  mixed-direction groups (`REFUSED_POSITIONAL_SCOPE`, exit 46); it proves
  runner accounting on one positionally-encoded trade only.
- A future registered cycle calls `intent_and_run` per identity under the
  canonical lock; the sandbox flock used in tests is still NOT evidence of
  canonical lock integration (`CANONICAL_INTEGRATION.md` §0).
- Defect history: `repro_mixed_direction/REPRO_FAIL.json` (committed
  f1f69c8e, untouched) -> fixed state `REPRO_FIXED.json` (verdict PASS).

## 7. Non-goals this round (unchanged)

No real data touched; no governance/registry/GO/ledger/lock writes outside
sandbox temp dirs; no commits; no registration; the sandbox bundles must
never be cited as freeze evidence for any future cycle (each real cycle
re-runs its own builder on the real manifests under the canonical lock —
see `CANONICAL_INTEGRATION.md`).
