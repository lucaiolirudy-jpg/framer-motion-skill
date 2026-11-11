const { chromium } = require('playwright'); const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = __dirname;
const srv = http.createServer((req, res) => { const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0])); if (!fs.existsSync(f)) { res.writeHead(404); return res.end(); } res.writeHead(200, { 'Content-Type': f.endsWith('.js') ? 'text/javascript' : f.endsWith('.html') ? 'text/html' : 'application/octet-stream' }); fs.createReadStream(f).pipe(res); }).listen(0);
(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[2])); const outdir = process.argv[3];
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const page = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('pageerror', e => console.error('PAGEERR', e.message)); page.on('console', m => { if (m.type() === 'error') console.error('PAGE', m.text()); });
  await page.goto(`http://localhost:${srv.address().port}/index.html`); await page.waitForFunction(() => window.READY === true, null, { timeout: 120000 });
  for (const j of jobs) {
    await page.evaluate(([n, p]) => window.setupScene(n, p), [j.scene, j.params || {}]);
    for (const t of (j.times || [0.4, 1.0, 2.0])) {
      // run sequentially up to t for stateful scenes
      const d = await page.evaluate((t) => { window.renderAt(t); return window.grab(0.9); }, t);
      fs.writeFileSync(path.join(outdir, `${j.id || j.scene}_${t}.jpg`), Buffer.from(d.split(',')[1], 'base64'));
    }
  }
  await b.close(); srv.close();
})();
