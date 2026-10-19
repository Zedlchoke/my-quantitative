'use strict';
// Icon generator — runs inside Electron (its bundled Chromium draws the
// canvas; the broken CLT Swift toolchain is not involved).
// Usage: npx electron icon_gen.js <out-png-1024>
const { app, BrowserWindow } = require('electron');
const fs = require('fs');

const out = process.argv[2] || '/tmp/paperdesk_icon_1024.png';

app.whenReady().then(async () => {
  const win = new BrowserWindow({ show: false, width: 1100, height: 1100 });
  const html = `<!DOCTYPE html><canvas id="c" width="1024" height="1024">
  </canvas><script>
    const c = document.getElementById('c').getContext('2d');
    const px = 1024;
    // rounded tile
    const inset = px * 0.06, r = px * 0.185;
    const tile = [inset, inset, px - 2*inset, px - 2*inset];
    c.beginPath();
    c.roundRect(...tile, r);
    c.clip();
    const g = c.createLinearGradient(0, 0, px, px);
    g.addColorStop(0, '#17203a'); g.addColorStop(1, '#293657');
    c.fillStyle = g; c.fillRect(0, 0, px, px);
    // grid
    c.strokeStyle = 'rgba(255,255,255,0.09)'; c.lineWidth = px * 0.005;
    for (let k = 1; k <= 3; k++) {
      const y = tile[1] + tile[3] * k / 4;
      c.beginPath(); c.moveTo(tile[0] + px*0.03, y);
      c.lineTo(tile[0] + tile[2] - px*0.03, y); c.stroke();
    }
    // equity polyline
    const pts = [[0.14,0.72],[0.28,0.62],[0.40,0.67],[0.52,0.48],
                 [0.66,0.53],[0.82,0.26]];
    const P = p => [tile[0] + tile[2]*p[0], tile[1] + tile[3]*p[1]];
    c.beginPath();
    c.moveTo(P(pts[0])[0], tile[1] + tile[3]);
    pts.forEach(p => c.lineTo(...P(p)));
    c.lineTo(P(pts[pts.length-1])[0], tile[1] + tile[3]);
    c.closePath();
    const ga = c.createLinearGradient(0, tile[1], 0, tile[1]+tile[3]);
    ga.addColorStop(0, 'rgba(46,224,139,0.28)');
    ga.addColorStop(1, 'rgba(46,224,139,0.03)');
    c.fillStyle = ga; c.fill();
    c.beginPath();
    pts.forEach((p, i) => i ? c.lineTo(...P(p)) : c.moveTo(...P(p)));
    c.strokeStyle = '#35e08b'; c.lineWidth = px * 0.034;
    c.lineCap = 'round'; c.lineJoin = 'round'; c.stroke();
    const last = P(pts[pts.length-1]);
    c.fillStyle = '#ffffff';
    c.beginPath(); c.arc(last[0], last[1], px * 0.028, 0, 7); c.fill();
  </script>`;
  await win.loadURL('data:text/html;charset=utf-8,' +
    encodeURIComponent(html));
  await new Promise(r => setTimeout(r, 300));
  const img = await win.webContents.capturePage();
  fs.writeFileSync(out, img.toPNG());
  console.log('icon png:', out);
  app.exit(0);
});
