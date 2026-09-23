#!/bin/bash
# Reproducible recovery of frozen engines for CRYPTO-HISTORICAL-REPLICATION-3F-V1.
# Usage: extract_frozen.sh <repo-root> <dest-dir>
# v11_root = research/adapter_v10 + research/v11 + ILLIQ tests   @ c97283e0d1681c24ee9a637a4fb1628d0334b7e1 (V11 freeze/terminal lineage)
# v14_root = research/adapter_v10 + research/v11 helpers + research/v14 + BASISLV tests @ 183554add4db82444d3e71beb24fb247c6b420b2 (V14 terminal)
set -euo pipefail
REPO="${1:?repo root}"; DEST="${2:?dest}"
V11C=c97283e0d1681c24ee9a637a4fb1628d0334b7e1
V14C=183554add4db82444d3e71beb24fb247c6b420b2
extract() { # commit src dst-root
  local c="$1" src="$2" root="$3"
  mkdir -p "$root/$(dirname "$src")"
  git -C "$REPO" show "$c:$src" > "$root/$src"
}
# ---- v11_root ----
V=$DEST/v11_root
for f in $(git -C "$REPO" ls-tree -r --name-only "$V11C" research/adapter_v10/ research/v11/); do extract "$V11C" "$f" "$V"; done
for t in test_v11i_illiq_amihud_causal.py test_v11i_illiq_amihud_identity.py test_v11i_illiq_amihud_pit.py test_v11i_oilever_delev_frozen.py test_v11p_a2_publication.py test_v11p_a3_costgate.py test_v11p_a4_dryrun.py; do extract "$V11C" "tests/$t" "$V"; done
for f in $(git -C "$REPO" ls-tree --name-only "$V11C" | grep -E '^(conftest.py|pytest.ini|setup.cfg|pyproject.toml)$' || true); do extract "$V11C" "$f" "$V"; done
git -C "$REPO" ls-tree --name-only "$V11C" tests/conftest.py 2>/dev/null | grep -q . && extract "$V11C" tests/conftest.py "$V" || true
# ---- v14_root ----
W=$DEST/v14_root
for f in $(git -C "$REPO" ls-tree -r --name-only "$V14C" research/adapter_v10/ research/v14/); do extract "$V14C" "$f" "$W"; done
for f in research/v11/__init__.py research/v11/families/__init__.py $(git -C "$REPO" ls-tree -r --name-only "$V14C" research/v11/families/oilever_delev/); do extract "$V14C" "$f" "$W"; done
for t in test_v14_family1_basislv.py test_v14_p1_cost_once.py; do extract "$V14C" "tests/$t" "$W"; done
for f in $(git -C "$REPO" ls-tree --name-only "$V14C" | grep -E '^(conftest.py|pytest.ini|setup.cfg|pyproject.toml)$' || true); do extract "$V14C" "$f" "$W"; done
git -C "$REPO" ls-tree --name-only "$V14C" tests/conftest.py 2>/dev/null | grep -q . && extract "$V14C" tests/conftest.py "$W" || true
echo "EXTRACTED v11_root $(find $V -name '*.py' | wc -l | tr -d ' ') py files; v14_root $(find $W -name '*.py' | wc -l | tr -d ' ') py files"

# ---- shared-era modules required by the adapter_v10 import closure ----
extract_closure() { # commit root
  local c="$1" root="$2"
  for f in $(git -C "$REPO" ls-tree -r --name-only "$c" research/cache_v10/ research/contract_v10.py research/global_ledger.py research/global_ledger/ research/pit_hooks_v10.py research/pit_hooks_v10/ research/hyp_a8_m01.py research/protocol/ 2>/dev/null || true); do
    mkdir -p "$root/$(dirname "$f")"; git -C "$REPO" show "$c:$f" > "$root/$f"
  done
}
extract_closure "$V11C" "$DEST/v11_root"
extract_closure "$V14C" "$DEST/v14_root"
echo "closure extracted"

# flat modules (exact paths) + protocol dir
extract_flat() { # commit root
  local c="$1" root="$2"
  for f in research/cache_v10.py research/contract_v10.py research/global_ledger.py research/hyp_a8_m01.py research/pit_hooks_v10.py research/resolved_contract.py; do
    git -C "$REPO" cat-file -e "$c:$f" 2>/dev/null && { mkdir -p "$root/$(dirname "$f")"; git -C "$REPO" show "$c:$f" > "$root/$f"; } || true
  done
  for f in $(git -C "$REPO" ls-tree -r --name-only "$c" research/protocol/ 2>/dev/null || true); do
    mkdir -p "$root/$(dirname "$f")"; git -C "$REPO" show "$c:$f" > "$root/$f"
  done
}
extract_flat "$V11C" "$DEST/v11_root"
extract_flat "$V14C" "$DEST/v14_root"
echo "flat modules extracted"

# repo-root contracts package
extract_contracts() { # commit root
  local c="$1" root="$2"
  for f in $(git -C "$REPO" ls-tree -r --name-only "$c" contracts/ 2>/dev/null || true); do
    mkdir -p "$root/$(dirname "$f")"; git -C "$REPO" show "$c:$f" > "$root/$f"
  done
}
extract_contracts "$V11C" "$DEST/v11_root"
extract_contracts "$V14C" "$DEST/v14_root"
echo "contracts extracted"

