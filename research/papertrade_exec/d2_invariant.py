"""SPEC D2 — GATE INVARIANT: NO BET_PAPER WITHOUT A VALID OPINION BINDING
(SPEC_D2_GATE_INVARIANT_2026-10-26.md, sha256 06e204d2…; DONG LANH, CHUA
KICH HOAT).

Vu viec goc: M48 (WSL, 2026-10-22) — mot dong BET_PAPER duoc ghi voi
ai_gate: null, khong opinion bound, khong ly do no-verdict, du ca production
V2 lan shadow V3 deu VETO truoc do 3 gio. Spec D2 lam cho vu do tro nen
KHONG THE tai dien: moi lan ghi BET_PAPER PHAI mang mot opinion binding HOP
LE (muc 2) neu khong BI TU CHOI GHI (muc 3) — tai CHINH moi diem ghi
DECISION cua desk (muc 4), bat ke nguyen nhan.

Cac luat da dong lanh o day (KHONG them, KHONG bot):
  * Binding hop le (muc 2): ai_gate la object; candidate_hash hex khong
    rong; opinion_verdict == "ALLOW"; file opinion PRODUCTION
    opinions_v2/<match_id>_<hash>.json ton tai va khop hash/match/verdict;
    prompt_sha256 == digest DA DANG KY cua chinh prompt_version cua opinion
    (cong thuc digest-blanked cua U0/M1 — khong tu suy); model_id thuoc
    chuoi DeepSeek-ONLY dang hieu luc (config ai_provider). KHONG kiem
    tuoi opinion (muc 2.5: journal co luat tuoi rieng).
  * Shadow KHONG BAO GIO tinh (muc 2.5): chi doc opinions_v2 (production);
    ai_review/shadow/ khong duoc doc o day.
  * Tu choi (muc 3): khong ghi dong DECISION; ung vien ve PENDING_AI voi
    last_detail "decision refused: no valid opinion bound (D2)";
    gate_event DECISION_REFUSED_NO_OPINION_BOUND voi dung 1 ma trong
    {AI_GATE_NULL, AI_GATE_MISSING_HASH, VERDICT_NOT_ALLOW,
    OPINION_FILE_MISSING, OPINION_MISMATCH}; counter telemetry rieng;
    khong dung lane, khong crash, khong tu dat.
  * Cac status khac (muc 2.6) khong bi kiem — wrapper la passthrough tinh
    cho moi dong khong phai BET_PAPER.
  * Flag: d2_gate_invariant_active theo dung luat feature-gate W4 (config
    feature_gates + GO token cua chu). Flag OFF = passthrough nguyen byte.
"""
from __future__ import annotations

import json
import string
from pathlib import Path

D2_SPEC_SHA256 = ("06e204d297a4273c116c669232695114a5d67b2192c19f8f93d5"
                  "d34547f47e32")
D2_REFUSAL_EVENT = "DECISION_REFUSED_NO_OPINION_BOUND"
D2_REFUSAL_DETAIL = "decision refused: no valid opinion bound (D2)"
D2_TELEMETRY_OUTCOME = "D2_REFUSED"
D2_REFUSAL_CODES = ("AI_GATE_NULL", "AI_GATE_MISSING_HASH", "VERDICT_NOT_ALLOW",
                    "OPINION_FILE_MISSING", "OPINION_MISMATCH")

_HEX = set(string.hexdigits)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def deepseek_chain() -> tuple[str, ...]:
    """Muc 2.4e: chuoi DeepSeek-ONLY 'dang hieu luc' — doc tu config
    ai_provider (model_id + fallback_models, dung thu tu config). Hien nay
    la deepseek-v4.1-flash-1017 + deepseek-v4.1-flash; neu chu doi config
    (hành dong cua chu), chuoi theo config moi. Doc khong duoc -> tra ve
    chuoi RONG (fail-closed: khong model nao thoa 2.4e)."""
    try:
        cfg = json.loads((_repo_root() / "research" / "papertrade_exec" /
                          "config.json").read_text())
        prov = cfg.get("ai_provider") or {}
        chain = [prov.get("model_id")] + list(prov.get("fallback_models") or [])
        return tuple(m for m in chain if m)
    except Exception:
        return ()


