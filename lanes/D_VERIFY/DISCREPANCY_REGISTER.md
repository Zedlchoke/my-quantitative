# DISCREPANCY REGISTER — Lane D_VERIFY · WINPROB-PLAYERFEAT-PREP-V1 · 2026-10-05

Overall verdict: **VERIFIED_WITH_MINOR** (0 BLOCKER, 0 MAJOR, 1 MINOR, 2 INFO).

| id | severity | lane | finding | evidence | disposition |
|---|---|---|---|---|---|
| MINOR-1 | MINOR | B_WNBA_FEAT | Documentation misstates Group B k=3 computed-row count: `FEATURE_TABLE_MANIFEST.md` and handoff text say "5,778 computed rows each" for k=3 and k=5; the table actually has **6,124** computed b3 rows (insufficient_history 344, not 690 — the MD copied the k=5 neutral-count row). The machine manifest JSON omits a b3 entry entirely (only b5 listed). The DATA is self-consistent and correct (`b3_games_played == 3` on all 6,124 non-null rows; reason counts sum to 11,976); only the MD/handoff narrative is wrong. No downstream law depends on the number. | `wnba_output.json` → computed_counts; table value counts of `b3_neutral_reason` | Correct the MD text + handoff wording in a controller-approved doc fix; the parquet needs no change |
| INFO-1 | INFO | D_VERIFY (self-reported) | D_VERIFY's first universe derivation kept the 2018 forfeit + 2023 postponed games (5,990) because pandas 3.0 string-dtype NA propagation defeated a bare `.str.contains` drop filter; after fixing the verifier's own filter (drop by `status_type_name` ∈ {STATUS_FORFEIT, STATUS_POSTPONED}), the universe reproduces 5,988 exactly. Lane B's code was correct; the initial delta was a verifier bug. Recorded for transparency. | `wnba_output.json` (final run) | None — verifier-side, resolved |
| INFO-2 | INFO | A_NBA_FEAT / B_WNBA_FEAT | Known-limitation registers in both lane handoffs are accurate as far as re-measured (exhibition disclosure 38 rows `is_exhibition=1` matches 19 games × 2 sides; 33 NULL-athlete 2026 rows not re-censused directly but consistent with 0-dup/0-orphan results and the lane's census; ESPN/league underlying rights remain UNVERIFIED — carried law, fail-closed). | `nba_recompute_output.json` → exhibition_rows_total=38 | None |

No BLOCKER, no MAJOR. No scored computation found. No outcome column found in either
feature table. No write outside D_VERIFY's allowed paths.
