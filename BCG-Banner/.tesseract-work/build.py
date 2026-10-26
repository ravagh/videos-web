"""Builds the editable Tesseract document for the BCG 8:1 header banner.

Usage: python3 -I build.py <checked-out editable.json> <output.json>
Canvas 3840x480 (8:1), 10 s seamless loop. Every element is a native, editable
layer (image, text, rect, shape, group). Times in ms.

Loop contract: every procedural animation has a period that divides 10 s and
every keyframed element is in the same state at 0 and 10000 ms.
"""
import json, math, random, sys

SRC, OUT = sys.argv[1], sys.argv[2]
W, H = 3840, 480
CX, CY = W / 2, H / 2
DUR = 10000
LOOP_S = DUR / 1000

# ------------------------------------------------------------------ palette
BLACK = [0.012, 0.016, 0.031, 1]          # #030408
BLUE = [0.243, 0.494, 1.0, 1]             # electric blue #3E7EFF
BLUE_L = [0.62, 0.75, 1.0, 1]             # star highlight #9EBFFF
BLUE_D = [0.09, 0.22, 0.62, 1]
ICE = [0.86, 0.91, 1.0, 1]
WHITE = [1, 1, 1, 1]


def a(c, alpha):
    return [c[0], c[1], c[2], alpha]


XB = ("Outfit ExtraBold", "Regular")
SB = ("Outfit SemiBold", "Regular")

# ------------------------------------------------------------------ ids / dynamics
_ids = [0]
_eff = [9000]
_kf = [0]
DYN = []


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
    "in": {"type": "cubicBezier", "x1": 0.55, "y1": 0, "x2": 0.85, "y2": 0.3},
}


def _keys(keys):
    out = []
    for t, v, e in keys:
        _kf[0] += 1
        val = {"type": "vector2", "value": v} if isinstance(v, (list, tuple)) else {"type": "float", "value": float(v)}
        out.append({"id": f"k{_kf[0]}", "layerTime": int(t), "value": val, "easing": EASE[e]})
    return out


def kf(lid, prop, keys):
    DYN.append({"target": {"kind": "layer", "layerId": lid, "propertyType": prop},
                "animator": {"type": "keyframes", "enabled": True, "keyframes": _keys(keys)}})


def kf_item(item, prop, keys):
    DYN.append({"target": {"kind": "fxItemProperty", "itemId": item, "propertyName": prop},
                "animator": {"type": "keyframes", "enabled": True, "keyframes": _keys(keys)}})


def kf_scale(lid, keys):
    kf(lid, "scaleX", keys)
    kf(lid, "scaleY", keys)


def js(lid, prop, code):
    DYN.append({"target": {"kind": "layer", "layerId": lid, "propertyType": prop},
                "animator": {"type": "jsScript", "layerTimeJsCode": code}})


def js_effect(eid, param, code):
    DYN.append({"target": {"kind": "effectProperty", "effectId": eid, "paramName": param},
                "animator": {"type": "jsScript", "layerTimeJsCode": code}})


# ------------------------------------------------------------------ layer builders
def T(x, y, ax=0, ay=0, s=100, o=100, r=0):
    sx, sy = (s, s) if not isinstance(s, (list, tuple)) else s
    return {"anchorPoint": [ax, ay], "position": [x, y], "scale": [sx, sy], "rotation": r, "opacity": o}


def AR(start, dur):
    return {"start": int(start), "duration": int(dur)}


ALL = AR(0, DUR)


def solid(c):
    return {"type": "solid", "color": list(c)}


def grad(x0, y0, x1, y1, stops, kind="linear"):
    return {"type": "gradient", "gradientType": kind, "start": [x0, y0], "end": [x1, y1],
            "stops": [{"offset": o, "color": list(c)} for o, c in stops]}


