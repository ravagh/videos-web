"""Procedural soundtrack + custom UI SFX for Meridian-Agro (numpy, local only).

Music: modern corporate track, 120 BPM, A minor / C major (Am-F-C-G), with
transition swells/crashes placed on the narration block changes.
"""
import sys, wave
import numpy as np

SR = 48000
OUT = sys.argv[1]
DUR = 30.4
BLOCKS = [6.2, 13.95, 21.25, 26.2]  # block changes (s) — swells land here
BREAK = (25.95, 26.2)               # short density drop before the CTA
rng = np.random.default_rng(7)
N = int(DUR * SR)
t_all = np.arange(N) / SR


def write(path, x, stereo=True):
    x = np.asarray(x)
    if x.ndim == 1:
        x = np.stack([x, x], 1) if stereo else x[:, None]
    pcm = (np.clip(x, -1, 1) * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(pcm.shape[1]); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x); s = 0.0
    for i, v in enumerate(x):
        s = (1 - a) * v + a * s; y[i] = s
    return y


def lp_fast(x, fc, passes=2):
    # IIR one-pole via cumulative trick is not exact; use FFT brickwall-ish soft LP instead
    X = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(x.shape[0], 1 / SR)
    H = 1 / np.sqrt(1 + (f / fc) ** (2 * passes))
    return np.fft.irfft(X * (H if X.ndim == 1 else H[:, None]), n=x.shape[0], axis=0)


def hp_fast(x, fc, order=2):
    X = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(x.shape[0], 1 / SR)
    H = 1 / np.sqrt(1 + (fc / np.maximum(f, 1e-3)) ** (2 * order))
    return np.fft.irfft(X * (H if X.ndim == 1 else H[:, None]), n=x.shape[0], axis=0)


def add(buf, sig, start, gain=1.0, pan=0.0):
    i = int(start * SR)
    if i >= len(buf):
        return
    sig = sig[: len(buf) - i]
    l = np.cos((pan + 1) * np.pi / 4); r = np.sin((pan + 1) * np.pi / 4)
    buf[i:i + len(sig), 0] += sig * gain * l * 1.414
    buf[i:i + len(sig), 1] += sig * gain * r * 1.414


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


# ---------------------------------------------------------------- instruments
def kick():
    d = 0.32; t = np.arange(int(d * SR)) / SR
    f = 45 + 85 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 9)
    click = rng.standard_normal(len(t)) * np.exp(-t * 400) * 0.25
    return (body + click) * 0.9


def clap():
    d = 0.25; t = np.arange(int(d * SR)) / SR
    n = rng.standard_normal(len(t))
    n = hp_fast(n, 900) ; n = lp_fast(n, 6000)
    env = np.exp(-t * 22) + 0.6 * np.exp(-((t - 0.012) ** 2) / 2e-5)
    return n * env * 0.5


def hat(open_=False):
    d = 0.18 if open_ else 0.05; t = np.arange(int(d * SR)) / SR
    n = hp_fast(rng.standard_normal(len(t)), 7000)
    return n * np.exp(-t * (18 if open_ else 90)) * 0.35


def pluck(f, d=0.32):
    t = np.arange(int(d * SR)) / SR
    s = (np.sin(2 * np.pi * f * t) + 0.45 * np.sin(4 * np.pi * f * t) + 0.18 * np.sin(6 * np.pi * f * t))
    return s * np.exp(-t * 11) * (1 - np.exp(-t * 900))


def bass(f, d):
    t = np.arange(int(d * SR)) / SR
    saw = 2 * ((f * t) % 1) - 1
    s = 0.6 * np.sin(2 * np.pi * f * t) + 0.25 * saw
    env = (1 - np.exp(-t * 300)) * np.exp(-t * 4.5)
    return s * env


def pad(freqs, d):
    t = np.arange(int(d * SR)) / SR
    s = np.zeros(len(t))
    for f in freqs:
        for det in (-0.12, 0.0, 0.12):
            ff = f * 2 ** (det / 12)
            s += 2 * ((ff * t + rng.random()) % 1) - 1
    s /= (len(freqs) * 3)
    att = np.minimum(1, t / 0.35); rel = np.minimum(1, (d - t) / 0.4)
    return s * att * rel


def crash(d=2.2):
    t = np.arange(int(d * SR)) / SR
    n = hp_fast(rng.standard_normal(len(t)), 4500)
    return n * np.exp(-t * 2.2) * 0.35


def riser(d=1.2):
    t = np.arange(int(d * SR)) / SR
    n = rng.standard_normal(len(t))
    n = hp_fast(n, 1500)
    env = (t / d) ** 2.2
    sweep = np.sin(2 * np.pi * np.cumsum(300 + 1500 * (t / d) ** 2) / SR) * 0.15
    out = (n * 0.5 + sweep) * env
    out[-int(0.01 * SR):] *= np.linspace(1, 0, int(0.01 * SR))
    return out


def impact():
    d = 1.4; t = np.arange(int(d * SR)) / SR
    f = 38 + 60 * np.exp(-t * 12)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2)
    s += 0.3 * np.sin(2 * np.pi * np.cumsum(2 * f) / SR) * np.exp(-t * 6)
    return s * 0.8


# ---------------------------------------------------------------- arrangement
BPM = 120; beat = 60 / BPM; bar = 4 * beat
prog = [  # (root midi for bass, chord tones for pluck/pad)
    (45, [57, 60, 64, 69]),   # Am
    (41, [53, 57, 60, 65]),   # F
    (48, [55, 60, 64, 67]),   # C
    (43, [55, 59, 62, 67]),   # G
]
mix = np.zeros((N, 2))
drums = np.zeros((N, 2)); music = np.zeros((N, 2)); fx = np.zeros((N, 2))
K, C = kick(), clap()
HC, HO = hat(), hat(True)


