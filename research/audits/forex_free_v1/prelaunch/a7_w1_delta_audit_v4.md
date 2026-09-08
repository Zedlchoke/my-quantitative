# A7 W1 Delta Audit v4 — FOREX-FREE-V1 (narrow B4 re-verification)

**VERDICT: `FOREX_FREE_V1_W1_LAUNCH_AUTHORIZED`**
w1_sha `f33a32a2f245d08447a67bb6a0b1f7276c7c5a85` · runner_sha256 `c71176e31cd63f28ea166f8469d36b54ca305f684eec1e47528a5987bf3ca1be`

- Audited tip: `4e763fb` (integration). Lane re-based: v3 audit commit `30f7b4d` → `068ddea` on top of `4e763fb`. A ff-only move was impossible — the v3 audit commit and the B4 repair commit both descend from `b245ee9`, mirroring the v3 lane move.
- Prior: v3 verdict `FOREX_FREE_V1_W1_BLOCKED`, sole open blocker **B4 HIGH**; B1/B2 carried PASS, C1 MEDIUM carried accepted.

## 1. Scope check (no regression)

`git diff b245ee9..4e763fb` touches **exactly one file**: `research/control/forex_free_v1_run/staged_data_manifest.json` (+4/−3) — the two `w1_freeze.json` digest entries `6f91d741… → 78db4205…` in `digests_exec2` and `digests_repro2`, plus a `b4_note`. Lane diff vs integration tip is the v2+v3 audit artifacts only. Nothing else changed vs v3's PASS state.

## 2. B4 — RESOLVED

| v4 condition | Result |
|---|---|
| manifest `digests_exec2` w1_freeze entry | `78db42051d54be9dbd769d46a612de4d22dbc5e96e69484a3baae3156d9c0e42` |
| manifest `digests_repro2` w1_freeze entry | `78db42051d54be9dbd769d46a612de4d22dbc5e96e69484a3baae3156d9c0e42` |
| sha256 of staged freeze, integration/lane | `78db4205…` (equal) |
| sha256 of staged freeze, exec-2 | `78db4205…` (equal) |
| sha256 of staged freeze, repro-2 | `78db4205…` (equal) |
| staged freeze byte-identity vs integration | exec-2 IDENTICAL, repro-2 IDENTICAL (cmp), exec-2↔repro-2 IDENTICAL |
| manifest replay, exec-2 tree | **156/156** ok, 0 mismatch, 0 missing |
| manifest replay, repro-2 tree | **156/156** ok, 0 mismatch, 0 missing |

Both digest maps: 156 entries, pairwise equal. Superseded `6f91d741…` no longer appears in the authoritative manifest. The v3 155/156 single-mismatch (freeze self-entry) is gone.

**Non-blocking residual note (recorded, accepted):** the stage-time *snapshot* copies of `staged_data_manifest.json` inside exec-2/repro-2 (staged_utc `2026-09-03T13:30:00Z`, pre-dating `4e763fb`) still carry the superseded `6f91d741…` entries and lack `b4_note`; replaying those local snapshots would show 155/156. This does not affect the verdict basis — the replay pillar is defined on the authoritative control-tree manifest (156/156 in both trees), and the staged data itself is byte-verified against it. C1-style accepted disposition; not a blocker.

## 3. Carried re-verification

- **B1 PASS (carried):** runner unchanged — `sha256(scored_runner.py)` = `c71176e3…` recomputed identically in integration/lane, exec-2, repro-2; matches freeze `code_hashes`.
- **B2 PASS (carried):** freeze bytes unchanged since v3 (`78db4205…` everywhere) — all v3 PASS findings tied to freeze contents (six arm digests, spec hashes 4/4, data_probe 3/3, sessions `5f818ef1…`, calendar `43202327…`) carry unchanged.
- **C1 MEDIUM (accepted, carried):** mitigation runtime re-verified at `4e763fb` — `publish_cell` refusals `LAUNCH_AUTHORIZATION_MISSING` / `LAUNCH_NOT_AUTHORIZED` / `W1_SHA_MISMATCH` all re-trigger correctly (`scored_runner.py:166-171`).
- **Freeze/manifest self-consistency:** `w1_freeze.json` `FOREX_FREE_V1_W1` and manifest `W1` both = declared `f33a32a2f245d08447a67bb6a0b1f7276c7c5a85`.

## 4. Regression checks

- Targeted suite `tests/assets/forex_free_v1`: **91 passed** (expected 91; matches v3).
- Tree states: integration clean at `4e763fb`; lane clean after re-base; exec-2/repro-2 detached exactly at `f33a32a` (staged freeze+manifest are the only working-tree modifications, per the established staging pattern).

## 5. Conclusion

The single v3 blocker B4 is resolved by repair `4e763fb`; no regression observed. **Blockers: none.** W1 launch is authorized on `w1_sha f33a32a2f245d08447a67bb6a0b1f7276c7c5a85`, runner `c71176e31cd63f28ea166f8469d36b54ca305f684eec1e47528a5987bf3ca1be`, execution trees exec-2/repro-2 at `f33a32a`.
