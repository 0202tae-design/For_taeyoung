"""Render a story JSON into a narrated, subtitled MP4 (plus thumbnail and metadata).

Usage:
  python3 render.py stories/001_toto_rainbow_umbrella.json --lang ko --out out/
  python3 render.py STORY --lang en --out out/ --res 1280x720 --preview 20
"""
import argparse
import json
import math
import os
import subprocess
import wave

import cairo
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import characters as chars
import music
import scenery
import tts
from draw import hexc, rounded_rect, smooth, lerp, rand

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "assets", "fonts", "Jua-Regular.ttf")
LW, LH = 1280, 720
FPS = 24
SR = tts.SR

PAD_START, GAP, PAD_END = 0.7, 0.55, 1.0
FADE = 0.4


# ---------------------------------------------------------------- text
class TextCache:
    def __init__(self, scale):
        self.scale = scale
        self.cache = {}

    def get(self, text, size, color="#3b2b24", stroke=0, stroke_color="#ffffff", max_width=None):
        key = (text, size, color, stroke, stroke_color, max_width)
        if key in self.cache:
            return self.cache[key]
        s = self.scale
        font = ImageFont.truetype(FONT, int(size * s))
        lines = wrap(text, font, max_width * s) if max_width else text.split("\n")
        sw = int(stroke * s)
        line_h = int(size * s * 1.25)
        widths = [font.getlength(ln) for ln in lines]
        w = int(max(widths) + sw * 2 + 8)
        h = int(line_h * len(lines) + sw * 2 + 8)
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        for i, ln in enumerate(lines):
            x = (w - widths[i]) / 2
            d.text((x, sw + 4 + i * line_h), ln, font=font, fill=color, stroke_width=sw, stroke_fill=stroke_color)
        arr = np.asarray(img).astype(np.float32)
        a = arr[..., 3:4] / 255.0
        bgra = np.concatenate([arr[..., 2:3] * a, arr[..., 1:2] * a, arr[..., 0:1] * a, arr[..., 3:4]], axis=2)
        data = bytearray(np.ascontiguousarray(bgra.astype(np.uint8)).tobytes())
        surf = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, w, h, w * 4)
        self.cache[key] = (surf, w / s, h / s, data)
        return self.cache[key]


def wrap(text, font, max_w):
    out = []
    for para in text.split("\n"):
        words = para.split(" ")
        cur = ""
        for word in words:
            trial = (cur + " " + word).strip()
            if font.getlength(trial) <= max_w or not cur:
                cur = trial
            else:
                out.append(cur)
                cur = word
        out.append(cur)
    return out


def paint_text(ctx, tc, text, cx, cy, size, alpha=1.0, scale=1.0, **kw):
    surf, w, h, _ = tc.get(text, size, **kw)
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(scale / tc.scale, scale / tc.scale)
    ctx.set_source_surface(surf, -w * tc.scale / 2, -h * tc.scale / 2)
    ctx.paint_with_alpha(alpha)
    ctx.restore()
    return w * scale, h * scale


# ---------------------------------------------------------------- timeline
def build_timeline(story, lang, cache_dir):
    scenes = []
    clips = []
    t = 0.0
    for si, sc in enumerate(story["scenes"]):
        start = t
        cur = start + PAD_START
        lines = []
        for li, line in enumerate(sc.get("lines", [])):
            text = line[lang]
            who = line.get("who", "narrator")
            voice = sc_actor_char(sc, who)
            audio = tts.synth(text, lang, voice, cache_dir)
            dur = len(audio) / SR
            lines.append({"start": cur, "end": cur + dur, "who": who, "text": text, "mood": line.get("mood")})
            clips.append((cur, audio))
            cur += dur + GAP
        end = max(cur - GAP + PAD_END, start + sc.get("min_duration", 3.0))
        scenes.append({"index": si, "data": sc, "start": start, "end": end, "lines": lines})
        t = end
    return scenes, clips, t