def rect(name, cx, cy, w, h, fill=(0, 0, 0, 0), rnd=0, stroke=None, sw=0, paint=None,
         anchor="center", effects=None, o=100, r=0, s=100, ar=ALL, blend="normal"):
    lid = nid()
    ax, ay = {"center": (w / 2, h / 2), "left": (0, h / 2), "right": (w, h / 2)}[anchor]
    rc = {"size": [w, h], "fillColor": list(fill), "roundness": rnd}
    if fill[3] == 0 and not paint:
        rc["fillEnabled"] = False
    if paint:
        rc["fillPaint"] = paint
    if stroke:
        rc.update(strokeEnabled=True, strokeColor=list(stroke), strokeWidth=sw)
    L = {"type": "Rect", "id": lid, "name": name, "blendMode": blend, "activeRange": ar,
         "transform": T(cx, cy, ax, ay, s=s, o=o, r=r), "rect": rc}
    if effects:
        L["effects"] = effects
    return L


def radial(name, cx, cy, r, stops, sy=100, o=100, blend="normal"):
    L = rect(name, cx, cy, 2 * r, 2 * r, paint=grad(r, r, 2 * r, r, stops, "radial"), o=o, blend=blend)
    L["transform"]["scale"] = [100, sy]
    return L


def fillst(c, o=1.0):
    return {"paint": solid(a(c, 1)), "fillRule": "nonZeroWinding", "blendMode": "normal", "opacity": o}


def strokest(c, w, o=1.0, cap="round", paint=None):
    return {"paint": paint or solid(a(c, 1)), "width": w, "cap": cap, "join": "round", "miterLimit": 4,
            "blendMode": "normal", "opacity": o}


def shape(name, cmds, fills=(), strokes=(), tr=None, effects=None, trim=None, blend="normal", ar=ALL):
    lid = nid()
    sh = {"path": {"commands": cmds}, "fills": list(fills), "strokes": list(strokes)}
    if trim is not None:
        sh["trim"] = {"start": 0, "end": trim, "mode": "simultaneously"}
    L = {"type": "Shape", "id": lid, "name": name, "blendMode": blend, "activeRange": ar,
         "transform": tr or T(0, 0), "shape": sh}
    if effects:
        L["effects"] = effects
    return L


def group(name, children, tr=None, effects=None, start=0, dur=DUR):
    lid = nid()
    g = {"type": "Group", "id": lid, "name": name, "blendMode": "normal",
         "playback": {"type": "windowed", "inputRange": AR(start, dur), "inputOffsetMs": -int(start),
                      "mapping": {"type": "linear", "input": AR(0, dur), "output": AR(0, dur)}},
         "transform": tr or T(0, 0), "layers": list(reversed(children))}  # children given back->front
    if effects:
        g["effects"] = effects
    return g


def glow(th=0.2, rad=24, inten=1.0):
    e = neff()
    return e, [{"id": e, "effect": {"type": "glow", "glowThreshold": th, "glowRadius": rad, "glowIntensity": inten}}]


def blur(amount):
    e = neff()
    return e, {"id": e, "effect": {"type": "gaussianBlur", "blurriness": amount, "repeatEdgePixels": False}}


K = 0.5522847


def M(x, y): return {"type": "moveTo", "x": x, "y": y}
def Lt(x, y): return {"type": "lineTo", "x": x, "y": y}
def C(c1x, c1y, c2x, c2y, x, y): return {"type": "cubicTo", "c1x": c1x, "c1y": c1y, "c2x": c2x, "c2y": c2y, "x": x, "y": y}
def Z(): return {"type": "close"}


def ellipse(cx, cy, rx, ry=None):
    ry = rx if ry is None else ry
    kx, ky = rx * K, ry * K
    return [M(cx, cy - ry), C(cx + kx, cy - ry, cx + rx, cy - ky, cx + rx, cy),
            C(cx + rx, cy + ky, cx + kx, cy + ry, cx, cy + ry),
            C(cx - kx, cy + ry, cx - rx, cy + ky, cx - rx, cy),
            C(cx - rx, cy - ky, cx - kx, cy - ry, cx, cy - ry), Z()]


