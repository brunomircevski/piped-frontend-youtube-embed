import json, sys
from PIL import Image, ImageChops, ImageFilter
W, H = 96, 108
def small(p): return Image.open(p).convert("L").resize((W, H))
def binarize(d): return d.point(lambda v: 255 if v > 24 else 0)
def vc(frames, done, thr=0.01):
    """Visually complete: first frame after which the viewport matches the settled final frame,
    ignoring regions still changing >=1.5s after the DOM marker (autoplay trailers etc.)."""
    end = frames[-1][0]
    fin = small(frames[-1][1])
    mask = Image.new("L", (W, H), 0)
    for t, p in frames:
        if t >= done + 1.5:
            mask = ImageChops.lighter(mask, binarize(ImageChops.difference(small(p), fin)))
    mask = mask.filter(ImageFilter.MaxFilter(5))
    keep = ImageChops.invert(mask)
    last_bad = 0.0
    for t, p in frames:
        d = ImageChops.multiply(binarize(ImageChops.difference(small(p), fin)), keep)
        if d.histogram()[255] / (W * H) > thr:
            last_bad = t
    later = [t for t, _ in frames if t > last_bad]
    return later[0] if later else last_bad
if __name__ == "__main__":
    for r in json.load(open(sys.argv[1])):
        if r["scenario"] != "player":
            print(r["tag"], "dom", round(r["done_s"], 2), "VC", round(vc(r["frames"], r["done_s"]), 2))
