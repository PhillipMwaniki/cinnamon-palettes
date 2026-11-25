"""Minimal palette wallpapers: a dusk sky, an accent sun with a soft halo,
layered ridge silhouettes and fine grain. Deterministic per palette."""
import math, random
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from theme import rgb, lerp

W, H = 2560, 1440


def ridge(rnd, w, base, amp, n=4):
    waves = [(rnd.uniform(0.7, 1.6) * (i + 1) ** 1.3, rnd.uniform(0, 6.28), amp / (i + 1) ** 1.4) for i in range(n)]
    pts = []
    for x in range(0, w + 16, 16):
        t = x / w * math.pi * 2
        y = base + sum(a * math.sin(f * t + ph) for f, ph, a in waves)
        pts.append((x, y))
    return pts


def render(p, path, size=(W, H)):
    w, h = size
    bg_dark, bg, bg_alt, accent, accent2 = (rgb(p[k]) for k in ("bg_dark", "bg", "bg_alt", "accent", "accent2"))
    rnd = random.Random(p["slug"])

    # sky: dark at the top, faintly accent-tinted towards the horizon
    sky = Image.new("RGB", (1, 64))
    horizon = lerp(bg, accent, 0.16)
    for y in range(64):
        sky.putpixel((0, y), lerp(bg_dark, horizon, (y / 63) ** 1.6))
    im = sky.resize((w, h), Image.BICUBIC)

    # sun + halo
    sx, sy, sr = w * rnd.uniform(0.6, 0.74), h * 0.5, h * 0.105
    halo = Image.new("RGB", (w // 4, h // 4))
    d = ImageDraw.Draw(halo)
    r = sr * 2.6 / 4
    d.ellipse((sx / 4 - r, sy / 4 - r, sx / 4 + r, sy / 4 + r), fill=tuple(round(c * 0.28) for c in accent))
    halo = halo.filter(ImageFilter.GaussianBlur(r * 0.55)).resize((w, h), Image.BICUBIC)
    im = ImageChops.add(im, halo)
    d = ImageDraw.Draw(im)
    d.ellipse((sx - sr, sy - sr, sx + sr, sy + sr), fill=lerp(accent, bg, 0.12))

    # ridges, back to front: tinted towards accent2 far away, near-black up front
    layers = 4
    for i in range(layers):
        t = i / (layers - 1)
        far = lerp(bg_alt, accent2, 0.18)
        col = lerp(far, bg_dark, t ** 0.8)
        base = h * (0.60 + 0.085 * i)
        pts = ridge(rnd, w, base, h * (0.05 + 0.02 * i))
        d.polygon(pts + [(w + 16, h), (0, h)], fill=col)

    # grain
    noise = Image.effect_noise((w, h), 18).convert("RGB")
    im = Image.blend(im, ImageChops.multiply(im, noise.point(lambda v: 205 + v // 6)), 0.3)

    im.save(path, quality=93)
    return path
