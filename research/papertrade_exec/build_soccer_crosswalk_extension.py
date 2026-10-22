"""Build the exec-owned PROVIDER_NAME_CROSSWALK_EXTENSION.csv from REAL
The-Odds-API events snapshots (freeze-sanctioned growth: SOCCER-INTL-WINPROB-
PROSPECTIVE-PREP-V1 FREEZE_SKELETON §5 — "extend the 8-pair seed empirically
from real payloads; fail-closed until then").

Law of construction (fail-closed at every step):
  1. The extension file is the PINNED seed's bytes VERBATIM (header + the 8
     evidenced pairs) followed ONLY by appended rows — the frozen anchor is a
     strict byte prefix, so the seed can never be rewritten or shrunk.
  2. A row is appended ONLY for a provider team name observed in a REAL
     captured events snapshot (bytes + sha256 persisted under the cycle's
     data root) that the pinned seed cannot resolve AND whose corpus spelling
     exists in the pinned results.csv team set. Never speculative; never
     fuzzy; one row per (provider_name, corpus_name).
  3. Evidence columns record the snapshot sha256 (first 12 hex), the event
     id(s) the name was observed on, and the corpus membership count.

Usage: python -m research.papertrade_exec.build_soccer_crosswalk_extension
Runs offline against the already-captured snapshots; prints the new sha256
for the pins.json data entry. The file itself is committed; re-pinning is a
deliberate, disclosed act (ERRATUM + registry phase).
"""
from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parent
SEED_PATH = Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
                 "soccer-intl-winprob-prospective-prep-v1/integration/"
                 "research/papertrade_soccer/PROVIDER_NAME_CROSSWALK_SEED.csv")
EXT_PATH = PKG_DIR / "PROVIDER_NAME_CROSSWALK_EXTENSION.csv"
CORPUS_CSV = Path("~/.my-quantitative-data/soccer-intl-winprob-prospective-"
                  "prep-v1/corpus/results.csv").expanduser()
DATA_DIR = Path("~/.my-quantitative-data/sports-papertrade-exec-v1/data")\
    .expanduser()
SEED_PAIRS = 8


def sha256(b: bytes) -> str:
    import hashlib
    return hashlib.sha256(b).hexdigest()


def corpus_teams() -> dict[str, int]:
    counts: dict[str, int] = {}
    with open(CORPUS_CSV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            counts[r["home_team"]] = counts.get(r["home_team"], 0) + 1
            counts[r["away_team"]] = counts.get(r["away_team"], 0) + 1
    return counts


def seed_provider_names() -> set[str]:
    rows = list(csv.reader(io.StringIO(SEED_PATH.read_text(encoding="utf-8"))))
    assert rows[0][:2] == ["provider_name", "corpus_name"], rows[0]
    pairs = {r[0] for r in rows[1:] if r}
    assert len(pairs) >= SEED_PAIRS, pairs
    return pairs


def observed_provider_teams() -> dict[str, list[str]]:
    """provider team name -> event ids, from every captured events snapshot."""
    out: dict[str, list[str]] = {}
    for snap in sorted(DATA_DIR.glob("events_*.json")):
        if snap.name.endswith(".meta.json"):
            continue
        meta_p = snap.with_name(snap.name.replace(".json", ".meta.json"))
        if not meta_p.exists():
            raise SystemExit(f"snapshot without meta record: {snap}")
        meta = json.loads(meta_p.read_text())
        body = snap.read_bytes()
        if meta.get("sha256") != sha256(body):
            raise SystemExit(f"snapshot bytes != meta sha: {snap}")
        for ev in json.loads(body):
            for side in ("home_team", "away_team"):
                out.setdefault(ev[side], []).append(
                    f"{ev['id']}({meta['sha256'][:12]})")
    return out


def main() -> int:
    seed_bytes = SEED_PATH.read_bytes()
    teams, corpus = observed_provider_teams(), corpus_teams()
    existing = seed_provider_names()
    if not EXT_PATH.exists():
        EXT_PATH.write_bytes(seed_bytes)   # anchor first: the seed is the
    else:                                  # strict byte prefix, then growth
        cur = EXT_PATH.read_bytes()
        if not cur.startswith(seed_bytes):
            raise SystemExit("existing extension does not extend the seed "
                             "verbatim; refusing")
    # parse any rows already appended by previous builds (idempotent growth)
    ext_rows: list[tuple[str, str, str, str, str]] = []
    for r in csv.reader(io.StringIO(
            EXT_PATH.read_bytes()[len(seed_bytes):].decode("utf-8"))):
        if r:
            ext_rows.append((r[0], r[1], r[2], r[3], r[4]))
    mapped = existing | {r[0] for r in ext_rows}
    appended = []
    for name in sorted(teams):
        if name in mapped:
            continue
        if name not in corpus:
            print(f"SKIP (not a corpus team; stays CROSSWALK_MISS): {name!r}")
            continue
        evs = ";".join(sorted(set(teams[name]))[:3])
        appended.append((name, name,
                         f"corpus results.csv {corpus[name]} rows; identity "
                         "pair (provider spelling == corpus spelling)",
                         f"YES — observed on events {evs}",
                         "EXTENDED_FROM_REAL_PAYLOAD"))
    if appended:
        with open(EXT_PATH, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            for row in appended:
                w.writerow(row)
                ext_rows.append(row)
    total = len(existing) + len(ext_rows)
    print(f"extension rows total (incl. seed 8): {total}")
    print(f"extension sha256: {sha256(EXT_PATH.read_bytes())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