def sc_actor_char(sc, who):
    for a in sc.get("actors", []):
        if a.get("id", a["char"]) == who:
            return a["char"]
    return "narrator" if who == "narrator" else who


def mix_audio(clips, total, seed):
    n = int(total * SR) + SR
    voice = np.zeros(n, dtype=np.float32)
    for start, audio in clips:
        st = int(start * SR)
        voice[st:st + len(audio)] += audio[: n - st]
    peak = np.max(np.abs(voice)) or 1.0
    voice *= 0.9 / peak
    bgm = music.generate(n / SR, seed=seed)[:n]
    bgm = np.pad(bgm, (0, n - len(bgm)))
    # duck music under narration
    env = (np.abs(voice) > 0.02).astype(np.float32)
    k = int(0.35 * SR)
    env = np.convolve(env, np.ones(k) / k, mode="same")
    gain = 0.17 - 0.09 * np.clip(env * 3, 0, 1)
    out = voice + bgm * gain
    out = np.clip(out, -1, 1)
    return out


def write_wav(path, audio):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((audio * 32767).astype(np.int16).tobytes())


# ---------------------------------------------------------------- actors
def actor_state(a, t, p, talking, line_mood, seed):
    x = a.get("x", 640)
    move = a.get("move", [0.0, 1.0])
    moving = False
    if isinstance(x, list):
        k = smooth((p - move[0]) / max(move[1] - move[0], 1e-3))
        moving = 0 < k < 1
        x0, x1 = x
        xx = lerp(x0, x1, k)
        face = a.get("face", 1 if x1 >= x0 else -1)
    else:
        xx = x
        face = a.get("face", 1)
    y = a.get("y", scenery.GROUND_Y + 50)
    action = a.get("action", "walk" if isinstance(x, list) else "idle")
    pose = {
        "t": t,
        "talking": talking,
        "blink": 1.0 if ((t + seed * 1.37) % 3.3) < 0.13 else 0.0,
        "arms": a.get("arms", "umbrella" if a.get("umbrella") else "down"),
        "mood": line_mood or a.get("mood", "happy"),
        "laugh": a.get("laugh", False),
    }
    lift = 0.0
    if action == "walk" and (moving or a.get("walk_always")):
        lift = abs(math.sin(t * 7 + seed)) * 8
        pose["rot"] = math.sin(t * 7 + seed) * 0.04
    elif action == "hop":
        ph = abs(math.sin(t * 4.5 + seed))
        lift = ph * 34
        pose["squash_y"] = 0.94 + 0.08 * ph
        pose["squash_x"] = 1.04 - 0.05 * ph
    elif action == "jump":
        ph = abs(math.sin(t * 5 + seed))
        lift = ph * 55
        pose["arms"] = "up"
    elif action == "shiver":
        xx += math.sin(t * 45) * 2.5
    else:
        br = math.sin(t * 2.2 + seed)
        pose["squash_y"] = 1 + 0.012 * br
        pose["squash_x"] = 1 - 0.008 * br
    if talking and action == "idle":
        lift = abs(math.sin(t * 3.5)) * 4
    return xx, y - lift, y, face, pose, lift


