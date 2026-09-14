"""Static contract checks for the repository-owned ZCode plugin."""
from __future__ import annotations

import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
PLUGIN = REPO / "plugins" / "quant-research-orchestrator"
AGENTS = (
    "quant-auditor.md",
    "quant-explorer.md",
    "quant-implementer.md",
    "quant-reproducer.md",
)


def _frontmatter(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "---", path
    closing = lines.index("---", 1)
    return lines[1:closing]


def test_plugin_and_marketplace_versions_match():
    manifest = json.loads(
        (PLUGIN / ".zcode-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    marketplace = json.loads(
        (REPO / "plugins" / "marketplace.json").read_text(encoding="utf-8")
    )
    entry = next(
        item
        for item in marketplace["plugins"]
        if item["name"] == "quant-research-orchestrator"
    )
    assert manifest["version"] == entry["version"]


def test_all_subagents_pin_glm_flash_high():
    for filename in AGENTS:
        frontmatter = _frontmatter(PLUGIN / "agents" / filename)
        assert frontmatter.count(
            "model: builtin:zai-coding-plan/GLM-5.3-Flash"
        ) == 1
        assert frontmatter.count("thoughtLevel: high") == 1
