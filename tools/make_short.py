import subprocess, math, sys, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
OUT = sys.argv[1]  # usage: make_short.py OUT.mp4 stories.json
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
_fc = {}
def F(p, s):
    k = (p, s)
    if k not in _fc: _fc[k] = ImageFont.truetype(p, s)
    return _fc[k]

WHITE, MUTED, GOLD = (255, 255, 255), (190, 198, 215), (255, 200, 70)
BALL, SEAM = (200, 30, 40), (250, 235, 220)
WOOD, WOOD_D = (235, 205, 150), (190, 150, 95)

def ease(t): t = max(0, min(1, t)); return 1 - (1 - t) ** 3
def seg(t, a, b): return ease((t - a) / (b - a))
def lerp(a, b, k): return a + (b - a) * k

# ---------- static stadium backdrop (night, floodlights, crowd, outfield) ----------
random.seed(4)
bg = Image.new("RGB", (W, H))
g = ImageDraw.Draw(bg)
for y in range(H):
    k = y / H
    g.line([(0, y), (W, y)], fill=(int(lerp(6, 20, k)), int(lerp(10, 26, k)), int(lerp(30, 52, k))))
# crowd stands band
for y in range(820, 1020):
    k = (y - 820) / 200
    g.line([(0, y), (W, y)], fill=(int(lerp(25, 40, k)), int(lerp(30, 42, k)), int(lerp(55, 70, k))))
for _ in range(1400):
    x, y = random.randint(0, W), random.randint(830, 1010)
    c = random.choice([(230, 80, 80), (80, 140, 240), (240, 200, 80), (220, 220, 230), (90, 200, 140)])
    r = random.randint(2, 4)
    g.ellipse([x - r, y - r, x + r, y + r], fill=tuple(int(v * 0.55) for v in c))
# outfield grass with mowing stripes
for y in range(1020, H):
    k = (y - 1020) / (H - 1020)
    g.line([(0, y), (W, y)], fill=(int(lerp(24, 40, k)), int(lerp(96, 130, k)), int(lerp(46, 58, k))))
for i in range(0, W, 120):
    g.polygon([(i, 1020), (i + 60, 1020), (i + 60 + (i - W / 2) * 0.9, H), (i + (i - W / 2) * 0.9, H)], fill=(36, 118, 54))
# floodlight towers
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gg = ImageDraw.Draw(glow)
for fx in (150, W - 150):
    g.line([(fx, 330), (fx, 830)], fill=(70, 75, 95), width=10)
    g.rectangle([fx - 70, 260, fx + 70, 340], fill=(90, 95, 115))
    for i in range(4):
        for j in range(2):
            g.rectangle([fx - 62 + i * 33, 268 + j * 36, fx - 36 + i * 33, 296 + j * 36], fill=(255, 250, 225))
    gg.ellipse([fx - 300, 0, fx + 300, 600], fill=(255, 240, 200, 40))
glow = glow.filter(ImageFilter.GaussianBlur(70))
bg = Image.alpha_composite(bg.convert("RGBA"), glow).convert("RGB")

# dark panel area for text (bottom)
panel = Image.new("RGBA", (W, H), (0, 0, 0, 0)); pd = ImageDraw.Draw(panel)
pd.rounded_rectangle([50, 1080, W - 50, 1790], radius=40, fill=(8, 12, 28, 205))
bg = Image.alpha_composite(bg.convert("RGBA"), panel).convert("RGB")

# ---------- drawing helpers ----------
def tc(d, y, s, f, col):
    d.text(((W - d.textlength(s, font=f)) / 2, y), s, font=f, fill=col)

def ball(d, cx, cy, r, rot):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BALL)
    d.ellipse([cx - r * 0.55, cy - r * 0.75, cx - r * 0.1, cy - r * 0.35], fill=(235, 90, 95))
    for off in (-0.12, 0.12):
        pts = []
        for k in range(-10, 11):
            a = k / 10 * 1.2
            x = cx + r * (math.sin(rot) * 0.0 + off) + r * 0.25 * math.cos(rot) * a
            y = cy + r * 0.92 * math.sin(a)
            xx = cx + (x - cx) * math.cos(rot) - (y - cy) * math.sin(rot)
            yy = cy + (x - cx) * math.sin(rot) + (y - cy) * math.cos(rot)
            pts.append((xx, yy))
        d.line(pts, fill=SEAM, width=max(2, int(r * 0.06)))