def d2_binding_check(row: dict, data_root, *,
                     sandbox: bool = False) -> tuple[bool, str | None]:
    """Muc 2 (dong lanh): kiem binding TREN DU LIEU DIA tai thoi diem ghi.
    Return (ok, None) hoac (False, ma tu choi trong D2_REFUSAL_CODES).
    Chi kiem dong BET_PAPER — nguoi goi dam bao (wrapper); ham nay van
    tinh toan cho bat ky row nao (tra AI_GATE_NULL cho row khong co gate)."""
    from research.papertrade_exec import ai_gate_v2 as G
    g = row.get("ai_gate")
    if not isinstance(g, dict):
        return False, "AI_GATE_NULL"
    chash = g.get("candidate_hash")
    if not isinstance(chash, str) or not chash or \
            not set(chash) <= _HEX:
        return False, "AI_GATE_MISSING_HASH"
    if g.get("opinion_verdict") != "ALLOW":
        return False, "VERDICT_NOT_ALLOW"
    match_id = row.get("match_id")
    # Muc 2.4: chi PRODUCTION opinions_v2. Shadow (ai_review/shadow/) khong
    # bao gio duoc doc o day — muc 2.5.
    f = (G.ai_review_dir(Path(data_root), sandbox) / "opinions_v2" /
         f"{match_id}_{chash}.json")
    if not f.exists():
        return False, "OPINION_FILE_MISSING"
    try:
        op = json.loads(f.read_text())
    except (OSError, json.JSONDecodeError):
        return False, "OPINION_FILE_MISSING"
    if str(op.get("candidate_hash")) != str(chash) or \
            str(op.get("match_id")) != str(match_id):
        return False, "OPINION_MISMATCH"
    if str(op.get("verdict") or "").strip().upper() != "ALLOW" or \
            str(op.get("verdict") or "").strip().upper() != \
            str(g.get("opinion_verdict")).strip().upper():
        return False, "OPINION_MISMATCH"
    # Muc 2.4d: digest DA DANG KY cua chinh prompt_version cua opinion —
    # cong thuc digest-blanked cua U0/M1 (ai_producer). KHONG tu suy digest;
    # version la / khong do duoc -> fail-closed (OPINION_MISMATCH).
    try:
        from research.papertrade_exec.ai_producer import registered_prompt_sha
        reg_sha, _, _ = registered_prompt_sha(_repo_root(),
                                              version=str(
                                                  op.get("prompt_version")
                                                  or ""))
    except Exception:
        return False, "OPINION_MISMATCH"
    if str(op.get("prompt_sha256") or "") != reg_sha:
        return False, "OPINION_MISMATCH"
    # Muc 2.4e: model trong chuoi DeepSeek-ONLY dang hieu luc.
    if op.get("model_id") not in deepseek_chain():
        return False, "OPINION_MISMATCH"
    return True, None


def _d2_telemetry(data_root, sandbox: bool, match_id, code: str) -> None:
    """Muc 3.5: counter rieng trong ai_review/telemetry.jsonl — khong bao
    gio raise vao decide path."""
    try:
        from research.papertrade_exec import ai_gate_v2 as G
        d = G.ai_review_dir(Path(data_root), sandbox)
        d.mkdir(parents=True, exist_ok=True)
        rec = {"plane": "sandbox" if sandbox else "real",
               "kind": D2_REFUSAL_EVENT, "outcome": D2_TELEMETRY_OUTCOME,
               "match_id": match_id, "code": code, "counter": "d2_refusals"}
        with open(d / "telemetry.jsonl", "a") as f:
            f.write(json.dumps({"ts_utc": G._now(), **rec},
                               sort_keys=True, default=str) + "\n")
    except Exception:
        pass


