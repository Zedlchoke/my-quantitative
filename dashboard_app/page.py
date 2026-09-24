"""The dashboard page (self-contained HTML/CSS/JS, no CDN).

Two tabs: "Tổng quan" (header status -> top strip -> family cards cho
MỌI family mà engine snapshot trả về — không hard-code số lượng —
-> one chart area (Tổng crypto + từng family) -> one
trades table with click-through detail) and "Daily/Weekly PNL" (a
Vietnam-timezone calendar — green profit / red loss days — plus weekly
[Wed 00:00 VN → Tue 24:00 VN] and monthly [rolls at 00:00 VN on the
1st] PnL tables over the same fail-closed combined history). A sleeve
mounted giữa chừng (BTC4H-BANDRIDGE) hiện như family thứ tư: số liệu
từ API hiện có (equity $100,000, 0 vị thế, 0 fill khi chưa có lệnh);
lịch sử trước mount giữ nguyên là chuỗi 3 sleeve và khoản vốn thêm
được đánh dấu là capital flow, không phải lợi nhuận. The page polls
``/api/snapshot.json`` every 30 s and re-renders; rendering is
pure client-side over the engine snapshot (no invented values: missing
fields render N/A)."""

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
  .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 10px; margin-top: 12px; }
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
  /* ---- tabs ---- */
  .tabs { display: flex; gap: 6px; max-width: 1440px; margin: 10px auto 0; padding: 0 18px; }
  .tabs button {
    border: 1px solid var(--line); border-bottom: none; background: #e9ebee;
    color: var(--muted); border-radius: 9px 9px 0 0; padding: 8px 18px;
    font-size: 13px; font-weight: 600; cursor: pointer;
  }
  .tabs button.on { background: var(--card); color: var(--ink); }
  .strip4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
  /* ---- pnl calendar ---- */
  .calhead { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 8px; }
  .calhead h2 { margin: 0; }
  .calnav button {
    border: 1px solid var(--line); background: #fff; border-radius: 8px;
    padding: 3px 11px; cursor: pointer; font-size: 13px; color: var(--ink);
  }
  .calnav button:disabled { opacity: .35; cursor: default; }
  .caldow, .calgrid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; }
  .caldow div { text-align: center; color: var(--muted); font-size: 11px; font-weight: 600; padding: 3px 0; }
  .daycell { min-height: 64px; border: 1px solid var(--line); border-radius: 8px; padding: 5px 7px; background: #fff; }
  .daycell.dgreen { background: var(--greenbg); border-color: #b7dfc3; }
  .daycell.dred { background: var(--redbg); border-color: #f3c1bd; }
  .daycell.dnone { background: #f6f7f9; border-color: #eceef1; }
  .daycell.dout { border: none; background: transparent; }
  .daycell.dtoday { outline: 2px solid #101828; outline-offset: -2px; }
  .daycell .dn { font-size: 11px; color: var(--muted); font-weight: 600; }
  .daycell .pv { font-size: 13.5px; font-weight: 700; margin-top: 7px; font-variant-numeric: tabular-nums; white-space: nowrap; }
  .daycell .pe { font-size: 10.5px; color: var(--muted); margin-top: 1px; font-variant-numeric: tabular-nums; }
  .legend { display: flex; gap: 14px; align-items: center; margin-top: 8px; font-size: 11px; color: var(--muted); flex-wrap: wrap; }
  .legend .sw { display: inline-block; width: 12px; height: 12px; border-radius: 3px; margin-right: 4px; vertical-align: -1px; border: 1px solid var(--line); }
  table.pnltable { border-collapse: collapse; width: 100%; font-size: 12px; font-variant-numeric: tabular-nums; }
  table.pnltable th {
    text-align: right; color: var(--muted); border-bottom: 1px solid var(--line);
    padding: 5px 8px; font-weight: 600; white-space: nowrap;
  }
  table.pnltable th.l, table.pnltable td.l { text-align: left; }
  table.pnltable td { text-align: right; padding: 5px 8px; border-bottom: 1px solid #f0f1f3; white-space: nowrap; }
  @media (max-width: 1100px) { .strip { grid-template-columns: repeat(2, 1fr); } .cards { grid-template-columns: 1fr; } .strip4 { grid-template-columns: repeat(2, 1fr); } }
</style>
</head>
<body>
<header>
  <img class="logo" src="{LOGO_SRC}" alt="logo">
  <div>
    <h1>Quant Shadow Dashboard</h1>
    <div class="sub">PROSPECTIVE-SHADOW-V1 · paper/shadow (không phải live trading) · vốn ban đầu 400,000 USDT (4 sleeve crypto)</div>
  </div>
  <span id="badge" class="badge stale">…</span>
  <div id="lastupdate"></div>
  <div id="statusreason"></div>
</header>

<div class="tabs">
  <button id="tab-overview" class="on">Tổng quan</button>
  <button id="tab-pnl">Daily/Weekly PNL</button>
</div>

<main id="main-overview">
  <div class="strip" id="strip"></div>
  <div class="cards" id="cards"></div>

  <div class="section">
    <h2>Equity theo thời gian</h2>
    <div class="btns" id="chartbtns">
      <button data-k="combined" class="on">Tổng crypto</button>
    </div>
    <div id="chartwrap">
      <svg id="chart" viewBox="0 0 1000 330" preserveAspectRatio="none"></svg>
      <div id="tip"></div>
    </div>
    <div class="note">Đường đứt là vốn gốc hiện hành (mỗi family $100,000; nạp thêm giữa chừng hiện thành bước vốn, không phải lợi nhuận). Khoảng mất dữ liệu không được nội suy — bị bỏ hở (fail-closed).</div>
  </div>

  <div class="section">
    <h2>Tất cả lệnh (4 family crypto)</h2>
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

<main id="main-pnl" style="display:none">
  <div id="pnlold" style="display:none" class="banner">
    Envelope chưa có khối pnl_periods (schema app cũ) — tab này cần app build mới.
  </div>
  <div id="pnlbody">
    <div class="strip strip4" id="pnlstrip"></div>

    <div class="section">
      <div class="calhead">
        <h2 id="caltitle">Lịch PnL hàng ngày</h2>
        <div class="calnav">
          <button id="calprev" title="Tháng trước">◀</button>
          <button id="calnext" title="Tháng sau">▶</button>
        </div>
        <span id="calmonthpnl" style="font-weight:700"></span>
      </div>
      <div class="caldow">
        <div>T2</div><div>T3</div><div>T4</div><div>T5</div><div>T6</div><div>T7</div><div>CN</div>
      </div>
      <div class="calgrid" id="calgrid"></div>
      <div class="legend">
        <span><span class="sw" style="background:var(--greenbg)"></span>lãi (giờ VN)</span>
        <span><span class="sw" style="background:var(--redbg)"></span>lỗ</span>
        <span><span class="sw" style="background:#f6f7f9"></span>không có mark hợp lệ (fail-closed)</span>
        <span>ô viền đậm = hôm nay</span>
        <span>bấm giữ chuột lên ô để xem chi tiết mark đầu/cuối</span>
      </div>
    </div>

    <div class="section">
      <h2>PnL theo tuần (00:00 thứ Tư → 24:00 thứ Ba, giờ VN)</h2>
      <div class="tblwrap" style="max-height:340px">
        <table class="pnltable">
          <thead><tr>
            <th class="l">Tuần</th><th>PnL $</th><th>PnL %</th>
            <th>Equity cuối</th><th>Số mark</th><th class="l">Mark cuối</th>
          </tr></thead>
          <tbody id="weeklybody"></tbody>
        </table>
      </div>
    </div>

    <div class="section">
      <h2>PnL theo tháng (chốt 00:00 ngày 1, giờ VN)</h2>
      <table class="pnltable">
        <thead><tr>
          <th class="l">Tháng</th><th>PnL $</th><th>PnL %</th>
          <th>Equity cuối</th><th>Số mark</th><th class="l">Mark cuối</th>
        </tr></thead>
        <tbody id="monthlybody"></tbody>
      </table>
    </div>

    <div class="note" id="pnlnote"></div>
  </div>
</main>

<div id="overlay"><div id="popup">
  <button class="close" onclick="closePopup()">Đóng</button>
  <h3 id="popuptitle"></h3>
  <div id="popupbody"></div>
</div></div>

<script>
"use strict";
var STATE = {env: null, chart: "combined", sortDesc: true, timer: null, countdown: 30, baseMsg: "", tab: "overview", pp: null};
var PNL = {cursor: null}; // tháng đang xem trên lịch {y, m} — giờ VN
var PNL_TZ = "Asia/Ho_Chi_Minh";
// Tên ngắn đã biết; mọi family KHÁC vẫn hiển thị (fallback = mã đầy đủ)
// — danh sách family luôn lấy từ API, không hard-code số lượng.
var FAM_SHORT = {"XSECT-FUND-CARRY-7D": "XSECT", "ILLIQ-AMIHUD-28D-W": "ILLIQ",
  "BASISLV-PREMFADE-28D": "BASISLV", "BTC4H-BANDRIDGE": "BANDRIDGE"};
function famList(env) {
  var fams = env && env.snapshot && env.snapshot.valuation &&
    env.snapshot.valuation.families || {};
  return Object.keys(fams).sort(function(a, b) {
    function first(fid) {
      var s = fams[fid] && fams[fid].series;
      return s && s.length ? String(s[0].ts) : "9999";
    }
    var fa = first(a), fb = first(b);
    return fa < fb ? -1 : fa > fb ? 1 : (a < b ? -1 : 1);
  });
}
function famShort(fid) { return FAM_SHORT[fid] || fid; }

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
  strip.push(box("Tổng equity (" + famList(env).length + " sleeve crypto)", fmtUSD(eq), "",
    vc && vc.as_of_utc ? ("mark " + fmtTime(vc.as_of_utc)) : ""));
  strip.push(box("Tổng PnL crypto", fmtUSD(tpnl), pnlClass(tpnl), "từ vốn ban đầu $400,000"));
  strip.push(box("Tổng PnL crypto %", fmtPct(tpct), pnlClass(tpct), "400,000 USDT gốc"));
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
    '<div class="box" style="grid-column: span 5;"><div class="lbl">Realized / Unrealized (' + famList(env).length + ' family crypto, mark ' +
    esc(ru.mark_timestamp_utc || "") + ')</div><div class="sml">' + ruNote + '</div></div>');

  var fams = snap && snap.valuation ? snap.valuation.families : null;
  var html = "";
  famList(env).forEach(function(fid) {
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
  el("cards").innerHTML = html;
  renderChartButtons(env);

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
  renderPnl(env);

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
function renderChartButtons(env) {
  var wrap = el("chartbtns");
  var want = ["combined"].concat(famList(env));
  var have = Array.prototype.map.call(wrap.querySelectorAll("button"), function(b) {
    return b.getAttribute("data-k");
  });
  var same = want.length === have.length && want.every(function(k, i) { return have[i] === k; });
  if (same) return;
  var hist = (env && env.app && env.app.combined_history) || {};
  var flows = hist.capital_flows || [];
  var total = (hist.baseline_equity || 0) + flows.reduce(function(acc, f) {
    return acc + (typeof f.amount_usdt === "number" ? f.amount_usdt : 0);
  }, 0);
  var combinedLabel = "Crypto " + (total ? Math.round(total).toLocaleString("en-US") : "400K");
  wrap.innerHTML = want.map(function(k, i) {
    var label = k === "combined" ? combinedLabel : famShort(k);
    return '<button data-k="' + esc(k) + '"' + (i === 0 ? ' class="on"' : "") + ">" + esc(label) + "</button>";
  }).join("");
  if (want.indexOf(STATE.chart) < 0) STATE.chart = "combined";
}
function chartSeries() {
  var env = STATE.env, snap = env && env.snapshot;
  if (!snap || !snap.valuation) return {pts: [], baseline: null, hist: null};
  if (STATE.chart === "combined") {
    var hist = (env.app || {}).combined_history;
    if (hist && hist.series && hist.series.length) {
      var flows = hist.capital_flows || [];
      var total = (hist.baseline_equity || 0) + flows.reduce(function(acc, f) {
        return acc + (typeof f.amount_usdt === "number" ? f.amount_usdt : 0);
      }, 0);
      return {pts: hist.series, baseline: total || null, hist: hist};
    }
    return {pts: (snap.valuation.combined || {}).series || [], baseline: null, hist: null};
  }
  var f = (snap.valuation.families || {})[STATE.chart];
  return {pts: (f && f.series) || [], baseline: 100000, hist: null};
}
function baselineAt(data, tMs) {
  // vốn gốc tại thời điểm t: baseline + các capital flow đã nạp tới t
  var base = data.baseline || 0;
  var hist = data.hist;
  if (!hist) return base;
  var cum = base;
  (hist.capital_flows || []).forEach(function(f) {
    var ft = new Date(f.ts_utc).getTime();
    if (!isNaN(ft) && ft <= tMs && typeof f.amount_usdt === "number") cum += f.amount_usdt;
  });
  return cum;
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
  var hasBase = typeof data.baseline === "number" && isFinite(data.baseline);
  var ymin = Infinity, ymax = -Infinity;
  valid.forEach(function(p) { ymin = Math.min(ymin, p.equity); ymax = Math.max(ymax, p.equity); });
  if (hasBase) {
    ymin = Math.min(ymin, data.baseline); ymax = Math.max(ymax, data.baseline);
    (data.hist && data.hist.capital_flows || []).forEach(function(f) {
      if (typeof f.amount_usdt === "number") { ymin = Math.min(ymin, f.amount_usdt); ymax = Math.max(ymax, f.amount_usdt); }
    });
  }
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
  // baseline: đường bước khi có capital flow (vốn gốc → sau nạp),
  // đường đứt đơn khi không có flow
  function drawDashed(x1, x2, v, label) {
    var y = Y(v);
    out.push('<line x1="' + x1 + '" y1="' + y + '" x2="' + x2 + '" y2="' + y + '" stroke="#9aa2af" stroke-dasharray="6 5" stroke-width="1.2"/>');
    if (label) out.push('<text x="' + (x2 - 4) + '" y="' + (y - 4) + '" text-anchor="end" font-size="10" fill="#6b7280">' + label + '</text>');
  }
  if (hasBase && data.hist && (data.hist.capital_flows || []).some(function(f) { return typeof f.amount_usdt === "number"; })) {
    var bounds = [t0].concat(data.hist.capital_flows
      .map(function(f) { var ft = new Date(f.ts_utc).getTime(); return isNaN(ft) ? null : ft; })
      .filter(function(v) { return v !== null && v > t0 && v < t1; }).sort(function(a, b) { return a - b; }));
    bounds.push(t1);
    for (var bi = 0; bi < bounds.length - 1; bi++) {
      var mid = (bounds[bi] + bounds[bi + 1]) / 2;
      drawDashed(X(bounds[bi]), X(bounds[bi + 1]), baselineAt(data, mid),
        bi === bounds.length - 2 ? ("vốn hiện hành " + Math.round(baselineAt(data, mid)).toLocaleString("en-US")) : null);
    }
    data.hist.capital_flows.forEach(function(f) {
      var ft = new Date(f.ts_utc).getTime();
      if (isNaN(ft) || ft <= t0 || ft >= t1 || typeof f.amount_usdt !== "number") return;
      var fx = X(ft);
      out.push('<line x1="' + fx + '" y1="' + T + '" x2="' + fx + '" y2="' + (H - B) + '" stroke="#d29922" stroke-dasharray="3 4" stroke-width="1"/>');
      out.push('<text x="' + (fx + 5) + '" y="' + (T + 10) + '" font-size="10" fill="#9a6700">＋' +
        Math.round(f.amount_usdt).toLocaleString("en-US") + " vốn " + esc(famShort(f.family_id)) + " (capital flow, không phải lợi nhuận)</text>");
    });
  } else if (hasBase) {
    drawDashed(L, W - R, data.baseline, "vốn ban đầu " + data.baseline.toLocaleString("en-US"));
  }
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
  svg._data = data;
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
    var base = svg._data ? baselineAt(svg._data, new Date(best.ts).getTime()) : g.baseline;
    var pnl = best.equity - base, pct = base ? pnl / base * 100 : null;
    tip.innerHTML = "<b>" + fmtTime(best.ts) + "</b><br>Equity: " + fmtUSD(best.equity) +
      "<br>PnL: " + fmtUSD(pnl) + " (" + fmtPct(pct) + ")";
    tip.style.display = "block";
    var wrap = el("chartwrap").getBoundingClientRect();
    tip.style.left = Math.min(ev.clientX - wrap.left + 12, wrap.width - 190) + "px";
    tip.style.top = (ev.clientY - wrap.top - 10) + "px";
  });
  svg.addEventListener("mouseleave", function() { tip.style.display = "none"; });
})();

/* ---------------- daily/weekly pnl tab ---------------- */
function vnDateStr(d) {
  // ngày lịch của thời điểm d theo giờ Việt Nam: "YYYY-MM-DD"
  var parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: PNL_TZ, year: "numeric", month: "2-digit", day: "2-digit"
  }).formatToParts(d);
  var o = {};
  parts.forEach(function(p) { if (p.type !== "literal") o[p.type] = p.value; });
  return o.year + "-" + o.month + "-" + o.day;
}
function keyOf(y, m) { return y + "-" + (m < 10 ? "0" + m : m); }
function pnlCls(e) {
  return !e || e.pnl_usdt === null || e.pnl_usdt === undefined ? "neu" : pnlClass(e.pnl_usdt);
}
function showTab(name) {
  STATE.tab = name;
  el("main-overview").style.display = name === "overview" ? "" : "none";
  el("main-pnl").style.display = name === "pnl" ? "" : "none";
  el("tab-overview").className = name === "overview" ? "on" : "";
  el("tab-pnl").className = name === "pnl" ? "on" : "";
}
function stripBoxPnl(lbl, entry, sub) {
  var cls = pnlCls(entry), val = entry && entry.pnl_usdt !== null && entry.pnl_usdt !== undefined ? fmtUSD(entry.pnl_usdt) : "N/A";
  var sml = sub || (entry ? (entry.label + (entry.open ? " · chưa đóng" : "") + " · " + fmtPct(entry.pnl_pct)) : "chưa có mark hợp lệ trong kỳ");
  return '<div class="box"><div class="lbl">' + lbl + '</div><div class="val ' + cls + '">' + val + '</div><div class="sml">' + sml + '</div></div>';
}
function renderPnl(env) {
  var pp = env && env.app && env.app.pnl_periods;
  if (!pp) {
    el("pnlbody").style.display = "none";
    el("pnlold").style.display = "";
    return;
  }
  el("pnlbody").style.display = "";
  el("pnlold").style.display = "none";
  STATE.pp = pp;
  var daily = pp.daily || [], weekly = pp.weekly || [], monthly = pp.monthly || [];
  var lastD = daily[daily.length - 1];
  var todayKey = vnDateStr(new Date());
  var strip = [];
  strip.push(stripBoxPnl("PnL tháng này", monthly[monthly.length - 1]));
  strip.push(stripBoxPnl("PnL tuần này (T4 → T3)", weekly[weekly.length - 1]));
  strip.push(stripBoxPnl("PnL hôm nay", lastD && lastD.key === todayKey ? lastD : null,
    lastD && lastD.key !== todayKey ? "chưa có mark hôm nay (mark cuối " + fmtTime(lastD.end_mark_utc) + ")" : undefined));
  var flowsNote = (pp.capital_flows || []).filter(function(f) { return typeof f.amount_usdt === "number"; })
    .map(function(f) { return "+" + fmtUSD(f.amount_usdt) + " vốn " + esc(famShort(f.family_id)); }).join(" · ");
  strip.push('<div class="box"><div class="lbl">Vốn gốc (sleeve sáng lập)</div><div class="val">' +
    fmtUSD(pp.baseline_equity) + '</div><div class="sml">' +
    (flowsNote ? flowsNote + "<br>" : "") +
    'mark cuối ' + fmtTime(pp.last_mark_utc) +
    ' (giờ VN) · ' + pp.point_count + ' mark hợp lệ</div></div>');
  el("pnlstrip").innerHTML = strip.join("");

  if (!PNL.cursor) {
    var base = pp.last_mark_utc ? vnDateStr(new Date(pp.last_mark_utc)) : todayKey;
    PNL.cursor = {y: +base.slice(0, 4), m: +base.slice(5, 7)};
  }
  drawCalendar();
  renderPeriodTable("weeklybody", weekly);
  renderPeriodTable("monthlybody", monthly);
  el("pnlnote").innerHTML =
    "Quy ước (owner 23/09/2026, bổ sung 24/09/2026): mọi ranh giới ngày/tuần/tháng chốt tại 00:00 (12 giờ đêm) <b>giờ Việt Nam (UTC+7)</b> — " +
    "tháng hiện tại được tính liên tục tới mark mới nhất, không chốt sớm. " +
    "Tuần bắt đầu 00:00 <b>thứ Tư</b> và kết thúc 24:00 thứ Ba — tuần hiện tại bắt đầu từ thứ Tư của tuần trước. " +
    "PnL một kỳ = equity mark cuối kỳ − equity mark gần nhất trước đầu kỳ − <b>vốn thêm nạp trong kỳ</b> (capital flow, " +
    "không tính là lợi nhuận); kỳ đầu nối từ vốn gốc của các sleeve sáng lập (" + esc(fmtUSD(pp.baseline_equity)) +
    "). Trước khi sleeve thứ tư (BANDRIDGE) được mount, chuỗi là tổng 3 sleeve sáng lập — lịch sử đó giữ nguyên. " +
    "Chỉ dùng mark hợp lệ (strict sum các sleeve đã mount tại mark chung); " +
    "kỳ không có mark hợp lệ thì <b>không có số</b> (fail-closed, không nội suy, không kéo giá trị cũ).";
}
function drawCalendar() {
  var pp = STATE.pp; if (!pp) return;
  var daily = pp.daily || [], monthly = pp.monthly || [];
  var y = PNL.cursor.y, m = PNL.cursor.m;
  el("caltitle").textContent = "Lịch PnL tháng " + (m < 10 ? "0" + m : m) + "/" + y + " (giờ VN)";
  var monthEntry = null;
  monthly.forEach(function(e) { if (e.key === keyOf(y, m)) monthEntry = e; });
  var mt = el("calmonthpnl");
  if (monthEntry && monthEntry.pnl_usdt !== null && monthEntry.pnl_usdt !== undefined) {
    mt.innerHTML = 'PnL tháng: <span class="' + pnlClass(monthEntry.pnl_usdt) + '">' + fmtUSD(monthEntry.pnl_usdt) +
      " (" + fmtPct(monthEntry.pnl_pct) + ')</span>' +
      (monthEntry.open ? ' <span class="note">· chưa đóng, tính tới mark ' + fmtTime(monthEntry.end_mark_utc) + "</span>" : "");
  } else {
    mt.textContent = "Chưa có mark hợp lệ trong tháng này";
  }
  var firstKey = daily.length ? daily[0].key.slice(0, 7) : null;
  var lastKey = daily.length ? daily[daily.length - 1].key.slice(0, 7) : null;
  var curKey = keyOf(y, m);
  el("calprev").disabled = !firstKey || curKey <= firstKey;
  el("calnext").disabled = !lastKey || curKey >= lastKey;
  var firstWd = (new Date(y, m - 1, 1).getDay() + 6) % 7; // T2 = 0
  var nDays = new Date(y, m, 0).getDate();
  var map = {};
  daily.forEach(function(e) { map[e.key] = e; });
  var todayKey = vnDateStr(new Date());
  var html = "";
  for (var i = 0; i < firstWd; i++) html += '<div class="daycell dout"></div>';
  for (var d = 1; d <= nDays; d++) {
    var key = keyOf(y, m) + "-" + (d < 10 ? "0" + d : d);
    var e2 = map[key];
    var cls = "daycell", val = "", title = key;
    if (e2 && e2.pnl_usdt !== null && e2.pnl_usdt !== undefined) {
      cls += e2.pnl_usdt > 0 ? " dgreen" : e2.pnl_usdt < 0 ? " dred" : "";
      val = '<div class="pv ' + pnlClass(e2.pnl_usdt) + '">' + fmtUSD(e2.pnl_usdt) + '</div>' +
        '<div class="pe">' + fmtPct(e2.pnl_pct) + (e2.capital_flows_usdt ? " · có nạp vốn" : "") + "</div>";
      title = key + " · mark " + (e2.start_from_seed ? "vốn gốc" : fmtTime(e2.start_mark_utc)) +
        " → " + fmtTime(e2.end_mark_utc) + " · equity " + fmtUSD(e2.start_equity) +
        " → " + fmtUSD(e2.end_equity) + " · " + e2.marks + " mark hợp lệ" +
        (e2.capital_flows_usdt ? " · ĐÃ NẠP VỐN +" + fmtUSD(e2.capital_flows_usdt) + " (" +
          (e2.capital_flow_families || []).map(famShort).join(", ") + ") — không tính là PnL" : "");
    } else if (e2) {
      val = '<div class="pv neu">N/A</div>';
      title = key + " · có mark nhưng thiếu mốc so sánh (fail-closed)";
    } else {
      cls += " dnone";
    }
    if (key === todayKey) cls += " dtoday";
    html += '<div class="' + cls + '" title="' + esc(title) + '"><div class="dn">' + d + "</div>" + val + "</div>";
  }
  el("calgrid").innerHTML = html;
}
function renderPeriodTable(tbodyId, rows) {
  var body = rows.slice().reverse().map(function(e) {
    var cls = pnlCls(e);
    return "<tr>" +
      '<td class="l"><b>' + esc(e.label) + "</b>" + (e.open ? ' <span class="chip warn">chưa đóng</span>' : "") +
      (e.capital_flows_usdt ? ' <span class="note" title="vốn thêm đã bị trừ khỏi PnL — không tính là lợi nhuận">nạp vốn +' +
        fmtUSD(e.capital_flows_usdt) + " (" + esc((e.capital_flow_families || []).map(famShort).join(", ")) + ")</span>" : "") + "</td>" +
      '<td class="' + cls + '">' + fmtUSD(e.pnl_usdt) + "</td>" +
      '<td class="' + cls + '">' + fmtPct(e.pnl_pct) + "</td>" +
      "<td>" + fmtUSD(e.end_equity) + "</td>" +
      "<td>" + e.marks + "</td>" +
      '<td class="l note">' + fmtTime(e.end_mark_utc) + "</td></tr>";
  });
  el(tbodyId).innerHTML = body.join("") ||
    '<tr><td colspan="6" class="l note">Chưa có mark hợp lệ nào (NOT_RUN — fail-closed, không bịa số).</td></tr>';
}
function shiftMonth(delta) {
  var c = PNL.cursor; if (!c) return;
  var m = c.m + delta, y = c.y;
  if (m < 1) { m = 12; y--; }
  if (m > 12) { m = 1; y++; }
  PNL.cursor = {y: y, m: m};
  drawCalendar();
}
el("tab-overview").addEventListener("click", function() { showTab("overview"); });
el("tab-pnl").addEventListener("click", function() { showTab("pnl"); });
el("calprev").addEventListener("click", function() { shiftMonth(-1); });
el("calnext").addEventListener("click", function() { shiftMonth(1); });

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
  var fams = famList(env);
  var sel = famSel.value;
  var opts = '<option value="">Mọi family</option>' + fams.map(function(fid) {
    return '<option value="' + esc(fid) + '">' + esc(famShort(fid)) + " (" + esc(fid) + ")</option>";
  }).join("");
  if (famSel.dataset.fams !== fams.join(",")) {
    famSel.innerHTML = opts;
    famSel.dataset.fams = fams.join(",");
    famSel.value = fams.indexOf(sel) >= 0 ? sel : "";
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
      '<td class="l">' + esc(famShort(t.family)) + "</td>" +
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
    el("popuptitle").textContent = (d.asset || "lệnh") + " · " + (famShort(d.family) || d.family || "") + " · " + id;
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
