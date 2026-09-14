"""Self-contained HTML renderer for the read-only shadow dashboard.

``generate_html(snapshot) -> str`` produces ONE self-contained page:
inline CSS, inline vanilla JS, a hand-rolled SVG equity chart. No CDN,
no external fetch, no third-party asset of any kind. The page is a
pure view: every control is read-only (toggles, filters, sorting,
client-side sanitized exports). It contains no write endpoint, no
order verb and no credential.

Presentation rules (plan section 9):

- the 300,000-USDT top-level account view comes FIRST, no click needed;
- no profit ranking between families and no celebratory labels: the
  dashboard reports evidence, it does not cheer;
- stop-loss / take-profit are always the honest N/A strings plus the
  true frozen exit policy; no stop or target number is ever invented;
- empty states say NOT_RUN / NO_TRADES_YET / UNAVAILABLE, never fake
  zeros;
- red banners for accounting mismatch, stale data, identity drift,
  ledger corruption; green is never emitted by this renderer.
"""

from __future__ import annotations

import html as _html
import json
from typing import Any, Dict, List, Mapping, Optional

from .snapshot import (
    LOCAL_TZ_NAME,
    SL_NA,
    TP_NA,
)

__all__ = ["generate_html"]


def _esc(value: Any) -> str:
    return _html.escape(str(value), quote=True)


def _usdt(value: Any) -> str:
    if value is None:
        return "UNAVAILABLE"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "UNAVAILABLE"
    sign = "-" if number < 0 else ""
    text = f"{abs(number):,.2f}"
    return f"{sign}{text}"


def _pct(value: Any) -> str:
    if value is None:
        return "UNAVAILABLE"
    try:
        return f"{float(value):+.4f}%"
    except (TypeError, ValueError):
        return "UNAVAILABLE"


def _value_or_unavailable(value: Any, kind: str = "usdt") -> str:
    if value is None:
        return "UNAVAILABLE"
    if kind == "pct":
        return _pct(value)
    if kind == "int":
        try:
            return str(int(value))
        except (TypeError, ValueError):
            return "UNAVAILABLE"
    return _usdt(value)


def _payload_json(snapshot: Mapping[str, Any]) -> str:
    text = json.dumps(snapshot, ensure_ascii=False, allow_nan=False)
    # keep the inline <script> safe
    return text.replace("</", "<\\/")


# ----------------------------------------------------------------------
# server-rendered fragments
# ----------------------------------------------------------------------
def _banners_html(snapshot: Mapping[str, Any]) -> str:
    rows = []
    for banner in snapshot.get("banners", []):
        level = banner.get("level", "neutral")
        code = _esc(banner.get("code", ""))
        message = _esc(banner.get("message", ""))
        rows.append(
            f'<div class="banner banner-{_esc(level)}">'
            f'<span class="banner-code">{code}</span>'
            f'<span class="banner-msg">{message}</span></div>'
        )
    return "\n".join(rows)


def _top_view_html(snapshot: Mapping[str, Any]) -> str:
    combined = snapshot.get("combined", {})
    today_hcm = (combined.get("today") or {}).get(LOCAL_TZ_NAME, {})
    today_utc = (combined.get("today") or {}).get("UTC", {})
    counters = snapshot.get("counters", {})
    dd_cur = combined.get("drawdown_current") or {}
    dd_max = combined.get("drawdown_max") or {}

    def today_cell(block: Mapping[str, Any]) -> str:
        status = block.get("status")
        if status == "OK":
            return (
                f"{_usdt(block.get('pnl_usdt'))} USDT "
                f"({_pct(block.get('pnl_pct'))})"
            )
        return f"UNAVAILABLE_FAIL_CLOSED — {_esc(block.get('reason') or 'thiếu mốc giá tại mốc giới hạn')}"

    items = [
        ("Starting virtual capital", "300,000 USDT (3 × 100,000 USDT isolated sleeves)"),
        (
            "Current combined virtual equity",
            f"{_usdt(combined.get('current_equity_usdt'))} USDT"
            f" <span class='ts' data-ts='{_esc(combined.get('current_equity_as_of_utc') or '')}'>"
            f"{_esc(combined.get('current_equity_as_of_utc') or 'UNAVAILABLE')}</span>",
        ),
        (
            f"Today PnL (00:00 {LOCAL_TZ_NAME} → latest mark)",
            today_cell(today_hcm)
            + f"<div class='window-stamps'>window start {_esc(today_hcm.get('window_start_utc') or 'UNAVAILABLE')}"
            f" → end {_esc(today_hcm.get('window_end_utc') or 'UNAVAILABLE')}"
            f"; boundary mark {_esc(today_hcm.get('boundary_mark_ts') or today_hcm.get('boundary_mark_required_at') or 'UNAVAILABLE')}</div>",
        ),
        (
            "Today PnL (00:00 UTC → latest mark)",
            today_cell(today_utc)
            + f"<div class='window-stamps'>window start {_esc(today_utc.get('window_start_utc') or 'UNAVAILABLE')}"
            f" → end {_esc(today_utc.get('window_end_utc') or 'UNAVAILABLE')}</div>",
        ),
        (
            "Total PnL since SHADOW_START_UTC",
            f"{_usdt(combined.get('total_pnl_usdt'))} USDT ({_pct(combined.get('total_pnl_pct'))})"
            f" <span class='muted'>anchor: {_esc(snapshot.get('shadow_start_utc') or 'UNAVAILABLE')}</span>",
        ),
        (
            "Realized / unrealized PnL (sleeves, fill-level evidence)",
            f"realized {_usdt(_sum_field(snapshot, 'realized_pnl_usdt'))} USDT / unrealized "
            f"{_usdt(_sum_field(snapshot, 'unrealized_pnl_usdt'))} USDT",
        ),
        (
            "Fees / slippage / funding (sleeve books)",
            f"fees {_usdt(_sum_field(snapshot, 'fees_usdt'))} / slippage "
            f"{_usdt(_sum_field(snapshot, 'slippage_usdt'))} / funding "
            f"{_usdt(_sum_field(snapshot, 'funding_usdt'))} USDT",
        ),
        (
            "Current gross / net / BTC-beta exposure (combined evidence per sleeve)",
            "per-sleeve values below (combined gross/net/beta are reported "
            "per isolated sleeve; no cross-sleeve netting)",
        ),
        (
            "Maximum drawdown (combined)",
            f"{_usdt(dd_max.get('drawdown_abs'))} USDT ({_pct(dd_max.get('drawdown_pct'))});"
            f" current {_usdt(dd_cur.get('drawdown_abs'))} USDT ({_pct(dd_cur.get('drawdown_pct'))})",
        ),
        (
            "Open positions / fills today / all virtual fills",
            f"{_value_or_unavailable(_sum_field(snapshot, 'open_position_count'), 'int')} / "
            f"{_value_or_unavailable(_sum_field(snapshot, 'fills_today'), 'int')} / "
            f"{_value_or_unavailable(_sum_field(snapshot, 'fills_total'), 'int')}",
        ),
        (
            "Last successful update / data freshness / system status",
            f"generated <span class='ts' data-ts='{_esc(snapshot.get('generated_utc') or '')}'>"
            f"{_esc(snapshot.get('generated_utc') or 'UNAVAILABLE')}</span>"
            f" · system status {_esc(snapshot.get('system_status') or 'UNAVAILABLE')}"
            f" · scheduler heartbeat: last completed "
            f"<span class='ts' data-ts='{_esc(((snapshot.get('scheduler_heartbeat') or {}).get('last_completed_event') or {}).get('scheduled_decision_utc') or '')}'>"
            f"{_esc(((snapshot.get('scheduler_heartbeat') or {}).get('last_completed_event') or {}).get('scheduled_decision_utc') or 'UNAVAILABLE')}</span>",
        ),
        (
            "SEPARATE counters (never conflated)",
            f"decisions {_value_or_unavailable(counters.get('decision_count'), 'int')} ·"
            f" order intents {_value_or_unavailable(counters.get('order_intent_count'), 'int')} ·"
            f" virtual fills {_value_or_unavailable(counters.get('fill_count'), 'int')} ·"
            f" closed positions {_value_or_unavailable(counters.get('closed_position_count'), 'int')}",
        ),
    ]
    rows = "\n".join(
        f"<div class='kv-row'><div class='kv-label'>{_esc(label)}</div>"
        f"<div class='kv-value'>{value_html}</div></div>"
        for label, value_html in items
    )
    return f"<div class='kv'>{rows}</div>"


