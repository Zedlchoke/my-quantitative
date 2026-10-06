# FREEZE_BUILDER_SPEC_NQ — deterministic NQ freeze builder (SPEC ONLY — nothing implemented, nothing run; today = NOT_RUN, D9-blocked)

- Round **FUTURES-5SYM-PRESCORED-20261005**, lane **NQ**, 2026-10-05. DRAFT-PENDING-OWNER.
- This file SPECIFIES the deterministic freeze builder an approved cycle would run at its
  registration freeze. **It is not code, has not been executed, and MUST hard-refuse while
  ADOPT-D9 is unsigned.** Builder status today: **NOT_RUN (D9-blocked)**.

## 0. Hard-refuse gate — ADOPT-D9 FIRST (binding precedence order)

1. **GATE-0 (D9)**: read the owner ruling state for **ADOPT-D9** (Option A = cease-guard standing
   law + cache_v3 canonicalization; `D8_D9_DECISION_SHEET.md`, sha256 `b1d6079f…f8ae`). If D9 is
   unsigned or ruled Option B:
   - the builder **writes nothing** (no output directory is created, no manifest, no partial
     files), **exits non-zero**, and emits a machine-readable refusal record
     `{"builder":"freeze_builder_nq","gate":"GATE-0_D9","verdict":"REFUSED_D9_UNSIGNED",
       "consumed_inputs":0,"outputs":0,"timestamp_utc":<now>}` to the caller's stdout only;
   - the refusal itself is the ONLY artifact, and it is advisory (no lane may convert it into a
     gate pass);
   - **today's status under this law: NOT_RUN — no invocation is even lawful until an owner
     ruling exists, so GATE-0 has never been reached.**
2. Only after GATE-0 passes (D9 = Option A, evidenced by a recorded owner ruling) may GATE-1+
   execute, in order: GATE-1 input digests → GATE-2 chain-law params → GATE-3 alias rule →
   GATE-4 build+digest → GATE-5 reproduction twin → GATE-6 manifest emit. Any gate failure ⇒
   `BLOCKED_<gate>` and stop; **no mid-flight repair** (launch-draft §6.3 law carried).

## 1. Input set + digests (verified by THIS lane in THIS worktree, 2026-10-05)

All inputs live under
`research/control/FUTURES-SIX-READINESS-20261004/nq/cache_v3/`. Re-hash result: **10/10 sha256 +
byte-size match** the committed manifest
`research/control/FUTURES-SIX-ADOPT-PREP-20261004/adopt/cache_v3_hashes.json` (sha256
`6cad549d…894d3`). Parquet metadata row counts re-measured the same pass.

| file | sha256 | bytes | rows (metadata) |
|---|---|---|---|
| `nq_outright_1m_v3.parquet` | `10cfe94d9c7754c009a849cca251c19d64733a8c36a74c736a87b56cbf8bc463` | 148,997,026 | 6,780,608 |
| `nq_annotated_1m_v3.parquet` | `e233da66420b3daa8a5dfff84bb8cc19083c305a5eb66f4a936083c9028f6522` | 178,545,904 | 6,780,608 |
| `nq_sessions_v3.parquet` | `30bc1ec3f4a476165b4681e036abc9e1ebb77ec6736725806fc5f767624920fe` | 1,230,715 | 11,715 |
| `held_volume_k5_v3.parquet` | `99ff1ca1475dbf1bbce7b5a43fa7c4e301d9c09a1849dbe42206bfe44fa56db6` | 26,034 | 4,219 |
| `held_volume_k5_cg_v3.parquet` | `99ff1ca1475dbf1bbce7b5a43fa7c4e301d9c09a1849dbe42206bfe44fa56db6` (byte-identical to plain) | 26,034 | 4,219 |
| `nq_held_daily_v3.parquet` | `b7bd830a46f46bb07da3b3cf1f3eee7a465a463506ddbd7692fd48125bcd00ce` | 361,375 | 4,219 |
| `contract_registry_v3.json` | `6a629d715e0f51d991928e7a86bef017442666f56b66b846f7660fe2865edcfb` | 35,833 | 113 clusters |
| `rebuild_stats.json` | `14869be55b83595624de0aec85cf2fd89cb1a04b96e4ab85915391c9edc00a34` | 1,227 | — |
| `v3_hold_segments_k5.parquet` | `46332bb5a20a7e548f2a7c96603ccd414dd4284e7a45a3915052818a5005335b` | 7,513 | 67 |
| `v3_rolls_spread_stats.parquet` | `29e9b85870cfd2db3af7960d8defa92c2eef0e4cc43de32a1e3f7cebd5b79954` | 8,997 | 66 |

