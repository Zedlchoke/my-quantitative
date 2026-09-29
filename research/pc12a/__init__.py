"""PC12A engine skeleton — PORTFOLIO-COMPOSITE-12ASSETS-100K-V1, implementation lane.

Dry-run (no-PnL) engine skeleton per the spec authority set committed at the
cycle's evidence HEAD:

- FILL_ACCOUNTING_SPEC.md   — fill model, spread-once law, book identity
- JOURNAL_SCHEMA.md         — journal_row@1 (incl. blocked signals)
- journal/fixtures/*.json   — fx1..fx6 hand-computed accounting gates (1e-9)
- CLASS_SPEC_VOLPROF_M1.md  — the 9 VOLPROF class candidates (frozen)
- DATA_AUDIT_REPORT.md      — .bi5 panel format, divisors, corrected C2 cells
- BACKTEST_CAMPAIGN_DESIGN.md — fold calendar (286 Fridays), stages
- GROUPING_PROPOSAL.md      — 3.6 forbidden feature list, 4.2 ONOFF twin rows

RGC-INC-1 law: this package's dry-run surfaces (run_dry.DRY_RUN_REPORT.json
and its journal) carry decision counts, fill counts and cost bills ONLY.
"""

__all__ = [
    "panels",
    "calendar_service",
    "cost_kernel",
    "journal",
    "books",
    "legs",
    "policy",
]

SCHEMA_JOURNAL_ROW = "journal_row@1"
CYCLE_ID = "PORTFOLIO-COMPOSITE-12ASSETS-100K-V1"
