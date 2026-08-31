#!/usr/bin/env python3
"""Validate project Claude skills, agents, settings, templates, and scripts."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLAUDE = ROOT / ".claude"
EXPECTED_SKILLS = {
    "repo-intake", "worktree-dispatch", "test-router", "gate-evidence",
    "pit-data-audit", "trial-freeze", "reproduce-reconcile", "agent-handoff",
}
EXPECTED_AGENTS = {"a1-controller", "a7-auditor", "implementation-agent"}


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise ValueError("missing first-line YAML frontmatter")
    raw = text.split("\n---\n", 1)[0][4:]
    result: dict[str, str] = {}
    for line in raw.splitlines():
        match = re.match(r"^([A-Za-z][A-Za-z0-9-]*):\s*(.*)$", line)
        if match:
            result[match.group(1)] = match.group(2).strip()
    return result


def main() -> int:
    errors: list[str] = []
    try:
        json.loads((CLAUDE / "settings.json").read_text(encoding="utf-8"))
        json.loads((CLAUDE / "skills/agent-handoff/assets/handoff.template.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"JSON: {exc}")

    found_skills = set()
    for path in sorted((CLAUDE / "skills").glob("*/SKILL.md")):
        try:
            meta = frontmatter(path)
            name = meta.get("name", "")
            if name != path.parent.name:
                errors.append(f"{path}: name must equal directory")
            if not meta.get("description"):
                errors.append(f"{path}: missing description")
            found_skills.add(name)
        except (OSError, ValueError) as exc:
            errors.append(f"{path}: {exc}")
    if found_skills != EXPECTED_SKILLS:
        errors.append(f"skills expected={sorted(EXPECTED_SKILLS)} found={sorted(found_skills)}")

    found_agents = set()
    for path in sorted((CLAUDE / "agents").glob("*.md")):
        try:
            meta = frontmatter(path)
            name = meta.get("name", "")
            if not re.fullmatch(r"[a-z][a-z0-9-]*", name):
                errors.append(f"{path}: invalid agent name {name!r}")
            if not meta.get("description"):
                errors.append(f"{path}: missing description")
            found_agents.add(name)
        except (OSError, ValueError) as exc:
            errors.append(f"{path}: {exc}")
    if found_agents != EXPECTED_AGENTS:
        errors.append(f"agents expected={sorted(EXPECTED_AGENTS)} found={sorted(found_agents)}")

    for script in sorted(CLAUDE.rglob("*.py")):
        proc = subprocess.run([sys.executable, "-m", "py_compile", str(script)], capture_output=True, text=True, check=False)
        if proc.returncode:
            errors.append(f"{script}: {proc.stderr.strip()}")

    if not (ROOT / "CLAUDE.md").is_file():
        errors.append("CLAUDE.md missing")
    print(json.dumps({"status": "PASS" if not errors else "FAIL", "errors": errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