def stumps(d, cx, base, h, bail_t):
    sw = 22
    for i in (-1, 0, 1):
        x = cx + i * 46
        d.rounded_rectangle([x - sw / 2, base - h, x + sw / 2, base], radius=8, fill=WOOD)
        d.rectangle([x - sw / 2 + 4, base - h + 6, x - sw / 2 + 8, base - 6], fill=WOOD_D)
    # bails fly off when bail_t > 0
    for j, side in enumerate((-1, 1)):
        bx = cx + side * 23 + side * 260 * bail_t
        by = min(base - h - 10 - 420 * bail_t + 700 * bail_t ** 2, 990)
        ang = side * bail_t * 9
        L = 50
        p1 = (bx - L / 2 * math.cos(ang), by - L / 2 * math.sin(ang))
        p2 = (bx + L / 2 * math.cos(ang), by + L / 2 * math.sin(ang))
        d.line([p1, p2], fill=WOOD, width=14)

def bat(d, cx, cy, ang, s=1.0):
    def rot(px, py):
        return (cx + px * math.cos(ang) - py * math.sin(ang), cy + px * math.sin(ang) + py * math.cos(ang))
    blade = [rot(-34 * s, 0), rot(34 * s, 0), rot(30 * s, 330 * s), rot(-30 * s, 330 * s)]
    handle = [rot(-12 * s, -150 * s), rot(12 * s, -150 * s), rot(12 * s, 0), rot(-12 * s, 0)]
    d.polygon(handle, fill=(40, 40, 50))
    d.polygon(blade, fill=WOOD)
    d.line([rot(0, 20 * s), rot(0, 300 * s)], fill=WOOD_D, width=int(6 * s))

def flagbar(d, x, y, w, h, cols):
    sh = h / len(cols)
    for i, c in enumerate(cols):
        d.rectangle([x, y + i * sh, x + w, y + (i + 1) * sh], fill=c)

def pill(d, y, text, col, a):
    f = F(FB, 38); tw = d.textlength(text, font=f)
    x0 = (W - tw) / 2 - 34
    d.rounded_rectangle([x0, y, x0 + tw + 68, y + 76], radius=38, fill=tuple(int(v * a) for v in col))
    if a > 0.4: tc(d, y + 17, text, f, (10, 12, 25))

FLAGS = {
    "IND": [(255, 153, 51), (255, 255, 255), (19, 136, 8)], "NZ": [(20, 20, 20), (255, 255, 255), (20, 20, 20)],
    "AUS": [(0, 0, 139), (255, 205, 0), (0, 132, 61)], "ENG": [(255, 255, 255), (206, 17, 36), (255, 255, 255)],
    "PAK": [(1, 65, 28), (1, 65, 28), (255, 255, 255)], "SA": [(0, 122, 77), (255, 182, 18), (222, 56, 49)],
    "SL": [(255, 190, 41), (141, 21, 58), (0, 83, 78)], "BAN": [(0, 106, 78), (244, 42, 65), (0, 106, 78)],
    "AFG": [(0, 0, 0), (210, 16, 52), (0, 122, 54)], "WI": [(123, 0, 44), (253, 185, 19), (123, 0, 44)],
    "ZIM": [(0, 135, 81), (252, 225, 0), (210, 16, 52)], "IRE": [(22, 155, 98), (255, 255, 255), (255, 136, 62)],
    "IRL": [(22, 155, 98), (255, 255, 255), (255, 136, 62)], "NED": [(174, 28, 40), (255, 255, 255), (33, 70, 139)],
    "SCO": [(0, 94, 184), (255, 255, 255), (0, 94, 184)], "NAM": [(0, 56, 168), (210, 16, 52), (0, 154, 68)],
    "UGA": [(0, 0, 0), (252, 220, 4), (217, 0, 0)], "MOZ": [(0, 150, 57), (0, 0, 0), (252, 225, 0)],
    "NEP": [(220, 20, 60), (255, 255, 255), (0, 56, 147)], "UAE": [(0, 115, 47), (255, 255, 255), (0, 0, 0)],
    "USA": [(178, 34, 52), (255, 255, 255), (60, 59, 110)], "OMA": [(219, 22, 26), (255, 255, 255), (0, 138, 62)],
}
GREY = [(90, 95, 115), (150, 155, 175), (90, 95, 115)]
def flag(code): return FLAGS.get((code or "").upper(), GREY)
PILLC = {"blue": (96, 165, 250), "red": (255, 90, 95), "green": (87, 214, 160), "gold": GOLD}
def C(a, col): return tuple(int(v * a) for v in col)