Reproduction stash: `cache_v3/_repro_run1/` (`held_volume_k5_v3.parquet` / `held_volume_k5_cg_v3.parquet`
byte-identical `99ff1ca1…6db6`; `run1_digests.json` sha256 `0b521219…f75`).

**GATE-1 law**: any digest or byte-size drift vs this table at freeze time ⇒ `BLOCKED_INPUT_DRIFT`,
never silent reuse (launch-draft §1 pinning law carried).

## 2. Chain params (GATE-2)

- **k = 5** volume-crossover rule (trailing-5-session mean volume, hold the max-mean candidate) —
  **UNCHANGED from baseline** (`front_by_volume_crossover`; k=5 is not a tunable here; re-fitting
  it on any outcome is forbidden by the PIT statement §1.2).
- **Cease-guard variant**: switch date = **max(volume-crossover date, cease-floor)** where the
  cease-floor fires when the held contract has no bars today or the session is past its
  bars-present cessation; immediate switch to the next quarterly (first candidate with data today,
  else first with any data), volume-blind; every guard fire recorded (session, old, new, trigger);
  the chain is INVALID if any held session is past cessation (`CEASE_GUARD_STANDARD.md` §2
  normative text + pseudocode, sha256 `6c58a3f8…1b44`). **Cessation source law**: cessation from
  the session table is full-sample construction — legal for the chain (each firing decision uses
  only time-t facts; `CACHE_V3_PIT_STATEMENT.md` §2 seam 2); any in-sample strategy use must
  re-derive cessation causally (absence-of-bars-today), which yields the identical chain.
- **Measured invariants the builder must reproduce and assert** (all from the re-hashed bytes):
  66 rolls; 4,219 held sessions; 0 NaN held-daily closes; cg chain ≡ plain chain (0 guard firings);
  exactly one `NQH0_2020 → NQM0_2020` roll at **2020-03-19** (dte +1; 85,489 vs 487,005); 66/66
  rolls with 0 ≤ dte ≤ 45; sessions 11,715; registry 113 clusters. Any invariant miss ⇒
  `BLOCKED_INVARIANT`.
- **D9-contingent param record**: the manifest must record WHICH guard law binds (plain k=5 only if
  D9 = Option B; k=5 + explicit cease-guard if D9 = Option A). Under this packet's own binding
  statement only Option A makes the packet executable — Option B routes back to SPEC_NQ's
  conditional-binding clause, i.e. the cycle is not formed.

## 3. Alias view rule application (GATE-3)

`instrument_id == 16908 AND ts_event < 2020-06-01 UTC ⇒ raw_symbol = 'NQM0'` (relabel, include);
ALL other dash rows are true calendar-spread rows and stay excluded; the rule is applied BEFORE the
dash-excluding filter. Fixed once by the `A_ALIAS_NOT_ABSENCE` adjudication (vendor-metadata
record-count reconciliation; zero outcome information); **not re-litigated per arm** — changing it
= owner amendment + full re-derivation + new chain digests (`CYCLE_LAUNCH_DRAFT.md` §2 alias law).
Provenance pin: `nq/alias_lineage.json` sha256 `8669ab65…1a68` (92,075 rows / 24,686,121 vol
recovered; `NQU8-NQM9` instrument_ids = [16908] only).

## 4. Outputs (GATE-4/GATE-6)

1. **Frozen panel** = the byte-verified input set (§1) copied (or hard-linked) into the cycle's
   selection-freeze directory; the builder does NOT re-derive the panel unless a re-ingestion
   occurred (which would require a new rebuild + re-hash under the same declared rules —
   `CACHE_V3_PIT_STATEMENT.md` §4 seam 5).
