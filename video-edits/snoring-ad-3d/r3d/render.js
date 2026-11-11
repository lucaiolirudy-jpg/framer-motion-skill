// usage: node render.js jobs.json   jobs: [{name, scene, params, dur, out}]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = __dirname;
const srv = http.createServer((req, res) => {
  const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!f.startsWith(ROOT) || !fs.existsSync(f)) { res.writeHead(404); return res.end(); }
  const ext = path.extname(f); res.writeHead(200, { 'Content-Type': ext === '.js' ? 'text/javascript' : ext === '.html' ? 'text/html' : 'application/octet-stream' });
  fs.createReadStream(f).pipe(res);
}).listen(0);
(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[2]));
  const port = srv.address().port;
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('console', m => { if (m.type() === 'error') console.error('PAGE', m.text()); });
  page.on('pageerror', e => console.error('PAGEERR', e.message));
  await page.goto(`http://localhost:${port}/index.html`);
  await page.waitForFunction(() => window.READY === true, null, { timeout: 120000 });
  const FPS = 30;
  for (const j of jobs) {
    if (j.skipIfExists && fs.existsSync(j.out)) continue;
    const t0 = Date.now();
    await page.evaluate(([n, p]) => window.setupScene(n, p), [j.scene, j.params || {}]);
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', j.out]);
    const n = Math.round(j.dur * FPS);
    for (let i = 0; i < n; i++) {
      const data = await page.evaluate((t) => { window.renderAt(t); return window.grab(0.93); }, i / FPS);
      const buf = Buffer.from(data.split(',')[1], 'base64');
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
    console.log(`${j.out} ${n}f ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  }
  await b.close(); srv.close();
})().catch(e => { console.error(e); process.exit(1); });
