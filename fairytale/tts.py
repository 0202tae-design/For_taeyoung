"""Text-to-speech with a per-character voice.

Backends:
  google  Google Cloud Text-to-Speech (natural voices). Needs GOOGLE_TTS_API_KEY.
  espeak  Offline espeak-ng. Robotic, only meant for previews.
"""
import base64
import hashlib
import json
import os
import subprocess
import urllib.request

import numpy as np

SR = 24000

# semitone offsets give each character its own voice
PITCH = {
    "narrator": 0.0,
    "bunny": 3.0,
    "squirrel": 5.0,
    "duck": 6.0,
    "cat": 4.0,
    "fox": 1.0,
    "bear": -5.0,
}

GOOGLE_VOICES = {
    "ko": os.environ.get("TTS_VOICE_KO", "ko-KR-Neural2-A"),
    "en": os.environ.get("TTS_VOICE_EN", "en-US-Neural2-F"),
}
LANG_CODES = {"ko": "ko-KR", "en": "en-US"}


def backend_name():
    forced = os.environ.get("TTS_BACKEND")
    if forced:
        return forced
    return "google" if os.environ.get("GOOGLE_TTS_API_KEY") else "espeak"


def _decode(path_or_bytes):
    """Decode any audio to mono float32 at SR using ffmpeg."""
    if isinstance(path_or_bytes, bytes):
        args = ["ffmpeg", "-loglevel", "error", "-i", "pipe:0"]
        inp = path_or_bytes
    else:
        args = ["ffmpeg", "-loglevel", "error", "-i", path_or_bytes]
        inp = None
    args += ["-f", "s16le", "-ac", "1", "-ar", str(SR), "pipe:1"]
    out = subprocess.run(args, input=inp, capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.int16).astype(np.float32) / 32768.0


def _google(text, lang, who):
    key = os.environ["GOOGLE_TTS_API_KEY"]
    body = {
        "input": {"text": text},
        "voice": {"languageCode": LANG_CODES[lang], "name": GOOGLE_VOICES[lang]},
        "audioConfig": {
            "audioEncoding": "LINEAR16",
            "sampleRateHertz": SR,
            "speakingRate": 0.9 if who == "narrator" else 0.95,
            "pitch": PITCH.get(who, 0.0),
        },
    }
    req = urllib.request.Request(
        "https://texttospeech.googleapis.com/v1/text:synthesize?key=" + key,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        audio = base64.b64decode(json.load(r)["audioContent"])
    return _decode(audio)


def _espeak(text, lang, who, tmp):
    voice = {"ko": "ko+f3", "en": "en-us+f3"}[lang]
    pitch = int(max(0, min(99, 50 + PITCH.get(who, 0) * 6)))
    speed = "150" if lang == "ko" else "140"
    subprocess.run(["espeak-ng", "-v", voice, "-p", str(pitch), "-s", speed, "-w", tmp, text], check=True)
    return _decode(tmp)


def synth(text, lang, who, cache_dir):
    backend = backend_name()
    os.makedirs(cache_dir, exist_ok=True)
    h = hashlib.sha1(f"{backend}|{lang}|{who}|{GOOGLE_VOICES.get(lang)}|{text}".encode()).hexdigest()[:16]
    cached = os.path.join(cache_dir, h + ".npy")
    if os.path.exists(cached):
        return np.load(cached)
    if backend == "google":
        audio = _google(text, lang, who)
    else:
        audio = _espeak(text, lang, who, os.path.join(cache_dir, h + ".wav"))
    # trim leading/trailing near-silence
    idx = np.where(np.abs(audio) > 0.01)[0]
    if len(idx):
        audio = audio[max(0, idx[0] - 600): idx[-1] + 2400]
    np.save(cached, audio)
    return audio