# ---------------------------------------------------------------- frames
def draw_frame(ctx, tc, story, scenes, lang, T, subtitles=True):
    sc = next((s for s in scenes if s["start"] <= T < s["end"]), scenes[-1])
    data = sc["data"]
    t = T - sc["start"]
    dur = sc["end"] - sc["start"]
    p = min(1.0, t / dur)

    ctx.save()
    z0, z1 = data.get("zoom", [1.0, 1.05])
    z = lerp(z0, z1, smooth(p))
    fx, fy = data.get("focus", [640, 420])
    ctx.translate(fx, fy)
    ctx.scale(z, z)
    ctx.translate(-fx, -fy)

    scenery.background(ctx, data, t, p)
    for pr in data.get("props", []):
        if pr.get("z", "back") == "back":
            scenery.prop(ctx, pr["type"], pr["x"], pr["y"], pr.get("scale", 1.0), t)

    current = next((ln for ln in sc["lines"] if ln["start"] <= T < ln["end"]), None)
    actors = []
    for i, a in enumerate(data.get("actors", [])):
        aid = a.get("id", a["char"])
        talking = current is not None and current["who"] == aid
        mood = current["mood"] if talking and current["mood"] else None
        appear = a.get("appear", 0.0)
        if p < appear:
            continue
        actors.append((a, actor_state(a, t, p, talking, mood, i + sc["index"] * 3)))
    for a, (x, y, ground, face, pose, lift) in sorted(actors, key=lambda e: e[1][2] + e[0].get("z", 0)):
        s = a.get("scale", 1.0)
        if a.get("shadow", True):
            chars.shadow(ctx, x, ground, 48 * s, lift)
        chars.draw_character(ctx, a["char"], x, y, s, face, pose, a.get("palette"), a.get("umbrella"))

    for pr in data.get("props", []):
        if pr.get("z") == "front":
            scenery.prop(ctx, pr["type"], pr["x"], pr["y"], pr.get("scale", 1.0), t)
    scenery.weather(ctx, data, t, p)
    ctx.restore()

    card = data.get("card")
    if card:
        bounce = 1 + 0.03 * math.sin(t * 2.5)
        appear = smooth(t / 0.8)
        paint_text(ctx, tc, card[lang], 640, data.get("card_y", 200), data.get("card_size", 78),
                   alpha=appear, scale=bounce * (0.7 + 0.3 * appear), color="#ff6f61", stroke=8,
                   max_width=1100)
        if data.get("card_sub"):
            paint_text(ctx, tc, data["card_sub"][lang], 640, data.get("card_y", 200) + 95, 40,
                       alpha=smooth((t - 0.6) / 0.8), color="#3b2b24", stroke=6, max_width=1100)

    if subtitles and current is not None and not data.get("hide_subtitles"):
        a = smooth((T - current["start"]) / 0.15) * smooth((current["end"] + 0.25 - T) / 0.15)
        surf, w, h, _ = tc.get(current["text"], 40, color="#ffffff", stroke=0, max_width=1040)
        bw, bh = w + 50, h + 22
        ctx.save()
        rounded_rect(ctx, 640 - bw / 2, 690 - bh, bw, bh, 22)
        ctx.set_source_rgba(0.12, 0.08, 0.2, 0.55 * a)
        ctx.fill()
        ctx.restore()
        paint_text(ctx, tc, current["text"], 640, 690 - bh / 2, 40, alpha=a, color="#ffffff", max_width=1040)

    fade_in = FADE * 2 if sc["index"] == 0 else FADE
    k = min(smooth(t / fade_in), smooth((dur - t) / FADE))
    if k < 1:
        ctx.rectangle(0, 0, LW, LH)
        ctx.set_source_rgba(0, 0, 0, 1 - k)
        ctx.fill()


def make_surface(width, height):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surf)
    ctx.scale(width / LW, height / LH)
    return surf, ctx


def render_video(story, lang, out_path, width, height, cache_dir, preview=None):
    scenes, clips, total = build_timeline(story, lang, cache_dir)
    if preview:
        total = min(total, preview)
    audio = mix_audio(clips, total, seed=story.get("seed", 1))
    wav_path = out_path + ".wav"
    write_wav(wav_path, audio[: int(total * SR)])

    surf, ctx = make_surface(width, height)
    tc = TextCache(width / LW)
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{width}x{height}", "-r", str(FPS), "-i", "pipe:0",
        "-i", wav_path,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out_path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    frames = int(total * FPS)
    for f in range(frames):
        ctx.save()
        ctx.set_source_rgb(1, 1, 1)
        ctx.paint()
        draw_frame(ctx, tc, story, scenes, lang, f / FPS)
        ctx.restore()
        surf.flush()
        proc.stdin.write(surf.get_data())
        if f % (FPS * 20) == 0:
            print(f"  [{lang}] {f / FPS:6.1f}s / {total:.1f}s", flush=True)
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg failed")
    os.remove(wav_path)
    write_srt(scenes, out_path[:-4] + ".srt")
    return scenes, total


