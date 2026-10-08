"""Builds the editable Tesseract document for the Meridian Blue agro-export ad.

Usage: python3 -I build.py <checked-out editable.json> <output.json> <land.geojson>
All visual elements are native, editable layers (text, shapes, rects, groups).
Times: ms. Block groups re-base their children to block-local time.
"""
import json, math, sys
from PIL import Image, ImageDraw

SRC, OUT, LAND = sys.argv[1], sys.argv[2], sys.argv[3]
W, H = 1080, 1920
DUR_MS = 30400

# ------------------------------------------------------------------ palette
NAVY = [0.043, 0.106, 0.169, 1]        # #0B1B2B
NAVY2 = [0.071, 0.157, 0.239, 1]       # card navy
NAVY_DEEP = [0.024, 0.063, 0.106, 1]
GRAPHITE = [0.118, 0.137, 0.161, 1]    # cinza grafite
EMERALD = [0.0, 0.816, 0.518, 1]       # #00D084
EMERALD_D = [0.0, 0.62, 0.40, 1]
GOLD = [0.91, 0.72, 0.29, 1]
GOLD_L = [0.98, 0.84, 0.48, 1]
WHITE = [1, 1, 1, 1]
GRAY = [0.62, 0.68, 0.74, 1]


def a(c, alpha):
    return [c[0], c[1], c[2], alpha]


XB = ("Montserrat ExtraBold", "Regular")
BD = ("Montserrat", "Bold")
SB = ("Montserrat SemiBold", "Regular")
MD = ("Montserrat Medium", "Regular")

# ------------------------------------------------------------------ ids / dynamics
_ids = [0]
_eff = [9000]
DYN = []
_kf = [0]


def nid():
    _ids[0] += 1
    return _ids[0]


def neff():
    _eff[0] += 1
    return _eff[0]


EASE = {
    "lin": {"type": "linear"},
    "hold": {"type": "hold"},
    "out": {"type": "cubicBezier", "x1": 0.16, "y1": 1, "x2": 0.3, "y2": 1},
    "inout": {"type": "cubicBezier", "x1": 0.65, "y1": 0, "x2": 0.35, "y2": 1},
    "in": {"type": "cubicBezier", "x1": 0.6, "y1": 0, "x2": 0.9, "y2": 0.4},
    "back": {"type": "cubicBezier", "x1": 0.34, "y1": 1.56, "x2": 0.64, "y2": 1},
    "soft": {"type": "cubicBezier", "x1": 0.25, "y1": 0.1, "x2": 0.25, "y2": 1},
}


def kf(lid, prop, keys):
    """keys: [(layerTime_ms, value, ease)] — value float or [x,y]."""
    out = []
    for t, v, e in keys:
        _kf[0] += 1
        val = {"type": "vector2", "value": v} if isinstance(v, (list, tuple)) else {"type": "float", "value": float(v)}
        out.append({"id": f"k{_kf[0]}", "layerTime": int(t), "value": val, "easing": EASE[e]})
    DYN.append({"target": {"kind": "layer", "layerId": lid, "propertyType": prop},
                "animator": {"type": "keyframes", "enabled": True, "keyframes": out}})


def kf_scale(lid, keys):
    kf(lid, "scaleX", keys)
    kf(lid, "scaleY", keys)


def js(lid, prop, code):
    DYN.append({"target": {"kind": "layer", "layerId": lid, "propertyType": prop},
                "animator": {"type": "jsScript", "layerTimeJsCode": code}})


def js_effect(eid, param, code):
    DYN.append({"target": {"kind": "effectProperty", "effectId": eid, "paramName": param},
                "animator": {"type": "jsScript", "layerTimeJsCode": code}})


def fade(lid, t_in, d_in=300, t_out=None, d_out=300, peak=100):
    keys = [(t_in, 0, "lin"), (t_in + d_in, peak, "out")]
    if t_out is not None:
        keys += [(t_out, peak, "lin"), (t_out + d_out, 0, "inout")]
    kf(lid, "opacity", keys)


# ------------------------------------------------------------------ layer builders
def T(x, y, ax=0, ay=0, s=100, o=100, r=0):
    sx, sy = (s, s) if not isinstance(s, (list, tuple)) else s
    return {"anchorPoint": [ax, ay], "position": [x, y], "scale": [sx, sy], "rotation": r, "opacity": o}


def AR(start, dur):
    return {"start": int(start), "duration": int(dur)}


def text(name, txt, cx, cy, w, h, size, font=XB, color=WHITE, just="center", ar=None,
         tracking=0, styles=None, effects=None, leading=None, lid=None):
    lid = lid or nid()
    ax = {"center": w / 2, "left": 0, "right": w}[just]
    x = cx
    st = {"text": txt, "fontFamily": font[0], "fontStyle": font[1], "fontSize": size,
          "fillColor": list(color), "strokeWidth": 0, "justification": just, "boxText": True,
          "boxPosition": [0, 0], "boxSize": [w, h], "verticalAlign": "center", "tracking": tracking}
    if leading:
        st["leading"] = leading
    L = {"type": "Text", "id": lid, "name": name, "blendMode": "normal", "activeRange": ar,
         "transform": T(x, cy, ax, h / 2), "sourceText": st}
    if styles:
        L["layerStyles"] = styles
    if effects:
        L["effects"] = effects
    return L


def grad_style(w, c0=GOLD_L, c1=EMERALD, mid=None):
    stops = [{"offset": 0, "color": list(c0)}, {"offset": 1, "color": list(c1)}]
    if mid:
        stops.insert(1, {"offset": 0.5, "color": list(mid)})
    return [{"id": neff(), "style": {"type": "gradientOverlay", "enabled": True, "opacity": 1,
                                       "gradientType": "linear", "start": [w * 0.1, 0], "end": [w * 0.9, 0],
                                       "blendMode": "normal", "stops": stops}}]


def rect(name, cx, cy, w, h, fill, rnd=0, stroke=None, sw=0, ar=None, paint=None, anchor="center",
         shadow=None, effects=None, o=100, lid=None):
    lid = lid or nid()
    ax, ay = {"center": (w / 2, h / 2), "left": (0, h / 2), "topleft": (0, 0)}[anchor]
    r = {"size": [w, h], "fillColor": list(fill), "roundness": rnd}
    if fill[3] == 0 and not paint:
        r["fillEnabled"] = False
    if paint:
        r["fillPaint"] = paint
    if stroke:
        r.update(strokeEnabled=True, strokeColor=list(stroke), strokeWidth=sw)
    L = {"type": "Rect", "id": lid, "name": name, "blendMode": "normal", "activeRange": ar,
         "transform": T(cx, cy, ax, ay, o=o), "rect": r}
    if shadow:
        L["dropShadow"] = shadow
    if effects:
        L["effects"] = effects
    return L


def radial(name, cx, cy, r, stops, ar, o=100, s=100):
    return rect(name, cx, cy, 2 * r, 2 * r, [0, 0, 0, 0], ar=ar, o=o,
                paint=lin_grad(r, r, 2 * r, r, stops, "radial")) | {"transform": T(cx, cy, r, r, s=s, o=o)}


def shadow(alpha=0.45, blur=40, off=(0, 18)):
    return {"color": [0, 0, 0, alpha], "blurRadius": blur, "spreadRadius": 0, "blendMode": "normal",
            "offset": list(off), "enabled": True}


def solid(c):
    return {"type": "solid", "color": list(c)}


def lin_grad(x0, y0, x1, y1, stops, kind="linear"):
    return {"type": "gradient", "gradientType": kind, "start": [x0, y0], "end": [x1, y1],
            "stops": [{"offset": o, "color": list(c)} for o, c in stops]}


