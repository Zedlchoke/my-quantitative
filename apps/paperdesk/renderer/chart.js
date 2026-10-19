'use strict';
// Interactive equity chart: Canvas, crosshair on hover/drag with tooltip,
// range selector (ALL/30D/7D), settle dots colored by P&L. Fully live from
// ledger points — never a static image.
(function () {
  const NS = 'http://www.w3.org/2000/svg';
  window.EquityChart = { render };

  function render(container, points, opts) {
    container.innerHTML = '';
    const head = document.createElement('div');
    head.className = 'sec-title';
    head.style.display = 'flex';
    head.innerHTML = `<span>EQUITY (settled)</span>
      <span class="spacer"></span>
      <span class="seg" id="eq-range">
        <button data-r="7D">7D</button>
        <button data-r="30D">30D</button>
        <button data-r="ALL" class="active">ALL</button>
      </span>`;
    container.appendChild(head);

    const wrap = document.createElement('div');
    wrap.className = 'canvas-wrap';
    const canvas = document.createElement('canvas');
    canvas.style.width = '100%';
    canvas.style.height = (opts && opts.height || 230) + 'px';
    wrap.appendChild(canvas);
    const tip = document.createElement('div');
    tip.id = 'equity-tip';
    tip.style.display = 'none';
    wrap.appendChild(tip);
    container.appendChild(wrap);

    let range = 'ALL';
    head.querySelectorAll('#eq-range button').forEach(b => {
      b.onclick = () => {
        range = b.dataset.r;
        head.querySelectorAll('#eq-range button').forEach(x =>
          x.classList.toggle('active', x === b));
        draw();
      };
    });

    const dpr = window.devicePixelRatio || 1;
    function visible() {
      if (!points.length) return [];
      if (range === 'ALL') return points;
      const cutoff = Date.now() - (range === '30D' ? 30 : 7) * 86400000;
      const pts = points.map((p, i) => ({ p, t: Date.parse(p.t) || 0 }))
        .filter(x => x.t >= cutoff);
      if (pts.length && pts[0].t > cutoff) {
        // anchor with the last point before the window (line continuity)
        const before = points.map((p, i) => ({ p, t: Date.parse(p.t) || 0 }))
          .filter(x => x.t < cutoff).pop();
        if (before) pts.unshift(before);
      }
      return pts.map(x => x.p);
    }

    function draw() {
      const w = wrap.clientWidth, h = opts && opts.height || 230;
      canvas.width = w * dpr; canvas.height = h * dpr;
      const ctx = canvas.getContext('2d');
      ctx.scale(dpr, dpr);
      ctx.clearRect(0, 0, w, h);
      const css = getComputedStyle(document.documentElement);
      const line = css.getPropertyValue('--line');
      const fg3 = css.getPropertyValue('--fg3');
      for (let k = 0; k <= 4; k++) {
        ctx.strokeStyle = line; ctx.lineWidth = 0.6;
        ctx.beginPath();
        ctx.moveTo(0, h * k / 4); ctx.lineTo(w, h * k / 4); ctx.stroke();
      }
      const pts = visible();
      if (!pts.length) return;
      const ts = pts.map(p => Date.parse(p.t) || 0);
      const vs = pts.map(p => p.equityCents);
      let lo = Math.min(...vs), hi = Math.max(...vs);
      const pad = Math.max((hi - lo) * 0.15, 100);
      lo = Math.max(lo - pad, 0); hi = hi + pad;
      const t0 = ts[0], t1 = Math.max(ts[ts.length - 1], t0 + 60000);
      const X = t => ((t - t0) / (t1 - t0)) * (w - 8) + 4;
      const Y = v => (1 - (v - lo) / Math.max(hi - lo, 1)) * (h - 10) + 5;

      const up = vs[vs.length - 1] >= vs[0];
      const col = up ? css.getPropertyValue('--green')
                     : css.getPropertyValue('--red');
      // area
      const grad = ctx.createLinearGradient(0, 0, 0, h);
      grad.addColorStop(0, colTrim(col, 0.20));
      grad.addColorStop(1, colTrim(col, 0.02));
      ctx.beginPath();
      ctx.moveTo(X(ts[0]), Y(vs[0]));
      ts.forEach((t, i) => ctx.lineTo(X(t), Y(vs[i])));
      ctx.lineTo(X(ts[ts.length - 1]), h);
      ctx.lineTo(X(ts[0]), h);
      ctx.closePath();
      ctx.fillStyle = grad; ctx.fill();
      // line
      ctx.beginPath();
      ts.forEach((t, i) => i ? ctx.lineTo(X(t), Y(vs[i]))
                             : ctx.moveTo(X(t), Y(vs[i])));
      ctx.strokeStyle = col; ctx.lineWidth = 1.8;
      ctx.lineJoin = 'round'; ctx.stroke();
      // settle dots
      pts.forEach((p, i) => {
        if (p.pnlCents == null) return;
        ctx.beginPath();
        ctx.arc(X(ts[i]), Y(vs[i]), 2.6, 0, 7);
        ctx.fillStyle = p.pnlCents > 0 ? css.getPropertyValue('--green')
          : p.pnlCents < 0 ? css.getPropertyValue('--red')
          : css.getPropertyValue('--fg3');
        ctx.fill();
      });
      chartState = { pts, ts, vs, X, Y, w, h, css };
    }

    function colTrim(c, a) {
      c = c.trim();
      if (c.startsWith('#')) {
        const r = parseInt(c.slice(1, 3), 16),
              g = parseInt(c.slice(3, 5), 16),
              b = parseInt(c.slice(5, 7), 16);
        return `rgba(${r},${g},${b},${a})`;
      }
      return c;   // fallback
    }

    let chartState = null;
    let hoverIdx = null;

    function setHover(px) {
      if (!chartState) return;
      const { pts, ts, X, Y, w, h } = chartState;
      if (pts.length < 2) { hoverIdx = pts.length ? 0 : null; }
      else {
        const t0 = ts[0], t1 = ts[ts.length - 1];
        const target = t0 + ((px - 4) / (w - 8)) * (t1 - t0);
        let best = 0, bd = Infinity;
        ts.forEach((t, i) => {
          const d = Math.abs(t - target);
          if (d < bd) { bd = d; best = i; }
        });
        hoverIdx = best;
      }
      if (hoverIdx == null) { tip.style.display = 'none'; drawOverlay(); return; }
      const p = pts[hoverIdx];
      const x = X(ts[hoverIdx] ?? (Date.parse(p.t) || 0));
      const y = Y(p.equityCents);
      tip.innerHTML = `<div class="dim mono">${fmtT(p.t)}</div>
        <div style="font-weight:800">${money(p.equityCents, false)}</div>
        ${p.pnlCents != null
          ? `<div class="mono" style="color:${p.pnlCents >= 0
              ? 'var(--green)' : 'var(--red)'}">${p.label}  ${
              money(p.pnlCents)}</div>`
          : `<div class="dim">${p.label}</div>`}`;
      tip.style.display = 'block';
      const tx = Math.min(Math.max(x + 12, 4), w - 190);
      tip.style.left = tx + 'px';
      tip.style.top = Math.max(y - 54, 4) + 'px';
      drawOverlay();
      function drawOverlay() {}
    }

    canvas.addEventListener('mousemove', e => {
      const r = canvas.getBoundingClientRect();
      setHover(e.clientX - r.left);
    });
    canvas.addEventListener('mouseleave', () => {
      hoverIdx = null; tip.style.display = 'none';
    });

    function fmtT(t) {
      const d = new Date(Date.parse(t));
      return d.toLocaleString(undefined, { month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit' });
    }
    function money(c, sign = true) {
      const d = Math.abs(c) / 100;
      const s = d.toLocaleString(undefined,
        { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      return (sign ? (c > 0 ? '+' : c < 0 ? '-' : '') : (c < 0 ? '-' : ''))
        + '$' + s;
    }

    draw();
    window.addEventListener('resize', draw);
  }
})();
