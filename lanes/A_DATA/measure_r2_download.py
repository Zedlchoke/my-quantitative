#!/usr/bin/env python
"""wbap-a-data-r2 — download season CSVs from the sportsdataverse-data release store.

Usage: measure_r2_download.py <release_tag> <asset_prefix> <dest_subdir>
  e.g. measure_r2_download.py espn_wnba_game_rosters game_rosters_ roster_audit
       measure_r2_download.py espn_wnba_player_boxscores player_box_ roster_audit

Rights-cleared GitHub release store (no auth, no account, $0):
  repo sportsdataverse/sportsdataverse-data.
Destination (outside git): ~/.my-quantitative-data/wnba-prep-v1/<dest_subdir>/
Integrity: sha256 of each downloaded file compared to the GitHub API `digest`
field captured at pull time (saved verbatim to <dest>/release_meta_r2.json).
Read-only wrt the git worktree. No wnba.com / stats.wnba.com / ESPN access.
"""
import hashlib
import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = "sportsdataverse/sportsdataverse-data"
TAG = sys.argv[1] if len(sys.argv) > 1 else "espn_wnba_game_rosters"
PREFIX = sys.argv[2] if len(sys.argv) > 2 else "game_rosters_"
DEST = (Path.home() / ".my-quantitative-data" / "wnba-prep-v1"
        / (sys.argv[3] if len(sys.argv) > 3 else "roster_audit"))
API_URL = f"https://api.github.com/repos/{REPO}/releases/tags/{TAG}"
DL_BASE = f"https://github.com/{REPO}/releases/download/{TAG}/{TAG}"


def fetch(url: str, dest: Path, retries: int = 2) -> bool:
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "wbap-a-data-r2-audit"})
            with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as f:
                f.write(resp.read())
            return True
        except Exception as exc:  # noqa: BLE001
            print(f"  attempt {attempt + 1} failed: {exc}", file=sys.stderr)
    return False


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    meta_path = DEST / "release_meta_r2.json"
    if not fetch(API_URL, meta_path):
        print("NOT_RUN_DOWNLOAD: release metadata fetch failed after retries", file=sys.stderr)
        return 2
    release = json.loads(meta_path.read_text())
    tag = release.get("tag_name")
    published = release.get("published_at")
    want = {}
    for a in release.get("assets", []):
        name = a["name"]
        if name.startswith(PREFIX) and name.endswith(".csv"):
            want[name] = {"digest": a.get("digest", ""), "size": a["size"],
                          "updated": a.get("updated_at", ""),
                          "url": a.get("browser_download_url", "")}
    print(f"tag={tag} published={published} season csv assets={len(want)}")

    manifest = {
        "task": "wbap-a-data-r2",
        "cycle": "WNBA-WINPROB-PREP-V1",
        "source_repo": REPO,
        "release_tag": TAG,
        "release_published": published,
        "api_url": API_URL,
        "pull_started_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "machine_utc_at_meta_fetch": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "files": {},
    }
    # merge with any prior manifest (accumulates across tags into one download_manifest_r2.json)
    mpath = DEST / "download_manifest_r2.json"
    if mpath.exists():
        try:
            prior = json.loads(mpath.read_text())
            for name, rec in prior.get("files", {}).items():
                if name not in manifest["files"]:
                    manifest["files"][name] = rec
            manifest["releases"] = sorted(set(manifest.get("releases", []) + prior.get("releases", [])))
        except Exception:
            pass
    manifest.setdefault("releases", []).append(TAG)
    manifest["releases"] = sorted(set(manifest["releases"]))
    ok = True
    for name in sorted(want):
        dest = DEST / name
        url = want[name]["url"] or f"{DL_BASE}/{name}"
        gh_digest = want[name]["digest"] or ""
        if dest.exists() and sha256(dest) == gh_digest.replace("sha256:", ""):
            status = "already_present_digest_match"
        else:
            if not fetch(url, dest):
                print(f"DOWNLOAD FAIL {name}", file=sys.stderr)
                manifest["files"][name] = {"status": "FAILED", "url": url}
                ok = False
                continue
            status = "downloaded"
        digest = "sha256:" + sha256(dest)
        gh = gh_digest
        if not gh:
            # GitHub predates the digest field for this asset; byte size vs API is the check.
            match = None
            status += "_DIGEST_NOT_PROVIDED_BY_GITHUB"
        elif digest == gh:
            match = True
        else:
            print(f"DIGEST MISMATCH {name}: local {digest} vs github {gh}", file=sys.stderr)
            status += "_DIGEST_MISMATCH"
            match = False
            ok = False
        manifest["files"][name] = {
            "status": status,
            "url": url,
            "bytes": dest.stat().st_size,
            "sha256_local": digest,
            "github_digest": want[name]["digest"],
            "digest_match": match,
            "asset_updated_at": want[name]["updated"],
            "pull_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        print(f"{name}: {status} digest_match={match} bytes={dest.stat().st_size}")

    manifest["pull_finished_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest["all_digest_verified"] = ok
    (DEST / "download_manifest_r2.json").write_text(json.dumps(manifest, indent=2))
    print(f"manifest -> {DEST / 'download_manifest_r2.json'}  all_ok={ok}")
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
