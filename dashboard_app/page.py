"""The single dashboard page (self-contained HTML/CSS/JS, no CDN).

One window, one screen: header status -> top strip -> three family
cards -> one chart area (Tổng 300K / XSECT / ILLIQ / BASISLV) -> one
trades table with click-through detail. The page polls
``/api/snapshot.json`` every 30 s and re-renders; rendering is pure
client-side over the fail-closed engine snapshot (no invented values:
missing fields render N/A)."""

from __future__ import annotations

from .logo import LOGO_DATA_URI

PAGE_HTML = r"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<title>Quant Shadow Dashboard — PROSPECTIVE-SHADOW-V1</title>
<style>
  :root {
    --bg: #f4f5f7; --card: #ffffff; --ink: #1c1e21; --muted: #6b7280;
    --line: #e3e5e8; --green: #1a7f37; --greenbg: #e6f4ea;
    --red: #c62828; --redbg: #fdecea; --gray: #6b7280; --graybg: #f1f2f4;
    --yellow: #9a6700; --yellowbg: #fff3d6; --blue: #1d4ed8;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--ink);
    font: 13px/1.45 -apple-system, "SF Pro Text", "Helvetica Neue", sans-serif;
  }
  header {
    display: flex; align-items: center; gap: 14px; flex-wrap: wrap;
    padding: 10px 18px; background: #101828; color: #fff;
  }
  header .logo {
    height: 52px; width: auto; border-radius: 8px; display: block;
    box-shadow: 0 2px 8px rgba(0,0,0,.35);
  }
  header h1 { font-size: 15px; margin: 0; font-weight: 600; }
  header .sub { color: #9fb0c9; font-size: 11.5px; }
  .badge {
    padding: 3px 10px; border-radius: 999px; font-weight: 700;
    font-size: 12px; letter-spacing: .3px;
  }
  .badge.live { background: #0f5132; color: #d1fae5; }
  .badge.stale { background: #7a4f00; color: #fff3d6; }
  .badge.error { background: #8e2323; color: #fdecea; }
  .badge.flat { background: #3f4854; color: #e5e7eb; }
  .badge.ok { background: #0f5132; color: #d1fae5; }
  .badge.warn { background: #7a4f00; color: #fff3d6; }
  #lastupdate { margin-left: auto; color: #c3cedd; font-size: 11.5px; text-align: right; }
  #statusreason { width: 100%; color: #c3cedd; font-size: 11.5px; }
  main { padding: 14px 18px 26px; max-width: 1440px; margin: 0 auto; }
  .strip { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; }
  .strip .box {
    background: var(--card); border: 1px solid var(--line);
    border-radius: 10px; padding: 10px 12px;
  }
  .box .lbl { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: .4px; }
  .box .val { font-size: 19px; font-weight: 700; margin-top: 3px; font-variant-numeric: tabular-nums; }
  .box .sml { font-size: 11.5px; color: var(--muted); margin-top: 2px; font-variant-numeric: tabular-nums; }
  .pos { color: var(--green); } .neg { color: var(--red); } .neu { color: var(--gray); }
  .cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 12px; }
  .fam { background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 12px 14px; }
  .fam h3 { margin: 0 0 2px; font-size: 13.5px; font-weight: 700; }
  .fam .chiprow { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
  .chip { padding: 2px 9px; border-radius: 999px; font-size: 11px; font-weight: 700; }
  .chip.ok { background: var(--greenbg); color: var(--green); }
  .chip.warn { background: var(--yellowbg); color: var(--yellow); }
  .chip.flat { background: var(--graybg); color: var(--gray); }
  .fam table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
  .fam td { padding: 2.5px 0; vertical-align: top; }
  .fam td:first-child { color: var(--muted); width: 46%; }
  .fam td:last-child { text-align: right; font-weight: 600; }
  .section { background: var(--card); border: 1px solid var(--line); border-radius: 10px; margin-top: 12px; padding: 12px 14px; }
  .section h2 { margin: 0 0 8px; font-size: 13.5px; }
  .btns { display: flex; gap: 6px; margin-bottom: 8px; flex-wrap: wrap; }
  .btns button {
    border: 1px solid var(--line); background: #fff; color: var(--ink);
    border-radius: 8px; padding: 4px 12px; font-size: 12px; cursor: pointer;
  }
  .btns button.on { background: #101828; color: #fff; border-color: #101828; }
  #chartwrap { position: relative; }
  #chart { width: 100%; height: auto; display: block; }
  #tip {
    position: absolute; pointer-events: none; display: none; z-index: 5;
    background: #101828; color: #fff; border-radius: 8px; padding: 7px 10px;
    font-size: 11.5px; white-space: nowrap; box-shadow: 0 4px 14px rgba(0,0,0,.25);
    font-variant-numeric: tabular-nums;
  }
  .filters { display: flex; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; align-items: center; }
  .filters select, .filters input {
    border: 1px solid var(--line); border-radius: 8px; padding: 4px 8px;
    font-size: 12px; background: #fff; color: var(--ink);
  }
  .filters input { width: 180px; }
  .tblwrap { overflow: auto; max-height: 430px; border: 1px solid var(--line); border-radius: 8px; }
  table.trades { border-collapse: collapse; width: 100%; font-size: 11.5px; }
  table.trades th {
    position: sticky; top: 0; background: #f8f9fb; text-align: right;
    padding: 6px 8px; border-bottom: 1px solid var(--line); white-space: nowrap;
    color: var(--muted); font-weight: 600; user-select: none;
  }
  table.trades th.l, table.trades td.l { text-align: left; }
  table.trades td { padding: 4px 8px; text-align: right; white-space: nowrap; border-bottom: 1px solid #f0f1f3; font-variant-numeric: tabular-nums; }
  table.trades tr.row { cursor: pointer; }
  table.trades tr.row:hover { background: #f6f8ff; }
  tr.rp { background: var(--greenbg); } tr.rn { background: var(--redbg); }
  .sidebuy { color: var(--green); font-weight: 700; }
  .sidesell { color: var(--red); font-weight: 700; }
  footer { color: var(--muted); font-size: 11px; margin-top: 10px; line-height: 1.6; word-break: break-all; }
  #overlay {
    display: none; position: fixed; inset: 0; background: rgba(16,24,40,.45);
    z-index: 20; align-items: center; justify-content: center;
  }
  #popup {
    background: #fff; border-radius: 12px; max-width: 760px; width: 92%;
    max-height: 84vh; overflow: auto; padding: 16px 18px;
  }
  #popup h3 { margin: 0 0 8px; font-size: 14px; }
  #popup table { width: 100%; border-collapse: collapse; font-size: 12px; }
  #popup td { border-bottom: 1px solid #f0f1f3; padding: 4px 6px; vertical-align: top; }
  #popup td:first-child { color: var(--muted); width: 40%; }
  #popup pre { background: #f6f7f9; border-radius: 8px; padding: 8px; font-size: 10.5px; overflow: auto; max-height: 220px; }
  #popup .close { float: right; border: 1px solid var(--line); background: #fff; border-radius: 8px; padding: 3px 10px; cursor: pointer; }
  .note { font-size: 11px; color: var(--muted); }
  .banner { background: var(--yellowbg); color: var(--yellow); border-radius: 8px; padding: 6px 10px; font-size: 11.5px; margin-top: 8px; }
  @media (max-width: 1100px) { .strip { grid-template-columns: repeat(2, 1fr); } .cards { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<header>
  <img class="logo" src="{LOGO_SRC}" alt="logo">
  <div>
    <h1>Quant Shadow Dashboard</h1>
    <div class="sub">PROSPECTIVE-SHADOW-V1 · paper/shadow (không phải live trading) · vốn ban đầu 300,000 USDT</div>
  </div>
  <span id="badge" class="badge stale">…</span>
  <div id="lastupdate"></div>
  <div id="statusreason"></div>
</header>

<main>
  <div class="strip" id="strip"></div>
  <div class="cards" id="cards"></div>

  <div class="section">
    <h2>Equity theo thời gian</h2>
    <div class="btns" id="chartbtns">
      <button data-k="combined" class="on">Tổng 300K</button>
      <button data-k="XSECT-FUND-CARRY-7D">XSECT</button>
      <button data-k="ILLIQ-AMIHUD-28D-W">ILLIQ</button>
      <button data-k="BASISLV-PREMFADE-28D">BASISLV</button>
    </div>
    <div id="chartwrap">
      <svg id="chart" viewBox="0 0 1000 330" preserveAspectRatio="none"></svg>
      <div id="tip"></div>
    </div>
    <div class="note">Đường đứt là vốn ban đầu (300,000 Tổng / 100,000 mỗi family). Khoảng mất dữ liệu không được nội suy — bị bỏ hở (fail-closed).</div>
  </div>

  <div class="section">
    <h2>Tất cả lệnh (cả 3 family)</h2>
    <div class="filters">
      <select id="ffamily"><option value="">Mọi family</option></select>
      <select id="fstate">
        <option value="">Mọi trạng thái nắm giữ</option>
        <option value="held">Đang nắm giữ</option>
        <option value="closed">Không còn vị thế</option>
      </select>
      <input id="fsearch" type="text" placeholder="Tìm tài sản… (vd DOGEUSDT)">
      <span class="note" id="rowcount"></span>
    </div>
    <div class="tblwrap">
      <table class="trades" id="tradestable">
        <thead><tr>
          <th class="l" id="thTime" title="Bấm để đổi chiều sắp xếp">Thời gian ▾</th>
          <th class="l">Family</th><th class="l">Tài sản</th><th>Side</th>
          <th class="l">Trạng thái</th><th>SL</th><th>TP</th>
          <th>Số lượng</th><th>Notional $</th><th>Giá vào/fill</th>
          <th>Giá hiện tại/thoát</th><th>Realized $</th><th>Unrealized $</th>
          <th>Tổng PnL $</th><th>Tổng PnL %</th><th>Fee</th>
          <th>Slippage</th><th>Funding</th><th>Gross sau lệnh</th>
        </tr></thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
    <div class="note">Bấm một dòng để xem chi tiết lệnh. SL/TP là "N/A" vì family đóng băng không có stop/take cố định (hiển thị đúng thực tế, không bịa). Trạng thái "unknown" là trạng thái thật từ ledger.</div>
  </div>

  <footer id="footer"></footer>
</main>

<div id="overlay"><div id="popup">
  <button class="close" onclick="closePopup()">Đóng</button>
  <h3 id="popuptitle"></h3>
  <div id="popupbody"></div>
</div></div>

<script>
"use strict";
var STATE = {env: null, chart: "combined", sortDesc: true, timer: null, countdown: 30, baseMsg: ""};
var FAM_ORDER = ["XSECT-FUND-CARRY-7D", "ILLIQ-AMIHUD-28D-W", "BASISLV-PREMFADE-28D"];
var FAM_SHORT = {"XSECT-FUND-CARRY-7D": "XSECT", "ILLIQ-AMIHUD-28D-W": "ILLIQ", "BASISLV-PREMFADE-28D": "BASISLV"};

function fmtUSD(x, dash) {
  if (x === null || x === undefined || !isFinite(x)) return (dash === undefined ? "N/A" : dash);
  var sign = x < 0 ? "-" : "";
  var v = Math.abs(x);
  var s = v.toLocaleString("en-US", {minimumFractionDigits: 2, maximumFractionDigits: 2});
  return sign + "$" + s;
}
function fmtNum(x, d) {
  if (x === null || x === undefined || !isFinite(x)) return "N/A";
  return Number(x).toLocaleString("en-US", {maximumFractionDigits: (d === undefined ? 4 : d)});
}
function fmtPct(x) {
  if (x === null || x === undefined || !isFinite(x)) return "N/A";
  return (x >= 0 ? "+" : "") + x.toFixed(3) + "%";
}
function pnlClass(x) {
  if (x === null || x === undefined || !isFinite(x) || Math.abs(x) < 1e-9) return "neu";
  return x > 0 ? "pos" : "neg";
}
function fmtTime(iso) {
  if (!iso) return "N/A";
  var d = new Date(iso);
  if (isNaN(d)) return String(iso);
  var p = function(n) { return (n < 10 ? "0" : "") + n; };
  return d.getFullYear() + "-" + p(d.getMonth()+1) + "-" + p(d.getDate()) + " " + p(d.getHours()) + ":" + p(d.getMinutes());
}
function el(id) { return document.getElementById(id); }
function esc(s) {
  return String(s === null || s === undefined ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function render(env) {
  STATE.env = env;
  var app = env.app || {}, snap = env.snapshot;
  var badge = el("badge"), reason = el("statusreason");
  var st = (app.status && app.status.state) || "DATA ERROR";
  badge.textContent = st;
  badge.className = "badge " + (st === "LIVE" ? "live" : st === "STALE" ? "stale" : "error");
  var reasons = ((app.status && app.status.reasons) || []).join(" · ");
  reason.textContent = reasons ? ("Trạng thái: " + reasons) : "";

  var vc = snap && snap.valuation ? snap.valuation.combined : null;
  var eq = vc ? vc.equity : null;
  var tpnl = vc ? vc.total_pnl_usdt : null;
  var tpct = vc ? vc.total_pnl_pct : null;
  var today = vc && vc.today ? (vc.today["Asia/Ho_Chi_Minh"] || vc.today["UTC"]) : null;
  var gross = app.gross_combined || {};
  var ru = app.realized_unrealized_totals || {};
  var strip = [];
  function box(lbl, val, valCls, sml) {
    return '<div class="box"><div class="lbl">' + lbl + '</div>' +
      '<div class="val ' + (valCls || "") + '">' + val + '</div>' +
      '<div class="sml">' + (sml || "") + '</div></div>';
  }
  strip.push(box("Tổng equity", fmtUSD(eq), "",
    vc && vc.as_of_utc ? ("mark " + fmtTime(vc.as_of_utc)) : ""));
  strip.push(box("Tổng PnL", fmtUSD(tpnl), pnlClass(tpnl), "từ vốn ban đầu $300,000"));
  strip.push(box("Tổng PnL %", fmtPct(tpct), pnlClass(tpct), "300,000 USDT gốc"));
  strip.push(box("PnL hôm nay", today && today.status === "OK" ? fmtUSD(today.pnl_usdt) : "N/A",
    today && today.status === "OK" ? pnlClass(today.pnl_usdt) : "neu",
    today && today.status === "OK" ? fmtPct(today.pnl_pct) + " · từ " + fmtTime(today.window_start_local) :
      "chưa có mốc 00:00 hợp lệ (fail-closed)"));
  strip.push(box("Gross exposure", fmtUSD(gross.usd), "",
    fmtPct(gross.pct) + " của equity · Σ|notional| vị thế mở"));
  el("strip").innerHTML = strip.join("");
  var ruNote = ru.realized_pnl === null || ru.realized_pnl === undefined
    ? (ru.reason ? esc(ru.reason) : "N/A")
    : ("realized " + fmtUSD(ru.realized_pnl) + " · unrealized " + fmtUSD(ru.unrealized_pnl));
  el("strip").insertAdjacentHTML("beforeend",
    '<div class="box" style="grid-column: span 5;"><div class="lbl">Realized / Unrealized (tổng 3 family, mark ' +
    esc(ru.mark_timestamp_utc || "") + ')</div><div class="sml">' + ruNote + '</div></div>');

  var fams = snap && snap.valuation ? snap.valuation.families : null;
  var html = "";
  FAM_ORDER.forEach(function(fid) {
    var f = fams ? fams[fid] : null;
    var meta = (app.families || {})[fid] || {};
    var chip = meta.chip || {chip: "N/A", tone: "warn"};
    var m = f && f.latest_valid_mark ? f.latest_valid_mark : {};
    var feq = m.equity;
    var ftp = f ? f.total_pnl_usdt : null;
    var ftpc = f ? f.total_pnl_pct : null;
    var ft = f && f.today ? f.today["Asia/Ho_Chi_Minh"] : null;
    var gr = meta.gross || {};
    var fills = snap && snap.counters ? null : null;
    function row(k, v, cls) { return "<tr><td>" + k + "</td><td class=\"" + (cls || "") + "\">" + v + "</td></tr>"; }
    html += '<div class="fam"><h3>' + esc(fid) + '</h3><div class="chiprow">' +
      '<span class="chip ' + (chip.tone || "warn") + '">' + esc(chip.chip) + "</span>" +
      (meta.heartbeat_data_status ? '<span class="note">decision: ' + esc(meta.heartbeat_data_status) + "</span>" : "") +
      (meta.next_decision_utc ? '<span class="note">lệnh kế: ' + fmtTime(meta.next_decision_utc) + "</span>" : "") +
      "</div><table>" +
      row("Equity", fmtUSD(feq)) +
      row("PnL tổng", fmtUSD(ftp) + " (" + fmtPct(ftpc) + ")", pnlClass(ftp)) +
      row("PnL hôm nay",
        ft && ft.status === "OK" ? fmtUSD(ft.pnl_usdt) + " (" + fmtPct(ft.pnl_pct) + ")" : "N/A",
        ft && ft.status === "OK" ? pnlClass(ft.pnl_usdt) : "neu") +
      row("Realized PnL", fmtUSD(m.realized_pnl), pnlClass(m.realized_pnl)) +
      row("Unrealized PnL", fmtUSD(m.unrealized_pnl), pnlClass(m.unrealized_pnl)) +
      row("Gross exposure", fmtUSD(gr.usd) + (gr.pct !== null && gr.pct !== undefined ? " (" + fmtPct(gr.pct) + ")" : "")) +
      row("Vị thế đang mở", gr.open_positions === null || gr.open_positions === undefined ? "N/A" : String(gr.open_positions)) +
      row("Số fill đã thực hiện", String(fillCount(fid))) +
      "</table>" +
      (chip.note ? '<div class="note">' + esc(chip.note) + "</div>" : "") +
      "</div>";
  });
  var x = app.xauusd_shadow || {};
  var xs = x.status || {};
  function xrow(k, v, cls) { return "<tr><td>" + k + '</td><td class="' + (cls || "") + '">' + v + "</td></tr>"; }
  html += '<div class="fam"><h3>XAUUSD-SHADOW-V1</h3><div class="chiprow">' +
    '<span class="chip ' + (x.available && !xs.last_error ? "ok" : "warn") + '">' +
    (x.available ? (xs.last_error ? "DEGRADED" : "OK") : "N/A") + "</span>" +
    '<span class="note">cycle riêng · internal shadow · read-only</span></div><table>' +
    xrow("Equity (USD)", fmtUSD(xs.equity_usd)) +
    xrow("Vị thế", esc(xs.position || "N/A")) +
    xrow("XAUUSD close", xs.last_close == null ? "N/A" : fmtNum(xs.last_close, 2)) +
    xrow("Bar mới nhất", esc(xs.last_bar || "N/A")) +
    xrow("Data gaps", xs.data_gaps && xs.data_gaps.length ? esc(JSON.stringify(xs.data_gaps)) : "none") +
    xrow("Ledger rows", xs.ledger_rows == null ? "N/A" : String(xs.ledger_rows)) +
    xrow("Lỗi gần nhất", esc(xs.last_error || "none")) +
    "</table>" +
    '<div class="note">SHADOW_OBSERVATION_ONLY · NOT A PROFITABILITY CLAIM · chi phí 4bps UNMEASURED-CONSERVATIVE</div></div>';
  el("cards").innerHTML = html;

  var banners = app.banners || [];
  var bhtml = "";
  banners.forEach(function(b) {
    if (b && b.message) bhtml += '<div class="banner">' + esc(b.message) + "</div>";
  });
  var oldB = document.getElementById("banners");
  if (oldB) oldB.remove();
  if (bhtml) {
    var bdiv = document.createElement("div");
    bdiv.id = "banners"; bdiv.innerHTML = bhtml;
    el("cards").after(bdiv);
  }

  drawChart();
  renderTable();

  var paths = app.paths || {};
  el("footer").innerHTML =
    "Dữ liệu (chỉ đọc, append-only): <b>" + esc(paths.runtime_root || "?") + "</b><br>" +
    "Engine: " + esc(app.engine_source || "?") + " · Ledgers: " + esc(paths.ledgers_dir || "?") +
    " · Marks: " + esc(paths.valuation_marks_dir || "?") + "<br>" +
    "Tự làm mới mỗi 30 giây · Chỉ đọc — không đặt lệnh, không sửa ledger · Paper/shadow account.";
}

function fillCount(fid) {
  var snap = STATE.env && STATE.env.snapshot;
  if (!snap || !snap.trades) return 0;
  var n = 0;
  snap.trades.forEach(function(t) { if (t.family === fid) n++; });
  return n;
}

/* ---------------- chart ---------------- */
function chartSeries() {
  var env = STATE.env, snap = env && env.snapshot;
  if (!snap || !snap.valuation) return {pts: [], baseline: 300000};
  var k = STATE.chart;
  if (k === "combined") {
    var s = (snap.valuation.combined || {}).series || [];
    return {pts: s, baseline: 300000};
  }
  var f = (snap.valuation.families || {})[k];
  return {pts: (f && f.series) || [], baseline: 100000};
}
function drawChart() {
  var svg = el("chart"), tip = el("tip");
  var data = chartSeries();
  var pts = (data.pts || []).filter(function(p) { return p.ts; });
  var W = 1000, H = 330, L = 70, R = 14, T = 12, B = 26;
  var out = [];
  if (!pts.length) {
    svg.innerHTML = '<text x="500" y="160" text-anchor="middle" fill="#6b7280" font-size="14">Chưa có dữ liệu mark hợp lệ (NOT_RUN)</text>';
    tip.style.display = "none";
    return;
  }
  var valid = pts.filter(function(p) { return p.status === "OK" && p.equity !== null && p.equity !== undefined; });
  if (!valid.length) {
    svg.innerHTML = '<text x="500" y="160" text-anchor="middle" fill="#6b7280" font-size="14">Không có mark OK — fail-closed, không nội suy</text>';
    return;
  }
  var t0 = new Date(pts[0].ts).getTime(), t1 = new Date(pts[pts.length-1].ts).getTime();
  if (!(t1 > t0)) t1 = t0 + 1;
  var ymin = Infinity, ymax = -Infinity;
  valid.forEach(function(p) { ymin = Math.min(ymin, p.equity); ymax = Math.max(ymax, p.equity); });
  ymin = Math.min(ymin, data.baseline); ymax = Math.max(ymax, data.baseline);
  var pad = (ymax - ymin) * 0.06 || 1; ymin -= pad; ymax += pad;
  function X(t) { return L + (t - t0) / (t1 - t0) * (W - L - R); }
  function Y(v) { return T + (1 - (v - ymin) / (ymax - ymin)) * (H - T - B); }
  // gridlines + Y labels
  out.push('<g>');
  for (var i = 0; i <= 4; i++) {
    var v = ymin + (ymax - ymin) * i / 4, y = Y(v);
    out.push('<line x1="' + L + '" y1="' + y + '" x2="' + (W - R) + '" y2="' + y + '" stroke="#eef0f3"/>');
    out.push('<text x="' + (L - 6) + '" y="' + (y + 3.5) + '" text-anchor="end" font-size="10" fill="#6b7280">' + Math.round(v).toLocaleString("en-US") + '</text>');
  }
  // X labels (~5)
  for (var j = 0; j <= 4; j++) {
    var t = t0 + (t1 - t0) * j / 4, x = X(t);
    var d = new Date(t);
    var p2 = function(n) { return (n < 10 ? "0" : "") + n; };
    var lbl = (d.getMonth()+1) + "/" + d.getDate() + " " + p2(d.getHours()) + ":" + p2(d.getMinutes());
    out.push('<text x="' + x + '" y="' + (H - 8) + '" text-anchor="middle" font-size="10" fill="#6b7280">' + lbl + '</text>');
  }
  out.push('<line x1="' + L + '" y1="' + (H - B) + '" x2="' + (W - R) + '" y2="' + (H - B) + '" stroke="#c8ccd2"/>');
  out.push('</g>');
  // baseline dashed
  var by = Y(data.baseline);
  out.push('<line x1="' + L + '" y1="' + by + '" x2="' + (W - R) + '" y2="' + by + '" stroke="#9aa2af" stroke-dasharray="6 5" stroke-width="1.2"/>');
  out.push('<text x="' + (W - R - 4) + '" y="' + (by - 4) + '" text-anchor="end" font-size="10" fill="#6b7280">vốn ban đầu ' + data.baseline.toLocaleString("en-US") + '</text>');
  // equity line with gaps (no interpolation across invalid/missing marks)
  var seg = [], inSeg = false;
  out.push('<path fill="none" stroke="#1d4ed8" stroke-width="1.7" d="');
  pts.forEach(function(p) {
    var ok = p.status === "OK" && p.equity !== null && p.equity !== undefined;
    if (!ok) { inSeg = false; return; }
    var x = X(new Date(p.ts).getTime()), y = Y(p.equity);
    out.push((inSeg ? "L" : "M") + x.toFixed(2) + " " + y.toFixed(2) + " ");
    inSeg = true; seg.push(p);
  });
  out.push('"/>');
  svg.innerHTML = out.join("");
  svg._pts = seg; svg._geom = {L: L, R: R, T: T, B: B, W: W, H: H, t0: t0, t1: t1, ymin: ymin, ymax: ymax, baseline: data.baseline};
}
(function chartHover() {
  var svg = el("chart"), tip = el("tip");
  svg.addEventListener("mousemove", function(ev) {
    var pts = svg._pts, g = svg._geom;
    if (!pts || !g) { tip.style.display = "none"; return; }
    var rect = svg.getBoundingClientRect();
    var px = (ev.clientX - rect.left) * (g.W / rect.width);
    var best = null, bestDx = Infinity;
    for (var i = 0; i < pts.length; i++) {
      var t = new Date(pts[i].ts).getTime();
      var x = g.L + (t - g.t0) / (g.t1 - g.t0) * (g.W - g.L - g.R);
      var dx = Math.abs(x - px);
      if (dx < bestDx) { bestDx = dx; best = pts[i]; }
    }
    if (!best || bestDx > 18) { tip.style.display = "none"; return; }
    var pnl = best.equity - g.baseline, pct = pnl / g.baseline * 100;
    tip.innerHTML = "<b>" + fmtTime(best.ts) + "</b><br>Equity: " + fmtUSD(best.equity) +
      "<br>PnL: " + fmtUSD(pnl) + " (" + fmtPct(pct) + ")";
    tip.style.display = "block";
    var wrap = el("chartwrap").getBoundingClientRect();
    tip.style.left = Math.min(ev.clientX - wrap.left + 12, wrap.width - 190) + "px";
    tip.style.top = (ev.clientY - wrap.top - 10) + "px";
  });
  svg.addEventListener("mouseleave", function() { tip.style.display = "none"; });
})();

/* ---------------- trades table ---------------- */
function tradeRows() {
  var env = STATE.env, snap = env && env.snapshot;
  if (!snap || !snap.trades) return [];
  var held = (env.app && env.app.held_assets_by_family) || {};
  return snap.trades.map(function(t) {
    var heldSet = held[t.family] || [];
    var isHeld = heldSet.indexOf(t.asset) >= 0;
    var realized = t.realized_pnl, unrealized = t.unrealized_pnl;
    var total = null;
    if (realized !== null && realized !== undefined && unrealized !== null && unrealized !== undefined) {
      total = realized + unrealized;
    } else if ((realized !== null && realized !== undefined) && (unrealized === null || unrealized === undefined)) {
      total = realized;
    }
    return {t: t, held: isHeld, total: total};
  });
}
function renderTable() {
  var env = STATE.env;
  var rows = tradeRows();
  var famSel = el("ffamily");
  if (famSel.options.length <= 1) {
    FAM_ORDER.forEach(function(fid) {
      var o = document.createElement("option");
      o.value = fid; o.textContent = FAM_SHORT[fid] + " (" + fid + ")";
      famSel.appendChild(o);
    });
  }
  var fam = famSel.value, stateF = el("fstate").value, q = el("fsearch").value.trim().toUpperCase();
  rows = rows.filter(function(r) {
    if (fam && r.t.family !== fam) return false;
    if (stateF === "held" && !r.held) return false;
    if (stateF === "closed" && r.held) return false;
    if (q && String(r.t.asset || "").toUpperCase().indexOf(q) < 0) return false;
    return true;
  });
  rows.sort(function(a, b) {
    var ta = a.t.actual_virtual_fill_time || a.t.signal_time || "";
    var tb = b.t.actual_virtual_fill_time || b.t.signal_time || "";
    if (ta === tb) return 0;
    return (ta < tb ? -1 : 1) * (STATE.sortDesc ? -1 : 1);
  });
  var body = [];
  rows.forEach(function(r) {
    var t = r.t;
    var time = t.actual_virtual_fill_time || t.signal_time || "N/A";
    var side = String(t.side || "").toLowerCase();
    var totalPct = t.return_pct;
    var slna = (env.app && env.app.sl_na) || "N/A";
    var cls = r.total === null || r.total === undefined ? "" : (Math.abs(r.total) < 1e-9 ? "" : (r.total > 0 ? "rp" : "rn"));
    body.push('<tr class="row ' + cls + '" data-id="' + esc(t.virtual_trade_id) + '">' +
      '<td class="l">' + fmtTime(time) + "</td>" +
      '<td class="l">' + esc(FAM_SHORT[t.family] || t.family) + "</td>" +
      '<td class="l"><b>' + esc(t.asset) + "</b></td>" +
      "<td>" + (side === "buy" ? '<span class="sidebuy">BUY</span>' : side === "sell" ? '<span class="sidesell">SELL</span>' : esc(t.side)) + "</td>" +
      '<td class="l" title="' + esc(t.exit_policy || "") + '">' + esc(t.status) + (r.held ? ' <span class="note">(đang nắm giữ)</span>' : "") + "</td>" +
      '<td title="' + esc(slna) + '">N/A</td>' +
      '<td title="' + esc((env.app && env.app.tp_na) || "N/A") + '">N/A</td>' +
      "<td>" + fmtNum(t.quantity, 4) + "</td>" +
      "<td>" + fmtUSD(t.notional) + "</td>" +
      "<td>" + fmtNum(t.entry_price, 6) + "</td>" +
      "<td>" + fmtNum(t.current_mark_or_exit_price, 6) + "</td>" +
      '<td class="' + pnlClass(t.realized_pnl) + '">' + fmtUSD(t.realized_pnl) + "</td>" +
      '<td class="' + pnlClass(t.unrealized_pnl) + '">' + fmtUSD(t.unrealized_pnl) + "</td>" +
      '<td class="' + pnlClass(r.total) + '">' + fmtUSD(r.total) + "</td>" +
      '<td class="' + pnlClass(totalPct) + '">' + (totalPct === null || totalPct === undefined ? "N/A" : fmtPct(totalPct)) + "</td>" +
      "<td>" + fmtUSD(t.fee) + "</td>" +
      "<td>" + fmtUSD(t.slippage) + "</td>" +
      "<td>" + fmtUSD(t.funding) + "</td>" +
      "<td>N/A</td></tr>");
  });
  el("tbody").innerHTML = body.join("") ||
    '<tr><td colspan="19" class="l" style="color:#6b7280">Không có lệnh khớp bộ lọc (NO_TRADES_YET nếu chưa từng có lệnh).</td></tr>';
  el("rowcount").textContent = rows.length + " fill";
}
document.getElementById("tbody").addEventListener("click", function(ev) {
  var tr = ev.target.closest("tr.row");
  if (tr) openPopup(tr.getAttribute("data-id"));
});
["ffamily", "fstate"].forEach(function(id) {
  el(id).addEventListener("change", renderTable);
});
el("fsearch").addEventListener("input", renderTable);
el("thTime").addEventListener("click", function() {
  STATE.sortDesc = !STATE.sortDesc;
  el("thTime").textContent = "Thời gian " + (STATE.sortDesc ? "▾" : "▴");
  renderTable();
});
document.getElementById("chartbtns").addEventListener("click", function(ev) {
  var b = ev.target.closest("button");
  if (!b) return;
  STATE.chart = b.getAttribute("data-k");
  Array.prototype.forEach.call(document.querySelectorAll("#chartbtns button"), function(x) {
    x.className = x === b ? "on" : "";
  });
  drawChart();
});

/* ---------------- popup ---------------- */
var LABELS = {
  virtual_trade_id: "ID lệnh ảo", family: "Family", asset: "Tài sản",
  side: "Side", status: "Trạng thái", event_id: "Event ID",
  signal_time: "Thời điểm tín hiệu", intended_fill_time: "Fill dự kiến",
  actual_virtual_fill_time: "Fill thực tế (ảo)", entry_price: "Giá vào/fill",
  current_mark_or_exit_price: "Giá hiện tại/thoát", quantity: "Số lượng",
  notional: "Notional USD", fee: "Fee", slippage: "Slippage",
  funding: "Funding", realized_pnl: "Realized PnL", unrealized_pnl: "Unrealized PnL",
  return_pct: "Tổng PnL %", stop_loss_price: "Stop Loss",
  take_profit_price: "Take Profit", exit_policy: "Chính sách thoát",
  ledger_digest: "Ledger digest", source_ts: "Thời điểm ghi ledger"
};
function openPopup(id) {
  fetch("/api/trade/" + encodeURIComponent(id) + ".json").then(function(r) { return r.json(); }).then(function(d) {
    el("popuptitle").textContent = (d.asset || "lệnh") + " · " + (FAM_SHORT[d.family] || d.family || "") + " · " + id;
    var rowsHtml = "";
    Object.keys(LABELS).forEach(function(k) {
      if (!(k in d)) return;
      var v = d[k];
      var txt = (v === null || v === undefined) ? "N/A" :
        (typeof v === "number" ? (Math.abs(v) < 1e15 ? v.toLocaleString("en-US", {maximumFractionDigits: 8}) : String(v)) : esc(v));
      rowsHtml += "<tr><td>" + LABELS[k] + "</td><td>" + txt + "</td></tr>";
    });
    var rest = {};
    Object.keys(d).forEach(function(k) { if (!(k in LABELS)) rest[k] = d[k]; });
    el("popupbody").innerHTML = "<table>" + rowsHtml + "</table>" +
      "<p class='note'>Dữ liệu gốc còn lại của lệnh (nguyên văn):</p><pre>" +
      esc(JSON.stringify(rest, null, 2)) + "</pre>";
    el("overlay").style.display = "flex";
  }).catch(function() {
    el("popuptitle").textContent = "Không tải được chi tiết";
    el("popupbody").textContent = "Lỗi tải /api/trade/" + id + ".json — thử lại ở lần làm mới sau.";
    el("overlay").style.display = "flex";
  });
}
function closePopup() { el("overlay").style.display = "none"; }
el("overlay").addEventListener("click", function(ev) { if (ev.target === el("overlay")) closePopup(); });

/* ---------------- refresh loop (30 s) ---------------- */
function tick() {
  fetch("/api/snapshot.json", {cache: "no-store"}).then(function(r) {
    if (!r.ok) throw new Error("HTTP " + r.status);
    return r.json();
  }).then(function(env) {
    if (!env || !env.snapshot) {
      el("badge").textContent = "DATA ERROR";
      el("badge").className = "badge error";
      el("statusreason").textContent = "snapshot lỗi hoặc chưa từng build thành công — thử lại ở vòng sau.";
      el("lastupdate").textContent = "Không đọc được dữ liệu";
      return;
    }
    render(env);
    var app = env.app || {};
    var lu = app.last_ok_refresh_utc ? ("Cập nhật lần cuối: " + fmtTime(app.last_ok_refresh_utc) + " (địa phương)") : "Chưa có lần cập nhật hợp lệ";
    if (app.engine_build_error) lu += " · lần build gần nhất LỖI — đang giữ snapshot cũ";
    STATE.baseMsg = lu;
    el("lastupdate").textContent = lu;
  }).catch(function(e) {
    el("badge").textContent = "DATA ERROR";
    el("badge").className = "badge error";
    el("lastupdate").textContent = "Lỗi kết nối server nội bộ: " + e;
  });
  STATE.countdown = 30;
}
tick();
setInterval(tick, 30000);
setInterval(function() {
  STATE.countdown -= 1;
  if (STATE.countdown < 0) STATE.countdown = 0;
  if (STATE.baseMsg) {
    el("lastupdate").textContent = STATE.baseMsg + " · làm mới sau " + STATE.countdown + "s";
  }
}, 1000);
</script>
</body>
</html>
"""

PAGE_HTML_BYTES = PAGE_HTML.replace("{LOGO_SRC}", LOGO_DATA_URI).encode("utf-8")
