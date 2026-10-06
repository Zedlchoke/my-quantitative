#!/bin/zsh
# Offline test runner for the futbt prep package.
# All tests run on deterministic synthetic fixtures — no network, no raw-data
# access, no lock required.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="${PYTHON:-/Users/hoangminhlong/my-quantitative/.venv/bin/python}"
cd "$HERE"
"$PY" -m unittest discover -s tests -t . -v 2>&1 | tail -25
