"""V6-P0b (A3): assembles the five P0b control artifacts from staged evidence.

Inputs (gitignored staging, hash-pinned):
  .staging_prices_v6/terms/            — fetched terms documents + curl evidence
  .staging_prices_v6/raw/              — probe documents (reader-channel renders)
  .staging_prices_v6/summaries/        — pinned PIT-store scan summaries

Outputs (committed):
  research/control/stocks_free_v6_run/p0b_price_authority.json
  research/control/stocks_free_v6_run/p0b_license_evidence.json
  research/control/stocks_free_v6_run/p0b_availability_evidence.json
  research/control/stocks_free_v6_run/p0b_sample_probe_report.json
  research/control/stocks_free_v6_run/p0b_bulk_download_plan.json

The writer is evidence-driven: verbatim quotes and hashes below are pinned
to the archived bytes; probe numbers come from the executed runner output.
Authorization statuses follow handbook §11.4; the coverage-census gate is
NOT_RUN in the light phase, so AUTHORIZED_INTERNAL_RESEARCH is deliberately
NOT recorded for any candidate.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


TERMS_DIR = Path(".staging_prices_v6/terms")
RAW_DIR = Path(".staging_prices_v6/raw")
SUMMARY_DIR = Path(".staging_prices_v6/summaries")
CONTROL_DIR = Path("research/control/stocks_free_v6_run")


def build_license_evidence() -> dict:
    docs = []
    spec = [
        ("stooq_homepage.html", "https://stooq.com/", "curl (plain HTTP)"),
        ("stooq_aapl.us_d.csv", "https://stooq.com/q/d/l/?s=aapl.us&i=d", "curl (plain HTTP)"),
        ("stooqpl_aapl_probe.csv", "https://stooq.pl/q/d/l/?s=aapl.us&i=d", "curl (plain HTTP)"),
        ("stooqpl_regulamin_probe.html", "https://stooq.pl/regulamin/", "curl (plain HTTP)"),
        ("stooqpl_homepage.html", "https://stooq.pl/", "curl (plain HTTP)"),
        ("stooqcom_regulamin_curl.html", "https://stooq.com/regulamin/", "curl (plain HTTP)"),
        ("massive_homepage.html", "https://massive.com/", "curl (plain HTTP)"),
        ("massive_pricing.html", "https://massive.com/pricing", "curl (plain HTTP)"),
        ("massive_terms.html", "https://massive.com/legal/terms", "curl (plain HTTP)"),
        ("massive_individuals_terms.html", "https://massive.com/legal/individuals-terms-of-service", "curl (plain HTTP)"),
        ("massive_businesses_terms.html", "https://massive.com/legal/businesses-terms-of-service", "curl (plain HTTP)"),
    ]
    for fname, url, channel in spec:
        p = TERMS_DIR / fname
        if not p.exists():
            continue
        docs.append(
            {
                "document": fname,
                "url": url,
                "channel": channel,
                "retrieved_time_utc": datetime.fromtimestamp(
                    p.stat().st_mtime, tz=timezone.utc
                ).isoformat(),
                "size_bytes": p.stat().st_size,
                "sha256": sha256_file(p),
            }
        )
    return {
        "schema": "stocks_free_v6_run/p0b_license_evidence@1",
        "generated_at_utc": now_utc(),
        "producer_role": "A3 (lane p0-a3-prices)",
        "retrieved_documents": docs,
        "stooq": {
            "candidate": "Stooq daily OHLCV (https://stooq.com, keyless)",
            "terms_url": "https://stooq.com/regulamin/",
            "terms_language": "Polish",
            "channel_note": (
                "plain-HTTP clients receive a JavaScript proof-of-work "
                "browser-verification challenge on both stooq.com and stooq.pl "
                "(archived challenge bytes pinned above); the terms page is NOT "
                "archived on the Wayback Machine (CDX query returned empty); the "
                "terms text was therefore read through a browser-equivalent "
                "rendering channel whose tool output to the agent is truncated "
                "at ~4000 of 5726 characters — verbatim quotes below are "
                "captured from that render and character-exact fidelity is NOT "
                "guaranteed; no challenge was solved, no gate was bypassed, no "
                "account or acceptance was performed"
            ),
            "quotes": [
                {
                    "quote_pl": "Korzystanie z serwisu oznacza akceptację regulaminu",
                    "translation": "Using the service constitutes acceptance of the terms",
                    "section": "§2 Zasady korzystania",
                    "classification": "BROWSE-WRAP ACCEPTANCE (no click-through; use = acceptance)",
                },
                {
                    "quote_pl": "Zabronione jest kopiowanie, powielanie lub w inny sposób wykorzystywanie danych serwisu w celach komercyjnych bez zgody autora",
                    "translation": "Copying, duplication or other use of the service's data for commercial purposes without the author's consent is prohibited",
                    "section": "§2 Zasady korzystania",
                    "classification": "COMMERCIAL USE: requires author consent",
                },
                {
                    "quote_pl": "Dane publikowane w serwisie mają charakter informacyjny i nie stanowią rekomendacji inwestycyjnej",
                    "translation": "Data published by the service is informational and does not constitute investment advice",
                    "section": "§2 Zasady korzystania",
                    "classification": "DISCLAIMER",
                },
                {
                    "quote_pl": "Administratorem danych osobowych jest Waldemar Bojarowski, właściciel marki Stooq, z siedzibą w Sopocie (Poland)",
                    "translation": "The personal-data controller is Waldemar Bojarowski, owner of the Stooq brand, based in Sopot, Poland",
                    "section": "§1 Postanowienia ogólne",
                    "classification": "CONTROLLER IDENTIFICATION",
                },
            ],
            "restriction_classification": {
                "internal_research_storage_of_free_daily_ohlcv": (
                    "NOT_EXPLICITLY_ADDRESSED_IN_RETRIEVED_FRAGMENTS — the "
                    "retrieved terms prohibit commercial use without consent "
                    "and impose acceptance-by-use, but no clause specifically "
                    "granting or forbidding non-commercial internal research "
                    "storage was retrievable in the captured ~4000/5726 chars; "
                    "owner authorization is required before any bulk storage"
                ),
                "redistribution": "PROHIBITED_BY_COMMERCIAL_CLAUSE_INTERPRETATION — no explicit grant; treat as forbidden without owner decision",
                "commercial_use": "REQUIRES_AUTHOR_CONSENT (verbatim quote above)",
                "account_or_signup_required": "NO for browsing and the documented CSV endpoint (keyless); VERIFIED only as far as the light-phase probes reach",
                "click_through_acceptance_required": "NO click-through; browse-wrap acceptance-by-use applies once data is used",
            },
        },
        "massive": {
            "candidate": "Massive (massive.com, formerly Polygon.io) — Basic plan, cross-check only",
            "terms_urls": [
                "https://massive.com/legal/terms",
                "https://massive.com/legal/individuals-terms-of-service",
                "https://massive.com/legal/businesses-terms-of-service",
                "https://massive.com/pricing",
            ],
            "quotes": [
                {
                    "quote": "accept these Terms as part of the account sign-up process for the Services labeled for individual or personal use and will remain in effect until terminated as specified herein. If you do not agree with the Agreement, please do not accept these Terms, and you may not access or use the Services.",
                    "source": "Massive for Individuals Terms of Service",
                    "classification": "SIGNUP + TERMS ACCEPTANCE REQUIRED",
                },
                {
                    "quote": "You must open an account with us to use the Services.",
                    "source": "Individuals Terms §3.1 Account Registration",
                    "classification": "ACCOUNT REQUIRED",
                },
                {
                    "quote": "\"APIs\" and other products and services designated for personal, individual, non-business, or non-commercial use (collectively, the \"Services\"). If you are using the Services for business or commercial purposes, you may not use any of the Services labeled for individual or personal use.",
                    "source": "Individuals Terms preamble",
                    "classification": "BASIC/INDIVIDUAL TIER IS NON-BUSINESS ONLY",
                },
                {
                    "quote": "Stocks Basic Great for trying our APIs $0 /month Sign up All US Stocks Tickers 5 API Calls / Minute 2 Years Historical Data 100% Market Coverage End of Day Data",
                    "source": "massive.com/pricing (captured static HTML)",
                    "classification": "PLAN SPEC: Basic = $0, 2-year depth, SIGN-UP GATED, 5 calls/min",
                },
                {
                    "quote": "use, redistribute, reverse assemble, reverse compile, copy, modify, display, disseminate, sublicense, sell, publish, reproduce, resell, transfer, or otherwise make available any portion of the Information to anyone other than Customer, its Authorized Users, or its E...",
                    "source": "Businesses Terms (use restrictions)",
                    "classification": "REDISTRIBUTION PROHIBITED (business terms)",
                },
                {
                    "quote": "limited right to access, receive, process, transmit, store, and use the Information available via the Services solely for its use in websites or software applications owned or licensed by Customer",
                    "source": "Businesses Terms §2.2 Information Access Grant",
                    "classification": "INTERNAL STORAGE PERMITTED ONLY UNDER BUSINESS TERMS (paid, account-gated)",
                },
            ],
            "restriction_classification": {
                "account_or_signup_required": "YES — hard gate; forbidden for agents without an owner data-authority decision (PLAN_stocks_v6 §15)",
                "internal_research_storage": "only under Businesses Terms (paid tier); Individuals/Basic tier is personal, non-business use only",
                "commercial_use": "Basic tier: NO; business use requires paid Business terms",
                "redistribution": "prohibited under both terms documents",
            },
        },
    }


def build_price_authority(availability: dict, probes_ok: bool) -> dict:
    return {
        "schema": "stocks_free_v6_run/p0b_price_authority@1",
        "generated_at_utc": now_utc(),
        "producer_role": "A3 (lane p0-a3-prices)",
        "s0_window": {"start": "2018-04-04", "end": "2025-07-24"},
        "binding_lesson": "B2_PRICE_FAIL_CLOSED (lessons_register.json): Stooq is a CANDIDATE, not a default",
        "candidates": {
            "stooq_daily_ohlcv": {
                "role": "PRIMARY candidate",
                "disposition": "UNAVAILABLE_FAIL_CLOSED",
                "disposition_scope": (
                    "scope-qualified: scripted, hash-pinnable retrieval is "
                    "UNAVAILABLE in this environment (bot gate + channel "
                    "fidelity failure); browser access itself works and the "
                    "source stays a documented candidate reopenable by owner "
                    "decision — the fail-closed disposition drives cycle "
                    "behavior until the owner re-opens the access channel"
                ),
                "gates": {
                    "license_entitlement_capture": "PASS_WITH_LIMITATIONS (terms text ~70% captured via rendering channel; gate evidence archived)",
                    "availability_evidence_table": availability["stooq_table_status"],
                    "corporate_action_cross_check_l7": (
                        "FAIL_CAUGHT (channel-integrity failure on TJX: rendered series "
                        "irreconcilable with the SEC 2:1 split fact and documented market "
                        "history; CMG 50:1 signature SEC-corroborated but fidelity-"
                        "unverifiable) — the L7 lesson operationalized: discovered in the "
                        "light phase, never at D2"
                    ),
                    "coverage_census_vs_s0": "NOT_RUN — bulk download explicitly deferred to the A1-scheduled heavy window; this gate CANNOT complete in the light phase",
                },
                "authorization_statement": (
                    "AUTHORIZED_INTERNAL_RESEARCH is deliberately NOT recorded. "
                    "With the coverage-census gate NOT_RUN, no candidate can "
                    "pass every gate in the light phase; final authorization "
                    "is deferred to the owner after the heavy phase "
                    "(run_contract.json phase_order, V6-P0b)."
                ),
                "blocking_findings": [
                    "stooq.com AND stooq.pl serve a JavaScript proof-of-work browser-verification challenge to plain-HTTP clients on ALL endpoints including the /q/d/l/ CSV endpoint (archived challenge bytes, sha256-pinned); scripted bulk retrieval is therefore NOT feasible via plain HTTP",
                    "the only channel that passes the gate (browser-equivalent renderer) delivers content to the agent through a summarization layer: TJX renders are irreconcilable with the SEC 2:1 split fact (2018-10..11, ratio=2, sha-pinned store facts) and with documented market history (no October 2018 selloff, December 2018 level wrong by ~2x, no split signature, mechanically regular volumes) — the channel cannot be certified for hash-pinned research bytes",
                    "the challenge was NOT solved and no gate bypassed (owner decision required for any scripted-access approach)",
                    "terms text captured ~4000/5726 chars through the rendering channel; character-exact fidelity not guaranteed; full-text review required before bulk authorization",
                    "acceptance-by-use (browse-wrap) + commercial-use-consent clause retrieved; internal non-commercial research storage not explicitly addressed in captured fragments",
                ],
            },
            "massive_basic": {
                "role": "CROSS_CHECK candidate only (2-year depth)",
                "disposition": "CANDIDATE_NOT_AUTHORIZED",
                "gates": {
                    "license_entitlement_capture": "PASS (full terms pages retrieved as raw bytes, sha256-pinned)",
                    "availability_evidence_table": "NOT_RUN — no data scope is reachable without signup",
                    "corporate_action_cross_check_l7": "NOT_RUN — unauthorized scope",
                    "coverage_census_vs_s0": "NOT_RUN — unauthorized scope",
                },
                "authorization_statement": (
                    "Every data path requires account signup + terms acceptance, "
                    "and the free Basic tier is expressly limited to personal, "
                    "individual, non-business, non-commercial use. Both the "
                    "signup and the acceptance are hard boundaries for agents "
                    "(PLAN_stocks_v6 §15; handbook §11.4). Cross-check scope is "
                    "recorded CANDIDATE_NOT_AUTHORIZED; see owner decision request."
                ),
            },
        },
        "frozen_conflict_policy_note": (
            "single-source default if only Stooq is ever authorized; any future "
            "mixing requires the frozen per-row provenance policy in "
            "p0b_bulk_download_plan.json (handbook §11.5)"
        ),
    }


def build_bulk_download_plan() -> dict:
    return {
        "schema": "stocks_free_v6_run/p0b_bulk_download_plan@1",
        "generated_at_utc": now_utc(),
        "status": "PLANNED_NOT_EXECUTED (light phase; A1 schedules the heavy window)",
        "census_scope": {
            "universe": "410-filer SEC panel (pinned PIT store, sha256 f53eb371...df955; CIK->ticker mapping archived at .staging_prices_v6/summaries/panel_cik_to_ticker.json)",
            "window": "S0 folds 2018-04-04..2025-07-24 (download full history per symbol; census measures the S0 intersection)",
            "endpoint": "https://stooq.com/q/d/l/?s=<symbol>.us&i=d (parameter semantics d1/d2=YYYYMMDD verified operationally in probes)",
            "politeness": ">=2s inter-request spacing, honest UA, no credentials; see access-channel blocker below",
        },
        "census_measures_per_symbol": [
            "first/last served date; served-history depth vs S0",
            "row count vs expected NYSE sessions inside S0 (USEquityRegularCalendar, frozen 2010-2030 table)",
            "missing session days (gaps) listed explicitly — never gap-patched",
            "duplicate dates, non-ascending delivery, OHLC interval violations (parser fails loud)",
            "last-date < 2025-07-24 => delisted/suspended survival flag (names keep history; never silently dropped — plan §2 leg 3)",
        ],
        "census_measures_panel_wide": [
            "panel coverage fraction per decision date (fraction of 410 with a served bar on/preceding the date)",
            "delisted-name survival count and histogram of last dates",
            "symbol-suffix taxonomy encountered (.us, .xus?, duplicates) and identity collisions",
            "revision/vintage behavior: re-download a fixed 10-symbol subset after >=24h and diff bytes; report added/changed rows (this is the ONLY provable revision test)",
        ],
        "expected_volume": {
            "symbols": 410,
            "requests": "410 (one full-history CSV per symbol) + 10 revision-check re-downloads",
            "bytes": "~0.5-1.5 MB per symbol full history => ~0.2-0.6 GB raw, gitignored, sha256-manifested",
            "duration": ">= 410 * 2s spacing ~= 14 min minimum; budget 1-2 h with retries",
        },
        "outputs": [
            ".staging_prices_v6/raw/<symbol>.csv + sha256_manifest.json (gitignored)",
            "research/control/stocks_free_v6_run/p0b_coverage_census.json (per-symbol + panel metrics)",
            "updated p0b_price_authority.json gate outcomes",
        ],
        "access_channel_blocker_for_owner": {
            "finding": "plain-HTTP clients receive a JS proof-of-work challenge on every stooq endpoint (both domains); browser-equivalent rendering works but is summary-lossy and cannot serve as a 410-symbol bulk channel",
            "options": [
                "A: authorize a scripted-access approach that satisfies stooq's browser check (owner decision; agent cannot invent consent)",
                "B: authorize an owner-provided compliant access path (e.g., direct licensed feed)",
                "C: accept BLOCKED_DATA_AUTHORITY close for the price leg (legitimate per plan §2)",
            ],
        },
        "frozen_conflict_policy": {
            "default": "single-source (Stooq) if it is the only authorized source",
            "if_a_second_source_is_authorized": {
                "per_row_provenance": "every row carries source_id + retrieved_time_utc + raw_sha256",
                "primary_role": "Stooq fills the series; the second source NEVER silently gap-patches (handbook §11.5)",
                "conflict_resolution": "on same-day value conflict: primary wins, conflict row written to a quarantine list published in the census; resolution is an owner-visible decision, never silent",
                "no_blending": "no averaged/interpolated prices from multiple sources, ever",
            },
        },
    }


def write_all(availability: dict, probes_ok: bool, probe_report: Optional[dict]) -> None:
    CONTROL_DIR.mkdir(parents=True, exist_ok=True)
    (CONTROL_DIR / "p0b_license_evidence.json").write_text(
        json.dumps(build_license_evidence(), indent=1), encoding="utf-8"
    )
    (CONTROL_DIR / "p0b_price_authority.json").write_text(
        json.dumps(build_price_authority(availability, probes_ok), indent=1),
        encoding="utf-8",
    )
    (CONTROL_DIR / "p0b_bulk_download_plan.json").write_text(
        json.dumps(build_bulk_download_plan(), indent=1), encoding="utf-8"
    )
    if probe_report is not None:
        (CONTROL_DIR / "p0b_sample_probe_report.json").write_text(
            json.dumps(probe_report, indent=1), encoding="utf-8"
        )


if __name__ == "__main__":
    raise SystemExit("invoke via p0b_assemble.py wrapper with probe results")
