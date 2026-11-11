# RDL form check — wrong vs correct (split screen + singles)

Style copied from a reference clip: vertical split screen with ❌/✅ badges and pose-tracked lines.

- `pose.py` MediaPipe Pose Landmarker (heavy) on each clip → `pose_*.json`
- `reps.py` torso angle per frame, rep tops/bottoms
- `ov.py` overlays: back line (red curved / green straight), shin line with dots, knee-height
  depth line + red "too low" zone, badges and label pills
- `compose2.py` timeline: 7.5 s synchronized split (B time-warped onto A's rep phases),
  4 s wrong single, 4 s correct single; framed for TikTok/Reels safe zones and the 4:5 feed crop;
  audio loudness-normalised to -14 LUFS
- `mannequin.html` / `mannequin_render.js` optional 3D anatomical mannequin (not used in the final cut)