def poly(pts, close=True):
    return [M(*pts[0])] + [Lt(*p) for p in pts[1:]] + ([Z()] if close else [])


# ------------------------------------------------------------------ timing (ms)
# Two kinetic beats per loop; each beat fires a logo pulse + shockwave.
BEAT_A, BEAT_B = 150, 5150          # text A / text B begin to emerge from the logo
IN_D = 900                          # per-character emergence sweep
A_OUT, B_OUT = 4300, 9300           # exits start
OUT_D = 650


def pulse_js(base, amp, beat_amp, period=2.5, decay=4.0):
    """Breathing sine (period divides the loop) plus an exponential spike at each beat."""
    return (f"var t=input.time.seconds;"
            f"function sp(t0){{var d=t-t0;if(d<0)d+= {LOOP_S};return Math.exp(-d*{decay});}}"
            f"var s=sp({BEAT_A/1000})+sp({BEAT_B/1000});"
            f"return {base}+{amp}*Math.sin(t*2*Math.PI/{period})+{beat_amp}*s;")


root = []  # back -> front

# =================================================================== BACKGROUND
root.append(rect("BG preto", CX, CY, W, H, BLACK))
# central electric-blue bloom, flattened into an ellipse for the 8:1 frame
bloom = radial("BG brilho central", CX, CY, 1500,
               [(0, a(BLUE, 0.30)), (0.25, a(BLUE, 0.13)), (0.6, a(BLUE_D, 0.05)), (1, a(BLUE_D, 0))], sy=34)
root.append(bloom)
js(bloom["id"], "opacity", pulse_js(80, 12, 25))

# angled light beams echoing the star's angles (slow drift, period = loop)
random.seed(7)
for i, (bx, bw, al, rot) in enumerate([(520, 220, 0.07, 28), (930, 120, 0.05, 28), (2950, 160, 0.06, -28),
                                         (3380, 260, 0.07, -28), (1250, 70, 0.04, 28), (2620, 70, 0.04, -28)]):
    beam = rect(f"BG feixe {i + 1}", bx, CY, bw, 1100, r=rot,
                paint=grad(0, 550, bw, 550, [(0, a(BLUE, 0)), (0.5, a(BLUE, al)), (1, a(BLUE, 0))]))
    root.append(beam)
    sgn = 1 if rot > 0 else -1
    js(beam["id"], "positionX", f"return {bx}+{sgn}*60*Math.sin(input.time.seconds*2*Math.PI/{LOOP_S}+{i});")
    js(beam["id"], "opacity", f"return 70+30*Math.sin(input.time.seconds*2*Math.PI/{LOOP_S / 2}+{i * 1.3});")

# fine perspective grid floor (very faint), scrolling toward the viewer, loop-safe
gcmds = []
for k in range(-40, 41):
    x0 = CX + k * 120
    gcmds += [M(CX + k * 22, 300), Lt(x0 * 1.0 + (x0 - CX) * 1.6, 560)]
grid_v = shape("BG grade perspectiva", gcmds, strokes=[strokest(BLUE, 1.2, o=0.10)])
root.append(grid_v)
hl = []
for j in range(6):
    hl.append(rect(f"BG grade linha {j + 1}", CX, 300, W, 1.5,
                   paint=grad(0, 0, W, 0, [(0, a(BLUE, 0)), (0.5, a(BLUE, 0.22)), (1, a(BLUE, 0))])))
for j, L in enumerate(hl):
    # each line rides an ease-in curve from the horizon (y=300) to below frame; phase-staggered, period 5 s
    js(L["id"], "positionY", f"var p=((input.time.seconds/5)+{j}/6)%1;return 300+p*p*260;")
    js(L["id"], "opacity", f"var p=((input.time.seconds/5)+{j}/6)%1;return Math.min(1,p*4)*100*(1-p*0.4);")