def _sum_field(snapshot: Mapping[str, Any], key: str) -> Optional[float]:
    total = 0.0
    seen = False
    for block in snapshot.get("families", {}).values():
        value = block.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            total += float(value)
            seen = True
        elif value is not None and key.endswith("_count") and isinstance(value, (int, float)):
            total += float(value)
            seen = True
    return total if seen else None


def _family_card(block: Mapping[str, Any]) -> str:
    fid = _esc(block.get("family_id", ""))
    today = (block.get("today") or {}).get(LOCAL_TZ_NAME, {})
    dd_cur = block.get("drawdown_current") or {}
    dd_max = block.get("drawdown_max") or {}
    counters = block.get("counters", {})
    open_positions = block.get("open_positions") or {}

    if today.get("status") == "OK":
        today_html = (
            f"{_usdt(today.get('pnl_usdt'))} USDT ({_pct(today.get('pnl_pct'))})"
            f"<div class='window-stamps'>{_esc(today.get('window_start_utc'))} → {_esc(today.get('window_end_utc'))}</div>"
        )
    else:
        today_html = (
            "<span class='gap-text'>UNAVAILABLE_FAIL_CLOSED</span>"
            f"<div class='window-stamps'>{_esc((today.get('reason') or '')[:180])}</div>"
        )

    pos_html = (
        ", ".join(
            f"{_esc(sym)} ({'long' if qty > 0 else 'short'} {abs(qty):g})"
            for sym, qty in sorted(open_positions.items())
        )
        or "none open"
    )
    status = _esc(block.get("status", "NOT_RUN"))
    return f"""
    <div class="card" id="card-{fid}">
      <div class="card-head">
        <span class="family-id">{fid}</span>
        <span class="chip chip-{status}">{status}</span>
      </div>
      <div class="card-sub">{_esc(block.get('identity', {}).get('historical_verdict_label') or 'UNAVAILABLE')}
        <span class="muted">· frozen historical verdict label (NOT rewritable)</span></div>
      <div class="card-equity">{_usdt(block.get('current_equity_usdt'))} <span class="muted">USDT</span>
        <span class="muted">as of <span class='ts' data-ts='{_esc(block.get('equity_as_of_utc') or '')}'>{_esc(block.get('equity_as_of_utc') or 'UNAVAILABLE')}</span></span></div>
      <div class="card-grid">
        <div>Today PnL (00:00 {LOCAL_TZ_NAME})<br><b>{today_html}</b></div>
        <div>Total PnL<br><b>{_usdt(block.get('total_pnl_usdt'))} USDT ({_pct(block.get('total_pnl_pct'))})</b></div>
        <div>Realized / unrealized<br><b>{_usdt(block.get('realized_pnl_usdt'))} / {_usdt(block.get('unrealized_pnl_usdt'))} USDT</b></div>
        <div>Fees / slippage / funding<br><b>{_usdt(block.get('fees_usdt'))} / {_usdt(block.get('slippage_usdt'))} / {_usdt(block.get('funding_usdt'))} USDT</b></div>
        <div>Fills today / since activation<br><b>{_value_or_unavailable(block.get('fills_today'), 'int')} / {_value_or_unavailable(block.get('fills_total'), 'int')}</b></div>
        <div>Open positions<br><b>{_value_or_unavailable(block.get('open_position_count'), 'int')}</b> <span class="muted">{pos_html}</span></div>
        <div>Winning / losing closed fills<br><b>{_value_or_unavailable(block.get('win_count'), 'int')} / {_value_or_unavailable(block.get('lose_count'), 'int')}</b>
          <span class="muted">measured from fill-level realized PnL only</span></div>
        <div>Blocked decisions<br><b>{_value_or_unavailable(block.get('blocked_decisions'), 'int')}</b></div>
        <div>Gross / net / BTC-beta<br><b>{_value_or_unavailable(block.get('gross'))} / {_value_or_unavailable(block.get('net'))} / {_value_or_unavailable(block.get('btc_beta'))}</b></div>
        <div>Drawdown current / max<br><b>{_usdt(dd_cur.get('drawdown_abs'))} ({_pct(dd_cur.get('drawdown_pct'))}) / {_usdt(dd_max.get('drawdown_abs'))} ({_pct(dd_max.get('drawdown_pct'))})</b></div>
        <div>Last signal / last fill / next decision<br>
          <b><span class='ts' data-ts='{_esc(block.get('last_signal_utc') or '')}'>{_esc(block.get('last_signal_utc') or 'UNAVAILABLE')}</span> /
          <span class='ts' data-ts='{_esc(block.get('last_fill_utc') or '')}'>{_esc(block.get('last_fill_utc') or 'UNAVAILABLE')}</span> /
          <span class='ts' data-ts='{_esc(block.get('next_decision_utc') or '')}'>{_esc(block.get('next_decision_utc') or 'UNAVAILABLE')}</span></b></div>
        <div>Counters (separate)<br><b>d {_value_or_unavailable(counters.get('decision_count'), 'int')} ·
          oi {_value_or_unavailable(counters.get('order_intent_count'), 'int')} ·
          f {_value_or_unavailable(counters.get('fill_count'), 'int')} ·
          cp {_value_or_unavailable(counters.get('closed_position_count'), 'int')}</b></div>
      </div>
      <div class="card-status">{_esc(block.get('status_reason_vi') or '')}</div>
      <div class="card-source muted">ledger digest <code>{_esc((block.get('ledger_digest') or 'UNAVAILABLE')[:16])}…</code>
        · source ts <span class='ts' data-ts='{_esc((block.get('source') or {}).get('as_of_utc') or '')}'>{_esc((block.get('source') or {}).get('as_of_utc') or 'UNAVAILABLE')}</span>
        · data age {_value_or_unavailable(block.get('data_age_seconds'))} s · exit policy: {_esc(block.get('exit_policy') or 'UNAVAILABLE')}</div>
    </div>"""


def _comparison_html(snapshot: Mapping[str, Any]) -> str:
    head = (
        "<tr><th>family</th><th>equity</th><th>today PnL</th><th>total PnL</th>"
        "<th>realized</th><th>unrealized</th><th>fees</th><th>slippage</th><th>funding</th>"
        "<th>fills today</th><th>fills total</th><th>open</th><th>blocked</th>"
        "<th>gross</th><th>net</th><th>btc_beta</th><th>dd now</th><th>dd max</th>"
        "<th>status</th><th>verdict label (frozen)</th><th>exit policy</th></tr>"
    )
    rows = []
    for fid, block in sorted(snapshot.get("families", {}).items()):
        today = (block.get("today") or {}).get(LOCAL_TZ_NAME, {})
        dd_cur = block.get("drawdown_current") or {}
        dd_max = block.get("drawdown_max") or {}
        today_txt = (
            _usdt(today.get("pnl_usdt"))
            if today.get("status") == "OK"
            else "UNAVAILABLE_FAIL_CLOSED"
        )
        rows.append(
            "<tr>"
            f"<td>{_esc(fid)}</td>"
            f"<td>{_usdt(block.get('current_equity_usdt'))}</td>"
            f"<td>{today_txt}</td>"
            f"<td>{_usdt(block.get('total_pnl_usdt'))} ({_pct(block.get('total_pnl_pct'))})</td>"
            f"<td>{_usdt(block.get('realized_pnl_usdt'))}</td>"
            f"<td>{_usdt(block.get('unrealized_pnl_usdt'))}</td>"
            f"<td>{_usdt(block.get('fees_usdt'))}</td>"
            f"<td>{_usdt(block.get('slippage_usdt'))}</td>"
            f"<td>{_usdt(block.get('funding_usdt'))}</td>"
            f"<td>{_value_or_unavailable(block.get('fills_today'), 'int')}</td>"
            f"<td>{_value_or_unavailable(block.get('fills_total'), 'int')}</td>"
            f"<td>{_value_or_unavailable(block.get('open_position_count'), 'int')}</td>"
            f"<td>{_value_or_unavailable(block.get('blocked_decisions'), 'int')}</td>"
            f"<td>{_value_or_unavailable(block.get('gross'))}</td>"
            f"<td>{_value_or_unavailable(block.get('net'))}</td>"
            f"<td>{_value_or_unavailable(block.get('btc_beta'))}</td>"
            f"<td>{_pct(dd_cur.get('drawdown_pct'))}</td>"
            f"<td>{_pct(dd_max.get('drawdown_pct'))}</td>"
            f"<td>{_esc(block.get('status'))}</td>"
            f"<td>{_esc(block.get('historical_verdict_label') or 'UNAVAILABLE')}</td>"
            f"<td>{_esc(block.get('exit_policy') or 'UNAVAILABLE')}</td>"
            "</tr>"
        )
    return (
        "<table class='compare'><thead>" + head + "</thead><tbody>"
        + "\n".join(rows)
        + "</tbody></table>"
    )


