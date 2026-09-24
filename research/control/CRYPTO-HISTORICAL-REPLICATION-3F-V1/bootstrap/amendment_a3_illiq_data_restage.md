# Amendment A3 — ILLIQ runs under EQUIVALENCE_DATA_RESTAGE_UNPROVEN (owner: "chạy cell ILLIQ và BASISLV trong hôm nay")

## Facts (measured)
- Engine: byte-frozen at c97283e0, 16/16 golden/identity/PIT/causal tests PASS,
  and the equivalence run traverses it end-to-end without error.
- Output-equivalence vs the A7 baseline FAILED at the registered 1e-9:
  net 0.7132 vs 0.5820 (rel 0.226), PF 1.4623 vs 1.3548 (0.079),
  MDD 0.0868 vs 0.0918 (0.055), positions 328 vs 336,
  hit-rate EXACT 24/52, funding +0.1109 vs implied baseline ~-0.019.
- Root causes narrowed, NOT closable from surviving bytes:
  (a) original funding bundles lost (INC-3-era layout; A7-r2-verified B-window
      bytes differ from the A-window originals only in window — value-layer
      equality unverifiable);
  (b) original instrument tick table lost (c1_fields cites 1e-07; hypothesis
      tested: constant 1e-07 changed nothing material -> ticks are NOT the
      driver; the funding/value layer is);
  (c) vision-zip vs REST provenance untested at bar level (F1 fold PF matches
      to 2%, suggesting mostly-identical bars).
- Tick hypothesis tested and REJECTED (documented); funding forensics blocked
  by lost bytes.

## Owner decision (recorded)
Run ILLIQ scored cells TODAY under:
- LABEL: `EQUIVALENCE_DATA_RESTAGE_UNPROVEN` on every ILLIQ cell/report line;
- standing disclosure: results are the FROZEN MECHANISM on BEST-EFFORT
  RESTAGED data; they are NOT the historical family's exact-identity numbers;
  weaker evidence tier than XSECT's provenance gate (measured mismatch, not
  mere unverifiability);
- all other A2 conditions stand (census, sanitized traversal evidence, A7
  prelaunch fresh-context, heavy lock, budget).

## Consequence for interpretation
ILLIQ replication results must be read as "does the frozen mechanism, on
faithfully-sourced public data, reproduce the near-miss behaviour?" — NOT as
a byte-exact identity replication. Any future restoration of the original
staged snapshot re-opens the equivalence gate (label upgrade path).
