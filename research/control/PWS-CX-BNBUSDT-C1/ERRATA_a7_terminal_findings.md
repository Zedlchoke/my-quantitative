# ERRATA per A7 terminal 4381cff1 (3 LOW, none blocking)
- F-1: trial_ledger.jsonl did not exist while CYCLE_VERDICT said '0 rows' — file now created EMPTY (0 rows); 0-trials state already corroborated by registry 0/18 + unchanged IDENTITY_REGISTRY + zero scored artifacts.
- F-2: C1 report sec7 pins stale sha for C2 (dbb973a1... vs final 7feeb2e7...); C2 content unchanged — final sha of record: 7feeb2e7 (see git history of C2_EXPOSURE_VERIFICATION.md).
- F-3: C3 prose said '4 handoff JSON'; 3 existed pre-A7 (council-P1, c1c2-data-pit, skeptic-verify); the A7 handoff is the 4th.