def _identity_html(snapshot: Mapping[str, Any]) -> str:
    identity = snapshot.get("identity", {})
    rows = []
    for fid, meta in sorted(identity.get("families", {}).items()):
        rows.append(
            "<tr>"
            f"<td>{_esc(fid)}</td>"
            f"<td>{_esc(meta.get('historical_family_id') or 'UNAVAILABLE')}</td>"
            f"<td class='verdict'>{_esc(meta.get('historical_verdict_label') or 'UNAVAILABLE')}</td>"
            f"<td>{_esc(meta.get('exit_policy') or 'UNAVAILABLE')}</td>"
            f"<td>{_esc(meta.get('manifest_entry_found'))}</td>"
            "</tr>"
        )
    policy = _esc(identity.get("verdict_labels_policy") or "verdict-labels policy: NOT_RUN (manifest not supplied)")
    return f"""
    <p class="muted">{policy}</p>
    <p>stop_loss_price: <b>{_esc(SL_NA)}</b><br>
       take_profit_price: <b>{_esc(TP_NA)}</b></p>
    <p class="muted">Không bao giờ tự bịa số stop/target. Nếu tương lai có SL/TP thì
       đó là một danh tính chiến lược MỚI và không thể viết lại lịch sử shadow này.
       "Distance to risk cap" (nếu hiển thị) chỉ là chẩn đoán, không phải lệnh.</p>
    <table class="compare identity-table"><thead>
      <tr><th>family</th><th>historical family</th><th>frozen verdict label</th>
      <th>exit policy (frozen adapter string)</th><th>manifest entry matched</th></tr>
    </thead><tbody>{''.join(rows)}</tbody></table>"""


# ----------------------------------------------------------------------
# page template (placeholders replaced; braces safe for CSS/JS)
# ----------------------------------------------------------------------
_TEMPLATE = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PROSPECTIVE-SHADOW-V1 — read-only owner dashboard</title>
<style>
:root {
  --bg: #101418; --panel: #171d24; --panel2: #1d252e; --line: #2a3441;
  --text: #dfe7ee; --muted: #8fa1b3; --red: #e5484d; --amber: #f5a524;
  --blue: #4c8dff; --teal: #2dd4bf; --violet: #a78bfa; --pink: #f472b6;
  --green-ok: #46a758;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text);
  font: 14px/1.45 -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
.wrap { max-width: 1280px; margin: 0 auto; padding: 16px; }
h1 { font-size: 20px; margin: 0 0 4px; }
h2 { font-size: 16px; margin: 28px 0 8px; border-bottom: 1px solid var(--line); padding-bottom: 6px; }
.muted { color: var(--muted); font-weight: 400; font-size: 12px; }
code { background: var(--panel2); padding: 1px 4px; border-radius: 4px; }
.banner { display: flex; gap: 10px; padding: 10px 12px; border-radius: 8px; margin: 8px 0;
  border: 1px solid var(--line); align-items: baseline; flex-wrap: wrap; }
.banner-red { background: rgba(229,72,77,.12); border-color: var(--red); }
.banner-neutral { background: rgba(245,165,36,.08); border-color: var(--amber); }
.banner-code { font-weight: 700; font-family: ui-monospace, monospace; }
.banner-red .banner-code { color: var(--red); }
.banner-neutral .banner-code { color: var(--amber); }
.chip { padding: 2px 8px; border-radius: 999px; font-size: 12px; border: 1px solid var(--line); }
.chip-RUNNING { color: var(--teal); border-color: var(--teal); }
.chip-STALE, .chip-DATA_BLOCKED, .chip-RISK_BLOCKED { color: var(--amber); border-color: var(--amber); }
.chip-STOPPED { color: var(--red); border-color: var(--red); }
.chip-NOT_RUN { color: var(--muted); }
.kv { border: 1px solid var(--line); border-radius: 10px; overflow: hidden; }
.kv-row { display: grid; grid-template-columns: minmax(220px, 34%) 1fr; gap: 10px;
  padding: 9px 12px; border-bottom: 1px solid var(--line); background: var(--panel); }
.kv-row:nth-child(odd) { background: var(--panel2); }
.kv-row:last-child { border-bottom: 0; }
.kv-label { color: var(--muted); }
.kv-value b { font-family: ui-monospace, monospace; }
.window-stamps { color: var(--muted); font-size: 11px; font-family: ui-monospace, monospace; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 12px; }
.card { border: 1px solid var(--line); background: var(--panel); border-radius: 10px; padding: 12px; }
.card-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.family-id { font-weight: 700; font-family: ui-monospace, monospace; }
.card-sub { color: var(--violet); font-size: 12px; margin: 2px 0 6px; }
.card-equity { font-size: 20px; font-weight: 700; font-family: ui-monospace, monospace; margin-bottom: 8px; }
.card-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12px; }
.card-grid > div { border: 1px solid var(--line); border-radius: 8px; padding: 6px 8px; background: var(--panel2); }
.card-status { margin-top: 8px; font-size: 12px; color: var(--amber); }
.card-source { margin-top: 6px; font-size: 11px; }
table.compare { width: 100%; border-collapse: collapse; font-size: 12px; display: block; overflow-x: auto; }
.compare th, .compare td { border: 1px solid var(--line); padding: 5px 7px; text-align: left; white-space: nowrap; }
.compare th { background: var(--panel2); position: sticky; top: 0; }
.verdict { color: var(--violet); font-family: ui-monospace, monospace; }
.controls { display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0; align-items: center; }
button, select, input { background: var(--panel2); color: var(--text); border: 1px solid var(--line);
  border-radius: 7px; padding: 5px 9px; font-size: 12px; }
button.active { border-color: var(--blue); color: var(--blue); }
button:hover { border-color: var(--muted); }
#chart-box { border: 1px solid var(--line); border-radius: 10px; background: var(--panel); padding: 8px; }
#chart-box svg { width: 100%; height: auto; display: block; }
#tooltip { position: fixed; pointer-events: none; display: none; z-index: 50;
  background: #0b0e12ee; border: 1px solid var(--line); border-radius: 8px; padding: 8px 10px;
  font-size: 12px; font-family: ui-monospace, monospace; max-width: 460px; }
.legend { display: flex; gap: 14px; flex-wrap: wrap; font-size: 12px; margin-top: 6px; }
.sw { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 4px; }
.gap-text { color: var(--red); font-family: ui-monospace, monospace; }
.empty-state { border: 1px dashed var(--line); color: var(--muted); border-radius: 10px;
  padding: 18px; text-align: center; margin: 10px 0; }
.table-scroll { max-height: 560px; overflow: auto; border: 1px solid var(--line); border-radius: 10px; }
#trades-table { width: 100%; border-collapse: collapse; font-size: 12px; }
#trades-table th { position: sticky; top: 0; background: var(--panel2); cursor: pointer; }
#trades-table th, #trades-table td { border-bottom: 1px solid var(--line); padding: 5px 7px; white-space: nowrap; }
#trades-table tr.rowline { cursor: pointer; }
#trades-table tr.rowline:hover { background: var(--panel2); }
.status-open { color: var(--teal); } .status-closed { color: var(--muted); }
#drawer { position: fixed; top: 0; right: -720px; width: 700px; max-width: 96vw; height: 100vh;
  background: var(--panel); border-left: 1px solid var(--line); z-index: 100; transition: right .18s ease;
  overflow-y: auto; padding: 16px; }
