#!/usr/bin/env zsh
# Fetch the 13 archived trading-hours windows for the 6E holiday grid.
# Each URL = fresh attempt budget (unique URL), 1 attempt here; polite 5s spacing.
set -u
FXEB=/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-readiness/prep/research/control/FUTURES-SIX-READINESS-20261004/fx_eb
PY=/Users/hoangminhlong/my-quantitative/.venv/bin/python
IDLIST="id=316,133,425,300,58,437,22,8478,5201,10191&pageNumber=1&pageSize=999&sortAsc=true"

fetch () { # ts from to _t suffix outfile
  local ts="$1" from="$2" to="$3" tparam="$4" out="$5" note="$6"
  local url="https://web.archive.org/web/${ts}id_/https://www.cmegroup.com/services/trading-hours-by-product?${IDLIST}&fromEventDate=${from}&toEventDate=${to}${tparam}"
  "$PY" "$FXEB/fetch_tool.py" "$url" "$out" "$note"
  sleep 5
}

fetch 20240708161438 2022-12-31 2023-01-02 "&isProtected&_t=1720455278630" "svc_20221231_20240708161438.json" "6E holiday window New Year 2023 (idlist incl. 58)"
fetch 20240708161438 2023-01-15 2023-01-17 "&isProtected&_t=1720455278636" "svc_20230115_20240708161438.json" "6E holiday window MLK 2023"
fetch 20240708161438 2023-02-19 2023-02-21 "&isProtected&_t=1720455278640" "svc_20230219_20240708161438.json" "6E holiday window Presidents 2023"
fetch 20240708161438 2023-04-06 2023-04-08 "&isProtected&_t=1720455278642" "svc_20230406_20240708161438.json" "6E holiday window Good Friday 2023"
fetch 20240708161438 2023-05-28 2023-05-30 "&isProtected&_t=1720455278644" "svc_20230528_20240708161438.json" "6E holiday window Memorial 2023"
fetch 20240708161438 2023-06-18 2023-06-20 "&isProtected&_t=1720455278646" "svc_20230618_20240708161438.json" "6E holiday window Juneteenth 2023"
fetch 20240708161438 2023-07-03 2023-07-05 "&isProtected&_t=1720455278650" "svc_20230703_20240708161438.json" "6E holiday window July-4 2023"
fetch 20240708161439 2023-09-03 2023-09-05 "&isProtected&_t=1720455278654" "svc_20230903_20240708161439.json" "6E holiday window Labor 2023"
fetch 20240708161439 2023-11-22 2023-11-24 "&isProtected&_t=1720455278656" "svc_20231122_20240708161439.json" "6E holiday window Thanksgiving 2023"
fetch 20240708161439 2023-12-24 2023-12-26 "&isProtected&_t=1720455278659" "svc_20231224_20240708161439.json" "6E holiday window Christmas 2023"
fetch 20240708161439 2023-12-31 2024-01-02 "&isProtected&_t=1720455278661" "svc_20231231_20240708161439.json" "6E holiday window New Year 2024"
fetch 20241220155340 2025-08-31 2025-09-02 "&isProtected&_t=1734710019546" "svc_20250831_20241220155340.json" "6E holiday window Labor 2025 (window sibling lost)"
fetch 20260926072615 2025-01-05 2025-01-07 "" "svc_20250105_20260926072615.json" "6E special closure 2025-01-09 Carter national day of mourning"
