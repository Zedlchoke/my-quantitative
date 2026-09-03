"""stocks_free_v1 research namespace (owner: A2/Z1 data-authority lane).

Modules:
- ``source_evidence``: machine-readable SOURCE_CANDIDATES license/zero-cost
  evidence registry (PLAN_stocks_free.md section 4.1 items 1-3).
- ``data_adapter``: deterministic rate-limited downloader with SHA-256
  manifests, retry/backoff and two-pull revision comparison (items 4, 12, 13).
- ``reconciliation``: raw NAV/distribution total-return reconstruction and
  provider-series conflict recording (items 7, 10, 14, 15).
- ``gap_audit``: missing/duplicate/out-of-order/non-positive/gap detection
  with injected session predicate (items 5, 11).

Raw provider payloads never enter Git; they live under the repo-external
staging area. Git stores checksum manifests, logs and short terms excerpts
only (PLAN_stocks_free.md section 2).
"""

VERSION = "stocks_free_v1/z1_a2@1"