#drawer.open { right: 0; }
#drawer h3 { margin-top: 0; }
.drawer-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 12px; }
.drawer-grid > div { border: 1px solid var(--line); border-radius: 8px; padding: 6px 8px; background: var(--panel2); }
.drawer-full { grid-column: 1 / -1; }
pre.rawfill { font-size: 11px; overflow-x: auto; border: 1px solid var(--line); border-radius: 8px; padding: 8px; background: #0b0e12; }
footer { margin: 30px 0 10px; color: var(--muted); font-size: 12px; border-top: 1px solid var(--line); padding-top: 10px; }
.honesty { border: 1px solid var(--line); background: var(--panel); border-radius: 10px; padding: 12px; }
@media (max-width: 720px) {
  .kv-row { grid-template-columns: 1fr; }
  .card-grid { grid-template-columns: 1fr; }
  .drawer-grid { grid-template-columns: 1fr; }
}
</style>
</head>
<body>
<div class="wrap">
  <h1>PROSPECTIVE-SHADOW-V1 — bảng điều khiển chủ sở hữu (chỉ đọc)</h1>
  <p class="muted">Read-only view over append-only shadow ledgers · generated
  <span class="ts" data-ts="__GENERATED__">__GENERATED__</span> · system status:
  <b>__SYSTEM_STATUS__</b> · timezone toggle:
  <button id="tz-toggle" type="button">show UTC</button>
  (mặc định hiển thị theo __LOCAL_TZ__ 00:00 cho "hôm nay")</p>
  <div id="banners">__BANNERS__</div>

  <h2>1. Tổng tài khoản 300,000 USDT (xem trước, không cần bấm)</h2>
  __TOP_VIEW__

  <h2>2. Biểu đồ vốn sở kinh hợp nhất — điểm đầu đúng 300,000 USDT</h2>
  <div class="controls">
    <span class="muted">range:</span>
    <button data-range="1D" type="button">1D</button>
    <button data-range="7D" type="button">7D</button>
    <button data-range="30D" type="button">30D</button>
    <button data-range="13W" type="button">13W</button>
    <button data-range="26W" type="button">26W</button>
    <button data-range="ALL" type="button" class="active">ALL</button>
    <span class="muted">sleeves:</span>
    <button id="tg-s0" type="button" class="active">sleeve 1</button>
    <button id="tg-s1" type="button" class="active">sleeve 2</button>
    <button id="tg-s2" type="button" class="active">sleeve 3</button>
    <button id="tg-combined" type="button" class="active">combined</button>
    <button id="tg-norm" type="button">normalized return %</button>
    <button id="tg-dd" type="button">drawdown</button>
  </div>
  <div id="chart-box"></div>
  <div id="tooltip"></div>
  <div class="legend">
    <span><span class="sw" style="background:var(--blue)"></span>combined equity (USDT)</span>
    <span><span class="sw" style="background:var(--teal)"></span>sleeve 1</span>
    <span><span class="sw" style="background:var(--amber)"></span>sleeve 2</span>
    <span><span class="sw" style="background:var(--pink)"></span>sleeve 3</span>
    <span><span class="sw" style="background:var(--muted)"></span>baseline 300,000</span>
    <span><span class="sw" style="background:var(--red)"></span>gap: UNAVAILABLE_FAIL_CLOSED (line broken — không nội suy)</span>
    <span>▲ entry</span><span>▼ exit</span><span>■ blocked</span><span>◆ cost-regime boundary</span><span>● incident</span>
  </div>

  <h2>3. Thẻ họ chiến lược + bảng so sánh</h2>
  <p class="muted">Không xếp hạng theo lợi nhuận, không nhãn ăn mừng: bảng chỉ báo cáo
  bằng chứng. Không thay đổi phân bổ hay trạng thái nghiên cứu.</p>
  <div class="cards">__CARDS__</div>
  __COMPARE__

  <h2>4. Bộ đếm bốn loại (không bao giờ gộp chung)</h2>
  __COUNTERS__

  <h2>5. Bảng lệnh / giao dịch ảo (mỗi dòng = một virtual fill)</h2>
  <div class="controls">
    <input id="f-search" type="search" placeholder="tìm kiếm (mọi cột)…">
    <select id="f-family"><option value="">family: all</option>__FAMILY_OPTIONS__</select>
    <input id="f-asset" type="text" placeholder="asset (ví dụ BTCUSDT)">
    <select id="f-side"><option value="">side: all</option><option>buy</option><option>sell</option></select>
    <select id="f-status"><option value="">status: all</option><option>open</option><option>closed</option><option>unknown</option></select>
    <select id="f-eventstatus"><option value="">event status: all</option>
      <option>OK</option><option>UNAVAILABLE_FAIL_CLOSED</option></select>
    <label class="muted">from <input id="f-from" type="date"></label>
    <label class="muted">to <input id="f-to" type="date"></label>
    <button id="btn-export-csv" type="button">export CSV (bảng đang lọc)</button>
    <button id="btn-export-json" type="button">export JSON (bảng đang lọc)</button>
    <button id="btn-export-equity" type="button">export JSON (equity series)</button>
  </div>
  __EMPTY_STATE__
  <div class="table-scroll">
  <table id="trades-table"><thead id="trades-head"></thead><tbody id="trades-body"></tbody></table>
  </div>
  <p class="muted">Export là dạng xem đã làm sạch phía client; KHÔNG phải authority
  over the ledgers; không chứa credential. stop_loss_price/take_profit_price luôn là
  "N/A" đúng như hợp đồng — không bao giờ bịa số stop/target.</p>

  <h2>6. Danh tính đã đóng băng + tính trung thực SL/TP</h2>
  <div class="honesty">__IDENTITY__</div>

  <footer>
    <div>Read-only: dashboard KHÔNG thể ghi lại giao dịch, vốn hay verdict; KHÔNG có
    endpoint ghi và KHÔNG có khả năng đặt lệnh. GET/HEAD only; mọi method khác → 405.</div>
    <div>Scheduler heartbeat: __HEARTBEAT__</div>
    <div>Identity status: __IDENTITY_STATUS__ · accounting: __ACCOUNTING__ ·
      browser render check: NOT_RUN_CONTROLLER_Q_PHASE (bằng chứng hình ảnh được ghi
      nhận ở phím Q của controller, không ở lane này).</div>
    <div>Reproduction status: NOT_RUN (dashboard không tự chạy reproduction; xem báo cáo control).</div>
    <div>Mọi số liệu mang source timestamp + ledger digest; thiếu input ⇒
      NOT_RUN / NO_TRADES_YET / UNAVAILABLE — không bao giờ là số 0 giả.</div>
  </footer>
</div>

<div id="drawer"><div id="drawer-content"></div></div>

<script id="shv1-payload" type="application/json">__PAYLOAD__</script>
<script>
"use strict";
var PAYLOAD = JSON.parse(document.getElementById("shv1-payload").textContent);
var LOCAL_TZ_NAME = "__LOCAL_TZ__";
var tzMode = "local"; // "local" | "utc"
var STATE = { range: "ALL", sleeves: [true, true, true], combined: true,
              norm: false, dd: false, sortKey: null, sortDir: 1 };

function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
  });
}
function parseTs(s) { return s ? new Date(s) : null; }
function fmtTs(s) {
  var d = parseTs(s);
  if (!d || isNaN(d.getTime())) return "UNAVAILABLE";
  if (tzMode === "utc") {
    return d.toISOString().replace("T", " ").replace(".000Z", "Z");
  }
  var loc = new Date(d.getTime() + 7 * 3600 * 1000);
  return loc.toISOString().replace("T", " ").replace(".000Z", "Z") + " ICT";
}
function applyTz() {
  document.querySelectorAll(".ts").forEach(function (el) {
    el.textContent = fmtTs(el.getAttribute("data-ts"));
  });
  drawChart();
  renderTable();
}
var tzBtn = document.getElementById("tz-toggle");
tzBtn.addEventListener("click", function () {
  tzMode = tzMode === "local" ? "utc" : "local";
  tzBtn.textContent = tzMode === "local" ? "show UTC" : ("show " + LOCAL_TZ_NAME);
  applyTz();
});
function num(v, d) {
  if (v == null || isNaN(v)) return "UNAVAILABLE";
  return Number(v).toLocaleString("en-US", { minimumFractionDigits: d == null ? 2 : d, maximumFractionDigits: d == null ? 2 : d });
}
function signed(v, d) {
  if (v == null || isNaN(v)) return "UNAVAILABLE";
  return (v > 0 ? "+" : "") + num(v, d);
}

