"""LAB DASHBOARD — Lớp 1: Collector (thuần stdlib).

Đọc mọi nguồn dữ liệu của chương trình (PLAN_dashboard.md §0) thành MỘT
snapshot dict. Mỗi trường mang `source` để mọi số trên dashboard truy
được artifact. Trạng thái sống đo best-effort, fail-closed: thiếu dữ
liệu là giá trị KHÔNG CÓ DỮ LIỆU, không bao giờ suy diễn.

Nguồn:
  - research/wayfinder/FAMILY_FAILURES.jsonl   (failure registry)
  - research/wayfinder/HYPOTHESIS_LEDGER.md    (denominators, P-9)
  - research/wayfinder/LESSONS.md              (P-1..P-11)
  - RULES.md §7                                (GO registry)
  - ~/.my-quantitative-governance/heavy_runtime (heavy lock round-2,
    chỉ-đọc) + <main>/.runtime (legacy round-1, chỉ-đọc)
  - control dir từng cycle sống + `git worktree list`
  - panel PnL: với mỗi cycle đóng, terminal SHA + evidence_path đã pin
    trong registry -> `git show <sha>:<path>` -> MAPPER theo schema.

Sinh plans/ACTIVE_CYCLES.json mỗi lần chạy (handbook §3.1).
"""

from __future__ import annotations

import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

NO_DATA = "KHÔNG CÓ DỮ LIỆU"
REGISTRY_REL = "research/wayfinder/FAMILY_FAILURES.jsonl"
LEDGER_REL = "research/wayfinder/HYPOTHESIS_LEDGER.md"
LESSONS_REL = "research/wayfinder/LESSONS.md"
RULES_REL = "RULES.md"
ACTIVE_CYCLES_REL = "plans/ACTIVE_CYCLES.json"

# Cycle sống theo RULES.md §7 (GO registry) — collector chỉ ĐỌC,
# không bao giờ ghi vào worktree/artifact của chúng (hard boundary).
LIVE_CYCLES = [
    {
        "cycle_id": "STOCKS-V11",
        "plan": "plans/PLAN_stocks_v11.md",
        "go_phrase": "GO STOCKS V11 SCORED EXECUTION",
        "worktree_rel": ".worktrees/stocks-free-v11/integration",
        "control_rel": "research/control/stocks_free_v11_run",
    },
    {
        "cycle_id": "CRYPTO-V16",
        "plan": "plans/PLAN_crypto_v16.md",
        "go_phrase": "GO CRYPTO V16 SCORED EXECUTION",
        "worktree_rel": ".worktrees/crypto/v16/integration",
        "control_rel": "research/control/v16_run",
    },
    {
        "cycle_id": "FOREX-FREE-V7",
        "plan": "plans/PLAN_forex_v7.md",
        "go_phrase": "GO FOREX V7 SCORED EXECUTION",
        "worktree_rel": ".worktrees/forex-free-v7/integration",
        "control_rel": "research/control/forex_free_v7_run",
    },
]


