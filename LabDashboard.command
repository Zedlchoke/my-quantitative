#!/bin/zsh
# LAB DASHBOARD — launcher double-click (PLAN_dashboard.md §2, lớp 3).
# Dùng .venv của MAIN checkout (worktree không có .venv riêng);
# pywebview==6.2.1 đã pin trong .venv đó.
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAIN_ROOT="$(git -C "$SCRIPT_DIR" worktree list --porcelain | head -1 | cut -d' ' -f2)"
PY="$MAIN_ROOT/.venv/bin/python"
if [ ! -x "$PY" ]; then
  echo "BLOCKED: không tìm thấy $PY (cần .venv với pywebview==6.2.1)" >&2
  exit 3
fi
cd "$SCRIPT_DIR"
exec "$PY" -m research.governance.lab_app