root += hl
# horizon fade so the grid dissolves into black near the logo
root.append(rect("BG horizonte fade", CX, 300, W, 120,
                 paint=grad(0, 0, 0, 120, [(0, a(BLACK, 1)), (1, a(BLACK, 0))]), anchor="center"))

# particles: three depth layers drifting upward; speed*10 s is a multiple of H -> seamless
random.seed(11)
for li, (n, rmin, rmax, speed, op) in enumerate([(70, 1.2, 2.2, 48, 45), (40, 2.0, 3.4, 96, 60), (16, 3.2, 5.0, 144, 70)]):
    pc = []
    for _ in range(n):
        x, y, r = random.uniform(10, W - 10), random.uniform(0, H), random.uniform(rmin, rmax)
        pc += ellipse(x, y, r) + ellipse(x, y + H, r)
    ge, gfx = glow(0.1, 6 + li * 4, 1.2)
    p = shape(f"BG partículas {li + 1}", pc, fills=[fillst(BLUE_L)], tr=T(0, 0, o=op), effects=gfx)
    root.append(p)
    js(p["id"], "positionY", f"return -((input.time.seconds*{speed})%{H});")
    js(p["id"], "positionX", f"return 14*Math.sin(input.time.seconds*2*Math.PI/{LOOP_S}+{li * 2});")
    js(p["id"], "opacity", f"return {op}*(0.7+0.3*Math.sin(input.time.seconds*2*Math.PI/{LOOP_S / (li + 2)}+{li}));")

# =================================================================== RAILS (geometric glow lines)
for yy in (54, 426):
    rail = rect(f"Trilho y{yy}", CX, yy, W * 0.92, 2,
                paint=grad(0, 0, W * 0.92, 0, [(0, a(BLUE, 0)), (0.32, a(BLUE, 0.35)), (0.5, a(BLUE_L, 0.0)),
                                              (0.68, a(BLUE, 0.35)), (1, a(BLUE, 0))]))
    root.append(rail)
# light pulses travelling outward from the logo along the rails (period 2.5 s)
for yy in (54, 426):
    for side in (-1, 1):
        ge, gfx = glow(0.05, 14, 1.6)
        pl = rect(f"Pulso trilho y{yy} {'esq' if side < 0 else 'dir'}", CX, yy, 220, 3,
                  paint=grad(0, 0, 220, 0, [(0, a(BLUE_L, 0)), (0.5, a(ICE, 1)), (1, a(BLUE_L, 0))]), effects=gfx)
        root.append(pl)
        ph = 0 if yy == 54 else 1.25
        js(pl["id"], "positionX", f"var p=((input.time.seconds+{ph})/2.5)%1;return {CX}+{side}*(420+p*1500);")
        js(pl["id"], "opacity", f"var p=((input.time.seconds+{ph})/2.5)%1;return 100*Math.sin(p*Math.PI);")

# =================================================================== LOGO CORE
LOGO_W, LOGO_H = 2000, 996
LS = 30  # % -> 600 x 299
LX, LY = CX, CY + 6

# geometric frame: wide hexagon badge around the logo, with light running along its edge
HEX = [(-390, 0), (-300, -172), (300, -172), (390, 0), (300, 172), (-300, 172)]
geo = []
outer = shape("Hexágono externo", poly([(x * 1.18, y * 1.18) for x, y in HEX]),
              strokes=[strokest(BLUE, 1.4, o=0.22)], tr=T(LX, LY), effects=glow(0.05, 12, 1.0)[1])
inner = shape("Hexágono", poly(HEX), strokes=[strokest(BLUE, 2.2, o=0.5)], tr=T(LX, LY), effects=glow(0.05, 18, 1.3)[1])
js(inner["id"], "opacity", pulse_js(80, 10, 20))
geo += [outer, inner]
for i in range(2):
    run = shape(f"Hexágono luz {i + 1}", poly(HEX), strokes=[strokest(ICE, 3.2)], tr=T(LX, LY),
                effects=glow(0.05, 16, 2.0)[1])
    run["shape"]["trim"] = {"start": 0, "end": 14, "offset": 0, "mode": "simultaneously"}
    js(run["id"], "trimOffset", f"return ((input.time.seconds/5)*360+{i * 180})%360;")
    geo.append(run)