def _git(root: Path, *args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True, text=True, timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.stdout if out.returncode == 0 else None


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def find_main_root(root: Path) -> str:
    """Main checkout = worktree đầu tiên trong `git worktree list`
    (luôn là checkout gốc chứa .worktrees/)."""
    out = _git(root, "worktree", "list", "--porcelain")
    if out:
        first = out.split("worktree ")[1].split("\n")[0]
        return first
    return str(root)


# ---------------------------------------------------------------------------
# Registry thất bại + panel PnL
# ---------------------------------------------------------------------------

def load_registry(root: Path) -> list[dict]:
    path = root / REGISTRY_REL
    try:
        lines = path.read_text(encoding="utf-8").strip().split("\n")
    except OSError:
        return []
    entries = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            entries.append({"_parse_error": True, "raw_prefix": line[:80]})
    return entries


def signature_counts(entries: list[dict]) -> list[dict]:
    counts = Counter(
        e["primary_failure"]["code"]
        for e in entries
        if isinstance(e.get("primary_failure"), dict) and "code" in e["primary_failure"]
    )
    return [{"code": c, "count": n, "source": REGISTRY_REL} for c, n in counts.most_common()]


# --- MAPPER: mỗi schema terminal một hàm, có test riêng -------------------
#
# Quy ước chung: mapper nhận dict JSON đã parse của artifact được pin
# (file evidence_path, hoặc file terminal trong thư mục evidence_path
# được pin) và trả về danh sách family; mỗi family có các arm với cột
# expectancy / pnl / pf / folds / mdd / margins. Giá trị không trích
# được để None -> renderer hiển thị NO_DATA. Số trích từ prose là chuỗi
# nguyên văn từ artifact (verbatim), không làm tròn lại.

_PAT_EXPECTANCY = re.compile(r"expectancy\s*([+-]?\d+(?:[.,]\d+)?)", re.I)
_PAT_PF = re.compile(r"\b(?:position_)?pf\s*([+-]?\d+(?:[.,]\d+)?)", re.I)
_PAT_FOLDS = re.compile(
    r"\bfolds?\b[^.;:]{0,24}?(\d\s*/\s*\d)"
    r"|(\d\s*/\s*\d)\b(?=[^.;]{0,40}?\bfolds?\b)", re.I)
_PAT_MDD = re.compile(r"\bmdd\s*([+-]?\d+(?:[.,]\d+)?\s*%?)", re.I)
_PAT_PNL = re.compile(
    r"(?:total\s+pnl|sum\s+pnl|fin-adj|net(?:_return_sum)?|pnl)\s*"
    r"([+-]?\d+(?:[.,]\d+)?\s*%?)", re.I)
_PAT_MARGIN = re.compile(r"margin\s*(?:to\s*(?:fail|[\d.]+)[^,;)]*?)?\s*"
                         r"([+-]?\d+(?:[.,]\d+)?)", re.I)


def _prose_find(text: str, pattern: re.Pattern) -> str | None:
    m = pattern.search(text or "")
    return m.group(0).strip() if m else None


def mapper_crypto_cell_results(doc: dict, doc_source: str) -> dict | None:
    """Schema `v14/v15_terminal_report_v1` (CRYPTO-V14, CRYPTO-V15):
    `cell_results` dict — mỗi cell có role/expectancy_per_day/PF/MDD/
    net(_return_sum)/folds_positive; V15 thêm `family_gate_tables` với
    margin_to_fail từng gate."""
    cells = doc.get("cell_results")
    if not isinstance(cells, dict):
        return None
    gates = doc.get("family_gate_tables") or {}
    families: dict[str, dict] = {}
    for cell_id, c in sorted(cells.items()):
        if not isinstance(c, dict):
            continue
        role = str(c.get("role", "unknown"))
        margins = None
        fam_key = cell_id
        # V15: gate table của family chứa margin từng gate FAIL (P-2);
        # khớp family với cell theo tiền tố id (A5-V15-F1... -> A5-F1-...)
        for fam_id, fam in sorted(gates.items()):
            if not isinstance(fam, dict):
                continue
            tokens = [t for t in fam_id.split("-") if t][:3]
            if tokens and all(t in cell_id for t in (tokens[0], tokens[-1])):
                fam_key = fam_id
                parts = []
                for gname, g in sorted(fam.items()):
                    if isinstance(g, dict) and g.get("verdict") == "FAIL" \
                            and "margin_to_fail" in g:
                        parts.append(f"{gname}: margin {g['margin_to_fail']}")
                if parts:
                    margins = "; ".join(parts)
                break
        fam = families.setdefault(fam_key, {"family_label": fam_key, "arms": []})
        fam["arms"].append({
            "role": role,
            "label": cell_id,
            "expectancy": c.get("expectancy_per_day"),
            "pnl": c.get("net_return_sum", c.get("net")),
            "pf": c.get("position_pf"),
            "folds": c.get("folds_positive"),
            "mdd": c.get("mdd"),
            "margins": margins,
        })
    if not families:
        return None
    return {
        "schema": doc.get("schema", "unknown"),
        "doc_source": doc_source,
        "families": list(families.values()),
    }


def mapper_forex_execution_summary(doc: dict, doc_source: str) -> dict | None:
    """FOREX-FREE-V1 `execution_summary.json`: cells[] với
    label `familyN:role:tier`, book{total_pnl,expectancy,profit_factor},
    mdd_usd, folds[]. FOREX-FREE-V2 cùng hình nhưng cell không có book —
    các cột số để None (NO_DATA), chỉ còn role + gates."""
    cells = doc.get("cells")
    if not isinstance(cells, list) or not cells:
        return None
    fam: dict[str, dict] = {"family_label": "cells", "arms": []}
    for c in cells:
        label = str(c.get("label") or c.get("cell_id") or "?")
        parts = label.split(":")
        role = parts[1] if len(parts) >= 2 else "unknown"
        book = c.get("book") or {}
        folds = c.get("folds") or []
        pos = sum(1 for f in folds if f.get("positive"))
        fam["arms"].append({
            "role": role,
            "label": label,
            "expectancy": book.get("expectancy"),
            "pnl": book.get("total_pnl"),
            "pf": book.get("profit_factor"),
            "folds": f"{pos}/{len(folds)}" if folds else None,
            "mdd": c.get("mdd_usd"),
            "margins": None,
        })
    # không một arm nào có số máy-đọc (vd FOREX-FREE-V2: cells chỉ có
    # gate verdicts) -> None để panel rơi về NO_DATA + ledger pointer
    numeric = ("expectancy", "pnl", "pf", "mdd")
    if not any(a[k] is not None for a in fam["arms"] for k in numeric):
        return None
    return {"schema": str(doc.get("schema", "execution_summary")),
            "doc_source": doc_source, "families": [fam]}


_ARM_ROLE_PAT = re.compile(
    r"\b(anchor|neighbou?r|neighbour|sham\s+control|causal[ _-]?negative[ _-]?control|control)\b", re.I)


def mapper_prose_verdicts(doc: dict, doc_source: str,
                          list_keys: tuple[str, ...]) -> dict | None:
    """Nhóm prose có ngữ pháp (STOCKS V3/V4 `family_results`,
    V8/V9/V10 + FOREX V5/V6 `family_verdicts`): mỗi family là chuỗi
    (hoặc dict chứa chuỗi) với các segment anchor/neighbour/control.
    Regex trích expectancy / pnl / pf / folds / mdd / margin VERBATIM;
    không khớp -> None."""
    fams = []
    for key in list_keys:
        val = doc.get(key)
        if not isinstance(val, dict):
            continue
        for fam_label, fam_val in val.items():
            role_hint = None
            m = re.match(r"^\s*(anchor|neighbou?r|sham\s+control|control)",
                         str(fam_label), re.I)
            if m:
                role_hint = m.group(1).lower()
            if isinstance(fam_val, dict):
                segments = [(k, v) for k, v in fam_val.items()
                            if isinstance(v, str)]
            elif isinstance(fam_val, str):
                # key của family đã nói rõ vai trò -> dùng nguyên chuỗi,
                # không tách (tránh tách sai bởi từ "anchor" trong prose)
                segments = ([(role_hint, fam_val)] if role_hint
                            else _split_prose_arms(fam_val))
            else:
                continue
            arms = []
            for role, text in segments:
                if _ARM_ROLE_PAT.fullmatch(role.strip()) is None and \
                        not isinstance(fam_val, str):
                    # khóa phụ (stress/drop_one_symbol...) của dict: giữ
                    # làm ghi chú, không phải arm anchor/neighbour/control
                    continue
                arms.append({
                    "role": role.strip(),
                    "label": fam_label if isinstance(fam_val, str) else role,
                    "expectancy": _prose_find(text, _PAT_EXPECTANCY),
                    "pnl": _prose_find(text, _PAT_PNL),
                    "pf": _prose_find(text, _PAT_PF),
                    "folds": _prose_find(text, _PAT_FOLDS),
                    "mdd": _prose_find(text, _PAT_MDD),
                    "margins": _prose_find(text, _PAT_MARGIN),
                })
            # arm không trích được BẤT KỲ số nào -> bỏ (số không có thật,
            # không hiển thị hàng rỗng giả vờ là dữ liệu)
            arms = [a for a in arms if any(
                a[k] for k in ("expectancy", "pnl", "pf", "folds", "mdd",
                               "margins"))]
            if arms:
                fams.append({"family_label": fam_label, "arms": arms})
    if not fams:
        return None
    return {"schema": str(doc.get("schema", "prose")), "doc_source": doc_source,
            "families": fams}


def _split_prose_arms(text: str) -> list[tuple[str, str]]:
    """Tách một chuỗi verdict dài thành các segment theo từ khoá arm
    (anchor / neighbour / sham control / control). Đoạn đầu nếu không
    mang nhãn arm thì coi là 'summary'."""
    marks = list(_ARM_ROLE_PAT.finditer(text))
    if not marks:
        return [("summary", text)]
    out: list[tuple[str, str]] = []
    pre = text[: marks[0].start()].strip()
    if pre:
        out.append(("summary", pre))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out.append((m.group(0).lower().strip(), text[m.start():end].strip()))
    return out


# --- Thứ tự file ưu tiên khi evidence_path là THƯ MỤC đã pin --------------
DIR_CANDIDATES = ["terminal_report.json", "terminal_verdict.json",
                  "execution_summary.json"]


def _choose_mapper(doc: dict) -> tuple[str, object]:
    schema = str(doc.get("schema", ""))
    if "terminal_report" in schema and isinstance(doc.get("cell_results"), dict):
        return "mapper_crypto_cell_results", mapper_crypto_cell_results
    if isinstance(doc.get("cells"), list) and (
            "book" in str(doc.get("cells", [{}])[0]) or doc.get("scored")):
        return "mapper_forex_execution_summary", mapper_forex_execution_summary
    if isinstance(doc.get("cells"), list):
        return "mapper_forex_execution_summary", mapper_forex_execution_summary
    for key in ("family_verdicts", "family_results"):
        if isinstance(doc.get(key), dict):
            return "mapper_prose_verdicts", (
                lambda d, s, _k=key: mapper_prose_verdicts(d, s, (_k,)))
    return "none", None


def _resolve_evidence_doc(root: Path, sha: str,
                          evidence_path: str | None) -> dict:
    """Đọc artifact terminal tại SHA đã pin. evidence_path là FILE -> đọc
    trực tiếp; là THƯ MỤC -> chỉ xét các tên file terminal chuẩn nằm
    TRONG thư mục được pin (không đoán đường dẫn ngoài pointer)."""
    if not evidence_path:
        return {"ok": False, "reason": "registry không pin evidence_path",
                "doc": None, "used_path": None, "mapper": "none"}
    target = evidence_path.rstrip("/")
    obj_type = _git(root, "cat-file", "-t", f"{sha}:{target}")
    if obj_type and obj_type.strip() == "blob":
        raw = _git(root, "show", f"{sha}:{target}")
        try:
            doc = json.loads(raw)
        except (json.JSONDecodeError, TypeError) as exc:
            return {"ok": False, "reason": f"JSON không parse được: {exc}",
                    "doc": None, "used_path": target, "mapper": "none"}
        return _map_doc(doc, target)
    if obj_type and obj_type.strip() == "tree":
        listing = _git(root, "ls-tree", "--name-only", sha, f"{target}/")
        for cand in DIR_CANDIDATES:
            cand_path = f"{target}/{cand}"
            if listing and cand_path in listing.split():
                raw = _git(root, "show", f"{sha}:{cand_path}")
                if raw:
                    try:
                        doc = json.loads(raw)
                    except json.JSONDecodeError as exc:
                        return {"ok": False,
                                "reason": f"JSON không parse được: {exc}",
                                "doc": None, "used_path": cand_path,
                                "mapper": "none"}
                    return _map_doc(doc, cand_path)
        return {"ok": False,
                "reason": "thư mục pin không chứa file terminal chuẩn",
                "doc": None, "used_path": target, "mapper": "none"}
    return {"ok": False, "reason": "git không thấy object tại SHA đã pin",
            "doc": None, "used_path": target, "mapper": "none"}


def _map_doc(doc: dict, used_path: str) -> dict:
    name, fn = _choose_mapper(doc)
    if fn is None:
        return {"ok": True, "doc": None, "used_path": used_path,
                "mapper": name, "reason": "schema không có mapper"}
    mapped = fn(doc, used_path)
    if mapped is None:
        return {"ok": True, "doc": None, "used_path": used_path,
                "mapper": name, "reason": "mapper không trích được arm nào"}
    return {"ok": True, "doc": mapped, "used_path": used_path,
            "mapper": name, "reason": None}


def collect_pnl_panel(root: Path, entries: list[dict]) -> list[dict]:
    """Với mỗi cycle đóng có terminal SHA pin trong registry: trích bảng
    anchor/neighbour/control. Không trích được -> NO_DATA + ledger
    pointer. Kết quả là MỘT mục mỗi (sha, evidence_path) — các family
    cùng cycle dùng chung bảng arm."""
    by_pair: dict[tuple[str, str | None], list[dict]] = {}
    order: list[tuple[str, str | None]] = []
    for e in entries:
        if "_parse_error" in e:
            continue
        ev = e.get("evidence") or {}
        sha = ev.get("terminal_sha")
        if not sha:
            continue
        pair = (sha, ev.get("evidence_path"))
        if pair not in by_pair:
            by_pair[pair] = []
            order.append(pair)
        by_pair[pair].append(e)

    panels = []
    for sha, path in order:
        fam_entries = by_pair[(sha, path)]
        res = _resolve_evidence_doc(root, sha, path)
        ledger_row = next(
            (fam.get("evidence", {}).get("ledger_row") for fam in fam_entries
             if fam.get("evidence", {}).get("ledger_row")), None)
        panels.append({
            "cycle_id": fam_entries[0].get("cycle_id"),
            "asset": fam_entries[0].get("asset"),
            "verdict_classes": sorted({fam.get("verdict_class", "?")
                                       for fam in fam_entries}),
            "terminal_sha": sha,
            "evidence_path": path,
            "ledger_row": ledger_row,
            "families": [fam.get("family_id") for fam in fam_entries],
            "mapper": res["mapper"],
            "table": res.get("doc"),
            "no_data_reason": res.get("reason") if res.get("doc") is None else None,
            "source": f"git show {sha}:{res.get('used_path') or '?'} (pin: {REGISTRY_REL})",
        })
    return panels


# ---------------------------------------------------------------------------
# Header: denominators, S1, GO registry
# ---------------------------------------------------------------------------

def collect_header(root: Path) -> dict:
    ledger_path = root / LEDGER_REL
    text = ""
    try:
        text = ledger_path.read_text(encoding="utf-8")
    except OSError:
        pass
    out = {"source": LEDGER_REL}
    pat_total = re.compile(
        r"Program total:\s*(\d+)\s*published\s*/\s*(\d+)\s*observed", re.I)
    m = pat_total.search(text)
    out["program"] = (
        {"published": int(m.group(1)), "observed": int(m.group(2))}
        if m else {"published": None, "observed": None, "note": NO_DATA})
    for asset in ("crypto", "stocks", "forex"):
        ma = re.search(
            rf"{asset}\s+(\d+)\s*published\s*/\s*(\d+)\s*observed", text, re.I)
        out[asset] = ({"published": int(ma.group(1)), "observed": int(ma.group(2))}
                      if ma else {"published": None, "observed": None,
                                  "note": NO_DATA})
    out["zero_survivors"] = True if re.search(
        r"0 survivors", text, re.I) else NO_DATA
    m_s1 = re.search(r"S1\s+untouched", text, re.I)
    out["s1"] = "S1 untouched (ledger)" if m_s1 else NO_DATA
    out["go_registry"] = collect_go_registry(root)
    return out


def collect_go_registry(root: Path) -> list[dict]:
    try:
        text = (root / RULES_REL).read_text(encoding="utf-8")
    except OSError:
        return []
    block = re.search(r"## 7\. GO phrase registry.*?```text\n(.*?)```",
                      text, re.S)
    if not block:
        return []
    rows = []
    for line in block.group(1).strip().split("\n"):
        m = re.match(r"\s*(GO \S+(?: \S+)*)\s*\(([^)]+)\)", line)
        if m:
            rows.append({"phrase": m.group(1).strip(),
                         "plan": m.group(2).strip(),
                         "source": f"{RULES_REL} §7"})
    return rows


# ---------------------------------------------------------------------------
# LESSONS P-1..P-11
# ---------------------------------------------------------------------------

def collect_lessons(root: Path) -> list[dict]:
    try:
        text = (root / LESSONS_REL).read_text(encoding="utf-8")
    except OSError:
        return []
    lines = text.split("\n")
    lessons = []
    i = 0
    while i < len(lines):
        m = re.match(r"^## (P-\d+)\s+—\s+(.+)$", lines[i])
        if m:
            body: list[str] = []
            j = i + 1
            while j < len(lines) and not lines[j].startswith("## "):
                body.append(lines[j])
                j += 1
            lessons.append({
                "id": m.group(1), "title": m.group(2).strip(),
                "body": "\n".join(body).strip(),
                "source": f"{LESSONS_REL} dòng {i + 1}",
            })
            i = j
        else:
            i += 1
    return lessons


# ---------------------------------------------------------------------------
# Near-miss (mục E của ledger — do Lead tuyển, trích nguyên văn)
# ---------------------------------------------------------------------------

def collect_near_misses(root: Path) -> dict:
    try:
        text = (root / LEDGER_REL).read_text(encoding="utf-8")
    except OSError:
        return {"body": NO_DATA, "source": LEDGER_REL}
    lines = text.split("\n")
    start = None
    for i, l in enumerate(lines):
        if l.startswith("## E."):
            start = i
            break
    if start is None:
        return {"body": NO_DATA, "source": LEDGER_REL}
    body = []
    for l in lines[start + 1:]:
        if l.startswith("## ") and not l.startswith("## E."):
            break
        body.append(l)
    return {"body": "\n".join(body).strip(),
            "source": f"{LEDGER_REL} mục E (từ dòng {start + 1})"}


# ---------------------------------------------------------------------------
# Heavy lock + ps
# ---------------------------------------------------------------------------

def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def collect_running(main_root: Path) -> dict:
    out: dict = {}
    runtimes = {
        "round2_home": Path.home() / ".my-quantitative-governance" / "heavy_runtime",
        "round1_legacy": main_root / ".runtime",
    }
    lock_rows, history_rows = [], []
    for name, rt in runtimes.items():
        if not rt.is_dir():
            lock_rows.append({"runtime": name, "lock": NO_DATA,
                              "source": str(rt)})
        else:
            lock = _read_json(rt / "heavy_worker.lock")
            lock_rows.append({"runtime": name,
                              "lock": lock if lock is not None else NO_DATA,
                              "source": str(rt / "heavy_worker.lock")})
            try:
                lines = (rt / "heavy_worker.history.jsonl").read_text(
                    encoding="utf-8").strip().split("\n")
                hist = [json.loads(l) for l in lines[-10:] if l.strip()]
            except (OSError, json.JSONDecodeError):
                hist = []
            history_rows.append({"runtime": name, "last": hist,
                                 "source": str(rt / "heavy_worker.history.jsonl")})
    out["heavy_lock"] = lock_rows
    out["heavy_history"] = history_rows
    try:
        ps = subprocess.run(["ps", "ax", "-o", "pid,etime,command"],
                            capture_output=True, text=True, timeout=15).stdout
        workers = [l.strip() for l in ps.split("\n")
                   if "python" in l and "grep" not in l][:12]
    except (OSError, subprocess.TimeoutExpired):
        workers = []
    out["ps_workers"] = {"rows": workers, "label": "đo bằng ps",
                         "source": "ps ax -o pid,etime,command"}
    return out


# ---------------------------------------------------------------------------
# Cycle sống
# ---------------------------------------------------------------------------

def collect_live_cycle(root: Path, main_root: Path, spec: dict) -> dict:
    wt = Path(spec["worktree_rel"])
    wt_abs = main_root / wt if wt.is_relative_to(".worktrees") else wt
    out = dict(spec)
    out["worktree_abs"] = str(wt_abs)
    if wt_abs.is_dir():
        head = _git(wt_abs, "rev-parse", "HEAD")
        branch = _git(wt_abs, "rev-parse", "--abbrev-ref", "HEAD")
        out["head"] = (head or "").strip() or NO_DATA
        out["head_short"] = out["head"][:12] if out["head"] != NO_DATA else NO_DATA
        out["branch"] = (branch or "").strip() or NO_DATA
        out["measured_status"] = "worktree tồn tại, HEAD đo được"
    else:
        out["head"] = out["head_short"] = out["branch"] = NO_DATA
        out["measured_status"] = "worktree không tồn tại"
    # control dir của cycle sống nằm TRONG worktree của nó; fallback
    # sang main checkout nếu worktree vắng (best-effort, chỉ ĐỌC)
    ctrl = wt_abs / spec["control_rel"]
    if not ctrl.is_dir():
        alt = main_root / spec["control_rel"]
        if alt.is_dir():
            ctrl = alt
    out["control_dir"] = str(ctrl)
    out["latest_artifacts"] = []
    if ctrl.is_dir():
        items = []
        for p in ctrl.iterdir():
            try:
                items.append((p.stat().st_mtime, p.name, p.is_file()))
            except OSError:
                continue
        items.sort(reverse=True)
        for mtime, name, is_file in items[:5]:
            ts = datetime.fromtimestamp(mtime, tz=timezone.utc)
            out["latest_artifacts"].append({
                "name": name, "mtime_utc": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "is_file": is_file})
        hb = _read_json(ctrl / "heartbeat.json")
        out["heartbeat"] = hb if hb is not None else NO_DATA
        try:
            ev_lines = (ctrl / "event_log.jsonl").read_text(
                encoding="utf-8").strip().split("\n")
            last = json.loads(ev_lines[-1]) if ev_lines and ev_lines[-1] else None
        except (OSError, json.JSONDecodeError, IndexError):
            last = None
        out["last_event"] = last if last is not None else NO_DATA
        state = _read_json(ctrl / "state.json")
        out["state"] = state if state is not None else NO_DATA
    else:
        out["heartbeat"] = out["last_event"] = out["state"] = NO_DATA
    # heavy-lock row của cycle này (từ registry round-2, chỉ-đọc)
    rt = Path.home() / ".my-quantitative-governance" / "heavy_runtime"
    hist = _read_json_array(rt / "heavy_worker.history.jsonl")
    rows = [h for h in hist if h.get("cycle_id") == spec["cycle_id"]]
    out["heavy_lock_rows"] = rows[-3:] if rows else []
    out["budget"] = NO_DATA  # không có artifact budget máy-đọc trong control dir
    return out


def _read_json_array(path: Path) -> list:
    try:
        return [json.loads(l) for l in
                path.read_text(encoding="utf-8").strip().split("\n") if l.strip()]
    except (OSError, json.JSONDecodeError):
        return []


# ---------------------------------------------------------------------------
# Snapshot tổng + ACTIVE_CYCLES.json
# ---------------------------------------------------------------------------

def collect_snapshot(root: Path) -> dict:
    root = Path(root).resolve()
    main_root = Path(find_main_root(root))
    entries = load_registry(root)
    snapshot = {
        "measured_at": utc_now(),
        "root": str(root),
        "main_root": str(main_root),
        "header": collect_header(root),
        "assets": [collect_live_cycle(root, main_root, s) for s in LIVE_CYCLES],
        "running": collect_running(main_root),
        "failures": {
            "entries": entries,
            "total": len(entries),
            "signature_counts": signature_counts(entries),
            "source": REGISTRY_REL,
        },
        "pnl": collect_pnl_panel(root, entries),
        "near_misses": collect_near_misses(root),
        "lessons": collect_lessons(root),
    }
    return snapshot


def build_active_cycles(snapshot: dict) -> dict:
    registry = {
        "measured_at": snapshot["measured_at"],
        "cycles": [],
        "source": "dashboard_collect.collect_snapshot (handbook §3.1)",
    }
    for a in snapshot["assets"]:
        registry["cycles"].append({
            "cycle_id": a["cycle_id"],
            "plan": a["plan"],
            "status": a["measured_status"],
            "phase": (a["latest_artifacts"][0]["name"]
                      if a["latest_artifacts"] else NO_DATA),
            "worktree": a["worktree_abs"],
            "branch": a["branch"],
            "head": a["head"],
            "budget": a["budget"],
            "go_phrase": a["go_phrase"],
            "s1": snapshot["header"]["s1"],
            "measured_at": snapshot["measured_at"],
        })
    return registry


def write_outputs(snapshot: dict, out_dir: Path) -> None:
    """Sinh plans/ACTIVE_CYCLES.json + dashboard/index.html."""
    try:
        from dashboard_render import render  # chạy trực tiếp / tests
    except ImportError:  # chạy qua `python -m research.governance...`
        from .dashboard_render import render
    root = Path(snapshot["root"])
    ac_path = root / ACTIVE_CYCLES_REL
    ac_path.parent.mkdir(parents=True, exist_ok=True)
    ac_path.write_text(
        json.dumps(build_active_cycles(snapshot), ensure_ascii=False,
                   indent=1) + "\n", encoding="utf-8")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(render(snapshot), encoding="utf-8")


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    snap = collect_snapshot(root)
    write_outputs(snap, root / "dashboard")
    print(f"snapshot measured_at={snap['measured_at']} "
          f"failures={snap['failures']['total']} pnl_cycles={len(snap['pnl'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
