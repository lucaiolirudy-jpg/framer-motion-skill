// node mannequin_render.js angles.json outdir   (angles: [[theta,phi],...])
const { chromium } = require('playwright'); const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = __dirname;
const srv = http.createServer((q, r) => { const f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0])); if (!fs.existsSync(f)) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': f.endsWith('.js') ? 'text/javascript' : f.endsWith('.html') ? 'text/html' : 'application/octet-stream' }); fs.createReadStream(f).pipe(r); }).listen(0);
(async () => {
  const A = JSON.parse(fs.readFileSync(process.argv[2])); const out = process.argv[3]; fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const pg = await b.newPage({ viewport: { width: 600, height: 800 } });
  pg.on('pageerror', e => console.error('PAGEERR', e.message));
  await pg.goto(`http://localhost:${srv.address().port}/mannequin.html`); await pg.waitForFunction(() => window.READY === true, null, { timeout: 60000 });
  for (let i = 0; i < A.length; i++) {
    const d = await pg.evaluate(([t, p, y]) => { window.pose(t, p, y); return window.grab(); }, [A[i][0], A[i][1], A[i][2] ?? 0.5]);
    fs.writeFileSync(path.join(out, String(i).padStart(4, '0') + '.png'), Buffer.from(d.split(',')[1], 'base64'));
  }
  await b.close(); srv.close(); console.log('done', A.length);
})();