def _alpha_split(paint, o):
    if paint.get("type") == "solid" and paint["color"][3] < 1:
        o = o * paint["color"][3]
        paint = solid(paint["color"][:3] + [1])
    return paint, o


def fillst(paint, o=1.0):
    paint, o = _alpha_split(paint, o)
    return {"paint": paint, "fillRule": "nonZeroWinding", "blendMode": "normal", "opacity": o}


def strokest(c, w, dashes=None, cap="round", o=1.0, paint=None):
    pp, o = _alpha_split(paint or solid(c), o)
    s = {"paint": pp, "width": w, "cap": cap, "join": "round", "miterLimit": 4,
         "blendMode": "normal", "opacity": o}
    if dashes:
        s["dashes"] = dashes
    return s


def shape(name, cmds, fills=(), strokes=(), ar=None, tr=None, trim=None, effects=None, lid=None, blend="normal"):
    lid = lid or nid()
    sh = {"path": {"commands": cmds}, "fills": list(fills), "strokes": list(strokes)}
    if trim is not None:
        sh["trim"] = {"start": 0, "end": trim, "mode": "simultaneously"}
    L = {"type": "Shape", "id": lid, "name": name, "blendMode": blend, "activeRange": ar,
         "transform": tr or T(0, 0), "shape": sh}
    if effects:
        L["effects"] = effects
    return L


def group(name, start, dur, children, tr=None, lid=None, effects=None):
    lid = lid or nid()
    g = {"type": "Group", "id": lid, "name": name, "blendMode": "normal",
         "playback": {"type": "windowed", "inputRange": AR(start, dur), "inputOffsetMs": -int(start),
                      "mapping": {"type": "linear", "input": AR(0, dur), "output": AR(0, dur)}},
         "transform": tr or T(0, 0), "layers": list(reversed(children))}  # children given back→front
    if effects:
        g["effects"] = effects
    return g


def audio(name, asset, start, dur, intrinsic, vol, src_start=0):
    return {"type": "Audio", "id": nid(), "name": name, "source": {"assetId": asset},
            "sourceRange": AR(src_start, dur), "sourceIntrinsicDuration": int(intrinsic),
            "playback": {"type": "windowed", "inputRange": AR(start, dur), "inputOffsetMs": -int(start),
                         "mapping": {"type": "linear", "input": AR(0, dur), "output": AR(0, dur)}},
            "volume": vol, "captionsEnabled": False}


# path helpers
K = 0.5522847


def M(x, y): return {"type": "moveTo", "x": x, "y": y}
def Lt(x, y): return {"type": "lineTo", "x": x, "y": y}
def C(c1x, c1y, c2x, c2y, x, y): return {"type": "cubicTo", "c1x": c1x, "c1y": c1y, "c2x": c2x, "c2y": c2y, "x": x, "y": y}
def Z(): return {"type": "close"}


def ellipse(cx, cy, rx, ry=None):
    ry = ry if ry is not None else rx
    kx, ky = rx * K, ry * K
    return [M(cx, cy - ry), C(cx + kx, cy - ry, cx + rx, cy - ky, cx + rx, cy),
            C(cx + rx, cy + ky, cx + kx, cy + ry, cx, cy + ry),
            C(cx - kx, cy + ry, cx - rx, cy + ky, cx - rx, cy),
            C(cx - rx, cy - ky, cx - kx, cy - ry, cx, cy - ry), Z()]


def poly(pts, close=False):
    c = [M(*pts[0])] + [Lt(*p) for p in pts[1:]]
    return c + ([Z()] if close else [])


def glow(th=0.25, rad=30, inten=1.2):
    return [{"id": neff(), "effect": {"type": "glow", "glowThreshold": th, "glowRadius": rad, "glowIntensity": inten}}]


def blur(amount):
    e = neff()
    return e, [{"id": e, "effect": {"type": "gaussianBlur", "blurriness": amount, "repeatEdgePixels": False}}]


def count_js(t0, t1, v0, v1, fmt):
    """Counter text with ease-out cubic. fmt: 'pct' | 'usd' | 'usdUSD'."""
    f = {
        "pct": "return v.toFixed(2).replace('.',',')+'%';",
        "usd": "return '$'+th(Math.round(v));",
        "usdUSD": "return '$'+th(Math.round(v))+' USD';",
    }[fmt]
    return ("function th(n){var s=String(n),o='';for(var i=0;i<s.length;i++){if(i>0&&(s.length-i)%3===0)o+='.';o+=s[i];}return o;}"
            f"var t=input.time.milliseconds;var p=Math.max(0,Math.min(1,(t-{t0})/{t1 - t0}));"
            f"var e=1-Math.pow(1-p,3);var v={v0}+({v1}-{v0})*e;" + f)


# =================================================================== GLOBAL BACKGROUND
root = []  # back → front
ar_all = AR(0, DUR_MS)
root.append(rect("BG navy→grafite", 540, 960, W, H, NAVY, ar=ar_all,
                 paint=lin_grad(540, 0, 540, H, [(0, [0.035, 0.09, 0.15, 1]), (0.55, NAVY), (1, GRAPHITE)])))
glow_bg = radial("BG glow esmeralda", 540, 860, 820, [(0, a(EMERALD, 0.20)), (0.45, a(EMERALD, 0.07)), (1, a(EMERALD, 0))], ar_all)
root.append(glow_bg)
js(glow_bg["id"], "opacity", "return 75+25*Math.sin(input.time.seconds*1.3);")
kf(glow_bg["id"], "positionY", [(0, 760, "lin"), (6000, 760, "lin"), (6600, 840, "inout"), (13800, 840, "lin"),
                                 (14400, 980, "inout"), (26000, 980, "lin"), (26600, 960, "inout")])
# grid
gcmds = []
for x in range(0, W + 1, 120):
    gcmds += [M(x, -120), Lt(x, H + 120)]
for y in range(-120, H + 121, 120):
    gcmds += [M(0, y), Lt(W, y)]
grid = shape("BG grid", gcmds, strokes=[strokest(a(WHITE, 0.05), 1, cap="butt")], ar=ar_all)
root.append(grid)
js(grid["id"], "positionY", "return (input.time.seconds*10)%120;")
# particles
import random
random.seed(11)
pc = []
for _ in range(34):
    x, y, r = random.uniform(30, W - 30), random.uniform(0, H), random.uniform(1.5, 3.6)
    pc += ellipse(x, y, r) + ellipse(x, y + H, r)
parts = shape("BG partículas", pc, fills=[fillst(solid(a(EMERALD, 1)))], ar=ar_all, tr=T(0, 0, o=22))
root.append(parts)
js(parts["id"], "positionY", f"return -((input.time.seconds*22)%{H});")
# vignette
root.append(rect("BG vinheta", 540, 960, W, H, [0, 0, 0, 0], ar=ar_all,
                 paint=lin_grad(540, 900, 540 + 1150, 900, [(0, [0, 0, 0, 0]), (0.55, [0, 0, 0, 0.08]), (1, [0.01, 0.03, 0.06, 0.7])], "radial")))

# =================================================================== BLOCK 1 (0–6250)
B1S, B1D = 0, 6250
ar1 = AR(0, B1D)
b1 = []
DX, DY = 540, 640  # dollar emblem centre
# burst behind $
burst = radial("$ burst", DX, DY, 300, [(0, a(EMERALD, 0.6)), (0.5, a(EMERALD, 0.18)), (1, a(EMERALD, 0))], ar1, o=0, s=60)
b1.append(burst)
kf(burst["id"], "opacity", [(1000, 0, "lin"), (1100, 90, "out"), (1900, 0, "soft")])
kf_scale(burst["id"], [(1000, 60, "lin"), (1900, 170, "out")])
disc = shape("$ disco", ellipse(DX, DY, 200), fills=[fillst(lin_grad(DX, DY - 200, DX, DY + 200, [(0, [0.08, 0.2, 0.3, 1]), (1, [0.04, 0.1, 0.16, 1])]))],
             strokes=[strokest(a(GOLD, 0.55), 2)], ar=ar1)