2. **Manifest** (`freeze_manifest_nq.json`), deterministic JSON with sorted keys, containing:
   - `input_digests`: the §1 table verbatim (path, sha256, bytes);
   - `params`: `{symbol:"NQ", k:5, guard_law:<"cease_guard_explicit"|"plain_k5">,
     alias_rule:"id16908<2020-06-01UTC->NQM0", session_switch_date:"2015-09-21",
     day_boundary_ct:"17:00", era_closes_ct:{"A":"16:15","B":"16:00"},
     dst_law:"fall_back_absolute_24h_preserved_as_measured"}`;
   - `invariants`: the §2 assertions with measured values;
   - `code_sha`: sha256 of every builder/rebuild source file consumed (at minimum
     `nq_deep_lib_v3.py`, `nq_rebuild_v3.py`, `nq_reproduce_digest.py` from
     `FUTURES-SIX-READINESS-20261004/nq/`) + the builder's own source sha;
   - `owner_ruling_refs`: D9 ruling pointer; cost-variant pointer (D3); ceiling pointer; all
     "pending" unless ruled;
   - `d9_gate`: `{status:"PASSED", ruling_ref:<path>}` (unreachable today).
3. **Digest law**: the frozen set's identity digests to be re-pinned at registration are the
   method digests already proven stable across independent rebuilds: held-chain key digest
   `d359b4d46d640fd45efdedda5a090c31b47b4a6928ec00d13aa7bbc1b0e07e3d` (both chains), sessions key
   digest `64203dd2e007ea6f01d5be15a6228ca17739219482ec5b826d67ee84c8f7da66` — run-1 = run-2 =
   ADOPT re-measure, 0 deltas (`cache_v3_hashes.json::deltas_vs_round1`).

## 5. Reproduction twin contract (GATE-5)

- The twin re-derives the held chain and sessions **from raw lineage** under the declared rules
  using the committed generators (`nq_rebuild_v3.py all`; loader `nq_deep_lib_v3.py::
  load_outright_1m_v3()` with `ALIAS_CUTOVER = 2020-06-01 UTC`) in a fresh process, then compares:
  (a) sorted fixed-dtype CSV sha256 of held-chain key columns (session_date, held) — must equal
  `d359b4d4…07e3d`; (b) sessions key digest — must equal `64203dd2…f7da66`; (c) panel row count +
  ts min/max — must equal 6,780,608 / 2010-06-06 22:00Z / 2026-09-30 23:59Z; (d)
  `assert_frame_equal(check_exact=True)` vs the frozen chain. Byte equality of parquets is NOT
  required (method disclosed in `reproduction.json`, sha256 `ec2d315b…e8cf`); logical equality IS.
- Any twin mismatch ⇒ `BLOCKED_REPRODUCTION`; the freeze is void, back to GATE-0 with the owner.
- Precedence evidence: this contract has already been satisfied once (round-1 two independent
  rebuilds + ADOPT re-measure, 0 deltas) — recorded as evidence, **not** as a GATE-5 execution for
  any future cycle (each cycle re-runs its own twin).

## 6. Pre-freeze gate list (ordered; ADOPT-D9 FIRST)

| order | gate | pass condition | current state |
|---|---|---|---|
| 0 | **ADOPT-D9** | recorded owner ruling = Option A (cease-guard standing law + cache_v3 canonical) | **OPEN — builder hard-refuses; today = NOT_RUN** |
| 1 | input digests | §1 table exact match | VERIFIED (this lane, 2026-10-05; re-run at any real freeze) |
| 2 | chain params | k=5 + guard law recorded; invariants asserted | params fixed; execution NOT_RUN |
| 3 | alias rule | boundary + target == pinned rule | pinned; execution NOT_RUN |
| 4 | build + digest | invariants pass; manifest assembled | NOT_RUN |
| 5 | reproduction twin | §5 comparisons equal | NOT_RUN (prior-round evidence only) |
| 6 | manifest emit | manifest sha256 into the selection freeze | NOT_RUN |

Heavy-lock discipline at any real execution: `research/researchctl.py locks inspect` before/after;
held ⇒ `NOT_RUN_RESOURCE_CONFLICT` (a full rebuild is a heavy job; digest verification alone is a
light read).

— End FREEZE_BUILDER_SPEC_NQ. Specification only; nothing implemented; GATE-0 unreached; NOT_RUN.