def text_block(d, a, s, y0=1130):
    pill(d, y0, s["tag"], PILLC.get(s.get("color", "blue"), (96, 165, 250)), a)
    y = y0 + 120
    for ln in s["headline"]:
        tc(d, y, ln, F(FB, s.get("headline_size", 84)), C(a, WHITE)); y += 105
    y += 30
    for i, ln in enumerate(s.get("details", [])):
        col = GOLD if i == 0 else MUTED
        tc(d, y, ln, F(FR, 46 if i == 0 else 40), C(a, col)); y += 70
    if s.get("teams"):
        t1, t2 = s["teams"]
        flagbar(d, W / 2 - 130, min(y + 10, 1700), 110, 60, flag(t1)); flagbar(d, W / 2 + 20, min(y + 10, 1700), 110, 60, flag(t2))

def scene_chase(s):
    # scoreboard counting up the winning total, ball flies for six at the end
    def fn(d, lt, a):
        t1, t2 = s["teams"]
        d.rounded_rectangle([140, 300, W - 140, 760], radius=30, fill=(12, 16, 30), outline=(60, 70, 100), width=4)
        flagbar(d, 190, 350, 110, 70, flag(t1)); flagbar(d, W - 300, 350, 110, 70, flag(t2))
        tc(d, 360, f"{t1}  v  {t2}", F(FB, 54), WHITE)
        runs = int(s["runs"] * seg(lt, 0.3, 2.6))
        tc(d, 470, f"{runs}/{s['wickets']}", F(FB, 150), GOLD)
        tc(d, 650, s.get("sub", ""), F(FR, 40), MUTED)
        if lt > 2.6:
            k = seg(lt, 2.6, 3.8)
            ball(d, lerp(W / 2, W - 140, k), 820 - 600 * k + 500 * k * k, 44, lt * 8)
        text_block(d, a, {**s, "teams": None})
    return fn

def scene_collapse(s):
    # ball hits the stumps, bails fly, "N ALL OUT" counter
    def fn(d, lt, a):
        hit = 0.9
        bx = lerp(-80, W / 2, seg(lt, 0, hit)) if lt < hit else W / 2 + 20
        stumps(d, W / 2, 780, 300, (lt - hit) if lt > hit else 0)
        if lt < hit + 0.1: ball(d, bx, 680, 40, lt * 10)
        if hit < lt < hit + 0.25:
            d.ellipse([W / 2 - 160, 520, W / 2 + 160, 840], outline=GOLD, width=10)
        n = int(s["runs"] * seg(lt, 1.0, 2.4))
        if lt > 1.0: tc(d, 300, f"{n} ALL OUT", F(FB, 110), (255, 90, 95))
        text_block(d, a, s)
    return fn

def scene_bigtotal(s):
    # bat swing, ball flies away, total counts up
    def fn(d, lt, a):
        bat(d, W / 2 - 120, 420, -1.2 + 1.9 * seg(lt, 0.2, 0.9), 1.1)
        if lt > 0.75:
            k = seg(lt, 0.75, 2.0)
            ball(d, lerp(W / 2, W + 100, k), lerp(620, 250, k), 46, lt * 9)
        n = int(s["runs"] * seg(lt, 0.6, 2.4))
        tc(d, 760, f"{n}/{s['wickets']}", F(FB, 96), GOLD)
        text_block(d, a, s)
    return fn

def scene_star(s):
    # player milestone: big number with a glowing ring (e.g. "100*" or "5/12")
    def fn(d, lt, a):
        r = 230 * seg(lt, 0, 0.8)
        d.ellipse([W / 2 - r, 560 - r, W / 2 + r, 560 + r], outline=GOLD, width=12)
        ang = 360 * seg(lt, 0.3, 1.8)
        if r > 40: d.arc([W / 2 - r + 30, 560 - r + 30, W / 2 + r - 30, 560 + r - 30], -90, -90 + ang, fill=(255, 90, 95), width=12)
        tc(d, 490, s["big"], F(FB, 130), C(seg(lt, 0.5, 1.2), WHITE))
        text_block(d, a, s)
    return fn

