"""Build the exec-owned TEAM NAME CROSSWALK from REAL journaled payloads.

W0.1 of PAPERDESK-FIXALL-NCAA-V1 (owner work package 2026-10-21): the settle
path compared ESPN abbreviations (DET/BOS/SA/OKC) against full ledger names
with a bare `!=` — every NBA bet stuck OPEN forever. This builder produces
ONE pinned crosswalk file (provider abbreviation + provider display name ->
canonical team id) with per-row evidence, so identity resolution has a single
measured source. Values are MEASURED from the pinned/journaled corpora:

  * NBA (30 teams) + observed WNBA teams: real ESPN scoreboard payloads —
    the exec settle-evidence captures under
    ~/.my-quantitative-data/sports-papertrade-exec-v1/ops/results/evidence/
    and the frozen nba26 corpus
    ~/.my-quantitative-data/nba-winprob-prospective-prep-v1/espn_schedule_2026_27/
  * remaining WNBA teams: the PINNED 2026 schedule CSV
    (~/.my-quantitative-data/wnba-2026-remainder-v1/refresh_20261007/
    wnba_schedule_2026.csv, sha 0ed97faf…) — home/away_abbreviation ->
    *_display_name, the exact bytes the fixture loader reads.

All-star exhibition squads (TEAM COOP / TEAM SPOON) are excluded by the
existing exhibition law. Output is sorted, deterministic, and re-pinned in
pins.json (data.team_name_crosswalk_csv) by the operator running this script.
"""
from __future__ import annotations

import collections
import csv
import hashlib
import json
from pathlib import Path

EVIDENCE_GLOBS = [
    ("espn_settle_evidence", "/Users/hoangminhlong/.my-quantitative-data/"
     "sports-papertrade-exec-v1/ops/results/evidence/espn_*.json"),
    ("nba26_frozen_corpus", "/Users/hoangminhlong/.my-quantitative-data/"
     "nba-winprob-prospective-prep-v1/espn_schedule_2026_27/"
     "scoreboard_*.json"),
]
WNBA_SCHEDULE_CSV = Path(
    "/Users/hoangminhlong/.my-quantitative-data/wnba-2026-remainder-v1/"
    "refresh_20261007/wnba_schedule_2026.csv")
OUT = Path(__file__).resolve().parent / "TEAM_NAME_CROSSWALK.csv"

LEAGUE_OF_PATH = {"espn_nba": "NBA", "espn_wnba": "WNBA"}


def _payload_pairs() -> dict:
    """(league, abbr) -> {display_name: [evidence,…]} from real payloads."""
    out: dict = collections.defaultdict(list)
    for label, pattern in EVIDENCE_GLOBS:
        for fp in sorted(Path("/").glob(pattern.lstrip("/"))):
            name = fp.name
            if label == "nba26_frozen_corpus":
                league = "NBA"        # pinned nba26 ESPN scoreboard corpus
            else:
                league = None
                for prefix, lg in LEAGUE_OF_PATH.items():
                    if name.startswith(prefix):
                        league = lg
                        break
            try:
                d = json.loads(fp.read_text())
            except Exception:
                continue
            for e in d.get("events", []):
                comps = (e.get("competitions") or [{}])
                for c in comps[0].get("competitors", []):
                    t = c.get("team", {})
                    ab, dn = t.get("abbreviation"), t.get("displayName")
                    if league and ab and dn and ab != "TBD":
                        rec = f"{label}:{name}"
                        if rec not in out[(league, ab, dn)]:
                            out[(league, ab, dn)].append(rec)
    return out


def _wnba_schedule_pairs() -> dict:
    out: dict = collections.defaultdict(list)
    with open(WNBA_SCHEDULE_CSV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("season") != "2026":
                continue
            if r.get("type_abbreviation") == "ALLSTAR":
                continue
            for side in ("home", "away"):
                ab = r.get(f"{side}_abbreviation")
                dn = r.get(f"{side}_display_name")
                if ab and dn and ab != "TBD":
                    rec = f"wnba_schedule_2026.csv#{r.get('id')}"
                    if rec not in out[("WNBA", ab, dn)]:
                        out[("WNBA", ab, dn)].append(rec)
    return out


def build() -> tuple[str, int]:
    rows: dict = {}
    for (league, ab, dn), ev in sorted(_payload_pairs().items()):
        rows.setdefault((league, ab), {"name": dn, "evidence": ev,
                                       "source": "espn_payload"})
    for (league, ab, dn), ev in sorted(_wnba_schedule_pairs().items()):
        key = (league, ab)
        if key in rows:
            for rec in ev:
                if rec not in rows[key]["evidence"]:
                    rows[key]["evidence"].append(rec)
        else:
            rows[key] = {"name": dn, "evidence": ev,
                         "source": "wnba_schedule_pinned_csv"}
    lines = ["league,provider_abbr,canonical_name,evidence_source,evidence"]
    for (league, ab), meta in sorted(rows.items()):
        if meta["name"].upper().startswith("TEAM "):
            continue                      # all-star exhibition squads
        ev = "; ".join(meta["evidence"][:3])
        lines.append(f'{league},{ab},"{meta["name"]}",{meta["source"]},'
                     f'"{ev}"')
    # Deliberate alias: ESPN legacy abbreviation for the Connecticut Sun
    # (the exec WNBA_FULL_NAMES table and older payloads spell CONN while the
    # pinned 2026 schedule spells CON). An alias is an evidence-cited extra
    # row — never a runtime guess.
    lines.append('WNBA,CONN,"Connecticut Sun",exec_alias,'
                 '"legacy ESPN abbreviation; mirrors exec WNBA_FULL_NAMES"')
    body = "\n".join(lines) + "\n"
    OUT.write_text(body, encoding="utf-8")
    sha = hashlib.sha256(body.encode()).hexdigest()
    return sha, len(lines) - 1


if __name__ == "__main__":
    sha, n = build()
    print(json.dumps({"path": str(OUT), "rows": n,
                      "sha256": sha}, indent=1))
    print("ACTION: re-pin pins.json data.team_name_crosswalk_csv.sha256 "
          "with the measured digest above.")
