# VENDOR PIN — edge-scanner local_guard

```yaml
upstream_repo: https://github.com/simonro/edge-scanner
upstream_commit: c927dcb0c5e8122269812d2cdfdc4a3ae71b2ab3   # refs/heads/main, "Release 2026-09-25"
pinned_utc: 2026-09-26T13:37:49Z                            # OWNER_DECISION_approval_2026-09-26.json; GO-1 consumed same session
license: MIT (c) 2026 "Tape to Edge" — LICENSE vendored verbatim; NOTICE vendored verbatim
vendored_by_cycle: EDGE-SCANNER-TOOLING-V1 (plans/PLAN_edge_scanner_tooling_v1.md, GO-1)
```

## Vendored files (sha256, upstream == vendored, verified at vendor time)

| file | upstream path | sha256 |
|---|---|---|
| `local_guard.py` | `scanner/local_guard.py` | `4418a2e1c50e2b7be642bf5c2d2f3745bee81f34378d637332bdeef91f88b762` |
| `LICENSE` | `LICENSE` | `5d44f49c87f1a8e86d5e423293fba1b077d611e055e63a5ddf1e7666f56e28e3` |
| `NOTICE` | `NOTICE` | `d84c264d4623e6c2d27ac14a0007470786ecb2b964b7c4813863731fd1a0d133` |

## Re-verification commands (any auditor)

```bash
git clone --depth 1 https://github.com/simonro/edge-scanner.git /tmp/es-verify
git -C /tmp/es-verify rev-parse HEAD        # must equal upstream_commit above
shasum -a 256 /tmp/es-verify/scanner/local_guard.py /tmp/es-verify/LICENSE /tmp/es-verify/NOTICE
shasum -a 256 research/platform_tools/thirdparty/edge-scanner/{local_guard.py,LICENSE,NOTICE}
```

## Re-pin law

Any change to the vendored bytes (including "harmless" edits, re-syncs to a
newer upstream SHA, or additional files from upstream) is a NEW owner decision.
Silent re-pinning is forbidden. If upstream dies, this pin plus the digests
above remain the authority for the vendored copy.

## Scope fence (plan §0 non_goals, binding)

NOT vendored and never to be added here: trigger catalog/setups, `stops.py`,
`size_hint`, alert score heuristic, `gates.py` constants, data providers
(Alpaca/Schwab/yfinance), dashboard-v2, plugin system. This directory holds
exactly the three files listed above.
