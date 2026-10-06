# FIX REPORT — trial_ledger.py reopen/append hash-chain defect (lane LEDGER-FIX)

- Cycle: `FUTURES-ES-PB1-V1` · Lane: `LEDGER-FIX` · Date: 2026-10-05
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep`
  (branch `prep/futures-es-reg-20261004`)
- HEAD at start AND at end of lane: `2291d562c32f01d484d77947650609d8050d6ad1`
  (verified once at start; end `git status --short` clean of tracked-file
  changes outside the authorized paths — see handoff `tree_status`)
- FAIL record authorizing the fix:
  `gate6/fix/FAIL_LEDGER_REPLAY.md` (reproduced 2026-10-04 at HEAD 71326c8c)
- Python: `/Users/hoangminhlong/my-quantitative/.venv/bin/python` · Zero
  network · Synthetic identities only (`SYNTH-*`) · Zero panel/parquet reads ·
  Zero quarantined-PnL reads.

---

## 1. The fix (exactly ONE line, method `_replay`)

```diff
--- research/control/FUTURES-ES-PB1-V1/gate6/trial_ledger.py
+++ research/control/FUTURES-ES-PB1-V1/gate6/trial_ledger.py  (uncommitted; controller commits)
@@ def _replay (per-line replay loop, L125) @@
                 self._seq = i
-                self._prev_sha = row.get("prev_row_sha")
+                self._prev_sha = _row_sha(row)
                 prev_parsed = row