def scene_live(s):
    def fn(d, lt, a):
        pr = 30 + 10 * math.sin(lt * 6)
        label = s.get("label", "LIVE NOW")
        f = F(FB, 90); tw = d.textlength(label, font=f)
        x0 = (W - tw - 90) / 2
        d.ellipse([x0 + 30 - pr, 420 - pr, x0 + 30 + pr, 420 + pr], fill=(230, 40, 50))
        d.text((x0 + 90, 375), label, font=f, fill=WHITE)
        ball(d, W / 2, 640, 70, lt * 4)
        pill(d, 1130, s.get("tag", "ON TODAY"), GOLD, a)
        y = 1250
        for m in s["matches"][:3]:
            tc(d, y, m[0], F(FB, 64), C(a, WHITE)); y += 82
            tc(d, y, m[1], F(FR, 40), C(a, MUTED)); y += 90
    return fn

def make_intro(date_label, count):
    def s_intro(d, lt, a):
        x = lerp(-120, W / 2, seg(lt, 0, 1.0)); y = 560 + 60 * math.sin(lt * 2)
        ball(d, x, y, 120 * (0.5 + 0.5 * seg(lt, 0, 1.0)), lt * 6)
        pill(d, 1150, "DAILY CRICKET UPDATE", GOLD, a)
        tc(d, 1290, "Cricket Today", F(FB, 104), C(a, WHITE))
        tc(d, 1440, date_label, F(FR, 50), C(a, MUTED))
        tc(d, 1560, f"{count} big stories in 30 seconds", F(FR, 44), C(a, GOLD))
    return s_intro

def make_outro(question):
    def s_outro(d, lt, a):
        stumps(d, W / 2, 760, 300, 0)
        ball(d, W / 2 + 170, 700 - abs(math.sin(lt * 3)) * 160, 50, lt * 6)
        tc(d, 1250, "Follow for daily", F(FB, 88), C(a, WHITE))
        tc(d, 1360, "cricket updates", F(FB, 88), C(a, WHITE))
        tc(d, 1520, question, F(FR, 46), C(a, GOLD))
        tc(d, 1590, "Tell us in the comments", F(FR, 40), C(a, MUTED))
    return s_outro

import json
DATA = json.load(open(sys.argv[2]))
KINDS = {"chase": (scene_chase, 7.0), "collapse": (scene_collapse, 6.5), "bigtotal": (scene_bigtotal, 6.0),
         "star": (scene_star, 6.0), "live": (scene_live, 5.0)}
stories = [s for s in DATA["stories"] if s["type"] != "live"]
SCENES = [(make_intro(DATA["date_label"], len(stories)), 4.0)]
for s in DATA["stories"]:
    mk, ln = KINDS[s["type"]]
    SCENES.append((mk(s), s.get("seconds", ln)))
SCENES.append((make_outro(DATA.get("question", "Which result surprised you?")), 4.5))
DUR = sum(s[1] for s in SCENES)


def frame(t):
    img = bg.copy(); d = ImageDraw.Draw(img)
    acc = 0
    for i, (fn, ln) in enumerate(SCENES):
        if t < acc + ln or i == len(SCENES) - 1: break
        acc += ln
    lt = t - acc
    a = seg(lt, 0, 0.4) * (1 - seg(lt, ln - 0.3, ln))
    fn(d, lt, a)
    # progress bar
    d.rounded_rectangle([80, 140, W - 80, 148], radius=4, fill=(50, 55, 80))
    d.rounded_rectangle([80, 140, 80 + max(8, int((W - 160) * t / DUR)), 148], radius=4, fill=GOLD)
    d.text((80, 1830), "Data: Sportradar", font=F(FR, 28), fill=(120, 130, 150))
    # fade to/from black between scenes
    if a < 1:
        ov = Image.new("RGB", (W, H), (0, 0, 0))
        img = Image.blend(ov, img, 0.35 + 0.65 * a)
    return img

p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                      "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
                      "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
for k in range(int(DUR * FPS)):
    p.stdin.write(frame(k / FPS).tobytes())
p.stdin.close(); p.wait(); print("dur", DUR)