def fmt_ts(x):
    ms = int(round(x * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(scenes, path):
    n = 0
    with open(path, "w", encoding="utf-8") as f:
        for sc in scenes:
            for ln in sc["lines"]:
                n += 1
                f.write(f"{n}\n{fmt_ts(ln['start'])} --> {fmt_ts(ln['end'] + 0.25)}\n{ln['text']}\n\n")


def render_thumbnail(story, lang, path, cache_dir):
    scenes, _, _ = build_timeline(story, lang, cache_dir)
    th = story.get("thumbnail", {})
    sc = scenes[th.get("scene", 0)]
    T = sc["start"] + th.get("t", 2.5)
    surf, ctx = make_surface(1280, 720)
    tc = TextCache(1.0)
    draw_frame(ctx, tc, story, scenes, lang, T, subtitles=False)
    # cover any card text, then add a big bold title
    title = story["title"][lang]
    paint_text(ctx, tc, title, 640, 120, 96 if lang == "ko" else 84, color="#ff6f61", stroke=12, max_width=1180)
    surf.write_to_png(path[:-4] + ".png")
    Image.open(path[:-4] + ".png").convert("RGB").save(path, quality=92)
    os.remove(path[:-4] + ".png")


def metadata(story, lang):
    title = story["title"][lang]
    moral = story.get("moral", {}).get(lang, "")
    summary = story.get("summary", {}).get(lang, "")
    if lang == "ko":
        full_title = f"{title} | 어린이 동화 애니메이션 | 3~8세"
        desc = (f"{summary}\n\n💡 오늘의 교훈: {moral}\n\n"
                "3~8세 어린이를 위한 짧은 동화 애니메이션이에요. 매주 2편, 새로운 이야기로 찾아와요!\n\n"
                "#동화 #어린이동화 #동화애니메이션 #유아 #잠자리동화")
        tags = ["동화", "어린이동화", "동화애니메이션", "유아동화", "잠자리동화", "인성동화", "키즈"]
    else:
        full_title = f"{title} | Bedtime Story for Kids | Ages 3-8"
        desc = (f"{summary}\n\n💡 Today's lesson: {moral}\n\n"
                "Short animated fairy tales for children ages 3 to 8. New stories twice a week!\n\n"
                "#bedtimestories #kidsstories #fairytales #storytime #kidsanimation")
        tags = ["bedtime stories", "kids stories", "fairy tales", "story time", "kids animation",
                "stories for toddlers", "moral stories"]
    return {
        "title": full_title[:100],
        "description": desc,
        "tags": tags + story.get("tags", {}).get(lang, []),
        "categoryId": "1",
        "defaultLanguage": lang,
        "defaultAudioLanguage": lang,
        "madeForKids": True,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("story")
    ap.add_argument("--lang", default="ko,en")
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    ap.add_argument("--res", default="1920x1080")
    ap.add_argument("--preview", type=float, help="render only the first N seconds")
    args = ap.parse_args()

    with open(args.story, encoding="utf-8") as f:
        story = json.load(f)
    width, height = map(int, args.res.split("x"))
    os.makedirs(args.out, exist_ok=True)
    cache = os.path.join(HERE, ".tts_cache")
    sid = story["id"]
    for lang in args.lang.split(","):
        base = os.path.join(args.out, f"{sid}_{lang}")
        print(f"[{lang}] TTS backend: {tts.backend_name()}")
        _, total = render_video(story, lang, base + ".mp4", width, height, cache, args.preview)
        render_thumbnail(story, lang, base + "_thumb.jpg", cache)
        meta = metadata(story, lang)
        meta.update({"video": base + ".mp4", "thumbnail": base + "_thumb.jpg", "captions": base + ".srt",
                     "duration": round(total, 1)})
        with open(base + ".json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        print(f"[{lang}] done: {base}.mp4 ({total:.1f}s)")


if __name__ == "__main__":
    main()
