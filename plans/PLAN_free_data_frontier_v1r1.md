# FREE-DATA-FRONTIER-V1R1 — OFR ENDPOINT REMEDIATION

> Successor remediation to terminal FREE-DATA-FRONTIER-V1. V1 remains
> append-only. This cycle corrects one falsified blocker and acquires the one
> named source V1 did not collect.

## Finding

V1 called `https://data.financialresearch.gov/v1/mnemonics/` and classified
the resulting HTTP 403 `Missing Authentication Token` as an edge/TLS/IP
blocker. The official STFM API documents and a fresh execution probe show the
correct inventory endpoint is:

```text
https://data.financialresearch.gov/v1/metadata/mnemonics/
```

That endpoint returned HTTP 200 on the same host. Therefore the V1 OFR
`BLOCKED_NETWORK` conclusion is false and must not be carried forward.

## Scope

Branch/worktree:

```text
cycle     FREE-DATA-FRONTIER-V1R1
branch    orca/free-data-frontier-v1r1-integration
worktree  .worktrees/free-data-frontier-v1r1/integration
base      terminal V1 integration commit
budget    0 scored cells
```

Tasks:

1. Correct the OFR route contract to the official query endpoints:
   `/metadata/mnemonics/`, `/metadata/query/?mnemonic=...`, and
   `/series/timeseries/?mnemonic=...` or `/series/full/?mnemonic=...`.
2. Add fixture tests proving exact endpoint construction and rejecting the
   obsolete V1 routes.
3. Run a live inventory canary and bounded acquisition of preregistered
   reference-rate/funding series including SOFR, EFFR, BGCR, TGCR and OBFR.
4. Store raw bytes outside Git under the existing frontier data root, with a
   new V1R1 manifest and SHA-256 verification.
5. Append a correction artifact that cites V1's false blocker without
   rewriting V1 artifacts.
6. Run targeted tests, compileall, manifest verification and an independent
   audit of the correction.

## Boundaries

- No changes to V1 terminal artifacts, scored ledgers, S1 or trading systems.
- No PnL, scoring, strategy selection or orders.
- Retrieval time never becomes historical availability time.
- No secret values in output or Git.
- Raw bytes remain outside Git; disk floor remains 15 GiB.
- A 200 response proves reachability and bytes, not profitability or
  historical PIT authorization.

## Terminal outcomes

```text
FREE_DATA_FRONTIER_V1R1_PASS_OFR_ACQUIRED
FREE_DATA_FRONTIER_V1R1_BLOCKED_SCHEMA
FREE_DATA_FRONTIER_V1R1_TECHABORT_PRESERVED
```

