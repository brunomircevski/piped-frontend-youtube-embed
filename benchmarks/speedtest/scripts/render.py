"""Render side-by-side YouTube vs Piped comparison video with on-screen timers."""
import json, statistics, subprocess, sys
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont
from vc import vc

RES, OUT = sys.argv[1], sys.argv[2]
FPS = 30
W, H = 1920, 1080
HDR = 120
PANE_W = 960
PAGE_H = H - HDR - 10
PAGE_W = round(960 * PAGE_H / 1080)
BG = (18, 18, 20)
FG = (235, 235, 235)
MUTED = (150, 150, 155)
GREEN = (60, 205, 110)
YELLOW = (250, 205, 70)
SITE_LABEL = {"youtube": "YouTube (official)", "piped": "Piped fork"}
SITE_HOST = {"youtube": "www.youtube.com", "piped": "piped.mircevski.ovh"}
SCEN_TITLE = {"search": "Search", "player": "Player", "channel": "Channel"}
SCEN_SUB = {
    "search": 'results?search_query=lofi hip hop  -  timer stops when results are visually complete',
    "player": "watch?v=dQw4w9WgXcQ  -  timer stops when the video starts playing",
    "channel": "@LinusTechTips  -  timer stops when the page is visually complete",
}
F = "/usr/share/fonts/truetype/dejavu/"
font = lambda name, size: ImageFont.truetype(F + name, size)
f_label, f_host, f_timer = font("DejaVuSans-Bold.ttf", 34), font("DejaVuSans.ttf", 20), font("DejaVuSansMono-Bold.ttf", 58)
f_big, f_mid, f_small = font("DejaVuSans-Bold.ttf", 84), font("DejaVuSans.ttf", 32), font("DejaVuSans.ttf", 24)
f_tab, f_tabb = font("DejaVuSansMono.ttf", 34), font("DejaVuSansMono-Bold.ttf", 34)

runs = json.load(open(RES))
for r in runs:
    r["stop"] = r["done_s"] if r["scenario"] == "player" else vc(r["frames"], r["done_s"])


def pick_median(scen, site):
    rs = sorted([r for r in runs if r["scenario"] == scen and r["site"] == site], key=lambda r: r["stop"])
    return rs[len(rs) // 2], [r["stop"] for r in rs]


@lru_cache(maxsize=64)
def page_img(path):
    return Image.open(path).convert("RGB").resize((PAGE_W, PAGE_H), Image.LANCZOS)


BLANK = Image.new("RGB", (PAGE_W, PAGE_H), (255, 255, 255))


def frame_at(run, t):
    cur = None
    for ft, p in run["frames"]:
        if ft <= t and ft >= 0:
            cur = p
        elif ft > t:
            break
    return page_img(cur) if cur else BLANK


def centered(d, cx, y, text, f, fill):
    w = d.textlength(text, font=f)
    d.text((cx - w / 2, y), text, font=f, fill=fill)


def race_frame(scen, rl, rr, t):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    for i, (site, run) in enumerate((("youtube", rl), ("piped", rr))):
        x0 = i * PANE_W
        im.paste(frame_at(run, t), (x0 + (PANE_W - PAGE_W) // 2, HDR))
        d.text((x0 + 30, 18), SITE_LABEL[site], font=f_label, fill=FG)
        d.text((x0 + 30, 62), SITE_HOST[site] + "  ·  " + SCEN_TITLE[scen].lower(), font=f_host, fill=MUTED)
        stopped = t >= run["stop"]
        shown = run["stop"] if stopped else t
        txt = f"{shown:5.2f} s"
        tw = d.textlength(txt, font=f_timer)
        d.text((x0 + PANE_W - 30 - tw, 22), txt, font=f_timer, fill=GREEN if stopped else YELLOW)
        if stopped:
            tag = "▶ PLAYING" if scen == "player" else "✓ LOADED"
            tw2 = d.textlength(tag, font=f_host)
            d.text((x0 + PANE_W - 30 - tw2, 88), tag, font=f_host, fill=GREEN)
    d.line([(PANE_W, 0), (PANE_W, H)], fill=(70, 70, 75), width=3)
    return im


def title_frame(scen, idx):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    centered(d, W / 2, 380, f"{idx}/3  {SCEN_TITLE[scen]} page", f_big, FG)
    centered(d, W / 2, 510, SCEN_SUB[scen], f_mid, MUTED)
    centered(d, W / 2, 580, "cold cache · median of 3 runs · both sides start at navigation start", f_small, MUTED)
    return im


def intro_frame():
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    centered(d, W / 2, 360, "YouTube  vs  Piped fork", f_big, FG)
    centered(d, W / 2, 490, "Page-load speed test · headless Chromium · 960x1080 viewport per side", f_mid, MUTED)
    centered(d, W / 2, 550, "Recorded on the homelab (mircevski.ovh) · 2026-11-23", f_small, MUTED)
    return im


def summary_frame(rows):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    centered(d, W / 2, 110, "Results (median of 3 cold runs)", f_big, FG)
    y = 300
    head = f"{'Page':<10}{'YouTube':>12}{'Piped':>12}{'Faster':>12}"
    centered(d, W / 2, y, head, f_tabb, MUTED)
    for scen, yt, pp in rows:
        y += 80
        winner = f"{yt / pp:.1f}x" if pp < yt else f"YT {pp / yt:.1f}x"
        line = f"{SCEN_TITLE[scen]:<10}{yt:>10.2f} s{pp:>10.2f} s{winner:>12}"
        centered(d, W / 2, y, line, f_tab, FG)
    centered(d, W / 2, 720, "Search/Channel: visually complete (viewport stops changing; autoplay regions ignored)", f_small, MUTED)
    centered(d, W / 2, 760, "Player: <video> playing (currentTime > 0). Piped fork plays via youtube-nocookie embed.", f_small, MUTED)
    centered(d, W / 2, 800, "Note: test runs on the same host as Piped, so Piped's own server hop is LAN-local.", f_small, MUTED)
    return im


def main():
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                           "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT],
                          stdin=subprocess.PIPE)
    emit = lambda im, n=1: [ff.stdin.write(im.tobytes()) for _ in range(n)]
    emit(intro_frame(), int(2.5 * FPS))
    rows, summary = [], {}
    for i, scen in enumerate(("search", "player", "channel"), 1):
        rl, yts = pick_median(scen, "youtube")
        rr, pps = pick_median(scen, "piped")
        rows.append((scen, rl["stop"], rr["stop"]))
        summary[scen] = {"youtube_runs_s": yts, "piped_runs_s": pps,
                         "youtube_median_s": rl["stop"], "piped_median_s": rr["stop"]}
        emit(title_frame(scen, i), int(2.0 * FPS))
        dur = max(rl["stop"], rr["stop"]) + 1.5
        n = int(dur * FPS)
        for k in range(n):
            emit(race_frame(scen, rl, rr, k / FPS))
        emit(race_frame(scen, rl, rr, dur), int(1.0 * FPS))  # hold
    emit(summary_frame(rows), int(7 * FPS))
    ff.stdin.close()
    ff.wait()
    json.dump(summary, open(OUT.rsplit(".", 1)[0] + "-summary.json", "w"), indent=1)
    for s, v in summary.items():
        print(s, {k: (round(x, 3) if isinstance(x, float) else [round(y, 3) for y in x]) for k, x in v.items()})


main()