root += geo

# shockwave rings fired at each beat
for bi, beat in enumerate((BEAT_A, BEAT_B)):
    ring = shape(f"Onda de choque {bi + 1}", poly([(x / 2, y / 2) for x, y in HEX]), strokes=[strokest(BLUE_L, 3)],
                 tr=T(LX, LY, o=0), effects=glow(0.05, 20, 1.6)[1])
    kf(ring["id"], "scaleX", [(beat, 100, "lin"), (beat + 1100, 330, "out")])
    kf(ring["id"], "opacity", [(beat, 0, "lin"), (beat + 60, 90, "lin"), (beat + 1100, 0, "out")])
    kf(ring["id"], "scaleY", [(beat, 100, "lin"), (beat + 1100, 230, "out")])
    root.append(ring)

# neon halo: the logo tinted electric blue and blurred, pulsing behind the crisp logo
be, bfx = blur(36)
halo = {"type": "Image", "id": nid(), "name": "Logo halo neon", "blendMode": "screen", "activeRange": ALL,
        "transform": T(LX, LY, LOGO_W / 2, LOGO_H / 2, s=LS * 1.02),
        "source": {"assetId": "bcg-logo", "fit": "contain"},
        "effects": [{"id": neff(), "effect": {"type": "tintTritone", "amount": 1,
                                                "blackR": BLUE[0], "blackG": BLUE[1], "blackB": BLUE[2],
                                                "whiteR": 0.45, "whiteG": 0.65, "whiteB": 1.0}}, bfx]}
root.append(halo)
js(halo["id"], "opacity", pulse_js(62, 22, 40))
js_effect(be, "blurriness", pulse_js(34, 6, 14))

logo = {"type": "Image", "id": nid(), "name": "Logo BCG", "blendMode": "normal", "activeRange": ALL,
        "transform": T(LX, LY, LOGO_W / 2, LOGO_H / 2, s=LS),
        "source": {"assetId": "bcg-logo", "fit": "contain"},
        "layerStyles": [{"id": neff(), "style": {"type": "outerGlow", "enabled": True, "color": a(BLUE, 0.7),
                                                  "size": 40, "spread": 0, "range": 50, "blendMode": "screen"}}]}
root.append(logo)
# subtle "breath" scale on the logo itself, peaking with each beat
js(logo["id"], "scaleX", pulse_js(LS, 0.25, 1.4))
js(logo["id"], "scaleY", pulse_js(LS, 0.25, 1.4))

# =================================================================== KINETIC HEADLINE (left of logo)
TXT_R = 1470          # right edge, docked to the logo
TXT_W = 1300


