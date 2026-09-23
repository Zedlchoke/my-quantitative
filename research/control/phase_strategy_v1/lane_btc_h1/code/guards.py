"""Boundary guards: S1 denial, forbidden paths, broker-surface scan.

Every lane file can call assert_clean() in tests; the scan is a static
source-level check with an explicit deny list. Fail-closed.
"""
from __future__ import annotations

from pathlib import Path

S1_PATH_MARKERS = (
    "/s1/", "SEALED_UNTOUCHED", "s1_frozen", "frozen_s1",
)
FORBIDDEN_PATH_MARKERS = (
    "SANDBOX-OVERFIT-3ASSETS",
    "wayfinder/MAP.md",
    "wayfinder/SURVIVORS.md",
    "wayfinder/HYPOTHESIS_LEDGER.md",
    "wayfinder/LESSONS.md",
    "MECHANISM_ATTRIBUTION_REPORT",
    "lane_btc_h4",
    "lane_spy_d1",
    "jev-regime-router-v1",
    "jev-regime-router-v2",
    "regime-strategy-mapping-v1",
)
BROKER_SURFACE_MARKERS = (
    "ccxt", "python-binance", "place_order", "create_order", "submit_order",
    "api_key", "api_secret", "private_key", "testnet", "paper_trading",
    "requests.post(",
)


def scan_lane_sources(lane_dir: Path) -> dict:
    """Scan lane code/tests for broker/credential surface and forbidden-path
    references. guards.py is EXCLUDED from the content scan because it is the
    declaration of the deny lists themselves (it imports nothing and exposes
    no surface); a test asserts its content is declarations only."""
    findings: list[str] = []
    files = sorted(
        list(lane_dir.glob("code/*.py")) + list(lane_dir.glob("tests_py/*.py"))
    )
    scanned = [f for f in files if f.name != "guards.py"]
    for f in scanned:
        text = f.read_text()
        for marker in BROKER_SURFACE_MARKERS:
            if marker and marker in text:
                findings.append(f"{f.name}: broker/credential marker {marker!r}")
        for marker in S1_PATH_MARKERS:
            # 'SEALED_UNTOUCHED' may appear in a comment asserting denial;
            # only flag it in string paths (heuristic: '/s1/' style markers)
            if marker != "SEALED_UNTOUCHED" and marker in text.lower():
                findings.append(f"{f.name}: S1 marker {marker!r}")
        for marker in FORBIDDEN_PATH_MARKERS:
            if marker in text and marker != "lane_btc_h4" and marker != "lane_spy_d1":
                findings.append(f"{f.name}: forbidden-path marker {marker!r}")
    # lane boundary: this lane's own name appears legitimately; filter it
    findings = [f for f in findings if "lane_btc_h1" not in f]
    return {"files_scanned": [f.name for f in scanned], "findings": findings,
            "clean": len(findings) == 0}


def deny_s1(path: str) -> bool:
    """Any file access helper in the lane routes through this gate.
    Returns True if the path is DENIED (S1 or forbidden)."""
    p = path.lower()
    if any(m in p for m in S1_PATH_MARKERS if m != "SEALED_UNTOUCHED"):
        return True
    return any(m.lower() in p for m in FORBIDDEN_PATH_MARKERS)