ring = shape("$ anel", ellipse(DX, DY, 222), strokes=[strokest(EMERALD, 5)], ar=ar1, trim=0, effects=glow(0.2, 16, 0.9))
kf(ring["id"], "trimEnd", [(150, 0, "lin"), (1050, 100, "out")])
orbit = shape("$ órbita", ellipse(0, -248, 7) + ellipse(0, 248, 4.5) + ellipse(-248, 0, 3.5),
              fills=[fillst(solid(GOLD_L))], ar=ar1, tr=T(DX, DY))
js(orbit["id"], "rotation", "return input.time.seconds*38;")
dollar = text("$ símbolo", "$", DX, DY + 8, 400, 400, 300, XB, WHITE, ar=ar1,
              styles=grad_style(400, GOLD_L, EMERALD), effects=glow(0.3, 28, 1.1))
kf(dollar["id"], "rotationY", [(0, 720, "lin"), (1100, 0, "out")])
emblem = group("$ emblema", 0, B1D, [disc, ring, orbit, dollar], tr=T(DX, DY, DX, DY))
b1.append(emblem)
kf_scale(emblem["id"], [(0, 35, "lin"), (750, 100, "back")])
kf(emblem["id"], "opacity", [(0, 0, "lin"), (250, 100, "out")])
js(emblem["id"], "positionY", f"var t=input.time.seconds;return {DY}+(t>1.2?Math.sin((t-1.2)*1.8)*7:0);")

# connectors $ → badge
BX, BY = 540, 1095
con = shape("Conectores", [M(DX - 160, DY + 155), C(DX - 230, DY + 300, 330, BY - 190, 330, BY - 82),
                           M(DX + 160, DY + 155), C(DX + 230, DY + 300, 750, BY - 190, 750, BY - 82),
                           M(DX, DY + 232), Lt(DX, BY - 82)],
            strokes=[strokest(EMERALD, 3, dashes=[2, 12])], ar=ar1, trim=0, effects=glow(0.2, 10, 0.8))
b1.append(con)
kf(con["id"], "trimEnd", [(1900, 0, "lin"), (2700, 100, "inout")])
fade(con["id"], 1900, 150, 5700, 300)
js(con["id"], "strokeDashOffset", "return -input.time.seconds*30;")
nodes = shape("Conectores nós", ellipse(330, BY - 82, 7) + ellipse(750, BY - 82, 7) + ellipse(DX, BY - 82, 7),
              fills=[fillst(solid(GOLD_L))], ar=ar1, tr=T(0, 0, o=0))
b1.append(nodes)
kf(nodes["id"], "opacity", [(2650, 0, "lin"), (2750, 100, "out"), (5700, 100, "lin"), (6000, 0, "lin")])

# badge 90 DIAS
bpill = rect("Badge pill", BX, BY, 640, 168, NAVY2, rnd=84, stroke=EMERALD, sw=3, ar=ar1, shadow=shadow(0.5, 36))
sw_ring = shape("Cronômetro aro", ellipse(0, 0, 40), strokes=[strokest(WHITE, 7)], ar=ar1, tr=T(BX - 205, BY + 6))
sw_top = shape("Cronômetro topo", poly([(-12, -58), (12, -58)]) + poly([(0, -58), (0, -46)]) + poly([(30, -36), (38, -44)]),
               strokes=[strokest(WHITE, 7)], ar=ar1, tr=T(BX - 205, BY + 6))
sw_hand = shape("Cronômetro ponteiro", poly([(0, 6), (0, -26)]), strokes=[strokest(EMERALD, 6)], ar=ar1, tr=T(BX - 205, BY + 6))
js(sw_hand["id"], "rotation", "var t=input.time.seconds-2.75;if(t<0)return 0;if(t<0.9)return 720*(1-Math.pow(1-t/0.9,3));return 0;")
b90 = text("Badge 90 DIAS", "90 DIAS", BX + 55, BY + 4, 400, 130, 88, XB, WHITE, ar=ar1)
badge = group("Badge 90 dias", 0, B1D, [bpill, sw_ring, sw_top, sw_hand, b90], tr=T(BX, BY, BX, BY, s=0))
b1.append(badge)
kf_scale(badge["id"], [(2700, 0, "lin"), (3050, 100, "back")])

# headline Até 7,80% em USD
hl = text("Até 7,80% em USD", "Até 7,80% em USD", 540, 1345, 1020, 140, 92, XB, WHITE, ar=ar1, styles=grad_style(1020, GOLD_L, EMERALD, GOLD))
b1.append(hl)
kf(hl["id"], "positionY", [(4150, 1420, "lin"), (4700, 1345, "out")])
fade(hl["id"], 4150, 350)
uline = rect("Sublinhado dourado", 540, 1440, 440, 5, GOLD, rnd=2.5, ar=ar1, paint=lin_grad(0, 0, 440, 0, [(0, a(GOLD, 0)), (0.5, GOLD_L), (1, a(GOLD, 0))]))
b1.append(uline)
kf(uline["id"], "scaleX", [(4500, 0, "lin"), (5100, 100, "out")])
sub1 = text("Sub renda", "RENDA PREVISÍVEL EM MOEDA FORTE", 540, 1500, 1000, 60, 30, SB, GRAY, ar=ar1, tracking=120)
b1.append(sub1)
fade(sub1["id"], 4700, 400)

block1 = group("BLOCO 1 · Gancho e moeda forte", B1S, B1D, b1, tr=T(540, 960, 540, 960))
kf(block1["id"], "opacity", [(5850, 100, "lin"), (6250, 0, "in")])
kf_scale(block1["id"], [(5850, 100, "lin"), (6250, 88, "in")])
kf(block1["id"], "positionY", [(5850, 960, "lin"), (6250, 900, "in")])
root.append(block1)

# =================================================================== BLOCK 2 (6200–14000)
B2S, B2D = 6200, 7800
ar2 = AR(0, B2D)
b2 = []
# ---- world map (dot matrix from Natural Earth 110m land)
LON0, LON1, LAT0, LAT1 = -125.0, 155.0, 72.0, -42.0
MX0, MY0, MW = 40.0, 600.0, 1000.0
SC = MW / (LON1 - LON0)
MH = (LAT0 - LAT1) * SC


def proj(lon, lat):
    return MX0 + (lon - LON0) * SC, MY0 + (LAT0 - lat) * SC


