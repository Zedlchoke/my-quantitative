# ERRATUM F-1 — cal_close sha-citation correction of record (append-only)

- Source: VERIFY F-1 (MINOR), this round's `verify/VERIFY_REPORT.md`.
- Defect: `cal_close/CAL_CLOSE_REPORT.md` (as committed in wave 1) cites
  round-1's claimed sha for the recovered capture
  `svc_20260401_..._0722114222` as `0700f57c…`; round-1's own verify
  report recorded `c8388564…` for that filename (status
  MISSING_FROM_DISK), and `0700f57c…` belongs to a DIFFERENT capture.
  The served bytes recovered this round match NEITHER claimed hash.
- Classification: citation error only. The lane's own capture is hashed
  in this round's `cal_close/SHA256SUMS_lane.txt` (verified 10/10 by
  VERIFY §C2), so the lane's evidence chain is intact; what is
  unverified is ROUND-1's claimed-hash row (already flagged
  MISSING_FROM_DISK there).
- Correction of record: for the recovered file, the authoritative hash is
  the one in THIS round's SHA256SUMS_lane.txt; round-1's claimed hashes
  for MISSING_FROM_DISK rows remain UNVERIFIED and must not be cited as
  evidence by any future consumer. No lane file is edited (append-only);
  this erratum supersedes the citation by reference.
- Safety check: no downstream arithmetic consumes either stale hash
  (checked: the delta JSON keys off this round's own hashes).

— End ERRATUM F-1.
