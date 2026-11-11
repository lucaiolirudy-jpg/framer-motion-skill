# Snoring ad — 3D cutaways + realistic B-roll + subtitle replica

Pipeline used to edit a 9:16 talking-head ad (5:36) with full-screen cutaways
(3D animations every 3–5 s, realistic photo B-roll for the "solutions already tried"),
re-creating the original burned-in karaoke subtitles on top of every cutaway.
Everything is kept inside the 4:5 safe area (center 1080×1350 of the 1080×1920 frame).

Media (source video, generated photos, rendered clips) is not committed.

## Layout (mirrors the working directory)
- `r3d/` — Three.js scene engine rendered headless with Playwright (SwiftShader WebGL)
  - `index.html` renderer, palette, text/easing helpers
  - `scenes.js` ~30 parametric scenes (decibel, clock, calendar, jaw/airway, bite, battery, shield, …)
  - `render.js jobs.json` renders clips to MP4 (30 fps); `stills.js` renders test frames
- `work/`
  - `transcribe.py` word-level transcript (faster-whisper)
  - `subseg.py` → `subocr.py` → `chunks.py` → `timeline_subs.py`: detect subtitle chunks, OCR them,
    per-frame highlighted word (`yelpass.py`), manual corrections in `subfix.json`
    → `subtimeline.json`
  - `subs.py` subtitle renderer calibrated on the original (Poppins Bold 71px, 0.93 horizontal squeeze,
    3px black outline, yellow `#FCFE00`, single line y=1399, two lines y=1366/1432)
  - `plan_full.py` cutaway plan (times aligned to the words) → `plan_full.json` + render jobs
  - `sfx.py` subtle synthesized whooshes on each cutaway
  - `compose.py` final composite: original video + cutaways + subtitle replica + SFX
  - `review*.py` contact sheets comparing original vs replicated subtitles

## Run
```bash
./fetch_deps.sh
python3 work/plan_full.py <dir>
node r3d/render.js work/jobs_full_0.json
python3 work/compose.py <dir> work/plan_full.json out.mp4
```
