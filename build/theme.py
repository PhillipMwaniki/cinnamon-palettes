"""Build a Cinnamon/GTK/Metacity theme for a palette by recolouring Mint-Y-Dark-Aqua.

Generalised from the Nocturne build: Mint-Y greys are mapped onto a ramp made
from the palette's surfaces, Mint-Y aqua becomes the palette accent, and Mint-Y
green/red become the palette's success/error colours.
"""
import colorsys, re, shutil
from pathlib import Path
from PIL import Image

SRC = Path("/usr/share/themes/Mint-Y-Dark-Aqua")
WM_SRC = Path("/usr/share/themes/Mint-Y/metacity-1")
HERE = Path(__file__).parent
SRC_ACCENT_HUE = 200 / 360  # Mint-Y aqua


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hexs(c):
    return "#%02x%02x%02x" % tuple(c)


def lerp(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def hls(c):
    return colorsys.rgb_to_hls(*(x / 255 for x in c))


def from_hls(h, l, s):
    return tuple(round(x * 255) for x in colorsys.hls_to_rgb(h, l, s))


def derived(p):
    """Palette colours plus the in-between shades the CSS templates use."""
    c = {k: rgb(v) for k, v in p.items() if isinstance(v, str) and v.startswith("#")}
    c["fg_mid"] = lerp(c["fg_dim"], c["fg"], 0.6)
    c["darkest"] = lerp(c["bg_dark"], (0, 0, 0), 0.5)
    c["on_accent"] = c["bg_dark"] if hls(c["accent"])[1] > 0.5 else c["fg"]
    c["on_accent2"] = c["bg_dark"] if hls(c["accent2"])[1] > 0.5 else c["fg"]
    return c


class Recolor:
    def __init__(self, p):
        self.c = c = derived(p)
        # Mint-Y grey level -> palette surface
        self.ramp = [
            (0, c["darkest"]),
            (24, lerp(c["darkest"], c["bg_dark"], 0.6)),
            (32, c["bg_dark"]),
            (46, c["bg"]),
            (58, c["bg_alt"]),
            (74, c["outline"]),
            (90, lerp(c["outline"], c["fg_dim"], 0.35)),
            (150, c["fg_dim"]),
            (195, lerp(c["fg_dim"], c["fg"], 0.7)),
            (222, lerp(c["fg_dim"], c["fg"], 0.9)),
            (255, c["fg"]),
        ]
        self.accent_out = set()  # every colour produced from an accent/success source

    def map_grey(self, v):
        for (v0, c0), (v1, c1) in zip(self.ramp, self.ramp[1:]):
            if v <= v1:
                return lerp(c0, c1, (v - v0) / (v1 - v0))
        return self.ramp[-1][1]

    @staticmethod
    def classify(c):
        h, l, s = hls(c)
        if max(c) - min(c) <= 14:
            return "grey", l
        if s > 0.35 and abs(h - SRC_ACCENT_HUE) < 0.06:
            return "accent", l
        if s > 0.5 and (h < 0.03 or h > 0.95):
            return "red", l
        if s > 0.35 and 0.2 < h < 0.42:
            return "green", l
        return "other", l

    def shade(self, target, l, l_ref):
        """Keep the source's relative lightness, shifted onto the target colour."""
        th, tl, ts = hls(target)
        nl = min(0.92, max(0.25, tl + (l - l_ref) * 0.8))
        return from_hls(th, nl, ts)

    def map(self, c, on_accent_glyph=False):
        kind, l = self.classify(c)
        if kind == "grey":
            if on_accent_glyph and sum(c) / 3 > 200:
                return self.c["on_accent"]
            return self.map_grey(sum(c) // 3)
        if kind == "accent":
            out = self.shade(self.c["accent"], l, 0.496)
        elif kind == "green":
            out = self.shade(self.c["success"], l, 0.48)
        elif kind == "red":
            return self.c["error"]
        else:
            return c
        self.accent_out.add(out)
        return out

    def is_accent_out(self, c):
        return c in self.accent_out

    # ---- text files -------------------------------------------------------
    HEX_RE = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
    RGBA_RE = re.compile(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(,\s*[\d.]+\s*)?\)")

    def text(self, t, glyph=False):
        def hx(m):
            v = m.group(1)
            if len(v) == 3:
                v = "".join(ch * 2 for ch in v)
            return hexs(self.map(rgb(v), glyph))

        def rg(m):
            out = self.map(tuple(int(m.group(i)) for i in (1, 2, 3)), glyph)
            if m.group(4):
                return "rgba(%d, %d, %d%s)" % (*out, m.group(4).rstrip())
            return "rgb(%d, %d, %d)" % out

        return self.RGBA_RE.sub(rg, self.HEX_RE.sub(hx, t))

    def has_src_accent(self, t):
        for m in self.HEX_RE.finditer(t):
            v = m.group(1)
            if len(v) == 6 and self.classify(rgb(v))[0] in ("accent", "green"):
                return True
        return False

    # ---- contrast: light text on accent backgrounds -------------------------
    def color_of(self, value):
        a = re.search(r"rgba\([^)]*,\s*([\d.]+)\s*\)", value)
        if a and float(a.group(1)) < 0.7:
            return None
        m = self.HEX_RE.search(value)
        if m:
            v = m.group(1)
            return rgb(v) if len(v) == 6 else None
        m = self.RGBA_RE.search(value)
        return tuple(int(m.group(i)) for i in (1, 2, 3)) if m else None

    DECL_RE = re.compile(r"(^|[;{\s])(color)\s*:\s*([^;}]+)")
    BG_RE = re.compile(r"background(?:-color|-image|-gradient-start)?\s*:\s*([^;}]+)")

    def fix_contrast(self, css):
        on = hexs(self.c["on_accent"])
        blocks = re.split(r"(?<=\})", css)

        def accent_bg(body):
            return any((c := self.color_of(v)) and self.is_accent_out(c) for v in self.BG_RE.findall(body))

        accent_sels = set()
        for b in blocks:
            if "{" in b:
                sel, body = b.split("{", 1)
                if accent_bg(body):
                    accent_sels.update(s.strip() for s in sel.split("}")[-1].split(","))

        def needs_fix(sel, body):
            if accent_bg(body):
                return True
            for s in (s.strip() for s in sel.split(",")):
                for a in accent_sels:
                    if s == a or s.startswith(a + " ") or s.startswith(a + " >"):
                        return True
            return False

        light = hls(self.c["on_accent"])[1] < 0.5  # only swap when accent is light

        out = []
        for b in blocks:
            if "{" in b and light:
                sel, body = b.split("{", 1)
                if needs_fix(sel.split("}")[-1], body):
                    def repl(m):
                        c = self.color_of(m.group(3))
                        if c and sum(c) / 3 > 150 and not self.is_accent_out(c):
                            return f"{m.group(1)}color: {on}"
                        return m.group(0)
                    body = self.DECL_RE.sub(repl, body)
                    b = sel + "{" + body
            out.append(b)
        return "".join(out)

    # ---- images ---------------------------------------------------------------
    def png(self, path):
        im = Image.open(path).convert("RGBA")
        px = im.load()
        w, h = im.size
        opaque = [px[x, y] for y in range(h) for x in range(w) if px[x, y][3] > 40]
        heavy = opaque and sum(self.classify(p[:3])[0] in ("accent", "green") for p in opaque) / len(opaque) > 0.08
        cache = {}
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if a == 0:
                    continue
                k = (r, g, b)
                if k not in cache:
                    cache[k] = self.map(k, heavy)
                px[x, y] = (*cache[k], a)
        im.save(path)


def fill(template, c, p):
    """Replace {name} tokens with hex colours and {name/alpha} with rgba()."""
    def sub(m):
        name, alpha = m.group(1), m.group(2)
        col = c[name]
        return "rgba(%d, %d, %d, %s)" % (*col, alpha) if alpha else hexs(col)
    return re.sub(r"\{([a-z_0-9]+)(?:/([\d.]+))?\}", sub, template).replace("@NAME@", p["name"])


def build(p, dest):
    dest = Path(dest).expanduser()
    rc = Recolor(p)
    c = rc.c
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(SRC, dest, ignore=shutil.ignore_patterns("xfwm4", "openbox-3", "thumbnail.png"))
    shutil.copy("/usr/share/common-licenses/GPL-3", dest / "COPYING")
    shutil.copytree(WM_SRC, dest / "metacity-1")
    for f in dest.glob("libadwaita-*/defaults-light.css"):
        f.write_text((f.parent / "defaults-dark.css").read_text())

    for f in dest.rglob("*"):
        if f.suffix in (".css", ".svg", ".xml", ".rc") or f.name in ("gtkrc", "themerc"):
            t = f.read_text()
            glyph = f.suffix == ".svg" and rc.has_src_accent(t)  # ticks/knobs on accent fills
            t = rc.text(t, glyph)
            if f.suffix == ".css":
                t = rc.fix_contrast(t)
            f.write_text(t)
        elif f.suffix == ".png":
            rc.png(f)

    on = hexs(c["on_accent"])
    for css in dest.glob("gtk-[34].0/gtk*.css"):
        t = css.read_text()
        for name, val in {
            "theme_selected_fg_color": on,
            "selected_fg_color": on,
            "wm_icon_close_bg": on,
            "success_color": hexs(c["success"]),
            "error_color": hexs(c["error"]),
            "warning_color": hexs(c["warning"]),
        }.items():
            t = re.sub(rf"(@define-color {name}) [^;]+;", rf"\1 {val};", t)
        t = re.sub(r"(--accent-fg-color:\s*)[^;]+;", rf"\g<1>{on};", t)
        css.write_text(t + fill((HERE / "gtk-extra.css").read_text(), c, p))

    cin = dest / "cinnamon/cinnamon.css"
    cin.write_text(cin.read_text() + fill((HERE / "cinnamon-extra.css").read_text(), c, p))

    name = dest.name
    (dest / "index.theme").write_text(
        f"[Desktop Entry]\nType=X-GNOME-Metatheme\nName={name}\n"
        f"Comment={p['name']} palette, recoloured from Mint-Y\nEncoding=UTF-8\n\n"
        f"[X-GNOME-Metatheme]\nGtkTheme={name}\nMetacityTheme={name}\n"
        "ButtonLayout=:minimize,maximize,close\n")
    return dest