def d2_append_decision(led, row: dict, *, data_root=None, args=None,
                       sandbox: bool | None = None, active: bool | None = None,
                       fc_row: dict | None = None,
                       quote_row: dict | None = None,
                       now_utc: str | None = None,
                       **append_kwargs) -> dict:
    """MUC 4 — DIEM GHI DUY NHAT: moi led.append_decision cua desk di qua
    wrapper nay. Hanh vi:
      * row khong phai DECISION+BET_PAPER -> passthrough nguyen byte
        (muc 2.6: cac status khac khong bi kiem; flag OFF cung passthrough).
      * BET_PAPER + binding hop le (muc 2) -> ghi binh thuong.
      * BET_PAPER + binding KHONG hop le -> TU CHOI (muc 3): khong ghi;
        PENDING_AI + last_detail; gate_event dung ma; counter telemetry;
        tra ve marker PENDING_AI (khong phai dong so — chi de caller
        journal khong crash). Caller tuyet doi khong duoc append marker.
    Byte-identical khi flag OFF: active=None -> doc flag tu
    execute.papertrade_flags(args); khong co args -> OFF (luat flag W4:
    OFF = DISABLED, hanh vi giong het truoc D2)."""
    if row.get("type") != "DECISION" or row.get("status") != "BET_PAPER":
        return led.append_decision(row, **append_kwargs)
    if active is None:
        active = False
        if args is not None:
            try:
                from research.papertrade_exec import execute as _E
                active = bool(_E.papertrade_flags(args).get(
                    "d2_gate_invariant_active"))
            except Exception:
                active = False
    if not active:
        return led.append_decision(row, **append_kwargs)
    if sandbox is None:
        sandbox = bool(getattr(args, "sandbox", False))
    ok, code = d2_binding_check(row, data_root, sandbox=sandbox)
    if ok:
        return led.append_decision(row, **append_kwargs)

    # ---------------- MUC 3: TU CHOI (fail-closed) ----------------
    from research.papertrade_exec import ai_gate_v2 as G
    assert code in D2_REFUSAL_CODES      # dung 1 ma trong danh sach spec
    now = now_utc or G._now()
    g = row.get("ai_gate") if isinstance(row.get("ai_gate"), dict) else {}
    chash = g.get("candidate_hash")
    if not (isinstance(chash, str) and chash and set(chash) <= _HEX):
        chash = ""
        try:
            chash = G.candidate_hash_for(row, fc_row, quote_row) or ""
        except Exception:
            chash = ""
    anchor = (row.get("anchor_utc") or (fc_row or {}).get("anchor_utc")
              or "")
    ctx = {"league": row.get("league"), "match_id": row.get("match_id"),
           "home": row.get("home"), "away": row.get("away"),
           "kickoff_utc": row.get("kickoff_utc"),
           "competition": row.get("competition"),
           "chosen_leg": row.get("chosen_leg"),
           "p_frozen": row.get("p_frozen"),
           "odds_frozen": row.get("odds_frozen"),
           "quote_row_sha256": (quote_row or {}).get("row_sha256"),
           "ev_net_by_leg": row.get("ev_net_by_leg"),
           "stake_cents": row.get("stake_cents")}
    try:
        G.pending_marker(Path(data_root), row.get("match_id", ""), chash,
                         anchor, D2_REFUSAL_DETAIL, context=ctx,
                         sandbox=sandbox)
        G.gate_event(Path(data_root), D2_REFUSAL_EVENT, sandbox=sandbox,
                     match_id=row.get("match_id"),
                     candidate_hash=chash or None,
                     code=code,
                     planned_decided_at_utc=now,
                     d2_spec_sha256=D2_SPEC_SHA256)
    except Exception:
        pass                      # khong bao gio lam crash decide path
    _d2_telemetry(data_root, sandbox, row.get("match_id"), code)
    return {"type": "DECISION", "status": "PENDING_AI",
            "match_id": row.get("match_id"), "league": row.get("league"),
            "kickoff_utc": row.get("kickoff_utc"),
            "reason": f"{D2_REFUSAL_DETAIL}: {code}",
            "d2_refused": True, "d2_code": code,
            "stake_cents": 0, "chosen_leg": None}