def headline(name, txt, beat, out_t, sel_ids):
    """Right-justified bold line that streams out of the logo char by char, then lifts away."""
    lid = nid()
    in_sel, out_sel, in_anim, out_anim = sel_ids
    L = {"type": "Text", "id": lid, "name": name, "blendMode": "normal", "activeRange": ALL,
         "transform": T(TXT_R, CY + 4, TXT_W, 70),
         "sourceText": {"text": txt, "fontFamily": XB[0], "fontStyle": XB[1], "fontSize": 108,
                        "fillColor": WHITE, "strokeWidth": 0, "justification": "right", "boxText": True,
                        "boxPosition": [0, 0], "boxSize": [TXT_W, 140], "verticalAlign": "center", "tracking": -10},
         "layerStyles": [{"id": neff(), "style": {"type": "gradientOverlay", "enabled": True, "opacity": 1,
                                                   "gradientType": "linear", "start": [0, 20], "end": [0, 120],
                                                   "blendMode": "normal",
                                                   "stops": [{"offset": 0, "color": WHITE},
                                                             {"offset": 1, "color": [0.74, 0.83, 1.0, 1]}]}},
                         {"id": neff(), "style": {"type": "outerGlow", "enabled": True, "color": a(BLUE, 0.55),
                                                   "size": 26, "spread": 0, "range": 50, "blendMode": "screen"}}],
         "animators": [
             {"id": in_anim, "name": "Entrada", "opacity": 0, "position": [90, 0], "blur": [18, 4],
              "scale": [100, 100],
              "selectors": [{"id": in_sel, "start": 0, "end": 1, "offset": 0, "units": "percentage",
                             "basedOn": "characters", "mode": "add", "amount": 1, "shape": "square"}]},
             {"id": out_anim, "name": "Saída", "opacity": 0, "position": [0, -70], "blur": [2, 16],
              "selectors": [{"id": out_sel, "start": 0, "end": 1, "offset": -1, "units": "percentage",
                             "basedOn": "characters", "mode": "add", "amount": 1, "shape": "square"}]},
         ]}
    # entry: the selected (hidden) range slides off the left, releasing chars from the right (logo side)
    kf_item(in_sel, "offset", [(beat, 0, "lin"), (beat + IN_D, -1.0, "out")])
    # exit: hidden range sweeps in from the left -> chars lift away left to right, last near the logo
    kf_item(out_sel, "offset", [(out_t, -1.0, "lin"), (out_t + OUT_D, 0.0, "in")])
    return L


tA = headline("Texto A · Brasil Cidade Grande", "Brasil Cidade Grande", BEAT_A, A_OUT, (9501, 9502, 9503, 9504))
tB = headline("Texto B · Venha jogar conosco", "Venha jogar conosco", BEAT_B, B_OUT, (9511, 9512, 9513, 9514))
# B is hidden during A's slot: hold its entry selector fully on until its beat
root += [tA, tB]

# accent underline that wipes out of the logo with each text and retracts on exit
for bi, (beat, out_t) in enumerate(((BEAT_A, A_OUT), (BEAT_B, B_OUT))):
    ge, gfx = glow(0.05, 14, 1.4)
    ul = rect(f"Sublinhado {bi + 1}", TXT_R, CY + 92, 360, 4, anchor="right", effects=gfx,
              paint=grad(0, 0, 360, 0, [(0, a(BLUE, 0)), (0.6, a(BLUE, 1)), (1, a(ICE, 1))]))
    kf(ul["id"], "scaleX", [(beat + 250, 0, "lin"), (beat + 950, 100, "out"), (out_t, 100, "lin"), (out_t + 500, 0, "in")])
    root.append(ul)

# =================================================================== DISCORD TAG (right of logo, docked)
PX0 = 2380           # pill left edge
PW, PH = 900, 176
PCY = CY + 4
pill_bg = rect("Discord pill fundo", PX0 + PW / 2, PCY, PW, PH, fill=[0.03, 0.06, 0.16, 1], rnd=PH / 2,
               paint=grad(0, 0, PW, 0, [(0, [0.05, 0.10, 0.26, 0.85]), (1, [0.02, 0.04, 0.10, 0.55])]))
ge, gfx = glow(0.05, 22, 1.2)
pill_line = rect("Discord pill contorno", PX0 + PW / 2, PCY, PW, PH, rnd=PH / 2, stroke=BLUE, sw=2.5, effects=gfx)
js_effect(ge, "glowIntensity", pulse_js(1.1, 0.3, 0.8))
# glowing status dot + label
dot = shape("Discord ponto", ellipse(0, 0, 9), fills=[fillst(BLUE_L)], tr=T(PX0 + 92, PCY - 38),
            effects=glow(0.05, 16, 2.0)[1])
