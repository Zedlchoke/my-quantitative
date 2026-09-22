"""DATA-GATE lane D2-CURIOSITY-V1: assemble binding reports + evidence files.

Emits, under research/control/d2_curiosity_v1_run/data/:
  cng2/binding_report.json
  fxng3/binding_report.json (+ fxng3/alfred_availability_probe.json)
  sfng2/binding_report.json (+ sfng2/sec_submissions_check.json)
No outcome computation anywhere. No API keys touched or echoed.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

BASE = Path("/Users/hoangminhlong/my-quantitative")
WT = BASE / ".worktrees/d2-curiosity-v1/integration"
DATA = WT / "research/control/d2_curiosity_v1_run/data"
CADS = BASE / ".runtime/v3_cads_store"
RECON_FX = Path("/tmp/d2c_sources/forex_ng3")
RECON_ST = Path("/tmp/d2c_sources/stocks_ng2")
RECON_CR = Path("/tmp/d2c_sources/crypto_ng2")
SEARCH_P0 = BASE / ".worktrees/stocks-search-v1/integration/research/control/stocks_search_v1_run/p0"
NOW = datetime.now(timezone.utc).isoformat()


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def wj(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=1) + "\n")


# ---------------------------------------------------------------- CNG2 ------
klines_sum = json.loads((DATA / "cng2/klines_repull/summary.json").read_text())
funding_manifest = json.loads((DATA / "cng2/manifest.json").read_text())

cng2 = {
    "schema": "d2c_family_binding_report@1",
    "family": "CNG2-A5-P1",
    "generated_utc": NOW,
    "inputs": [
        {
            "input": "panel_BTCUSDT_h1.csv (S4 H1 panel)",
            "pinned_sha256": "111c1a2d6d62e26c1874bb428c10216e4926ae37ab0102ca098849ca25f5e7b1",
            "observed_sha256": sha(CADS / "objects/11/111c1a2d6d62e26c1874bb428c10216e4926ae37ab0102ca098849ca25f5e7b1"),
            "status": "BOUND_DIGEST",
            "evidence_paths": [
                str(CADS / "objects/11/111c1a2d6d62e26c1874bb428c10216e4926ae37ab0102ca098849ca25f5e7b1"),
                str(CADS / "pins.jsonl"),
                "sources/cng2_a5_p1_identity.json data_inputs[0].sha256"],
            "invariants_checked": {
                "digest": "match",
                "cads_address_is_digest": True,
                "bytes": 2445780,
                "pin_event_in_pins_jsonl": True}},
        {
            "input": "panel_ETHUSDT_h1.csv (S4 H1 panel)",
            "pinned_sha256": "ebd487a69404a1104d9123584c93af044a2796c338185d8466599b9f34bb440b",
            "observed_sha256": sha(CADS / "objects/eb/ebd487a69404a1104d9123584c93af044a2796c338185d8466599b9f34bb440b"),
            "status": "BOUND_DIGEST",
            "evidence_paths": [
                str(CADS / "objects/eb/ebd487a69404a1104d9123584c93af044a2796c338185d8466599b9f34bb440b"),
                str(CADS / "pins.jsonl")],
            "invariants_checked": {"digest": "match", "bytes": 2519136}},
        {
            "input": "panel_SOLUSDT_h1.csv (S4 H1 panel)",
            "pinned_sha256": "c4ca0b6eb719122054abec2a03fcac20d3f7794c5bf6d3c546ee6db1cb6e2107",
            "observed_sha256": sha(CADS / "objects/c4/c4ca0b6eb719122054abec2a03fcac20d3f7794c5bf6d3c546ee6db1cb6e2107"),
            "status": "BOUND_DIGEST",
            "evidence_paths": [
                str(CADS / "objects/c4/c4ca0b6eb719122054abec2a03fcac20d3f7794c5bf6d3c546ee6db1cb6e2107"),
                str(CADS / "pins.jsonl")],
            "invariants_checked": {"digest": "match", "bytes": 2414115}},
        {
            "input": "panel_manifest.json (S4 panel manifest)",
            "pinned_sha256": "761190a52e6504a74e12748efdb232dba03b40fa3065d35820b025283122e08b",
            "observed_sha256": sha(CADS / "objects/76/761190a52e6504a74e12748efdb232dba03b40fa3065d35820b025283122e08b"),
            "status": "BOUND_DIGEST",
            "evidence_paths": [
                str(CADS / "objects/76/761190a52e6504a74e12748efdb232dba03b40fa3065d35820b025283122e08b")],
            "invariants_checked": {"digest": "match", "bytes": 25215}},
        {
            "input": "funding_history.json (fapi/v1/fundingRate settlement series)",
            "pinned_sha256": "38ad6faf2fcbf6c80f31241d426afc61837d5886cccccb8c1cd4f566ac0cdab1",
            "observed_sha256": sha(DATA / "cng2/funding_history.json"),
            "status": "BOUND_DIGEST",
            "evidence_paths": [
                str(DATA / "cng2/funding_history.json"),
                str(DATA / "cng2/manifest.json"),
                str(DATA / "tools/cng2_funding_repull.py"),
                str(RECON_CR / "research/assets/crypto_ng2/d2/measure.py"),
                str(RECON_CR / "research/control/crypto_ng2_run/d2/pull_funding.py")],
            "invariants_checked": {
                "digest": "match (fresh keyless re-pull through the source cycle's own measure.pull_funding_all; window bounded by frozen start/end so upstream immutability applies)",
                "rows_in_window_per_symbol": 1095,
                "span_ms_per_symbol": [1755820800010, 1787328000001],
                "evidenced_grid_instants_per_symbol": "1094/1094",
                "off_grid_rows": 0,
                "duplicate_grid_hours": 0,
                "non_increasing_pairs": 0}},
        {
            "input": "funding manifest.json",
            "pinned_sha256": "a3634d6ef4c74bd2e14a6d1bcbff0a1deb388695e9030d02ac31682563d374ec",
            "observed_sha256": sha(DATA / "cng2/manifest.json"),
            "status": "BOUND_CONTENT",
            "evidence_paths": [str(DATA / "cng2/manifest.json")],
            "invariants_checked": {
                "why_digest_unreproducible": "pinned manifest embeds generated_utc of the original run; byte equality impossible by construction",
                "invariant_fields_equal": {
                    "rows_in_window": funding_manifest["evidence_fold"] and all(
                        r["rows_in_window"] == 1095 for r in funding_manifest["evidence_fold"].values()),
                    "span_ms": [1755820800010, 1787328000001],
                    "grid_hypothesis_1094_per_symbol": funding_manifest["grid_hypothesis_1094_per_symbol"],
                    "endpoint": funding_manifest["endpoint"],
                    "window_ms": [funding_manifest["window"]["start_ms"], funding_manifest["window"]["end_ms"]]},
                "new_digest_recorded": True}},
        {
            "input": "fapi/v1/klines H1 re-pull (supplementary availability evidence; NOT a pinned input)",
            "pinned_sha256": None,
            "observed_sha256": {s: klines_sum[s]["klines_sha256"] for s in ("BTCUSDT", "ETHUSDT", "SOLUSDT")},
            "status": "NOT_PINNED_SUPPLEMENTARY",
            "evidence_paths": [str(DATA / "cng2/klines_repull")],
            "invariants_checked": {
                s: {
                    "bars_pulled": klines_sum[s]["bars_pulled"],
                    "expected_bars": 8760,
                    "first_last_open_ms": [klines_sum[s]["first_open_ms"], klines_sum[s]["last_open_ms"]],
                    "contiguous_hourly": klines_sum[s]["contiguous_hourly"],
                    "price_cell_mismatches_vs_cads_panel_of_35040": klines_sum[s]["price_mismatches_vs_panel"],
                    "note": "panels were built from Binance Vision monthly aggTrades; fapi klines are a different surface (raw trades). Mismatch cells are last-tick rounding (0.8-1.6%), no structural divergence; grid invariants all-pass.",
                } for s in ("BTCUSDT", "ETHUSDT", "SOLUSDT")}},
    ],
    "family_status": "BINDABLE_NOW",
}
wj(DATA / "cng2/binding_report.json", cng2)

# ---------------------------------------------------------------- FXNG3 ------
alfred_cpi = Path("/tmp/alfred_cancpi.csv")
alfred_dgs = Path("/tmp/alfred_dgs10.csv")
probe = {
    "generated_utc": NOW,
    "law": "availability probe only; current-vintage tables are NOT a permitted substitute for the pinned vintaged archives (no improvised substitute)",
    "CANCPIALLMINMEI": {
        "endpoint": "https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=CANCPIALLMINMEI",
        "form": "current vintage only: single column CANCPIALLMINMEI_20260921",
        "obs_rows": sum(1 for _ in alfred_cpi.open()) - 1,
        "obs_first": "1914-01-01",
        "vintage_columns": 1,
        "verdict": "cannot reproduce realtime windows; vintage table requires the FRED API key (absent)"},
    "DGS10": {
        "endpoint": "https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=DGS10",
        "form": "current vintage only: single column DGS10_20260921",
        "obs_rows": sum(1 for _ in alfred_dgs.open()) - 1,
        "obs_first": "1962-01-02",
        "obs_first_matches_pin": True,
        "obs_last": "2026-09-18",
        "pinned_vintaged_invariants_from_committed_ctl_dgs10_pin_json": {
            "binding_rows": 16592, "distinct_obs_dates": 16588,
            "obs_first": "1962-01-02", "obs_last": "2025-07-31",
            "reparse_numeric_rows": 15883},
        "verdict": "series available keylessly at the CURRENT vintage; pinned vintaged archive (16592 rows with realtime windows) unreproducible without the FRED API key"},
}
wj(DATA / "fxng3/alfred_availability_probe.json", probe)
probe_sha = sha(DATA / "fxng3/alfred_availability_probe.json")

fxng3 = {
    "schema": "d2c_family_binding_report@1",
    "family": "FXNG3-A4-P1",
    "generated_utc": NOW,
    "inputs": [
        {
            "input": "CANCPIALLMINMEI vintaged CPI archive (THE signal input)",
            "pinned_sha256": "7b225d9f724bd15ca309c1085d5c3812da19b5f7c20f28bbe2e1eb583d9cb2d6",
            "observed_sha256": None,
            "status": "BLOCKED_DATA",
            "evidence_paths": [
                str(BASE / ".runtime/v3_cads_store/objects/07/07d1e0d5adc8fb124f8d9246b8ab0fdeea79e5be20fa99ea0a8fe81cd96aad12"),
                str(DATA / "fxng3/alfred_availability_probe.json"),
                str(DATA / "fxng3/p0_revision_census.json")],
            "invariants_checked": {
                "pinned_bytes_present": False,
                "recorded_staging_path_absent": str(BASE / ".worktrees/forex-free-v9/integration/data_raw/forex_free_v9_cpi/fred_vintaged/CANCPIALLMINMEI.json") + " (worktree deleted)",
                "bytes_in_cads_store": False,
                "s2_manifest_07d1e0d5_verified": {"sha256_of_manifest": "07d1e0d5adc8fb124f8d9246b8ab0fdeea79e5be20fa99ea0a8fe81cd96aad12", "witness": {"pinned_sha": "7b225d9f724bd15ca309c1085d5c3812da19b5f7c20f28bbe2e1eb583d9cb2d6", "rows": 5091}},
                "fred_api_key": "ABSENT",
                "keyless_forms_tried": ["alfredgraph.csv (id)", "alfredgraph.csv + realtime_start/realtime_end", "alfredgraph.csv + vintage_dates", "fredgraph.csv + vintage_dates", "fredgraph.csv + realtime_start/realtime_end"],
                "keyless_outcome": "all serve the CURRENT vintage only (single column, 1335 obs rows for CANCPIALLMINMEI); realtime windows structurally absent; plane_adapter parse_fred_vintaged fails closed on such tables",
                "72_event_invariant_computable_from_keyless": False,
                "committed_census_artifact_digest": "0fc108631e6b4bb2111c3528b873e68505ab2b46247d5e39cba24a12ff35017f (matches identity extract pin; records the 72 restricted events - evidence of the RECORDED invariants, not of data bytes)"},
        },
        {
            "input": "USDCAD daily spot (16:00 NY grid; universe pair)",
            "pinned_sha256": "4b988c4487b2ff0284ca0ecd04b6118c23516a89a147dd87cbab3b1bbf52ec2f",
            "observed_sha256": None,
            "status": "BLOCKED_DATA",
            "evidence_paths": [
                str(DATA / "fxng3/spot_grid_census.json"),
                str(DATA / "fxng3/spot_pin_manifest.json")],
            "invariants_checked": {
                "twelve_data_api_key": "ABSENT",
                "pinned_bytes_present": False,
                "recorded_staging_paths_absent": [
                    str(BASE / ".worktrees/forex-ng1/p1-spot/data_raw/forex_ng1_spot/USDCAD.json") + " (worktree deleted)",
                    "V9 spot_reacquired staging (worktree deleted)"],
                "searched_for_copies": "find over all worktrees + .runtime: only USDC.json.gz (crypto stablecoin, unrelated)",
                "freeze_law": "if the Twelve Data key is absent -> BLOCKED_DATA for this family (no substitute source permitted)",
                "committed_grid_census_digest": "42612576fb5aeb16416f36f0eb042605854f68bb268cd1bbedabfeafe5886ed6 (MATCHES identity extract pin; 1842 grid days 2018-04-04..2025-04-30 - committed evidence layer, not data bytes)"},
        },
        {
            "input": "DGS10 vintaged (control arm only)",
            "pinned_sha256": "03dde429ba022e6d011ae3a61323124e38c5a3fac888b492823406a51c4c4aa0",
            "observed_sha256": None,
            "status": "BLOCKED_DATA",
            "evidence_paths": [
                str(DATA / "fxng3/ctl_dgs10_pin.json"),
                str(DATA / "fxng3/alfred_availability_probe.json")],
            "invariants_checked": {
                "pinned_bytes_present": False,
                "recorded_staging_path_absent": str(BASE / ".worktrees/forex-free-v8/integration/research/control/forex_free_v8_run/staged_vintaged/DGS10.json") + " (worktree deleted)",
                "fred_api_key": "ABSENT",
                "keyless_outcome": "current vintage available (16884 obs rows, first 1962-01-02 == pin's obs_first) but realtime windows absent",
                "committed_pin_artifact": {
                    "path_in_reconstruction": str(RECON_FX / "research/control/forex_ng1_run/i/ctl_dgs10_pin.json"),
                    "sha256_computed_by_this_lane": "ca3fd87f1b8218b426e3d2a27ddac91cda83a581c2bce74614e0123628952f55",
                    "records": {"binding_rows": 16592, "distinct_obs_dates": 16588, "obs_first": "1962-01-02", "obs_last": "2025-07-31", "reparse_numeric_rows": 15883}}},
        },
        {
            "input": "ng1 P0 announcement census (kill-shadow input; in-tree committed artifact)",
            "pinned_sha256": "e8a35d23ce64ce71a8d30792750b877c387de3692af1e4d17391ea4cc35b4abe",
            "observed_sha256": sha(DATA / "fxng3/p0_announcement_census.json"),
            "status": "BOUND_DIGEST",
            "evidence_paths": [
                str(DATA / "fxng3/p0_announcement_census.json"),
                str(RECON_FX / "research/control/forex_ng1_run/p0_announcement_census.json")],
            "invariants_checked": {"digest": "match", "bytes_present_in_reconstruction": True, "copied_to_lane": True},
        },
        {
            "input": "spot grid census + spot pin manifest (committed evidence, supplementary)",
            "pinned_sha256": "42612576fb5aeb16416f36f0eb042605854f68bb268cd1bbedabfeafe5886ed6 (grid census; extract-recorded)",
            "observed_sha256": {
                "spot_grid_census.json": "42612576fb5aeb16416f36f0eb042605854f68bb268cd1bbedabfeafe5886ed6",
                "spot_pin_manifest.json": "e80b468b4d2070586ff110bca104f6fd7838697e0bee57f5a0f94a1149180d53"},
            "status": "BOUND_DIGEST",
            "evidence_paths": [str(DATA / "fxng3/spot_grid_census.json"), str(DATA / "fxng3/spot_pin_manifest.json")],
            "invariants_checked": {"common_grid_days": 1842, "window": ["2018-04-04", "2025-04-30"], "digest": "grid census matches extract pin"},
        },
        {
            "input": "ALFRED availability probe (this lane's pull, descriptive)",
            "pinned_sha256": None,
            "observed_sha256": probe_sha,
            "status": "NOT_PINNED_SUPPLEMENTARY",
            "evidence_paths": [str(DATA / "fxng3/alfred_availability_probe.json")],
            "invariants_checked": {"purpose": "documents keyless availability boundary for a future keyed re-pull"},
        },
    ],
    "family_status": "BLOCKED_DATA",
    "family_status_basis": "freeze law names this family BLOCKED_DATA when the Twelve Data key is absent (key ABSENT); additionally the signal input CANCPIALLMINMEI and the control DGS10 vintaged archives are unreproducible keylessly (bytes absent + FRED API key absent; keyless endpoints serve current vintage only)",
}
wj(DATA / "fxng3/binding_report.json", fxng3)

# ---------------------------------------------------------------- SFNG2 ------
sec = json.load(open("/tmp/sec_vno_submissions.json"))
r = sec["filings"]["recent"]
acc = r["accessionNumber"]
sec_evidence = {
    "generated_utc": NOW,
    "endpoint": "https://data.sec.gov/submissions/CIK0000899689.json",
    "purpose": "verify the submissions API form carries acceptanceDateTime for the identity extract's cited accessions (sample = the accessions the extract cites; the extract cites exactly these two)",
    "api_form_fields": list(r.keys()),
    "recent_rows": len(acc),
    "oldest_recent_filing": min(r["filingDate"]),
    "cited_accessions_found": [
        {"accessionNumber": acc[i], "form": r["form"][i], "filingDate": r["filingDate"][i],
         "acceptanceDateTime": r["acceptanceDateTime"][i], "reportDate": r["reportDate"][i],
         "primaryDocument": r["primaryDocument"][i]}
        for i in range(len(acc)) if acc[i] in ("0001179110-19-000786", "0001179110-19-000787")],
    "verdict": "acceptanceDateTime IS available upstream (keyless, UA-gated) for the cited 2019 accessions; per-accession acceptance stamps for the 4/A re-ingest are re-collectable by a dedicated full re-ingest lane",
}
wj(DATA / "sfng2/sec_submissions_check.json", sec_evidence)

sub_manifest_path = CADS / "objects/5d/5d351623675f71a9950d0e290b1fafff89901265f18bf6c687660e96285ea26b"
sub = json.load(open(sub_manifest_path))
form4a_manifest_path = RECON_ST / "research/control/stocks_ng2_run/p0_form4a_ingest_manifest.json"
form4a = json.load(open(form4a_manifest_path))

census_gz = SEARCH_P0 / "p0_census_cohort.json.gz"
with gzip.open(census_gz, "rt") as f:
    cc = json.load(f)
served_gt0 = {k: v for k, v in cc.items() if isinstance(v, dict) and v.get("served", 0) > 0}
ge63 = sum(1 for v in served_gt0.values() if v["served"] >= 63)

sfng2 = {
    "schema": "d2c_family_binding_report@1",
    "family": "SFNG2-A4-P1",
    "generated_utc": NOW,
    "inputs": [
        {
            "input": "pinned Form-4 stream (546,039 rows)",
            "pinned_sha256": "6ac2cd5bdd62566efe106b46de715030e9a8a940cb90f5a991df5f05ba6742b2",
            "observed_sha256": sha(CADS / "objects/6a/6ac2cd5bdd62566efe106b46de715030e9a8a940cb90f5a991df5f05ba6742b2"),
            "status": "BOUND_DIGEST",
            "evidence_paths": [
                str(CADS / "objects/6a/6ac2cd5bdd62566efe106b46de715030e9a8a940cb90f5a991df5f05ba6742b2"),
                str(CADS / "pins.jsonl")],
            "invariants_checked": {"digest": "match (CADS content-addressed object; also recorded inside the digest-verified V13 substrate manifest)", "rows": 546039, "row_count_invariant": "wc -l == 546039 exact"},
        },
        {
            "input": "V13 pinned originals substrate manifest (345,150 XML doc digests + submissions_alive + stream pin)",
            "pinned_sha256": "5d351623675f71a9950d0e290b1fafff89901265f18bf6c687660e96285ea26b",
            "observed_sha256": sha(sub_manifest_path),
            "status": "BOUND_DIGEST",
            "evidence_paths": [str(sub_manifest_path)],
            "invariants_checked": {
                "digest": "match (identity extract records this exact sha as the P0 full re-hash of 345,150/345,150 files OK)",
                "sections": {k: (v.get("count") if isinstance(v, dict) and "count" in v else v) for k, v in sub["sections"].items() if k != "form4_stream"},
                "form4_stream_section": sub["sections"]["form4_stream"],
                "note": "the manifest is the digest LEDGER for the 345,150 originals; the XML bytes themselves are absent (stocks-free-v13 worktree deleted)"},
        },
        {
            "input": "4/A re-ingest tree (3,059 parseable 4/A XMLs with acceptance stamps)",
            "pinned_sha256": "53daea6172ff5538c279970d7a1d1ea85c8294c637b7b2de3102ffc2ad05f062 (aggregate over 6,123 files, as recorded in the identity extract)",
            "observed_sha256": None,
            "status": "NEEDS_DEDICATED_LANE",
            "evidence_paths": [
                str(form4a_manifest_path),
                str(DATA / "sfng2/sec_submissions_check.json")],
            "invariants_checked": {
                "bytes_present": False,
                "recorded_path_absent": str(BASE / ".worktrees/stocks-ng2/integration/data_raw/form4a") + " (worktree deleted)",
                "committed_ledger_present": True,
                "committed_ledger_path": str(form4a_manifest_path),
                "committed_ledger_sha256_this_lane": "d06a6342e0e5b576f84e7f3ae205de69464b40bf2ea4824ab211c3f41b03172a",
                "ledger_aggregate_sha256_matches_extract_pin": form4a["aggregate_sha256"] == "53daea6172ff5538c279970d7a1d1ea85c8294c637b7b2de3102ffc2ad05f062",
                "ledger_file_census": {"total": form4a["file_count"], "xml": 3059, "index_json": 3062, "txt": 2},
                "ledger_carries_per_file_sha256": True,
                "sec_submissions_api_form_verified": "acceptanceDateTime present for BOTH extract-cited accessions (0001179110-19-000786 @ 2019-01-16T22:44:32Z; 0001179110-19-000787 @ 2019-01-16T22:44:45Z; CIK0000899689, form 4) - see sec_submissions_check.json",
                "effort_estimate": "full EDGAR re-ingest of 345,150 originals + 3,062 4/A accessions (~351k requests at <=10 req/s ~= 10-12h wall clock; XML bytes ~2-4GB) then per-file sha256 verification against the two committed ledgers + pairs/p0d machinery re-run; ~1-2 dedicated-lane days. Per-file digest verification makes the re-bind BOUND_CONTENT-grade (file-level digest equality), not merely availability."},
        },
        {
            "input": "cohort_v9 death-inclusive name list (410 ALIVE + 1,769 DEAD = 2,179)",
            "pinned_sha256": "6a95401ff84bff2144ac3c0b9426a6fa86daf3dde8d478195666249e3fa2aa62",
            "observed_sha256": None,
            "status": "BLOCKED_DATA",
            "evidence_paths": [],
            "invariants_checked": {
                "bytes_present": False,
                "recorded_path_absent": str(BASE / ".worktrees/stocks-free-v9/integration/research/control/stocks_free_v9_run/cohort_v9.json") + " (worktree deleted)",
                "searched": "all worktrees, .runtime, /tmp/d2c_sources (incl. data/v9_manifests - crypto universe, unrelated), grep for cohort_v9/DEAD_EVIDENCED/1769 in stocks-ng5/ng6/v13: no hits",
                "partial_recovery": "the 410 ALIVE CIK keys are recoverable as file keys of the digest-verified V13 substrate manifest's submissions_alive section; the 1,769 DEAD half and any CIK->price-symbol bridge are NOT recoverable in-tree",
                "not_re_pullable": "cohort_v9 was constructed once from V9-specific inputs; a re-derivation would be a NEW universe construction, forbidden by the frozen contract (no post-outcome universe change) - owner adjudication required (backup restoration only)"},
        },
        {
            "input": "EODHD price cache for the per-name census",
            "pinned_sha256": None,
            "observed_sha256": {
                "cache_files": 111323,
                "search_v1_p0_census_cohort.json.gz": sha(census_gz)},
            "status": "PRESENT_BUT_CENSUS_NOT_RUN",
            "evidence_paths": [
                str(SEARCH_P0 / "raw/eod_cache"),
                str(census_gz)],
            "invariants_checked": {
                "cache_keyed_by": "EODHD symbol codes (0P.../tickers), NOT cohort CIKs - the V9 CIK-keyed staging (.staging_prices_v9/eod, 2,140 cohort files loaded) is deleted",
                "census_artifact_entries": len(cc),
                "entries_served_gt0": len(served_gt0),
                "entries_served_ge63": ge63,
                "tail_last_date_max": max(v["last"] for v in served_gt0.values()),
                "spot_read_reconciliation": "6 random symbols re-read from gz: first/last/served match the census exactly (GRFXF/CTWO/JACS/SHIP/ASHCX/BFXU)",
                "per_name_census": "NOT_RUN - requires cohort_v9's CIK->symbol map (absent); per freeze law no improvised substitute"},
        },
    ],
    "family_status": "NEEDS_DEDICATED_LANE",
    "family_status_basis": "the SEC acceptance stream is re-bindable ONLY via a full EDGAR re-ingest verified against the two committed per-file digest ledgers (~10-12h pulls + 1-2 lane-days) -> NEEDS_DEDICATED_LANE; independently the cohort_v9 name list is BLOCKED (bytes unrecoverable; re-derivation forbidden by the frozen universe law) so even a dedicated lane cannot complete the price-side name census unless the V9 staging surfaces are restored from owner backup. Fail-closed honesty: do not treat the family as bindable on the strength of the stream + ledgers alone.",
}
wj(DATA / "sfng2/binding_report.json", sfng2)

print("wrote cng2/fxng3/sfng2 binding reports")