/* ---------------- equity chart (hand-rolled SVG) ---------------- */
var NS = "http://www.w3.org/2000/svg";
var RANGE_SPANS = { "1D": 864e5, "7D": 7 * 864e5, "30D": 30 * 864e5, "13W": 91 * 864e5, "26W": 182 * 864e5, "ALL": null };
var SLEEVE_COLORS = ["#2dd4bf", "#f5a524", "#f472b6"];
function el(name, attrs) {
  var node = document.createElementNS(NS, name);
  for (var k in attrs || {}) node.setAttribute(k, attrs[k]);
  return node;
}
function chartData() {
  var pts = (PAYLOAD.combined || {}).chart_points || [];
  var now = parseTs(PAYLOAD.now_utc || PAYLOAD.generated_utc) || new Date();
  var span = RANGE_SPANS[STATE.range];
  if (span) {
    var cutoff = now.getTime() - span;
    pts = pts.filter(function (p) { var d = parseTs(p.ts); return d && d.getTime() >= cutoff; });
  }
  return pts;
}
function sleeveSeries() {
  var fams = Object.keys(PAYLOAD.families || {}).sort();
  var now = parseTs(PAYLOAD.now_utc || PAYLOAD.generated_utc) || new Date();
  var span = RANGE_SPANS[STATE.range];
  return fams.map(function (fid, i) {
    var pts = PAYLOAD.families[fid].chart_points || [];
    if (span) pts = pts.filter(function (p) { var d = parseTs(p.ts); return d && d.getTime() >= now.getTime() - span; });
    return { fid: fid, idx: i, points: pts };
  });
}
function drawChart() {
  var box = document.getElementById("chart-box");
  box.innerHTML = "";
  var pts = chartData();
  if (!pts.length) {
    box.innerHTML = "<div class='empty-state'>NO_TRADES_YET — chưa có dữ liệu biểu đồ "
      + "(pre-activation: mọi giá trị NOT_RUN/UNAVAILABLE, không có điểm 0 giả).</div>";
    return;
  }
  var W = 1160, H = 420, padL = 74, padR = 16, padT = 16, padB = 42;
  var ddH = STATE.dd ? 110 : 0, gapMain = STATE.dd ? (H - padB - 20) : (H - padB);
  var times = pts.map(function (p) { return parseTs(p.ts).getTime(); });
  var tMin = Math.min.apply(null, times), tMax = Math.max.apply(null, times);
  if (tMax === tMin) tMax = tMin + 1;
  var base = PAYLOAD.combined.baseline_usdt || 300000;
  var vals = [];
  pts.forEach(function (p) { if (p.status === "OK" && p.equity != null) vals.push(STATE.norm ? (p.equity / base - 1) * 100 : p.equity); });
  if (!vals.length) vals = [0, 1];
  var vMin = Math.min.apply(null, vals), vMax = Math.max.apply(null, vals);
  if (!STATE.norm) { vMin = Math.min(vMin, base); vMax = Math.max(vMax, base); }
  else { vMin = Math.min(vMin, 0); vMax = Math.max(vMax, 0); }
  if (vMax === vMin) { vMax += 1; vMin -= 1; }
  var pad = (vMax - vMin) * 0.06; vMin -= pad; vMax += pad;
  function X(t) { return padL + (t - tMin) / (tMax - tMin) * (W - padL - padR); }
  function Y(v) { return padT + (vMax - v) / (vMax - vMin) * (gapMain - padT); }
  var svg = el("svg", { viewBox: "0 0 " + W + " " + H, role: "img",
    "aria-label": "combined equity chart starting at 300,000 USDT" });

  // gridlines + y labels
  for (var g = 0; g <= 4; g++) {
    var v = vMin + (vMax - vMin) * g / 4;
    svg.appendChild(el("line", { x1: padL, x2: W - padR, y1: Y(v), y2: Y(v), stroke: "#2a3441", "stroke-width": 1 }));
    var lbl = el("text", { x: padL - 6, y: Y(v) + 4, "text-anchor": "end", fill: "#8fa1b3", "font-size": 11 });
    lbl.textContent = STATE.norm ? (v.toFixed(2) + "%") : num(v, 0);
    svg.appendChild(lbl);
  }
  // x labels
  for (var gx = 0; gx <= 4; gx++) {
    var t = tMin + (tMax - tMin) * gx / 4;
    var xl = el("text", { x: X(t), y: gapMain + 18, "text-anchor": "middle", fill: "#8fa1b3", "font-size": 11 });
    xl.textContent = fmtTs(new Date(t).toISOString()).slice(0, 16);
    svg.appendChild(xl);
  }
  // baseline at 300,000 (or 0% normalized)
  var baseV = STATE.norm ? 0 : base;
  svg.appendChild(el("line", { x1: padL, x2: W - padR, y1: Y(baseV), y2: Y(baseV),
    stroke: "#8fa1b3", "stroke-dasharray": "6 5", "stroke-width": 1 }));
  var bl = el("text", { x: W - padR - 4, y: Y(baseV) - 5, "text-anchor": "end", fill: "#8fa1b3", "font-size": 11 });
  bl.textContent = STATE.norm ? "baseline 0%" : "baseline 300,000 USDT";
  svg.appendChild(bl);

  // combined line with VISIBLE gaps (line broken at UNAVAILABLE intervals)
  var dPath = "", penDown = false, gapIdx = 0;
  pts.forEach(function (p) {
    var x = X(parseTs(p.ts).getTime());
    if (p.status === "OK" && p.equity != null) {
      var v = STATE.norm ? (p.equity / base - 1) * 100 : p.equity;
      var y = Y(v);
      dPath += (penDown ? " L " : " M ") + x.toFixed(1) + " " + y.toFixed(1);
      penDown = true;
    } else {
      penDown = false;
      svg.appendChild(el("circle", { cx: x, cy: gapMain - 8, r: 4, fill: "#e5484d" }));
      if (gapIdx < 6) {
        var gl = el("text", { x: x, y: padT + 10 + 0, "text-anchor": "middle", fill: "#e5484d", "font-size": 10 });
        gl.textContent = "GAP";
        svg.appendChild(gl);
      }
      gapIdx++;
    }
  });
  svg.appendChild(el("path", { d: dPath, fill: "none", stroke: "#4c8dff", "stroke-width": 2 }));

  // sleeve lines
  sleeveSeries().forEach(function (s) {
    if (!STATE.sleeves[s.idx % 3]) return;
    var d = "", down = false;
    s.points.forEach(function (p) {
      if (p.status === "OK" && p.equity != null) {
        var v = STATE.norm ? (p.equity / (base / 3) - 1) * 100 : p.equity;
        d += (down ? " L " : " M ") + X(parseTs(p.ts).getTime()).toFixed(1) + " " + Y(v).toFixed(1);
        down = true;
      } else down = false;
    });
    svg.appendChild(el("path", { d: d, fill: "none", stroke: SLEEVE_COLORS[s.idx % 3],
      "stroke-width": 1.2, opacity: 0.85 }));
  });

  // markers
  ((PAYLOAD.markers) || []).forEach(function (m) {
    var d = parseTs(m.ts);
    if (!d) return;
    var x = X(d.getTime());
    if (x < padL || x > W - padR) return;
    var color = { entry: "#2dd4bf", exit: "#8fa1b3", blocked: "#f5a524",
                  cost_regime_boundary: "#a78bfa", incident: "#e5484d" }[m.kind] || "#8fa1b3";
    var y = padT + 24;
    var shape;
    if (m.kind === "entry") shape = el("path", { d: "M " + x + " " + (y + 5) + " l 5 8 l -10 0 Z", fill: color });
    else if (m.kind === "exit") shape = el("path", { d: "M " + x + " " + (y + 13) + " l 5 -8 l -10 0 Z", fill: color });
    else if (m.kind === "blocked") shape = el("rect", { x: x - 4, y: y, width: 8, height: 8, fill: color });
    else if (m.kind === "cost_regime_boundary") shape = el("path", { d: "M " + x + " " + y + " l 4 6 l -4 6 l -4 -6 Z", fill: color });
    else shape = el("circle", { cx: x, cy: y + 4, r: 4, fill: color });
    var title = el("title", {});
    title.textContent = m.kind + ": " + (m.label || "") + " @ " + fmtTs(m.ts);
    shape.appendChild(title);
    svg.appendChild(shape);
  });

  // drawdown subplot
  if (STATE.dd) {
    var ddTop = H - padB + 8;
    var ddSeries = (PAYLOAD.combined || {}).drawdown_series || [];
    var okDd = ddSeries.filter(function (p) { return p.status === "OK" && p.drawdown_pct != null; });
    if (okDd.length) {
      var dMax = 0;
      okDd.forEach(function (p) { dMax = Math.max(dMax, p.drawdown_pct); });
      dMax = Math.max(dMax, 0.5);
      function Yd(v) { return ddTop + (v / dMax) * (padB - 16); }
      svg.appendChild(el("line", { x1: padL, x2: W - padR, y1: ddTop, y2: ddTop, stroke: "#2a3441" }));
      var dPath2 = "", dDown = false;
      ddSeries.forEach(function (p) {
        var x = X(parseTs(p.ts).getTime());
        if (p.status === "OK" && p.drawdown_pct != null) {
          dPath2 += (dDown ? " L " : " M ") + x.toFixed(1) + " " + Yd(p.drawdown_pct).toFixed(1);
          dDown = true;
        } else dDown = false;
      });
      svg.appendChild(el("path", { d: dPath2, fill: "none", stroke: "#e5484d", "stroke-width": 1.4 }));
      var ddl = el("text", { x: padL - 6, y: ddTop + 12, "text-anchor": "end", fill: "#e5484d", "font-size": 10 });
      ddl.textContent = "dd%";
      svg.appendChild(ddl);
    }
  }

  // hover hit layer
  var hit = el("rect", { x: padL, y: padT, width: W - padL - padR, height: gapMain - padT, fill: "transparent" });
  hit.addEventListener("mousemove", function (ev) { showTip(ev, pts, base); });
  hit.addEventListener("mouseleave", hideTip);
  svg.appendChild(hit);
  box.appendChild(svg);
}
function nearestPoint(pts, t) {
  var best = null, bestDist = Infinity;
  pts.forEach(function (p) {
    var d = parseTs(p.ts); if (!d) return;
    var dist = Math.abs(d.getTime() - t);
    if (p.status === "OK" && dist < bestDist) { bestDist = dist; best = p; }
  });
  return best;
}
function showTip(ev, pts, base) {
  var svg = ev.currentTarget.ownerSVGElement;
  var box = document.getElementById("chart-box").getBoundingClientRect();
  var scale = 1160 / box.width;
  var xClient = (ev.clientX - box.left) * scale;
  var t0 = chartTimes[0], t1 = chartTimes[chartTimes.length - 1];
  var t = t0 + (xClient - 74) / (1160 - 74 - 16) * (t1 - t0);
  var p = nearestPoint(pts, t);
  var tip = document.getElementById("tooltip");
  if (!p) { hideTip(); return; }
  var lines = ["<b>" + esc(fmtTs(p.ts)) + "</b>"];
  if (p.equity != null) {
    lines.push("combined equity: <b>" + num(p.equity) + "</b> USDT");
    lines.push("cumulative PnL: " + signed(p.cumulative_pnl) + " USDT");
    lines.push("change since previous valid mark: " + signed(p.daily_pnl) + " USDT");
    var contrib = p.contributions || {};
    Object.keys(contrib).sort().forEach(function (fid, i) {
      var c = contrib[fid];
      lines.push("<span style='color:" + SLEEVE_COLORS[i % 3] + "'>●</span> " + esc(fid)
        + ": " + num(c.equity) + " USDT (PnL " + signed(c.pnl) + ")");
    });
  } else {
    lines.push("<span class='gap-text'>GAP: UNAVAILABLE_FAIL_CLOSED</span>");
    lines.push(esc(p.reason || ""));
  }
  tip.innerHTML = lines.join("<br>");
  tip.style.display = "block";
  tip.style.left = Math.min(ev.clientX + 14, window.innerWidth - 480) + "px";
  tip.style.top = (ev.clientY + 14) + "px";
}
function hideTip() { document.getElementById("tooltip").style.display = "none"; }
var chartTimes = [0, 1];
var _origDraw = drawChart;
drawChart = function () {
  var pts = chartData();
  chartTimes = pts.length ? pts.map(function (p) { return parseTs(p.ts).getTime(); }) : [0, 1];
  _origDraw();
};