js(dot["id"], "opacity", "return 65+35*Math.sin(input.time.seconds*2*Math.PI/1.25);")
lab = {"type": "Text", "id": nid(), "name": "Discord rótulo", "blendMode": "normal", "activeRange": ALL,
       "transform": T(PX0 + 118, PCY - 38, 0, 22),
       "sourceText": {"text": "DISCORD", "fontFamily": SB[0], "fontStyle": SB[1], "fontSize": 30,
                      "fillColor": BLUE_L, "strokeWidth": 0, "justification": "left", "boxText": True,
                      "boxPosition": [0, 0], "boxSize": [400, 44], "verticalAlign": "center", "tracking": 420}}
url = {"type": "Text", "id": nid(), "name": "Discord link", "blendMode": "normal", "activeRange": ALL,
       "transform": T(PX0 + 76, PCY + 24, 0, 45),
       "sourceText": {"text": "discord.gg/bcgrp", "fontFamily": SB[0], "fontStyle": SB[1], "fontSize": 74,
                      "fillColor": WHITE, "strokeWidth": 0, "justification": "left", "boxText": True,
                      "boxPosition": [0, 0], "boxSize": [800, 90], "verticalAlign": "center", "tracking": 0},
       "layerStyles": [{"id": neff(), "style": {"type": "outerGlow", "enabled": True, "color": a(BLUE, 0.6),
                                                 "size": 20, "spread": 0, "range": 50, "blendMode": "screen"}}]}
# shimmer sweep across the pill, once per text beat (masked to the pill shape)
pill_mask = rect("Discord pill máscara", PX0 + PW / 2, PCY, PW, PH, fill=WHITE, rnd=PH / 2)
pill_mask["isHidden"] = False
shim = rect("Discord brilho varredura", PX0, PCY, 180, PH * 2, r=20, blend="screen",
            paint=grad(0, 0, 180, 0, [(0, a(ICE, 0)), (0.5, a(ICE, 0.22)), (1, a(ICE, 0))]))
shim["trackMatte"] = {"mode": "alpha", "layer": pill_mask["id"]}
kf(shim["id"], "positionX", [(0, PX0 - 200, "lin"),
                             (BEAT_A + 1100, PX0 - 200, "lin"), (BEAT_A + 2100, PX0 + PW + 200, "inout"),
                             (BEAT_B + 1100, PX0 - 200, "hold"), (BEAT_B + 2100, PX0 + PW + 200, "inout")])
discord = group("Discord tag", [pill_bg, pill_line, shim, pill_mask, dot, lab, url])
root.append(discord)

# =================================================================== VIGNETTE (edges)
root.append(rect("Vinheta esquerda", 0, CY, 700, H, anchor="left",
                 paint=grad(0, 0, 700, 0, [(0, a(BLACK, 0.95)), (1, a(BLACK, 0))])))
root.append(rect("Vinheta direita", W, CY, 700, H, anchor="right",
                 paint=grad(0, 0, 700, 0, [(0, a(BLACK, 0)), (1, a(BLACK, 0.95))])))
root.append(rect("Vinheta topo", CX, 0, W, 90, anchor="center",
                 paint=grad(0, 0, 0, 90, [(0, a(BLACK, 0.8)), (1, a(BLACK, 0))])))
root.append(rect("Vinheta base", CX, H, W, 90, anchor="center",
                 paint=grad(0, 0, 0, 90, [(0, a(BLACK, 0)), (1, a(BLACK, 0.8))])))

# =================================================================== assemble
doc = json.load(open(SRC))
doc["dimensions"] = {"width": W, "height": H}
doc["duration"] = DUR / 1000
doc["backgroundColor"] = BLACK
comp = doc["composition"]
comp["name"] = "BCG Banner 8:1 (loop 10s)"
comp["layers"] = list(reversed(root))  # front first
comp["dynamics"] = {"entries": DYN}
json.dump(doc, open(OUT, "w"), ensure_ascii=False, indent=1)
print(f"layers={len(root)} dynamics={len(DYN)} last id={_ids[0]}")