land = json.load(open(LAND))
S4 = 4
img = Image.new("L", (int(MW * S4), int(MH * S4)), 0)
dr = ImageDraw.Draw(img)
for f in land["features"]:
    g = f["geometry"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    for p in polys:
        ring_ = p[0]
        pts = [((proj(lo, la)[0] - MX0) * S4, (proj(lo, la)[1] - MY0) * S4) for lo, la in ring_]
        dr.polygon(pts, fill=255)
STEP = 13.0
dots = []
y = STEP / 2
while y < MH:
    x = STEP / 2
    while x < MW:
        if img.getpixel((int(x * S4), int(y * S4))) > 0:
            dots.append((MX0 + x, MY0 + y))
        x += STEP
    y += STEP
mapc = []
for (x, y) in dots:
    mapc += ellipse(x, y, 3.7)
mapdots = shape("Mapa-múndi (pontos)", mapc, fills=[fillst(solid([0.42, 0.53, 0.64, 1]))], ar=ar2, tr=T(0, 0, o=55))
# routes
USA = proj(-77, 38.5)
ORIG = {"EUROPA": proj(-3.7, 40.4), "ÁFRICA": proj(30.8, 28.5), "ÁSIA": proj(116.4, 35.0)}


def arc(p1, p2, k=0.34):
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    d = math.hypot(dx, dy)
    h = k * d
    c1 = (p1[0] + dx * 0.25, min(p1[1], p2[1]) - h)
    c2 = (p1[0] + dx * 0.75, min(p1[1], p2[1]) - h)
    return [M(*p1), C(c1[0], c1[1], c2[0], c2[1], *p2)]


route_layers, route_halo = [], []
times = {"EUROPA": (700, 1900), "ÁFRICA": (1000, 2300), "ÁSIA": (1250, 2900)}
for name, p in ORIG.items():
    k = 0.30 if name != "ÁSIA" else 0.26
    halo = shape(f"Rota halo {name}", arc(p, USA, k), strokes=[strokest(a(EMERALD, 0.18), 10)], ar=ar2, trim=0)
    r = shape(f"Rota {name}", arc(p, USA, k), strokes=[strokest(EMERALD, 4.5, dashes=[1, 13])], ar=ar2, trim=0, effects=glow(0.15, 12, 1.0))
    t0, t1 = times[name]
    for L_ in (halo, r):
        kf(L_["id"], "trimEnd", [(t0, 0, "lin"), (t1, 100, "inout")])
    js(r["id"], "strokeDashOffset", "return -input.time.seconds*40;")
    route_layers += [halo, r]
# nodes + labels
node_layers = []
for name, p in ORIG.items():
    t0 = times[name][0]
    n = shape(f"Nó {name}", ellipse(0, 0, 9), fills=[fillst(solid(EMERALD))], ar=ar2, tr=T(p[0], p[1], s=0))
    kf_scale(n["id"], [(t0 - 200, 0, "lin"), (t0 + 100, 100, "back")])
    pr = shape(f"Pulso {name}", ellipse(0, 0, 9), strokes=[strokest(EMERALD, 2.5)], ar=ar2, tr=T(p[0], p[1]))
    js(pr["id"], "scaleX", f"var t=input.time.seconds-{t0 / 1000};return t<0?0:100+((t*1000)%1400)/1400*260;")
    js(pr["id"], "scaleY", f"var t=input.time.seconds-{t0 / 1000};return t<0?0:100+((t*1000)%1400)/1400*260;")
    js(pr["id"], "opacity", f"var t=input.time.seconds-{t0 / 1000};return t<0?0:100*(1-((t*1000)%1400)/1400);")
    lab = text(f"Rótulo {name}", name, p[0], p[1] + 40, 240, 60, 26, BD, a(WHITE, 0.85), ar=ar2, tracking=80)
    fade(lab["id"], t0, 300)
    node_layers += [pr, n, lab]
# USA destination
UT = 2600
usa_pulse = []
for i in range(2):
    pr = shape(f"Pulso EUA {i}", ellipse(0, 0, 14), strokes=[strokest(GOLD_L, 3)], ar=ar2, tr=T(USA[0], USA[1]))
    off = UT / 1000 + i * 0.7
    for prop in ("scaleX", "scaleY"):
        js(pr["id"], prop, f"var t=input.time.seconds-{off};return t<0?0:100+((t*1000)%1400)/1400*300;")
    js(pr["id"], "opacity", f"var t=input.time.seconds-{off};return t<0?0:100*(1-((t*1000)%1400)/1400);")
    usa_pulse.append(pr)
usa = shape("Nó EUA", ellipse(0, 0, 14), fills=[fillst(solid(GOLD_L))], ar=ar2, tr=T(USA[0], USA[1], s=0), effects=glow(0.2, 18, 1.3))
kf_scale(usa["id"], [(UT - 300, 0, "lin"), (UT + 50, 100, "back"), (6500, 100, "lin"), (6800, 150, "out"), (7100, 115, "soft")])
usa_lab = text("Rótulo EUA", "EUA", USA[0], USA[1] + 62, 160, 60, 30, XB, GOLD_L, ar=ar2, tracking=100)
fade(usa_lab["id"], UT, 300)
mapgrp = group("Mapa e rotas", 0, B2D, [mapdots] + route_layers + node_layers + usa_pulse + [usa, usa_lab], tr=T(540, 820, 540, 820))
kf_scale(mapgrp["id"], [(0, 60, "lin"), (800, 100, "out")])
kf(mapgrp["id"], "opacity", [(0, 0, "lin"), (450, 100, "out")])
b2.append(mapgrp)
# opening "aperture" ring for the map reveal
ap = shape("Abertura mapa", ellipse(0, 0, 120), strokes=[strokest(EMERALD, 3)], ar=ar2, tr=T(540, 820, s=10, o=0))
kf_scale(ap["id"], [(0, 10, "lin"), (800, 520, "out")])
kf(ap["id"], "opacity", [(0, 90, "lin"), (800, 0, "soft")])
b2.append(ap)

# ---- seal Meridian Blue (top)
def meridian_emblem(cx, cy, r, arx):
    outer = shape("Selo anel", ellipse(cx, cy, r), strokes=[strokest(GOLD, 3)], ar=arx)
    globe = shape("Selo globo", ellipse(cx, cy, r * 0.72) + ellipse(cx, cy, r * 0.32, r * 0.72) + poly([(cx - r * 0.72, cy), (cx + r * 0.72, cy)])
                  + poly([(cx, cy - r * 0.72), (cx, cy + r * 0.72)]),
                  strokes=[strokest(EMERALD, 3)], ar=arx)
    return [outer, globe]


SY = 215
seal_parts = meridian_emblem(540, SY, 58, ar2)
seal_bg = shape("Selo fundo", ellipse(540, SY, 58), fills=[fillst(solid(NAVY2))], ar=ar2)
seal_txt = text("Selo MERIDIAN BLUE", "MERIDIAN BLUE", 540, SY + 112, 900, 80, 60, XB, WHITE, ar=ar2, tracking=60)
seal_sub = text("Selo sub", "PRIVATE BONDS  ·  EUA", 540, SY + 170, 900, 44, 26, SB, GOLD_L, ar=ar2, tracking=300)
seal = group("Selo Meridian Blue (EUA)", 0, B2D, [seal_bg] + seal_parts + [seal_txt, seal_sub], tr=T(540, SY + 80, 540, SY + 80, s=0))
kf_scale(seal["id"], [(1500, 0, "lin"), (1900, 100, "back")])
kf(seal["id"], "opacity", [(1500, 0, "lin"), (1700, 100, "out")])
b2.append(seal)

# ---- container 3D + tag
CY = 1265
track = shape("Trilho contêiner", poly([(60, CY + 108), (1020, CY + 108)]), strokes=[strokest(a(EMERALD, 0.6), 3, dashes=[2, 14])], ar=ar2, trim=0)
kf(track["id"], "trimEnd", [(2900, 0, "lin"), (3600, 100, "out")])
js(track["id"], "strokeDashOffset", "return input.time.seconds*60;")
b2.append(track)
arrow_us = shape("Seta EUA", poly([(84, CY + 96), (66, CY + 108), (84, CY + 120)]), strokes=[strokest(EMERALD, 3)], ar=ar2, tr=T(0, 0, o=0))
fade(arrow_us["id"], 3500, 300)
b2.append(arrow_us)


def side_y(x):
    top = -40 - (x - 110) * (35 / 60)
    return top, top + 130


cshadow = shape("Contêiner sombra", ellipse(0, 112, 175, 16), fills=[fillst(solid([0, 0, 0, 0.45]))], ar=ar2)
front = shape("Contêiner frente", poly([(-170, -40), (110, -40), (110, 90), (-170, 90)], True),
              fills=[fillst(lin_grad(0, -40, 0, 90, [(0, [0.0, 0.66, 0.45, 1]), (1, [0.0, 0.48, 0.33, 1])]))], ar=ar2)
side = shape("Contêiner lateral", poly([(110, -40), (170, -75), (170, 55), (110, 90)], True), fills=[fillst(solid([0.0, 0.38, 0.27, 1]))], ar=ar2)
top = shape("Contêiner topo", poly([(-170, -40), (-110, -75), (170, -75), (110, -40)], True), fills=[fillst(solid([0.25, 0.85, 0.62, 1]))], ar=ar2)
cor = []
for x in range(-150, 110, 20):
    cor += [M(x, -32), Lt(x, 82)]
corr = shape("Contêiner corrugado", cor, strokes=[strokest([0.0, 0.36, 0.25, 1], 3, cap="butt")], ar=ar2)
dc = []
for x in (128, 152):
    t_, b_ = side_y(x)
    dc += [M(x, t_ + 8), Lt(x, b_ - 8)]
doors = shape("Contêiner portas", dc, strokes=[strokest([0.0, 0.25, 0.18, 1], 3)], ar=ar2)
edges = shape("Contêiner arestas", poly([(-170, 90), (-170, -40), (110, -40), (170, -75)]) + poly([(110, -40), (110, 90)]),
              strokes=[strokest([0.6, 1, 0.82, 0.7], 2)], ar=ar2)
plate = rect("Contêiner placa", -30, 25, 150, 46, [0.02, 0.1, 0.16, 0.85], rnd=6, ar=ar2)
plate_t = text("Contêiner placa texto", "MB · USA", -30, 26, 150, 46, 22, XB, GOLD_L, ar=ar2, tracking=60)
cont_inner = group("Contêiner corpo", 0, B2D, [front, side, top, corr, doors, edges, plate, plate_t], tr=T(0, 0))
js(cont_inner["id"], "positionY", "var t=input.time.seconds;return t>4?Math.sin((t-4)*3.2)*3:0;")
speed = shape("Linhas de velocidade", poly([(200, -20), (330, -20)]) + poly([(215, 20), (380, 20)]) + poly([(205, 60), (300, 60)]),
              strokes=[strokest(a(WHITE, 0.6), 3)], ar=ar2, tr=T(0, 0, o=0))
kf(speed["id"], "opacity", [(3000, 0, "lin"), (3100, 90, "lin"), (3800, 90, "lin"), (4100, 0, "soft")])
container = group("Contêiner 3D Agro Exportação", 0, B2D, [cshadow, speed, cont_inner], tr=T(1400, CY))
kf(container["id"], "positionX", [(3000, 1400, "lin"), (3900, 600, "out"), (7800, 520, "lin")])
b2.append(container)
# tag
TY = 1475
tag_tie = shape("Tag ligação", poly([(0, 0), (0, 40)]), strokes=[strokest(GOLD, 2.5, dashes=[2, 8])], ar=ar2, tr=T(540, TY - 92))
tag_bg = rect("Tag fundo", 540, TY, 820, 108, NAVY2, rnd=54, stroke=GOLD, sw=2.5, ar=ar2, shadow=shadow(0.45, 30))
gar = [M(0, -30), C(6, -18, 30, -6, 28, 10), C(26, 26, 12, 32, 0, 32), C(-12, 32, -26, 26, -28, 10), C(-30, -6, -6, -18, 0, -30), Z(),
       M(0, -22), C(7, 0, 7, 18, 0, 31), M(0, -22), C(-7, 0, -7, 18, 0, 31), M(-8, 32), Lt(-11, 39), M(0, 32), Lt(0, 40), M(8, 32), Lt(11, 39)]
garlic = shape("Ícone alho", gar, strokes=[strokest(WHITE, 3.2)], ar=ar2, tr=T(205, TY - 2))
tag_l = text("Tag AGRO EXPORTAÇÃO", "AGRO EXPORTAÇÃO", 690, TY + 2, 440, 70, 36, XB, WHITE, just="right", ar=ar2, tracking=20)
tag_s = text("Tag separador", "|", 718, TY, 30, 70, 40, XB, GOLD, ar=ar2)
tag_r = text("Tag ALHO", "ALHO", 744, TY + 2, 200, 70, 36, XB, EMERALD, just="left", ar=ar2, tracking=20)
tag = group("Tag Agro Exportação | Alho", 0, B2D, [tag_tie, tag_bg, garlic, tag_l, tag_s, tag_r], tr=T(540, TY, 540, TY, s=0))
kf_scale(tag["id"], [(4100, 0, "lin"), (4450, 100, "back")])
kf(tag["id"], "positionY", [(4100, TY - 80, "lin"), (4450, TY, "out")])
b2.append(tag)

block2 = group("BLOCO 2 · Tese da operação", B2S, B2D, b2, tr=T(540, 960, 540, 960))
kf(block2["id"], "opacity", [(0, 0, "lin"), (200, 100, "lin"), (7400, 100, "lin"), (7800, 0, "in")])
kf_scale(block2["id"], [(7400, 100, "lin"), (7800, 112, "in")])
root.append(block2)

# =================================================================== BLOCK 3 (13950–21300)
B3S, B3D = 13950, 7350
ar3 = AR(0, B3D)
b3 = []
hdr3 = text("Cabeçalho bloco 3", "RENTABILIDADE  •  GARANTIAS REAIS", 540, 430, 1000, 50, 28, SB, GRAY, ar=ar3, tracking=200)
b3.append(hdr3)
CW, CH, CYC = 470, 830, 990
C1X, C2X = 287, 793


def card_bg(cx, accent):
    bg = rect("Card fundo", cx, CYC, CW, CH, a(NAVY2, 0.96), rnd=38, stroke=a(EMERALD, 0.35), sw=2, ar=ar3, shadow=shadow(0.55, 46, (0, 24)),
              paint=lin_grad(0, 0, 0, CH, [(0, [0.09, 0.2, 0.3, 0.97]), (1, [0.05, 0.12, 0.19, 0.97])]))
    bar = rect("Card acento", cx, CYC - CH / 2 + 3, 120, 6, accent, rnd=3, ar=ar3)
    return [bg, bar]


# ---- card 1: rentabilidade
c1 = card_bg(C1X, EMERALD)
c1h = text("Card1 título", "RENTABILIDADE", C1X, 640, 420, 44, 24, SB, GRAY, ar=ar3, tracking=220)
icon_box = rect("Ícone gráfico caixa", C1X, 745, 104, 104, a(EMERALD, 0.10), rnd=26, stroke=a(EMERALD, 0.6), sw=2.5, ar=ar3)
bars = []
for i, (bh) in enumerate((18, 30, 44)):
    bars.append(rect(f"Ícone barra {i}", C1X - 26 + i * 22, 785 - bh / 2, 13, bh, a(EMERALD, 0.45), rnd=3, ar=ar3))
chart_line = shape("Ícone linha ascendente", poly([(-34, 14), (-12, -6), (4, 4), (32, -26)]) + poly([(18, -27), (32, -26), (31, -12)]),
                   strokes=[strokest(EMERALD, 5)], ar=ar3, tr=T(C1X, 750), trim=0)
kf(chart_line["id"], "trimEnd", [(500, 0, "lin"), (1200, 100, "out")])
c1l1 = text("Card1 label mínimo", "MÍNIMO GARANTIDO", C1X, 850, 440, 44, 26, SB, a(WHITE, 0.8), ar=ar3, tracking=80)
c1v1 = text("Card1 valor 4,50%", "4,50%", C1X, 932, 440, 110, 100, XB, WHITE, ar=ar3)
js(c1v1["id"], "textContent", count_js(1450, 2650, 0, 4.5, "pct"))
arrowd = shape("Seta ➔ projeção", poly([(0, -22), (0, 18)]) + poly([(-13, 5), (0, 19), (13, 5)]), strokes=[strokest(GOLD_L, 5)], ar=ar3, tr=T(C1X, 1022, o=0))
kf(arrowd["id"], "opacity", [(2750, 0, "lin"), (2950, 100, "out")])
kf(arrowd["id"], "positionY", [(2750, 1005, "lin"), (3050, 1022, "out")])
c1l2 = text("Card1 label projeção", "PROJEÇÃO", C1X, 1088, 440, 44, 26, SB, a(WHITE, 0.8), ar=ar3, tracking=80)
fade(c1l2["id"], 2900, 300)
c1v2 = text("Card1 valor 7,80%", "7,80%", C1X, 1170, 440, 110, 100, XB, WHITE, ar=ar3, styles=grad_style(440, GOLD_L, EMERALD))
js(c1v2["id"], "textContent", count_js(3000, 4000, 4.5, 7.8, "pct"))
fade(c1v2["id"], 2950, 250)
spark_pts = [(C1X - 185, 1345), (C1X - 130, 1330), (C1X - 85, 1338), (C1X - 30, 1310), (C1X + 20, 1318), (C1X + 75, 1290), (C1X + 120, 1296), (C1X + 185, 1262)]
spark = shape("Card1 sparkline", poly(spark_pts), strokes=[strokest(EMERALD, 4, paint=lin_grad(C1X - 185, 0, C1X + 185, 0, [(0, a(EMERALD, 0.3)), (1, GOLD_L)]))], ar=ar3, trim=0)
kf(spark["id"], "trimEnd", [(3000, 0, "lin"), (4000, 100, "out")])
spark_dot = shape("Card1 sparkline ponto", ellipse(C1X + 185, 1262, 8), fills=[fillst(solid(GOLD_L))], ar=ar3, tr=T(0, 0, o=0), effects=glow(0.2, 12, 1.2))
kf(spark_dot["id"], "opacity", [(3950, 0, "lin"), (4100, 100, "out")])
card1 = group("Card 1 · Rentabilidade", 0, B3D, c1 + [c1h, icon_box] + bars + [chart_line, c1l1, c1v1, arrowd, c1l2, c1v2, spark, spark_dot],
              tr=T(C1X, CYC, C1X, CYC))
kf(card1["id"], "positionX", [(0, 540, "lin"), (700, C1X, "out"), (7000, C1X, "lin"), (7350, 540, "in")])
kf_scale(card1["id"], [(0, 70, "lin"), (700, 100, "out"), (7000, 100, "lin"), (7350, 0, "in")])
kf(card1["id"], "opacity", [(0, 0, "lin"), (350, 100, "out"), (7150, 100, "lin"), (7350, 0, "lin")])
js(card1["id"], "positionY", f"return {CYC}+Math.sin(input.time.seconds*1.6)*7;")
b3.append(card1)

# ---- card 2: garantias
c2 = card_bg(C2X, GOLD)
c2h = text("Card2 título", "GARANTIAS REAIS", C2X, 640, 420, 44, 24, SB, GRAY, ar=ar3, tracking=220)


def lock_seal(cy, t_lock, name):
    ring_ = shape(f"Selo {name} anel", ellipse(0, 0, 74), strokes=[strokest(GOLD_L, 3, dashes=[1, 10])], ar=ar3, tr=T(0, 0))
    js(ring_["id"], "rotation", "return input.time.seconds*25;")
    disc_ = shape(f"Selo {name} disco", ellipse(0, 0, 60), fills=[fillst(lin_grad(0, -60, 0, 60, [(0, EMERALD), (1, EMERALD_D)]))], ar=ar3, effects=glow(0.5, 14, 0.6))
    body = rect(f"Selo {name} cadeado corpo", 0, 12, 46, 38, NAVY_DEEP, rnd=7, ar=ar3)
    hole = shape(f"Selo {name} fechadura", ellipse(0, 8, 5) + poly([(0, 10), (0, 22)]), fills=[fillst(solid(EMERALD))], strokes=[strokest(EMERALD, 4)], ar=ar3)
    shackle = shape(f"Selo {name} haste", [M(-14, -6), Lt(-14, -16), C(-14, -36, 14, -36, 14, -16), Lt(14, -6)], strokes=[strokest(NAVY_DEEP, 7)], ar=ar3, tr=T(0, -14))
    kf(shackle["id"], "positionY", [(t_lock + 120, -14, "lin"), (t_lock + 300, 0, "in")])
    flash = shape(f"Selo {name} flash", ellipse(0, 0, 70), strokes=[strokest(GOLD_L, 4)], ar=ar3, tr=T(0, 0, o=0))
    kf(flash["id"], "opacity", [(t_lock + 300, 0, "lin"), (t_lock + 330, 100, "lin"), (t_lock + 800, 0, "soft")])
    kf_scale(flash["id"], [(t_lock + 300, 100, "lin"), (t_lock + 800, 170, "out")])
    g = group(f"Selo {name}", 0, B3D, [ring_, disc_, body, hole, shackle, flash], tr=T(C2X, cy, 0, 0, s=0))
    kf_scale(g["id"], [(t_lock - 10, 0, "lin"), (t_lock, 170, "lin"), (t_lock + 160, 94, "in"), (t_lock + 300, 100, "out")])
    kf(g["id"], "opacity", [(t_lock - 10, 0, "lin"), (t_lock + 80, 100, "lin")])
    return g


sealA = lock_seal(790, 4250, "Estoques")
txtA = text("Garantia Estoques Certificados", "Estoques\nCertificados", C2X, 935, 430, 100, 36, BD, WHITE, ar=ar3, leading=44)
kf(txtA["id"], "positionX", [(4500, C2X - 40, "lin"), (4850, C2X, "out")])
fade(txtA["id"], 4500, 300)
sealB = lock_seal(1110, 5550, "Recebíveis")
txtB = text("Garantia Cessão Fiduciária", "Cessão Fiduciária\nde Recebíveis", C2X, 1255, 430, 100, 34, BD, WHITE, ar=ar3, leading=42)
kf(txtB["id"], "positionX", [(5800, C2X - 40, "lin"), (6150, C2X, "out")])
fade(txtB["id"], 5800, 300)
card2 = group("Card 2 · Garantias reais", 0, B3D, c2 + [c2h, sealA, txtA, sealB, txtB], tr=T(C2X, CYC, C2X, CYC))
kf(card2["id"], "positionX", [(0, 540, "lin"), (700, C2X, "out"), (7000, C2X, "lin"), (7350, 540, "in")])
kf_scale(card2["id"], [(0, 70, "lin"), (700, 100, "out"), (7000, 100, "lin"), (7350, 0, "in")])
kf(card2["id"], "opacity", [(0, 0, "lin"), (350, 100, "out"), (7150, 100, "lin"), (7350, 0, "lin")])
js(card2["id"], "positionY", f"return {CYC}+Math.sin(input.time.seconds*1.6+1.7)*7;")
b3.append(card2)
block3 = group("BLOCO 3 · Rentabilidade e garantias", B3S, B3D, b3, tr=T(540, 960, 540, 960))
kf(hdr3["id"], "opacity", [(300, 0, "lin"), (700, 100, "out"), (6900, 100, "lin"), (7200, 0, "lin")])
root.append(block3)

# =================================================================== BLOCK 4 (21250–26300)
B4S, B4D = 21250, 5050
ar4 = AR(0, B4D)
b4 = []
PY, PW, PH = 955, 960, 780
panel_bg = rect("Painel fundo", 540, PY, PW, PH, NAVY2, rnd=42, stroke=a(EMERALD, 0.4), sw=2, ar=ar4, shadow=shadow(0.55, 50, (0, 26)),
                paint=lin_grad(0, 0, 0, PH, [(0, [0.09, 0.2, 0.3, 0.97]), (1, [0.05, 0.12, 0.19, 0.97])]))
live = shape("Indicador ao vivo", ellipse(0, 0, 8), fills=[fillst(solid(GOLD_L))], ar=ar4, tr=T(150, PY - PH / 2 + 72))
js(live["id"], "opacity", "return 55+45*Math.sin(input.time.seconds*6);")
p_hdr = text("Painel título", "OPORTUNIDADE EXCLUSIVA", 176, PY - PH / 2 + 72, 760, 46, 28, SB, GOLD_L, just="left", ar=ar4, tracking=220)
div1 = rect("Painel divisor 1", 540, PY - PH / 2 + 125, 840, 2, a(WHITE, 0.10), ar=ar4)
# row 1
r1y = PY - PH / 2 + 205
r1_lab = text("Linha1 label", "Aporte Mínimo", 120, r1y, 600, 50, 34, SB, GRAY, just="left", ar=ar4)
r1_val = text("Linha1 valor", "$5.000 USD", 120, r1y + 90, 760, 110, 92, XB, WHITE, just="left", ar=ar4)
js(r1_val["id"], "textContent", count_js(600, 1700, 0, 5000, "usdUSD"))
coin = shape("Ícone moeda", ellipse(0, 0, 44), fills=[fillst(solid(a(EMERALD, 0.12)))], strokes=[strokest(EMERALD, 3)], ar=ar4, tr=T(900, r1y + 50))
coin_t = text("Ícone moeda $", "$", 900, r1y + 52, 80, 80, 48, XB, EMERALD, ar=ar4)
js(coin["id"], "rotationY", "var t=input.time.seconds;return t<1.7?Math.max(0,1.7-t)/1.7*720:0;")
js(coin_t["id"], "rotationY", "var t=input.time.seconds;return t<1.7?Math.max(0,1.7-t)/1.7*720:0;")
row1 = group("Linha 1 · Aporte mínimo", 0, B4D, [r1_lab, r1_val, coin, coin_t], tr=T(0, 0))
kf(row1["id"], "positionX", [(250, -60, "lin"), (650, 0, "out")])
kf(row1["id"], "opacity", [(250, 0, "lin"), (550, 100, "out")])
div2 = rect("Painel divisor 2", 540, r1y + 175, 840, 2, a(WHITE, 0.10), ar=ar4)
# row 2
r2y = r1y + 250
r2_lab = text("Linha2 label", "Captação Total", 120, r2y, 600, 50, 34, SB, GRAY, just="left", ar=ar4)
r2_val = text("Linha2 valor", "$162.000", 120, r2y + 90, 760, 110, 92, XB, WHITE, just="left", ar=ar4, styles=grad_style(560, WHITE, EMERALD))
js(r2_val["id"], "textContent", count_js(2300, 3800, 0, 162000, "usd"))
bar_y = r2y + 205
bar_track = rect("Barra trilho", 540, bar_y, 840, 22, a(WHITE, 0.10), rnd=11, ar=ar4)
bar_fill = rect("Barra progresso", 120, bar_y, 840, 22, EMERALD, rnd=11, ar=ar4, anchor="left",
                paint=lin_grad(0, 0, 840, 0, [(0, EMERALD_D), (0.7, EMERALD), (1, GOLD_L)]), effects=glow(0.4, 14, 0.9))
kf(bar_fill["id"], "scaleX", [(2300, 0, "lin"), (3800, 100, "out")])
pct = text("Barra %", "100%", 960, bar_y + 48, 200, 40, 26, XB, GOLD_L, just="right", ar=ar4)
js(pct["id"], "textContent", "var t=input.time.milliseconds;var p=Math.max(0,Math.min(1,(t-2300)/1500));var e=1-Math.pow(1-p,3);return Math.round(e*100)+'%';")
fade(pct["id"], 2300, 200)
vl = text("Volume limitado", "VOLUME LIMITADO", 120, bar_y + 48, 500, 40, 24, SB, GOLD_L, just="left", ar=ar4, tracking=200)
fade(vl["id"], 3700, 300)
row2 = group("Linha 2 · Captação total", 0, B4D, [r2_lab, r2_val, bar_track, bar_fill, pct, vl], tr=T(0, 0))
kf(row2["id"], "positionX", [(1900, -60, "lin"), (2300, 0, "out")])
kf(row2["id"], "opacity", [(1900, 0, "lin"), (2200, 100, "out")])
panel = group("Painel de oportunidade", 0, B4D, [panel_bg, live, p_hdr, div1, row1, div2, row2], tr=T(540, PY, 540, PY))
kf(panel["id"], "scaleY", [(0, 4, "lin"), (450, 100, "out")])
kf(panel["id"], "scaleX", [(0, 80, "lin"), (450, 100, "out")])
kf(panel["id"], "opacity", [(0, 0, "lin"), (200, 100, "lin")])
b4.append(panel)
# Reg S badge
RY = 1560
reg_bg = rect("Badge Reg S fundo", 540, RY, 640, 80, a(NAVY_DEEP, 0.8), rnd=40, stroke=a(GRAY, 0.55), sw=1.5, ar=ar4)
reg_i = shape("Badge Reg S ícone", ellipse(0, 0, 13) + poly([(0, -3), (0, 7)]) + ellipse(0, -8, 1.6), strokes=[strokest(GRAY, 2.6)], ar=ar4, tr=T(262, RY))
reg_t = text("Badge Reg S texto", "Reg S  |  Não residentes nos EUA", 560, RY + 1, 560, 60, 28, SB, a(WHITE, 0.85), ar=ar4)
reg = group("Badge Reg S", 0, B4D, [reg_bg, reg_i, reg_t], tr=T(0, 0))
kf(reg["id"], "positionY", [(3900, 40, "lin"), (4250, 0, "out")])
kf(reg["id"], "opacity", [(3900, 0, "lin"), (4200, 100, "out")])
b4.append(reg)
blur4_id, blur4 = blur(0)
block4 = group("BLOCO 4 · Ticket e exclusividade", B4S, B4D, b4, tr=T(540, 960, 540, 960), effects=blur4)
js_effect(blur4_id, "blurriness", "var t=input.time.milliseconds;return t<4650?0:Math.min(60,(t-4650)/400*60);")
kf(block4["id"], "opacity", [(4650, 100, "lin"), (5050, 0, "in")])
kf_scale(block4["id"], [(4650, 100, "lin"), (5050, 94, "in")])
root.append(block4)

# =================================================================== BLOCK 5 (26200–30400)
B5S, B5D = 26200, DUR_MS - 26200
ar5 = AR(0, B5D)
b5 = []
focus = rect("Foco escurecer", 540, 960, W, H, [0, 0, 0, 0], ar=ar5,
             paint=lin_grad(540, 960, 540 + 1100, 960, [(0, [0, 0, 0, 0]), (0.5, [0.01, 0.03, 0.06, 0.35]), (1, [0.01, 0.03, 0.06, 0.85])], "radial"))
fade(focus["id"], 0, 500)
b5.append(focus)
# brand mini
mini = group("Marca Meridian Blue (mini)", 0, B5D,
             [shape("Mini fundo", ellipse(540, 620, 40), fills=[fillst(solid(NAVY2))], ar=ar5)] + meridian_emblem(540, 620, 40, ar5)
             + [text("Mini MERIDIAN BLUE", "MERIDIAN BLUE", 540, 700, 700, 50, 34, XB, a(WHITE, 0.9), ar=ar5, tracking=80)], tr=T(0, 0))
kf(mini["id"], "opacity", [(250, 0, "lin"), (650, 100, "out")])
kf(mini["id"], "positionY", [(250, 30, "lin"), (650, 0, "out")])
b5.append(mini)
BY5 = 960
# ripple rings (click)
rings = []
for i, d in enumerate((0, 160)):
    rr = rect(f"Onda clique {i}", 540, BY5, 800, 150, [0, 0, 0, 0], rnd=75, stroke=EMERALD, sw=4, ar=ar5, o=0)
    t0 = 1800 + d
    kf(rr["id"], "opacity", [(t0, 0, "lin"), (t0 + 40, 90, "lin"), (t0 + 900, 0, "soft")])
    kf_scale(rr["id"], [(t0, 100, "lin"), (t0 + 900, 135, "out")])
    rings.append(rr)
wave = radial("Onda de luz", 860, 990, 300, [(0, a(EMERALD, 0.5)), (0.6, a(EMERALD, 0.12)), (1, a(EMERALD, 0))], ar5, o=0, s=10)
kf(wave["id"], "opacity", [(1800, 0, "lin"), (1850, 100, "lin"), (2900, 0, "soft")])
kf_scale(wave["id"], [(1800, 10, "lin"), (2900, 420, "out")])
b5 += rings + [wave]
# button
btn_glow_id_list = []
bglow = rect("Botão brilho", 540, BY5, 800, 150, EMERALD, rnd=75, ar=ar5, effects=[{"id": neff(), "effect": {"type": "gaussianBlur", "blurriness": 40, "repeatEdgePixels": False}}])
js(bglow["id"], "opacity", "var t=input.time.seconds;var f=(t>1.8&&t<2.6)?(1-(t-1.8)/0.8)*45:0;return Math.min(100,40+18*Math.sin(t*5.2)+f);")
bbody = rect("Botão", 540, BY5, 800, 150, EMERALD, rnd=75, ar=ar5, paint=lin_grad(0, 0, 0, 150, [(0, [0.15, 0.9, 0.62, 1]), (1, EMERALD_D)]),
             shadow=shadow(0.5, 30, (0, 14)))
btxt = text("Botão texto", "ACESSAR TERM SHEET", 500, BY5 + 2, 640, 90, 46, XB, NAVY_DEEP, ar=ar5, tracking=30)
bico = shape("Botão seta", poly([(-14, 0), (14, 0)]) + poly([(2, -12), (15, 0), (2, 12)]), strokes=[strokest(NAVY_DEEP, 6)], ar=ar5, tr=T(850, BY5))
btn_pulse = group("Botão (pulso)", 0, B5D, [bglow, bbody, btxt, bico], tr=T(540, BY5, 540, BY5))
pulse_js = ("var t=input.time.seconds;var s=t>0.6?100+2.6*Math.sin((t-0.6)*5.2):100;"
            "if(t>1.8&&t<2.1){var p=(t-1.8)/0.3;s=s-6*Math.sin(Math.PI*p);}return s;")
js(btn_pulse["id"], "scaleX", pulse_js)
js(btn_pulse["id"], "scaleY", pulse_js)
button = group("Botão ACESSAR TERM SHEET", 0, B5D, [btn_pulse], tr=T(540, BY5, 540, BY5))
kf_scale(button["id"], [(200, 60, "lin"), (700, 100, "back")])
kf(button["id"], "opacity", [(200, 0, "lin"), (450, 100, "out")])
b5.append(button)
cta_sub = text("CTA apoio", "Garanta sua alocação agora", 540, BY5 + 150, 900, 60, 36, SB, a(WHITE, 0.9), ar=ar5)
kf(cta_sub["id"], "opacity", [(2300, 0, "lin"), (2700, 100, "out")])
kf(cta_sub["id"], "positionY", [(2300, BY5 + 185, "lin"), (2700, BY5 + 150, "out")])
b5.append(cta_sub)
# cursor
cur = shape("Cursor", poly([(0, 0), (0, 62), (15, 48), (26, 72), (36, 67), (25, 44), (44, 44)], True),
            fills=[fillst(solid(WHITE))], strokes=[strokest(NAVY_DEEP, 3)], ar=ar5, tr=T(980, 1560, s=125, o=0))
cur["dropShadow"] = shadow(0.5, 12, (0, 6))
kf(cur["id"], "positionX", [(900, 980, "lin"), (1700, 862, "inout")])
kf(cur["id"], "positionY", [(900, 1560, "lin"), (1700, 990, "inout")])
kf(cur["id"], "opacity", [(900, 0, "lin"), (1150, 100, "out")])
kf_scale(cur["id"], [(1780, 125, "lin"), (1860, 105, "in"), (2050, 125, "out")])
b5.append(cur)
# legal
legal = text("Aviso regulatório", "Oferta destinada exclusivamente a investidores não residentes nos EUA (Regulation S). "
             "Rentabilidade projetada não é garantia de resultados futuros. Investimentos envolvem riscos, inclusive de perda do capital. "
             "Leia o Term Sheet e os documentos da oferta antes de investir.",
             540, 1735, 960, 200, 24, MD, a(GRAY, 0.85), ar=ar5, leading=32)
fade(legal["id"], 500, 500)
b5.append(legal)
block5 = group("BLOCO 5 · CTA", B5S, B5D, b5, tr=T(540, 960, 540, 960))
root.append(block5)

# =================================================================== AUDIO
A = []
A.append(audio("Narração (nivelada)", "narracao", 0, 30197, 30197, 0.71))
music = audio("Trilha corporativa (procedural)", "music", 0, DUR_MS, DUR_MS, 0.3)
A.append(music)
js(music["id"], "volume", "var t=input.time.seconds;var g=0.3;if(t<0.15)g*=t/0.15;return g;")
SFX = [  # (name, asset, start_ms, file_ms, gain)
    ("SFX whoosh entrada", "sfx_whoosh_a", 0, 600, 0.55),
    ("SFX clique $ trava", "sfx_click", 1080, 65, 0.8),
    ("SFX pop 90 DIAS", "sfx_pop", 2700, 180, 0.75),
    ("SFX whoosh bloco 2", "sfx_whoosh_b", 5900, 500, 0.6),
    ("SFX conexão digital rotas", "sfx_data", 6850, 2000, 0.22),
    ("SFX whoosh contêiner", "sfx_whoosh_a", 9150, 600, 0.5),
    ("SFX pop tag", "sfx_pop", 10300, 180, 0.6),
    ("SFX whoosh bloco 3", "sfx_whoosh_b", 13700, 500, 0.6),
    ("SFX contagem 4,50%", "sfx_counter_1200", 15400, 1200, 0.16),
    ("SFX contagem 7,80%", "sfx_counter_1000", 16950, 1000, 0.16),
    ("SFX trava estoques", "sfx_lock", 18200, 450, 0.42),
    ("SFX trava recebíveis", "sfx_lock", 19500, 450, 0.42),
    ("SFX cards recolhem", "sfx_collapse", 20950, 700, 0.5),
    ("SFX contagem aporte", "sfx_counter_1000", 21850, 1000, 0.14),
    ("SFX barra preenchendo", "sfx_barfill", 23550, 1500, 0.4),
    ("SFX notificação Reg S", "sfx_ping", 25150, 480, 0.35),
    ("SFX whoosh foco", "sfx_whoosh_b", 25950, 500, 0.5),
    ("SFX clique mouse", "sfx_click", 27990, 65, 0.9),
    ("SFX ping confirmação", "sfx_ping", 28060, 480, 0.5),
]
for name, asset, st, d, g in SFX:
    A.append(audio(name, asset, st, d, d, g))

# =================================================================== assemble
doc = json.load(open(SRC))
doc["duration"] = DUR_MS / 1000
doc["backgroundColor"] = NAVY
comp = doc["composition"]
comp["name"] = "Meridian Agro Exportação 30s"
comp["layers"] = list(reversed(root)) + A   # front first; audio has no visuals
comp["dynamics"] = {"entries": DYN}
json.dump(doc, open(OUT, "w"), ensure_ascii=False, indent=1)
print(f"layers ok, dynamics={len(DYN)}, map dots={len(dots)}, last id={_ids[0]}")