def in_break(t0):
    return BREAK[0] <= t0 < BREAK[1]


nbars = int(np.ceil(DUR / bar))
for b in range(nbars):
    t0 = b * bar
    root, chord = prog[b % 4]
    # pad (whole bar)
    add(music, pad([midi(n) for n in chord[:3]], bar + 0.2), t0, 0.16)
    for s in range(16):  # 16th grid
        ts = t0 + s * beat / 4
        if ts >= DUR - 0.4 or in_break(ts):
            continue
        intro = ts < 0.0
        # kick: four on the floor
        if s % 4 == 0:
            add(drums, K, ts, 0.85)
        if s % 8 == 4:
            add(drums, C, ts, 0.55, 0.0)
        if s % 4 == 2:
            add(drums, HO if s == 14 else HC, ts, 0.5, 0.25)
        elif s % 2 == 1:
            add(drums, HC, ts, 0.22, -0.25)
        # bass: 8th-note pulse
        if s % 2 == 0:
            add(music, bass(midi(root - 12 + (12 if s in (6, 14) else 0)), beat / 2 * 0.95), ts, 0.55)
        # pluck arpeggio (16ths), bright but quiet
        note = chord[[0, 2, 1, 3, 2, 1, 3, 2][s % 8]] + 12
        add(music, pluck(midi(note)), ts, 0.14, 0.35 if s % 2 else -0.35)

# transitions: riser into each block change, crash + impact on arrival
for tb in BLOCKS:
    r = riser(1.1)
    add(fx, r, tb - 1.1, 0.35)
    add(fx, crash(), tb, 0.45)
    add(fx, impact(), tb, 0.35)
add(fx, crash(), 0.0, 0.35)
add(fx, impact(), 0.0, 0.4)

# final chord ring-out
for n in [57, 60, 64, 69, 72]:
    add(music, pluck(midi(n), 1.6) * 0.8, DUR - 1.5, 0.18)
add(fx, crash(1.4), DUR - 1.5, 0.25)

drums = lp_fast(drums, 11000)
music = lp_fast(music, 9000)
# gentle presence dip in the music bed (narration lives at 1-4 kHz)
mix = drums * 0.9 + music + fx
f_dip = hp_fast(lp_fast(mix, 3500), 1200)
mix = mix - 0.35 * f_dip
# fade tail
fade = np.ones(N); tail = int(0.6 * SR); fade[-tail:] = np.linspace(1, 0, tail) ** 2
mix *= fade[:, None]
peak = np.max(np.abs(mix)); mix = mix / peak * 0.5  # −6 dBFS peak; level set in Tesseract
write(OUT + '/music-corporate-v1.wav', mix)


# ---------------------------------------------------------------- custom SFX
def sfx_counter(d, n, f0=1100, f1=2100):
    out = np.zeros(int(d * SR))
    for i in range(n):
        ts = i * d / n
        f = f0 + (f1 - f0) * (i / max(1, n - 1))
        L = int(0.045 * SR); t = np.arange(L) / SR
        blip = np.sin(2 * np.pi * f * t) * np.exp(-t * 70) * (1 - np.exp(-t * 3000))
        j = int(ts * SR); out[j:j + L] += blip[: len(out) - j]
    return out / np.max(np.abs(out)) * 0.5


def sfx_lock():
    d = 0.45; t = np.arange(int(d * SR)) / SR
    thump = np.sin(2 * np.pi * np.cumsum(90 + 140 * np.exp(-t * 60)) / SR) * np.exp(-t * 28)
    c1 = hp_fast(rng.standard_normal(len(t)), 2500) * np.exp(-t * 500)
    t2 = np.clip(t - 0.085, 0, None)
    c2 = hp_fast(rng.standard_normal(len(t)), 3000) * np.exp(-t2 * 650) * (t >= 0.085)
    ring = np.sin(2 * np.pi * 2350 * t2) * np.exp(-t2 * 35) * (t >= 0.085) * 0.25
    s = thump * 0.8 + c1 * 0.5 + c2 * 0.6 + ring
    return s / np.max(np.abs(s)) * 0.5


def sfx_data(d=2.0):
    out = np.zeros(int(d * SR))
    times = np.sort(rng.uniform(0, d - 0.1, 26))
    for ts in times:
        f = rng.choice([880, 1320, 1760, 2093, 2637])
        L = int(rng.uniform(0.02, 0.05) * SR); t = np.arange(L) / SR
        b = np.sign(np.sin(2 * np.pi * f * t)) * 0.35 + np.sin(2 * np.pi * f * t)
        b *= np.exp(-t * 60)
        j = int(ts * SR); out[j:j + L] += b[: len(out) - j] * rng.uniform(0.4, 1)
    t = np.arange(len(out)) / SR
    sweep = np.sin(2 * np.pi * np.cumsum(400 + 900 * t / d) / SR) * 0.12 * np.sin(np.pi * t / d)
    out = lp_fast(out + sweep, 7000)
    return out / np.max(np.abs(out)) * 0.5


write(OUT + '/sfx-counter-1200.wav', sfx_counter(1.2, 12))
write(OUT + '/sfx-counter-1000.wav', sfx_counter(1.0, 10, 1300, 2300))
write(OUT + '/sfx-counter-1500.wav', sfx_counter(1.5, 14, 900, 2000))
write(OUT + '/sfx-lock.wav', sfx_lock())
write(OUT + '/sfx-data-route.wav', sfx_data(2.0))
print('ok')