document.querySelectorAll("[data-range]").forEach(function (btn) {
  btn.addEventListener("click", function () {
    document.querySelectorAll("[data-range]").forEach(function (b) { b.classList.remove("active"); });
    btn.classList.add("active");
    STATE.range = btn.getAttribute("data-range");
    drawChart();
  });
});
function toggleBtn(id, key, idx) {
  var btn = document.getElementById(id);
  btn.addEventListener("click", function () {
    if (idx == null) STATE[key] = !STATE[key];
    else STATE[key][idx] = !STATE[key][idx];
    btn.classList.toggle("active", idx == null ? STATE[key] : STATE[key][idx]);
    drawChart();
  });
}
toggleBtn("tg-combined", "combined", null);
toggleBtn("tg-norm", "norm", null);
toggleBtn("tg-dd", "dd", null);
toggleBtn("tg-s0", "sleeves", 0);
toggleBtn("tg-s1", "sleeves", 1);
toggleBtn("tg-s2", "sleeves", 2);

/* ---------------- trades table ---------------- */
var COLUMNS = [
  ["virtual_trade_id", "virtual_trade_id"], ["family", "family"], ["asset", "asset"],
  ["side", "side"], ["status", "status"], ["signal_time", "signal_time"],
  ["intended_fill_time", "intended_fill_time"], ["actual_virtual_fill_time", "actual_virtual_fill_time"],
  ["entry_price", "entry_price"], ["current_mark_or_exit_price", "mark/exit"],
  ["quantity", "quantity"], ["notional", "notional"], ["fee", "fee"], ["slippage", "slippage"],
  ["funding", "funding"], ["realized_pnl", "realized_pnl"], ["unrealized_pnl", "unrealized_pnl"],
  ["return_pct", "return_%"], ["stop_loss_price", "stop_loss_price"],
  ["take_profit_price", "take_profit_price"], ["exit_policy", "exit_policy"]
];
function eventStatus(row) {
  var ev = (PAYLOAD.event_index || {})[row.event_id];
  return ev ? ev.status : "UNKNOWN";
}
function filteredRows() {
  var q = document.getElementById("f-search").value.trim().toLowerCase();
  var fam = document.getElementById("f-family").value;
  var asset = document.getElementById("f-asset").value.trim().toUpperCase();
  var side = document.getElementById("f-side").value;
  var st = document.getElementById("f-status").value;
  var evst = document.getElementById("f-eventstatus").value;
  var from = document.getElementById("f-from").value;
  var to = document.getElementById("f-to").value;
  var rows = (PAYLOAD.trades || []).filter(function (r) {
    if (fam && r.family !== fam) return false;
    if (asset && String(r.asset || "").toUpperCase().indexOf(asset) === -1) return false;
    if (side && r.side !== side) return false;
    if (st && r.status !== st) return false;
    if (evst && eventStatus(r) !== evst) return false;
    var ts = String(r.actual_virtual_fill_time || "");
    if (from && ts.slice(0, 10) < from) return false;
    if (to && ts.slice(0, 10) > to) return false;
    if (q) {
      var blob = JSON.stringify(r).toLowerCase();
      if (blob.indexOf(q) === -1) return false;
    }
    return true;
  });
  if (STATE.sortKey) {
    var k = STATE.sortKey;
    rows = rows.slice().sort(function (a, b) {
      var va = a[k], vb = b[k];
      if (va == null && vb == null) return 0;
      if (va == null) return 1; if (vb == null) return -1;
      if (typeof va === "number" && typeof vb === "number") return (va - vb) * STATE.sortDir;
      return String(va).localeCompare(String(vb)) * STATE.sortDir;
    });
  }
  return rows;
}
function renderTable() {
  var head = document.getElementById("trades-head");
  var body = document.getElementById("trades-body");
  var tr = document.createElement("tr");
  COLUMNS.forEach(function (col) {
    var th = document.createElement("th");
    th.textContent = col[1];
    th.addEventListener("click", function () {
      if (STATE.sortKey === col[0]) STATE.sortDir *= -1;
      else { STATE.sortKey = col[0]; STATE.sortDir = 1; }
      renderTable();
    });
    tr.appendChild(th);
  });
  head.innerHTML = "";
  head.appendChild(tr);
  var rows = filteredRows();
  body.innerHTML = "";
  rows.forEach(function (r) {
    var trr = document.createElement("tr");
    trr.className = "rowline";
    COLUMNS.forEach(function (col) {
      var td = document.createElement("td");
      var v = r[col[0]];
      if (["signal_time", "intended_fill_time", "actual_virtual_fill_time"].indexOf(col[0]) >= 0) {
        td.textContent = v == null ? "UNAVAILABLE" : fmtTs(v);
      } else if (col[0] === "status") {
        td.innerHTML = "<span class='status-" + esc(v) + "'>" + esc(v) + "</span>";
      } else if (v == null) {
        td.textContent = "UNAVAILABLE";
      } else if (typeof v === "number") {
        td.textContent = num(v, 4);
      } else {
        td.textContent = String(v);
      }
      trr.appendChild(td);
    });
    trr.addEventListener("click", function () { openDrawer(r.virtual_trade_id); });
    body.appendChild(trr);
  });
  var emptyDiv = document.getElementById("table-empty-note");
  if (emptyDiv) emptyDiv.textContent = rows.length
    ? "" : "(bộ lọc hiện tại: 0 dòng hiển thị — dữ liệu gốc vẫn nguyên vẹn trong ledger)";
}
["f-search", "f-family", "f-asset", "f-side", "f-status", "f-eventstatus", "f-from", "f-to"]
  .forEach(function (id) {
    document.getElementById(id).addEventListener("input", renderTable);
    document.getElementById(id).addEventListener("change", renderTable);
  });

