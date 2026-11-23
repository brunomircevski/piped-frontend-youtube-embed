"""Capture cold-cache page loads of YouTube vs Piped with CDP screencast + in-page done markers."""
import asyncio, base64, json, os, sys, time
from playwright.async_api import async_playwright

OUT = sys.argv[1]
RUNS = int(sys.argv[2]) if len(sys.argv) > 2 else 3
VIDEO_ID = "dQw4w9WgXcQ"
SITES = {
    "youtube": "https://www.youtube.com",
    "piped": "https://piped.mircevski.ovh",
}
SCENARIOS = {
    "search": "/results?search_query=lofi+hip+hop",
    "player": f"/watch?v={VIDEO_ID}",
    "channel": "/@LinusTechTips",
}

# Runs in every frame (incl. the youtube-nocookie iframe used by the Piped fork).
INIT = r"""
(() => {
  const mode = %s;
  window.__done = null;
  const thumbsReady = () => {
    let n = 0;
    for (const img of document.images) {
      if (!img.complete || !img.naturalWidth) continue;
      const r = img.getBoundingClientRect();
      if (r.width < 120 || r.height < 60) continue;
      if (r.bottom <= 0 || r.top >= innerHeight || r.right <= 0 || r.left >= innerWidth) continue;
      if (getComputedStyle(img).visibility === 'hidden' || getComputedStyle(img).opacity === '0') continue;
      n++;
    }
    return n >= 4;
  };
  const playing = () => {
    const v = document.querySelector('video');
    return v && !v.paused && v.currentTime > 0 && v.readyState >= 3;
  };
  const tick = () => {
    if (window.__done) return;
    const ok = mode === 'player' ? playing() : (window === top && thumbsReady());
    if (ok) {
      const ad = !!document.querySelector('.ad-showing');
      window.__done = {t: performance.timeOrigin + performance.now(), ad};
      return;
    }
    setTimeout(tick, 16);
  };
  tick();
})();
"""

PERF = """(() => {
  const n = performance.getEntriesByType('navigation')[0] || {};
  const fcp = performance.getEntriesByName('first-contentful-paint')[0];
  return {origin: performance.timeOrigin, ttfb: n.responseStart, dcl: n.domContentLoadedEventEnd,
          load: n.loadEventEnd, fcp: fcp ? fcp.startTime : null};
})()"""


async def run_one(browser, site, scen, idx):
    base = SITES[site]
    url = base + SCENARIOS[scen]
    tag = f"{scen}_{site}_{idx}"
    fdir = os.path.join(OUT, tag)
    os.makedirs(fdir, exist_ok=True)
    ctx = await browser.new_context(viewport={"width": 960, "height": 1080}, locale="en-US",
                                    device_scale_factor=1)
    # Pre-answer the EU cookie consent wall so YouTube shows content, not a dialog.
    await ctx.add_cookies([{"name": "SOCS", "value": "CAI", "domain": ".youtube.com", "path": "/"}])
    await ctx.add_init_script(INIT % json.dumps(scen))
    page = await ctx.new_page()
    cdp = await ctx.new_cdp_session(page)
    frames = []

    def on_frame(ev):
        ts = ev["metadata"]["timestamp"]
        n = len(frames)
        p = os.path.join(fdir, f"{n:05d}.jpg")
        with open(p, "wb") as f:
            f.write(base64.b64decode(ev["data"]))
        frames.append((ts, p))
        asyncio.ensure_future(cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]}))

    cdp.on("Page.screencastFrame", on_frame)
    await page.goto("about:blank")
    await page.set_content("<body style='background:#fff'></body>")
    await cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 85, "everyNthFrame": 1,
                                            "maxWidth": 960, "maxHeight": 1080})
    await asyncio.sleep(0.5)
    t0 = time.time()
    await page.goto(url, wait_until="commit", timeout=60000)
    done = None
    deadline = t0 + 30
    while time.time() < deadline and done is None:
        for fr in page.frames:
            try:
                d = await fr.evaluate("window.__done")
            except Exception:
                continue
            if d:
                done = d
                break
        await asyncio.sleep(0.05)
    await asyncio.sleep(1.5 if scen == "player" else 4.0)  # keep recording after done (settle tail)
    await cdp.send("Page.stopScreencast")
    perf = await page.evaluate(PERF)
    await ctx.close()
    res = {
        "tag": tag, "site": site, "scenario": scen, "run": idx, "url": url,
        "t0": t0,
        "done_s": (done["t"] / 1000 - t0) if done else None,
        "ad": done.get("ad") if done else None,
        "nav_offset_s": perf["origin"] / 1000 - t0,
        "ttfb_ms": perf["ttfb"], "fcp_ms": perf["fcp"], "dcl_ms": perf["dcl"], "load_ms": perf["load"],
        "frames": [(ts - t0, p) for ts, p in frames],
    }
    print(f"{tag}: done={res['done_s'] and round(res['done_s'], 3)}s ad={res['ad']} "
          f"ttfb={perf['ttfb'] and round(perf['ttfb'])} fcp={perf['fcp'] and round(perf['fcp'])} frames={len(frames)}",
          flush=True)
    return res


async def main():
    os.makedirs(OUT, exist_ok=True)
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chromium", headless=True,
                                          args=["--autoplay-policy=no-user-gesture-required"])
        for scen in SCENARIOS:
            for i in range(RUNS):
                for site in (SITES if i % 2 == 0 else list(SITES)[::-1]):  # alternate order
                    results.append(await run_one(browser, site, scen, i))
        await browser.close()
    with open(os.path.join(OUT, "results.json"), "w") as f:
        json.dump(results, f, indent=1)


asyncio.run(main())
