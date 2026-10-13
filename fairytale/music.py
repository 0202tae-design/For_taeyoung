"""Procedural, copyright-free music-box background music."""
import numpy as np

SR = 24000

PROGRESSIONS = [
    [0, 7, 9, 5],   # I V vi IV
    [0, 9, 5, 7],   # I vi IV V
    [5, 0, 7, 0],   # IV I V I
    [0, 5, 9, 7],   # I IV vi V
]
MAJOR = [0, 2, 4, 5, 7, 9, 11]


def _chord(root):
    """Diatonic triad (semitones) on a scale-degree root."""
    deg = MAJOR.index(root % 12)
    return [MAJOR[(deg + k) % 7] + 12 * ((deg + k) // 7) for k in (0, 2, 4)]


def _note(freq, dur, amp):
    t = np.arange(int(dur * SR)) / SR
    env = np.exp(-t * 3.2) * np.minimum(1, t * 400)
    wave = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(2 * np.pi * freq * 4 * t) * np.exp(-t * 6)
    return (wave * env * amp).astype(np.float32)


def generate(seconds, seed=0):
    rng = np.random.default_rng(seed)
    key = int(rng.choice([0, 2, 5, 7]))  # C, D, F, G
    prog = PROGRESSIONS[seed % len(PROGRESSIONS)]
    bpm = float(rng.choice([80, 86, 92]))
    beat = 60.0 / bpm
    n = int(seconds * SR) + SR * 3
    out = np.zeros(n, dtype=np.float32)
    patterns = [[0, 1, 2, 1, 3, 1, 2, 1], [0, 2, 1, 2, 3, 2, 1, 2], [0, 1, 2, 3, 2, 1, 2, 1]]
    pat = patterns[seed % len(patterns)]
    bar = 0
    pos = 0.0
    while pos < seconds:
        chord = _chord(prog[bar % 4])
        tones = chord + [chord[0] + 12]
        base = 60 + key  # middle C region
        for i, k in enumerate(pat):
            st = int((pos + i * beat / 2) * SR)
            f = 440 * 2 ** ((base + tones[k] - 69) / 12)
            note = _note(f, 1.6, 0.18)
            out[st:st + len(note)] += note[: max(0, n - st)]
        # soft bass on each bar
        st = int(pos * SR)
        f = 440 * 2 ** ((base - 12 + chord[0] - 69) / 12)
        t = np.arange(int(beat * 4 * SR)) / SR
        bass = (np.sin(2 * np.pi * f * t) * np.exp(-t * 0.9) * np.minimum(1, t * 50) * 0.16).astype(np.float32)
        out[st:st + len(bass)] += bass[: max(0, n - st)]
        pos += beat * 4
        bar += 1
    out = out[: int(seconds * SR)]
    fade = min(len(out) // 4, 2 * SR)
    if fade:
        out[:fade] *= np.linspace(0, 1, fade)
        out[-fade:] *= np.linspace(1, 0, fade)
    peak = np.max(np.abs(out)) or 1.0
    return out / peak