```

Root cause (per FAIL record, confirmed by code read): replay restored the
chain cursor from the LAST ROW'S `prev_row_sha` FIELD — a pointer to the
second-to-last row — instead of the canonical hash OF the last row, which is
what `_append` (L150) maintains. The first append after any reopen therefore
linked to the wrong predecessor and the verifier (correctly) rejected the
chain. The verifier's law itself was never touched; no other method, docstring
or constant was modified.

## 2. M2 — comprehensive synthetic suite (`gate6/fix/test_ledger_fix.py`)

Run output (verbatim): `gate6/fix/test_ledger_fix_output.txt`.
Suite exit code 1 solely because case G1 records a deviation (FINDING, §4);
every check belonging to the fix's proof passed.

| Cat | Case | Result |
|-----|------|--------|
| A — FAIL-record reproduction | A1 session-1 append + verify ok | PASS |
| A | A2 reopen + append does NOT raise (pre-fix: `LedgerError: hash-chain break at line 2`) | PASS |
| A | A3 verify ok after reopen+append (rows=2) | PASS |
| B — multi-session reopen ×5 | B1.1–B1.5 five sessions (8/4/4/4/4 rows over 24 SYNTH ids), each reopen+append+verify ok | PASS ×5 |
| B | B2 final verify ok end-to-end | PASS |
| B | B3 total rows == 24 | PASS |
| B | B4 observed == 24, ledger complete | PASS |
| B | B5 independent disk-bytes chain re-verification (fresh parse + `_row_sha`, not module verify) | PASS |
| C — bytes-never-rewritten | C1 line count only grows 3→5→7 | PASS |
| C | C2 session-1 bytes are an EXACT PREFIX of final bytes | PASS |
| C | C3 file strictly grew, no byte rewritten | PASS |
| D — tampering | D1 non-final-row tamper rejected NAMING the successor: `hash-chain break at line 3` | PASS |
| D | D2a final-row tamper: chain verify alone stays ok (law: no successor link to break) | PASS |
| D | D2b final-row tamper DETECTED by `summary().file_sha256` digest change (chain law as written in `_replay` docstring) | PASS |
| D | D3 truncated middle line rejected (fail-closed `JSONDecodeError`) | PASS |
| E — interrupted write | E1 torn final line: reopen FAILS CLOSED (never silent) | PASS |
| E | E2 rejected as malformed JSON — raw `json.JSONDecodeError`, NOT a `LedgerError` | PASS |
| E | E3 failed reopen does NOT rewrite/repair the file (append-only holds on the read path) | PASS |
| E | E4 `verify()` on torn file also fails closed | PASS |
| F — duplicate/retry accounting | F1 PASS→PASS refused (double-terminal) | PASS |
| F | F2 PASS→FAIL refused (append-only, no overwrite) | PASS |
| F | F3 slot-level `REFUSED` is TERMINAL (class law: one terminal row PASS/FAIL/REFUSED per identity); PASS after it refused | PASS |
| F | F4 run-level `record_refusal` (identity_id=None) consumes NO slot, never counts observed; PASS after it allowed | PASS |
| F | F5 observed == PASS+FAIL rows exactly (2 PASS incl. published=False + 1 FAIL == 3; disk `counts_observed` recount == 3) | PASS |
| F | F6 publication failure still counts observed | PASS |
| F | F7 terminal law restored across reopen (PASS re-refused) | PASS |
| F | F8 terminal law restored across reopen (FAIL re-refused) | PASS |
| G — fresh-path verify | G1 `verify()` before any append on a fresh path | **FINDING** (raises `FileNotFoundError`, see §4) |
| G | G2 fresh path: first append then verify ok | PASS |
| G | G3 empty-but-existing file: verify ok, rows 0 | PASS |

**Suite total: 33 PASS / 1 recorded deviation (G1 → FINDING) / 2 FINDINGS.**

## 3. M3 — regression vs the ORIGINAL smoke test: 28/28 ALL GREEN

The original `gate6/synthetic_smoke_test.py` was re-run UNMODIFIED (byte-copy,
`cmp`-proven identical) in a sandbox under
`gate6/fix/smoke_regress/research/control/FUTURES-ES-PB1-V1/gate6/` that
mirrors the original directory depth, with `trial_ledger.py` a SYMLINK to the
real fixed module (so the fixed file itself is what executed) and the freeze
JSON copied for the script's relative `HERE.parents[3]` resolution. This was
necessary because the committed `gate6/smoke/` ledger is already
terminal-complete; a naive re-run at the original location would append to it
(double-terminal) and would also write outside this lane's boundary. Sandbox
outputs stay under `gate6/fix/**`; the committed `gate6/smoke/` evidence is
untouched. Verbatim output: `gate6/fix/smoke_regression_output.txt` —
**28 pass / 0 fail — ALL GREEN**. No prior test depended on the buggy replay
(the smoke test used a single ledger session; its reopen coverage was the
constructor-level reads only).

## 4. FINDINGS (recorded, NOT invented, NOT fixed — outside the one-line mandate)

1. **F-1 / torn final lines (M2 case E): the frozen law is SILENT.** The
   module docstring, the `_append` comment (`single line + '\n', flush +
   fsync`), the `_replay` docstring (blank-line / seq / chain errors) and the
   original smoke test (no torn-write handling anywhere) say nothing about a
   torn FINAL line. Actual behavior, asserted by the suite: reopen/verify
   FAIL CLOSED with a raw `json.JSONDecodeError` (not a `LedgerError` with a
   ledger-specific message), and the file is never rewritten or
   repair-truncated (append-only law holds even on the read path). The write
   side (single-line append + fsync) is the mitigation. Mapping the decode
   error to `LedgerError` would be a law amendment and was NOT done.
2. **F-2 / `verify()` on a never-written path (M2 case G1):** raises
   `FileNotFoundError` instead of returning ok, while `summary()` handles the
   same state gracefully (`file_sha256: None`). Orthogonal to the fix: for a
   nonexistent file `_replay` raises at `open()`, before the loop containing
   L125 can ever run, so the one-line change cannot affect this path
   (pre-existing edge, present at the FAIL-record HEAD too). Law is silent;
   left as-is.

## 5. Artifacts (all under the authorized boundary)

| Path | Role |
|------|------|
| `gate6/trial_ledger.py` | the authorized ONE-LINE fix (uncommitted) |
| `gate6/fix/FAIL_LEDGER_REPLAY.md` | pre-existing FAIL record (unchanged) |
| `gate6/fix/test_ledger_fix.py` | M2 synthetic suite (this lane) |
| `gate6/fix/test_ledger_fix_output.txt` | verbatim suite run output |
| `gate6/fix/smoke_regression_output.txt` | M3 verbatim 28/28 output |
| `gate6/fix/smoke_regress/` | M3 sandbox (byte-copy of original smoke test + symlinked fixed module + freeze copy; run outputs inside) |
| `gate6/fix/FIX_REPORT.md` | this report |
| `dispatch/handoff_LEDGER-FIX.json` | structured handoff (zcode_orch_v3_handoff@1) |

— End FIX_REPORT. No commit/stage/push performed (controller commits).
