# YouTube vs Piped fork speedtest

Page-load comparison between youtube.com and this Piped fork, run in headless
Chromium (960x1080 viewport per side, cold cache, median of 3 runs, both sides
start timing at navigation start). Recorded 2026-11-23 on the homelab.

- `scripts/capture.py <out_dir> [runs]` - drives Chromium, saves screenshot
  frames and `results.json` (see `raw-runs.json` for the recorded runs).
- `scripts/vc.py` - visual-completeness detector (when the viewport stops changing).
- `scripts/render.py <results.json> <out.mp4>` - renders the side-by-side video
  and a `-summary.json`.
- `raw-runs.json`, `summary.json` - recorded results.
- `youtube-vs-piped.mp4` - the rendered video (git-ignored, regenerate it with `render.py`).

Search/Channel stop when the page is visually complete (autoplay regions
ignored); Player stops when the `<video>` is playing (`currentTime > 0`). The
test ran on the same host as Piped, so Piped's own server hop is LAN-local.