/* ---------------- sanitized client-side exports ---------------- */
function download(name, text, mime) {
  var blob = new Blob([text], { type: mime });
  var a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  document.body.appendChild(a);
  a.click();
  setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 400);
}
function csvOf(rows) {
  if (!rows.length) return "";
  var cols = COLUMNS.map(function (c) { return c[0]; });
  var head = cols.join(",");
  var lines = rows.map(function (r) {
    return cols.map(function (c) {
      var v = r[c] == null ? "UNAVAILABLE" : String(r[c]);
      return '"' + v.replace(/"/g, '""') + '"';
    }).join(",");
  });
  return head + "\\n" + lines.join("\\n");
}
document.getElementById("btn-export-csv").addEventListener("click", function () {
  download("shv1_trades_filtered.csv", csvOf(filteredRows()), "text/csv");
});
document.getElementById("btn-export-json").addEventListener("click", function () {
  download("shv1_trades_filtered.json", JSON.stringify(filteredRows(), null, 2), "application/json");
});
document.getElementById("btn-export-equity").addEventListener("click", function () {
  var out = {
    cycle_id: PAYLOAD.cycle_id, exported_at_utc: PAYLOAD.generated_utc,
    note: PAYLOAD.exports_note, baseline_usdt: PAYLOAD.combined.baseline_usdt,
    combined: PAYLOAD.combined.chart_points,
    drawdown: PAYLOAD.combined.drawdown_series,
    sleeves: Object.keys(PAYLOAD.families).sort().map(function (fid) {
      return { family_id: fid, ledger_digest: PAYLOAD.families[fid].ledger_digest,
               points: PAYLOAD.families[fid].chart_points };
    })
  };
  download("shv1_equity_series.json", JSON.stringify(out, null, 2), "application/json");
});

/* ---------------- detail drawer ---------------- */
function kvRow(label, value) {
  return "<div><div class='muted'>" + esc(label) + "</div><div>" + value + "</div></div>";
}
function openDrawer(tradeId) {
  var det = (PAYLOAD.trade_index || {})[tradeId];
  var box = document.getElementById("drawer-content");
  if (!det) {
    box.innerHTML = "<h3>Chi tiết</h3><p>Không tìm thấy virtual_trade_id " + esc(tradeId) + "</p>";
  } else {
    var html = "<h3>" + esc(det.virtual_trade_id) + "</h3>"
      + "<p class='muted'>family " + esc(det.family) + " · arm " + esc(det.arm) + " · "
      + esc(det.asset) + " · " + esc(det.side) + " · " + esc(det.status) + "</p>"
      + "<p>stop_loss_price: <b>" + esc(det.stop_loss_price) + "</b><br>"
      + "take_profit_price: <b>" + esc(det.take_profit_price) + "</b><br>"
      + "exit_policy (frozen): <b>" + esc(det.exit_policy) + "</b></p>"
      + "<div class='drawer-grid'>"
      + kvRow("decision timestamp (UTC)", "<span class='ts' data-ts='" + esc(det.decision_timestamp_utc || "") + "'>" + esc(fmtTs(det.decision_timestamp_utc)) + "</span>")
      + kvRow("feature cutoff (UTC)", "<span class='ts' data-ts='" + esc(det.feature_cutoff_utc || "") + "'>" + esc(fmtTs(det.feature_cutoff_utc)) + "</span>")
      + kvRow("data availability (observed_at)", "<span class='ts' data-ts='" + esc(det.data_available_at_utc || "") + "'>" + esc(fmtTs(det.data_available_at_utc)) + "</span>")
      + kvRow("data status", esc(det.data_status))
      + kvRow("signal value", esc(det.signal_value == null ? "UNAVAILABLE" : det.signal_value))
      + kvRow("cross-sectional rank", esc(det.cross_sectional_rank == null ? "UNAVAILABLE" : det.cross_sectional_rank))
      + kvRow("eligible universe", esc(JSON.stringify(det.eligible_universe)))
      + kvRow("target / previous weight", esc(det.target_weight == null ? "UNAVAILABLE" : det.target_weight) + " / " + esc(det.previous_weight == null ? "UNAVAILABLE" : det.previous_weight))
      + kvRow("requested qty / notional", esc(det.requested_qty == null ? "UNAVAILABLE" : det.requested_qty) + " / " + esc(det.requested_notional == null ? "UNAVAILABLE" : det.requested_notional))
      + kvRow("virtual filled qty", esc(det.virtual_filled_qty == null ? "UNAVAILABLE" : det.virtual_filled_qty))
      + kvRow("intended price", esc(det.intended_price == null ? "UNAVAILABLE" : det.intended_price))
      + kvRow("virtual avg fill price", esc(det.virtual_avg_fill_price == null ? "UNAVAILABLE" : det.virtual_avg_fill_price))
      + kvRow("current mark", det.current_mark == null ? "UNAVAILABLE" : esc(det.current_mark) + " <span class='muted'>(" + esc(det.current_mark_source || "") + ")</span>")
      + kvRow("exit price", esc(det.exit_price == null ? "— (open)" : det.exit_price))
      + kvRow("fee", esc(det.fee == null ? "UNAVAILABLE" : det.fee))
      + kvRow("slippage", esc(det.slippage == null ? "UNAVAILABLE" : det.slippage))
      + kvRow("funding cashflows", fundingRows(det.funding_cashflows))
      + kvRow("total transaction cost", esc(det.total_transaction_cost == null ? "UNAVAILABLE" : det.total_transaction_cost))
      + kvRow("realized (USDT / %)", esc(det.realized_pnl_usdt == null ? "UNAVAILABLE" : det.realized_pnl_usdt) + " / " + esc(det.return_pct == null ? "UNAVAILABLE" : det.return_pct + "%"))
      + kvRow("unrealized (USDT)", esc(det.unrealized_pnl_usdt == null ? "UNAVAILABLE" : det.unrealized_pnl_usdt))
      + kvRow("linked event_id", "<code>" + esc(det.event_id) + "</code>")
      + kvRow("statuses (accounting/data/risk)", esc(JSON.stringify(det.statuses)))
      + "</div>"
      + "<div class='drawer-grid' style='margin-top:6px'>"
      + "<div class='drawer-full'><b>Lý do vào (tiếng Việt):</b> " + esc(det.entry_reason_vi) + "</div>"
      + "<div class='drawer-full'><b>Lý do thoát (tiếng Việt):</b> " + esc(det.exit_reason_vi) + "</div>"
      + "<div class='drawer-full'><b>Diagnostic — distance to risk cap:</b> UNAVAILABLE "
      + "(chỉ chẩn đoán, không phải lệnh; cần chuỗi mark + ngưỡng cap đã đóng băng).</div>"
      + "</div>"
      + miniPriceChart(det)
      + "<p class='muted'>digests — config: <code>" + esc(det.config_digest) + "</code> · data: <code>"
      + esc(det.data_snapshot_digest) + "</code> · cost: <code>" + esc(det.cost_regime_digest)
      + "</code> · code freeze: <code>" + esc(det.code_freeze_sha) + "</code><br>"
      + "source ledger: <code>" + esc((det.source_ledger || {}).path) + "</code> · digest <code>"
      + esc((det.source_ledger || {}).digest) + "</code> · source ts "
      + "<span class='ts' data-ts='" + esc(det.source_ts || "") + "'>" + esc(fmtTs(det.source_ts)) + "</span></p>"
      + "<details><summary class='muted'>raw virtual_fill_event (ledger bytes)</summary>"
      + "<pre class='rawfill'>" + esc(JSON.stringify(det.raw_virtual_fill_event, null, 2)) + "</pre></details>";
    box.innerHTML = html;
  }
  document.getElementById("drawer").classList.add("open");
}
function fundingRows(flows) {
  if (!flows || !flows.length) return "UNAVAILABLE";
  return flows.map(function (f, i) {
    return "cashflow[" + i + "] " + esc(f.amount == null ? "UNAVAILABLE" : f.amount)
      + " @ " + esc(f.funding_time_utc || "?") + " (rate " + esc(f.rate == null ? "?" : f.rate) + ")";
  }).join("<br>");
}
function miniPriceChart(det) {
  var series = det.price_series || [];
  if (!series.length) {
    return "<p class='muted'>price series: UNAVAILABLE (không có mốc giá nào của tài sản này trong ledger).</p>";
  }
  var W = 660, H = 120, padL = 46, padR = 10, padT = 10, padB = 16;
  var times = series.map(function (p) { return parseTs(p.ts).getTime(); });
  var tMin = Math.min.apply(null, times), tMax = Math.max.apply(null, times);
  if (tMax === tMin) tMax = tMin + 1;
  var prices = series.map(function (p) { return p.price; });
  var pMin = Math.min.apply(null, prices), pMax = Math.max.apply(null, prices);
  if (pMax === pMin) { pMax += 1; pMin -= 1; }
  function X(t) { return padL + (t - tMin) / (tMax - tMin) * (W - padL - padR); }
  function Y(p) { return padT + (pMax - p) / (pMax - pMin) * (H - padT - padB); }
  var svg = "<svg viewBox='0 0 " + W + " " + H + "' style='width:100%;background:var(--panel2);border:1px solid var(--line);border-radius:8px;margin-top:8px'>";
  var d = "";
  series.forEach(function (p, i) {
    d += (i ? " L " : " M ") + X(parseTs(p.ts).getTime()).toFixed(1) + " " + Y(p.price).toFixed(1);
  });
  svg += "<path d='" + d + "' fill='none' stroke='#4c8dff' stroke-width='1.5'/>";
  series.forEach(function (p) {
    var color = p.kind === "exit" ? "#8fa1b3" : "#2dd4bf";
    svg += "<circle cx='" + X(parseTs(p.ts).getTime()).toFixed(1) + "' cy='" + Y(p.price).toFixed(1)
      + "' r='3' fill='" + color + "'><title>" + esc(p.kind) + " " + esc(fmtTs(p.ts)) + " @ " + esc(p.price) + "</title></circle>";
  });
  (det.blocked_event_markers || []).forEach(function (m) {
    var t = parseTs(m.ts); if (!t) return;
    svg += "<rect x='" + (X(t.getTime()) - 3).toFixed(1) + "' y='" + padT + "' width='6' height='8' fill='#f5a524'><title>blocked @ " + esc(fmtTs(m.ts)) + "</title></rect>";
  });
  svg += "<text x='" + (padL - 4) + "' y='" + (padT + 8) + "' text-anchor='end' fill='#8fa1b3' font-size='9'>" + pMax.toFixed(2) + "</text>";
  svg += "<text x='" + (padL - 4) + "' y='" + (H - padB) + "' text-anchor='end' fill='#8fa1b3' font-size='9'>" + pMin.toFixed(2) + "</text>";
  svg += "</svg>";
  svg += "<p class='muted'>entry ● teal · exit ● grey · blocked ■ amber (mini series từ fill prices trong ledger)</p>";
  return svg;
}
document.addEventListener("click", function (ev) {
  var drawer = document.getElementById("drawer");
  if (drawer.classList.contains("open") && !drawer.contains(ev.target)) {
    drawer.classList.remove("open");
  }
});

/* ---------------- init ---------------- */
var famSel = document.getElementById("f-family");
Object.keys(PAYLOAD.families || {}).sort().forEach(function (fid) {
  var opt = document.createElement("option");
  opt.value = fid; opt.textContent = "family: " + fid;
  famSel.appendChild(opt);
});
document.querySelectorAll("[data-range]").forEach(function (b) {
  b.classList.toggle("active", b.getAttribute("data-range") === "ALL");
});
drawChart();
renderTable();
applyTz();
</script>
</body>
</html>
"""


def _counters_html(snapshot: Mapping[str, Any]) -> str:
    counters = snapshot.get("counters", {})
    rows = [
        ("decision_count", "strategy decisions emitted (ONE append-only record per scheduled decision, even when no trade is possible)"),
        ("order_intent_count", "symbol-level TARGET_INTENT entries emitted across decided events (an intent is NOT a fill)"),
        ("fill_count", "virtual fills executed in the isolated sleeve books (one decision can produce several symbol-level fills)"),
        ("closed_position_count", "virtual positions fully closed (a subset of fills)"),
    ]
    html_rows = "\n".join(
        f"<tr><td><code>{key}</code></td><td><b>{_value_or_unavailable(counters.get(key), 'int')}</b></td>"
        f"<td class='muted'>{_esc(desc)}</td></tr>"
        for key, desc in rows
    )
    return (
        "<table class='compare'><tbody>" + html_rows + "</tbody></table>"
        "<p class='muted'>Bốn số này KHÔNG được dán nhãn chung là “số lệnh” — "
        "chúng đo bốn sự kiện khác nhau (plan section 9.4).</p>"
    )


def generate_html(snapshot: Mapping[str, Any]) -> str:
    """Render the self-contained read-only dashboard page."""
    cards = "\n".join(
        _family_card(block)
        for _, block in sorted(snapshot.get("families", {}).items())
    )
    empty_state = (
        "<div class='empty-state' id='table-empty-state'>NO_TRADES_YET — chưa có virtual fill nào "
        "trong các sổ cái (pre-activation). Mọi số liệu là NOT_RUN / UNAVAILABLE, "
        "không bao giờ là số 0 giả.</div><div id='table-empty-note' class='muted'></div>"
        if not snapshot.get("trades")
        else "<div id='table-empty-note' class='muted'></div>"
    )
    heartbeat = snapshot.get("scheduler_heartbeat", {})
    last_completed = (heartbeat.get("last_completed_event") or {}).get("scheduled_decision_utc")
    replacements = {
        "__PAYLOAD__": _payload_json(snapshot),
        "__GENERATED__": _esc(snapshot.get("generated_utc") or "UNAVAILABLE"),
        "__SYSTEM_STATUS__": _esc(snapshot.get("system_status") or "UNAVAILABLE"),
        "__LOCAL_TZ__": _esc(LOCAL_TZ_NAME),
        "__BANNERS__": _banners_html(snapshot),
        "__TOP_VIEW__": _top_view_html(snapshot),
        "__CARDS__": cards,
        "__COMPARE__": _comparison_html(snapshot),
        "__COUNTERS__": _counters_html(snapshot),
        "__FAMILY_OPTIONS__": "".join(
            f"<option value='{_esc(fid)}'>{_esc(fid)}</option>"
            for fid in sorted(snapshot.get("families", {}))
        ),
        "__EMPTY_STATE__": empty_state,
        "__IDENTITY__": _identity_html(snapshot),
        "__HEARTBEAT__": _esc(
            f"last completed {(last_completed or 'UNAVAILABLE')} · "
            f"{heartbeat.get('ledger_byte_count', 'UNAVAILABLE')} ledger bytes "
            f"({heartbeat.get('method')})"
        ),
        "__IDENTITY_STATUS__": _esc(
            (snapshot.get("identity") or {}).get("identity_status") or "NOT_RUN"
        ),
        "__ACCOUNTING__": (
            "OK (measured: every event identity passed)"
            if snapshot.get("accounting_ok")
            else "ACCOUNTING_MISMATCH (red banner above)"
        ),
    }
    page = _TEMPLATE
    for key, value in replacements.items():
        page = page.replace(key, value)
    return page