# iterative top-level import closure (max 6 rounds)
extract_import_closure() { # commit root
  local c="$1" root="$2"
  for round in 1 2 3 4 5 6; do
    local missing
    missing=$(cd "$root" && "$PYBIN" - <<PYEOF
import ast, os, sys
have=set()
for dirpath,_,files in os.walk('.'):
    if '.git' in dirpath: continue
    for fn in files:
        if fn.endswith('.py'):
            rel=os.path.relpath(os.path.join(dirpath,fn),'.')
            parts=rel.split(os.sep)
            if parts[-1]=='__init__.py' and len(parts)>1: have.add('/'.join(parts[:-1]))
            else: have.add(rel[:-3])
            if len(parts)>1: have.add('/'.join(parts[:-1]))
        elif fn in ('pyproject.toml','setup.cfg','pytest.ini'):
            pass
miss=set()
for dirpath,_,files in os.walk('.'):
    if '.git' in dirpath: continue
    for fn in files:
        if not fn.endswith('.py'): continue
        p=os.path.join(dirpath,fn)
        try: tree=ast.parse(open(p).read())
        except Exception: continue
        for node in ast.walk(tree):
            mods=[]
            if isinstance(node,ast.Import):
                mods=[a.name for a in node.names]
            elif isinstance(node,ast.ImportFrom) and node.level==0 and node.module:
                mods=[node.module]
            for m in mods:
                top=m.split('.')[0]
                if top in ('research','tests','contracts','reports') or top in have: continue
                # stdlib/site-packages check: try import
                try: __import__(top)
                except Exception: miss.add(top)
print('\n'.join(sorted(miss)))
PYEOF
)
    [ -z "$missing" ] && break
    for m in $missing; do
      for f in $(git -C "$REPO" ls-tree -r --name-only "$c" "$m" "$m.py" 2>/dev/null || true); do
        mkdir -p "$root/$(dirname "$f")"; git -C "$REPO" show "$c:$f" > "$root/$f"
      done
    done
    echo "round $round extracted: $missing"
  done
}
export PYBIN="${PYBIN:-python3}"
extract_import_closure "$V11C" "$DEST/v11_root"
extract_import_closure "$V14C" "$DEST/v14_root"
echo "import closure done"

# reports package (manual, closure layer N)
extract_reports() { # commit root
  local c="$1" root="$2"
  for f in $(git -C "$REPO" ls-tree -r --name-only "$c" reports/ 2>/dev/null || true); do
    mkdir -p "$root/$(dirname "$f")"; git -C "$REPO" show "$c:$f" > "$root/$f"
  done
}
extract_reports "$V11C" "$DEST/v11_root"
extract_reports "$V14C" "$DEST/v14_root"
echo "reports extracted"

# data package + any remaining repo-root py packages referenced by tests
extract_data() { # commit root
  local c="$1" root="$2"
  for f in $(git -C "$REPO" ls-tree -r --name-only "$c" data/ 2>/dev/null || true); do
    mkdir -p "$root/$(dirname "$f")"; git -C "$REPO" show "$c:$f" > "$root/$f"
  done
}
extract_data "$V11C" "$DEST/v11_root"
extract_data "$V14C" "$DEST/v14_root"
echo "data extracted"

# all remaining top-level research/*.py flat modules from the commit
extract_research_flat_all() { # commit root
  local c="$1" root="$2"
  for f in $(git -C "$REPO" ls-tree --name-only "$c" research/ | grep '\.py$'); do
    git -C "$REPO" cat-file -e "$c:$f" 2>/dev/null && git -C "$REPO" show "$c:$f" > "$root/$f"
  done
}
extract_research_flat_all "$V11C" "$DEST/v11_root"
extract_research_flat_all "$V14C" "$DEST/v14_root"
echo "research flat-all extracted"

# frozen control artifacts the identity tests read
extract_control() { # commit root
  local c="$1" root="$2"; shift 2
  for d in "$@"; do
    for f in $(git -C "$REPO" ls-tree -r --name-only "$c" "$d" 2>/dev/null || true); do
      mkdir -p "$root/$(dirname "$f")"; git -C "$REPO" show "$c:$f" > "$root/$f"
    done
  done
}
extract_control "$V11C" "$DEST/v11_root" research/control/v11_run/
extract_control "$V14C" "$DEST/v14_root" research/control/v14_run/
echo "control artifacts extracted"

# v14_root also needs the V11 publication-identity module (V12-inherited identity law)
mkdir -p "$DEST/v14_root/research/v11"; git -C "$REPO" show "$V14C:research/v11/publication_identity.py" > "$DEST/v14_root/research/v11/publication_identity.py"
for f in $(git -C "$REPO" ls-tree -r --name-only "$V14C" research/v12/ 2>/dev/null || true); do mkdir -p "$DEST/v14_root/$(dirname "$f")"; git -C "$REPO" show "$V14C:$f" > "$DEST/v14_root/$f"; done
