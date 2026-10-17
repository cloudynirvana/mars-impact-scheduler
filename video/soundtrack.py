"""Synthesize the soundtrack (118 s, stereo) and mix the voiceover over it.

The music is all generated here: no samples, so nothing to license. The
voiceover lines are vo/line_N.wav, made by voiceover.py, and the music ducks
under them.
"""
import wave
from pathlib import Path

import numpy as np

SR, DUR = 44100, 118.0
t = np.arange(int(SR * DUR)) / SR
L, R = np.zeros_like(t), np.zeros_like(t)
rng = np.random.default_rng(11)
note = lambda m: 440 * 2 ** ((m - 69) / 12)

# One line per scene; keep in step with SCENES in src/Film.jsx.
VO_START = [1.5, 8.8, 17.8, 27.8, 43.8, 54.4, 63.4, 70.6, 89.6, 110.4]
SCENE_EDGE = [8, 17, 27, 43, 54, 63, 70, 89, 109.83]


def env(start, attack, decay):
    x = np.clip(t - start, 0, None)
    return np.where(t < start, 0, np.where(x < attack, x / max(attack, 1e-6), np.exp(-(x - attack) / decay)))


def lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same")


# A slow minor progression, two bars each: Dm - Bb - F - C, repeating.
chords = [[38, 50, 53, 57], [34, 46, 50, 53], [41, 53, 57, 60], [36, 48, 52, 55]]
for i in range(10):
    s, e = i * 12.0, i * 12.0 + 13.5
    w = np.clip((t - s) / 2.5, 0, 1) * np.clip((e - t) / 2.5, 0, 1)
    for m in chords[i % 4]:
        f = note(m)
        L += 0.055 * w * np.sin(2 * np.pi * f * t)
        R += 0.055 * w * np.sin(2 * np.pi * f * 1.005 * t + 1.1)
        L += 0.018 * w * np.sin(2 * np.pi * f * 2 * t)  # a touch of the octave

# A low pulse through the data sections, picking up where the argument does.
for b in np.arange(17.0, 89.0, 0.8):
    x = np.clip(t - b, 0, None)
    hit = 0.3 * env(b, 0.004, 0.11) * np.sin(2 * np.pi * (48 + 55 * np.exp(-x * 26)) * x)
    L += hit
    R += hit

# A whoosh into each new scene.
noise = lowpass(rng.standard_normal(len(t)), 36)
for s in SCENE_EDGE:
    w = np.exp(-((t - s + 0.35) / 0.32) ** 2)
    L += 0.45 * w * noise
    R += 0.45 * w * np.roll(noise, 500)

# The four launch windows arrive as four bright chimes.
for i, b in enumerate([19.4, 20.3, 21.2, 22.1]):
    ping = 0.17 * env(b, 0.003, 0.9) * np.sin(2 * np.pi * note(79 + 3 * i) * t)
    L += ping
    R += ping

# Mars turning: a slow rising sweep under the longitude scene.
x = np.clip(t - 55.0, 0, 7.5)
freq = 140 + 150 * np.clip(x / 7.5, 0, 1)
sweep = 0.14 * ((t > 55) & (t < 62.5)) * np.sin(2 * np.pi * np.cumsum(freq) / SR)
L += sweep
R += np.roll(sweep, 300)

# The Hellas reveal: a deep, open fifth.
w = np.clip((t - 80) / 2.5, 0, 1) * np.clip((92 - t) / 3, 0, 1)
for m in (31, 38, 50):
    L += 0.05 * w * np.sin(2 * np.pi * note(m) * t)
    R += 0.05 * w * np.sin(2 * np.pi * note(m) * 1.004 * t)

# The payload scene: a held low chord, no pulse, so the close has air.
w = np.clip((t - 90) / 4, 0, 1) * np.clip((110 - t) / 4, 0, 1)
for m in (36, 48, 55, 60):
    L += 0.045 * w * np.sin(2 * np.pi * note(m) * t)
    R += 0.045 * w * np.sin(2 * np.pi * note(m) * 1.004 * t + 0.7)

# Voiceover, with the music ducked underneath it.
vo = np.zeros_like(t)
for i, start in enumerate(VO_START, 1):
    f = Path(f"vo/line_{i}.wav")
    if not f.exists():
        continue
    with wave.open(str(f)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), "<i2") / 32768
        x = np.interp(np.arange(0, len(x), w.getframerate() / SR), np.arange(len(x)), x)
    a = int(start * SR)
    vo[a:a + len(x)] += x[:len(vo) - a]
speaking = lowpass((np.abs(vo) > 0.01).astype(float), int(0.4 * SR))
duck = 1 - 0.68 * np.clip(speaking * 3, 0, 1)
peak = max(np.abs(L).max(), np.abs(R).max())
L = L / peak * 0.6 * duck + 0.92 * vo
R = R / peak * 0.6 * duck + 0.92 * vo

fade = np.clip(t / 1.2, 0, 1) * np.clip((DUR - t) / 2.5, 0, 1)
st = np.stack([L, R], 1) * fade[:, None]
st = st / np.abs(st).max() * 0.86
Path("public").mkdir(exist_ok=True)
with wave.open("public/soundtrack.wav", "wb") as f:
    f.setnchannels(2)
    f.setsampwidth(2)
    f.setframerate(SR)
    f.writeframes((st * 32767).astype("<i2").tobytes())
