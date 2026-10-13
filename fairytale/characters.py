"""Cartoon animal characters.

Every character is drawn with its feet at the origin, facing right when
face=1. `pose` carries the per-frame animation state:
  t        seconds since the scene started
  talking  True while this character's line is being read
  blink    0..1 eyelid closure
  arms     "down" | "up" | "umbrella" | "wave"
  mood     "happy" | "sad" | "surprised"
"""
import math

from draw import TAU, OUTLINE, hexc, blob, ellipse_path, fill_stroke, rgba

WHITE = (1, 1, 1)
BLUSH = hexc("#ff9fb2", 0.55)


def _eyes(ctx, y, dx, size, pose, face):
    look = 4 * face
    for sx in (-1, 1):
        x = sx * dx + look
        closed = pose["blink"]
        if pose["mood"] == "happy" and pose.get("laugh"):
            closed = 1.0
        if closed > 0.85:
            ctx.set_line_width(3.2)
            rgba(ctx, OUTLINE)
            ctx.arc(x, y + 1, size * 0.9, math.pi * 1.1, math.pi * 1.9)
            ctx.stroke()
            continue
        ry = size * 1.25 * (1 - closed)
        if pose["mood"] == "surprised":
            ry *= 1.15
        blob(ctx, x, y, size, ry, OUTLINE, outline=False)
        blob(ctx, x + size * 0.35, y - ry * 0.4, size * 0.38, size * 0.38, WHITE, outline=False)
        if pose["mood"] == "sad":
            ctx.set_line_width(2.5)
            rgba(ctx, OUTLINE)
            ctx.move_to(x - size * 1.2, y - size * 2.1 - sx * 2)
            ctx.line_to(x + size * 1.2, y - size * 2.1 + sx * 2)
            ctx.stroke()


def _mouth(ctx, x, y, w, pose):
    rgba(ctx, OUTLINE)
    ctx.set_line_width(3)
    if pose["talking"]:
        o = 0.35 + 0.65 * abs(math.sin(pose["t"] * 14))
        blob(ctx, x, y + 4, w * 0.55, w * 0.5 * o + 1.5, hexc("#b5404f"), lw=2.5)
    elif pose["mood"] == "sad":
        ctx.arc(x, y + 10, w * 0.6, math.pi * 1.2, math.pi * 1.8)
        ctx.stroke()
    elif pose["mood"] == "surprised":
        blob(ctx, x, y + 5, w * 0.35, w * 0.45, hexc("#b5404f"), lw=2.5)
    else:
        ctx.arc(x, y - 2, w * 0.6, math.pi * 0.15, math.pi * 0.85)
        ctx.stroke()


def _arms(ctx, pose, body_y, body_rx, color, length=34, thick=11):
    t = pose["t"]
    mode = pose["arms"]
    for sx in (-1, 1):
        # angle from straight down, positive = outward
        if mode == "up":
            th = 2.5 + math.sin(t * 8 + sx) * 0.15
        elif mode == "wave" and sx == 1:
            th = 2.4 + math.sin(t * 9) * 0.4
        elif mode == "umbrella" and sx == 1:
            th = 2.75
        elif mode == "hug":
            th = 1.35
        else:
            th = 0.45 + math.sin(t * 2 + sx) * 0.05
        x0 = sx * body_rx * 0.8
        ex = x0 + sx * math.sin(th) * length
        ey = body_y + math.cos(th) * length
        ctx.set_line_cap(1)
        ctx.set_line_width(thick + 6)
        rgba(ctx, OUTLINE)
        ctx.move_to(x0, body_y)
        ctx.line_to(ex, ey)
        ctx.stroke()
        ctx.set_line_width(thick)
        rgba(ctx, color)
        ctx.move_to(x0, body_y)
        ctx.line_to(ex, ey)
        ctx.stroke()
        if sx == 1:
            pose["_hand"] = (ex, ey)


def _feet(ctx, color, spread=20, rx=20, ry=10):
    blob(ctx, -spread, -ry, rx, ry, color)
    blob(ctx, spread, -ry, rx, ry, color)


# ---------------------------------------------------------------- bunny
def bunny(ctx, pose, face, palette=None):
    p = palette or {}
    fur = hexc(p.get("fur", "#fbf7f2"))
    belly = hexc(p.get("belly", "#ffffff"))
    inner = hexc(p.get("inner", "#ffb6c8"))
    t = pose["t"]
    # cotton tail
    blob(ctx, -40 * face, -50, 16, 16, fur)
    _feet(ctx, fur)
    blob(ctx, 0, -62, 44, 54, fur)
    blob(ctx, 4 * face, -55, 27, 34, belly, outline=False)
    _arms(ctx, pose, -78, 44, fur, length=32)
    # ears (behind head)
    wig = math.sin(t * 3) * 0.06
    for sx in (-1, 1):
        rot = sx * 0.18 + wig * sx
        blob(ctx, sx * 20, -212, 14, 44, fur, rot=rot)
        blob(ctx, sx * 20, -210, 7, 32, inner, rot=rot, outline=False)
    blob(ctx, 0, -145, 50, 46, fur)
    _eyes(ctx, -152, 18, 6, pose, face)
    blob(ctx, -32 + 4 * face, -128, 9, 6, BLUSH, outline=False)
    blob(ctx, 32 + 4 * face, -128, 9, 6, BLUSH, outline=False)
    blob(ctx, 4 * face, -136, 6, 4.5, inner, lw=2)
    _mouth(ctx, 4 * face, -124, 14, pose)


# ---------------------------------------------------------------- bear
def bear(ctx, pose, face, palette=None):
    p = palette or {}
    fur = hexc(p.get("fur", "#a8754f"))
    belly = hexc(p.get("belly", "#e3c19b"))
    _feet(ctx, fur, spread=26, rx=26, ry=13)
    blob(ctx, 0, -72, 58, 66, fur)
    blob(ctx, 4 * face, -64, 38, 44, belly, outline=False)
    _arms(ctx, pose, -96, 58, fur, length=40, thick=18)
    for sx in (-1, 1):
        blob(ctx, sx * 38, -200, 18, 18, fur)
        blob(ctx, sx * 38, -200, 9, 9, belly, outline=False)
    blob(ctx, 0, -165, 56, 50, fur)
    blob(ctx, 5 * face, -146, 24, 17, belly)
    _eyes(ctx, -175, 21, 6, pose, face)
    blob(ctx, 5 * face, -155, 9, 6.5, OUTLINE, outline=False)
    blob(ctx, -38 + 4 * face, -150, 9, 6, BLUSH, outline=False)
    blob(ctx, 38 + 4 * face, -150, 9, 6, BLUSH, outline=False)
    _mouth(ctx, 5 * face, -141, 13, pose)


# ---------------------------------------------------------------- squirrel
def squirrel(ctx, pose, face, palette=None):
    p = palette or {}
    fur = hexc(p.get("fur", "#d98b4a"))
    belly = hexc(p.get("belly", "#f7dcb9"))
    t = pose["t"]
    sway = math.sin(t * 2.5) * 0.08
    # big curly tail
    ctx.save()
    ctx.translate(-34 * face, -40)
    ctx.rotate(sway * face)
    ctx.scale(-face, 1)
    ctx.move_to(0, 0)
    ctx.curve_to(60, -10, 75, -110, 30, -150)
    ctx.curve_to(0, -175, -30, -140, -5, -120)
    ctx.curve_to(25, -100, 20, -40, -5, -10)
    ctx.close_path()
    fill_stroke(ctx, fur)
    ctx.move_to(25, -40)
    ctx.curve_to(45, -70, 45, -110, 25, -135)
    rgba(ctx, belly)
    ctx.set_line_width(6)
    ctx.stroke()
    ctx.restore()
    _feet(ctx, fur, spread=14, rx=14, ry=8)
    blob(ctx, 0, -48, 30, 40, fur)
    blob(ctx, 3 * face, -44, 18, 26, belly, outline=False)
    _arms(ctx, pose, -60, 30, fur, length=22, thick=8)
    for sx in (-1, 1):
        ctx.move_to(sx * 14, -132)
        ctx.line_to(sx * 26, -168)
        ctx.line_to(sx * 32, -128)
        ctx.close_path()
        fill_stroke(ctx, fur)
    blob(ctx, 0, -110, 36, 32, fur)
    blob(ctx, 4 * face, -100, 16, 11, belly, outline=False)
    _eyes(ctx, -116, 13, 5, pose, face)
    blob(ctx, 4 * face, -104, 4.5, 3.5, OUTLINE, outline=False)
    blob(ctx, -22 + 4 * face, -98, 6, 4, BLUSH, outline=False)
    blob(ctx, 22 + 4 * face, -98, 6, 4, BLUSH, outline=False)
    _mouth(ctx, 4 * face, -94, 9, pose)


# ---------------------------------------------------------------- duck
def duck(ctx, pose, face, palette=None):
    p = palette or {}
    body = hexc(p.get("fur", "#ffd84a"))
    beak = hexc(p.get("beak", "#ff9a3c"))
    t = pose["t"]
    _feet(ctx, beak, spread=14, rx=16, ry=7)
    blob(ctx, 0, -42, 40, 34, body)
    # tail
    ctx.move_to(-34 * face, -50)
    ctx.line_to(-54 * face, -70)
    ctx.line_to(-38 * face, -36)
    ctx.close_path()
    fill_stroke(ctx, body)
    flap = math.sin(t * 12) * 0.5 if pose["arms"] in ("up", "wave") else 0.1
    blob(ctx, -6 * face, -44, 22, 14, hexc("#f5c636"), rot=-flap * face)
    blob(ctx, 8 * face, -100, 32, 30, body)
    ctx.save()
    ctx.translate(36 * face, -94)
    ctx.scale(face, 1)
    if pose["talking"]:
        o = abs(math.sin(t * 14)) * 7
    else:
        o = 0
    ctx.move_to(-6, -6)
    ctx.curve_to(16, -12, 26, -4, 24, 0 - o * 0.2)
    ctx.curve_to(12, 2, 4, 2, -6, 2)
    ctx.close_path()
    fill_stroke(ctx, beak, lw=2.5)
    ctx.move_to(-6, 2 + o * 0.3)
    ctx.curve_to(6, 6 + o, 18, 6 + o, 22, 2 + o * 0.5)
    ctx.curve_to(10, 10 + o, 0, 10 + o, -6, 6)
    ctx.close_path()
    fill_stroke(ctx, beak, lw=2.5)
    ctx.restore()
    _eyes(ctx, -108, 11, 5, dict(pose, talking=False), face)
    ctx.save()
    ctx.translate(8 * face, 0)
    blob(ctx, 12 * face, -88, 7, 4.5, BLUSH, outline=False)
    ctx.restore()
    # head tuft
    ctx.move_to(4 * face, -128)
    ctx.curve_to(0, -146, 14 * face, -146, 10 * face, -132)
    rgba(ctx, OUTLINE)
    ctx.set_line_width(3)
    ctx.stroke()


# ---------------------------------------------------------------- fox / cat
def _pointy_animal(ctx, pose, face, fur, belly, inner, tail):
    t = pose["t"]
    sway = math.sin(t * 2.2) * 0.12
    ctx.save()
    ctx.translate(-36 * face, -36)
    ctx.rotate(sway * face)
    ctx.scale(-face, 1)
    if tail == "fox":
        ctx.move_to(0, 0)
        ctx.curve_to(40, 10, 85, -10, 95, -55)
        ctx.curve_to(70, -40, 30, -30, 0, -22)
        ctx.close_path()
        fill_stroke(ctx, fur)
        ctx.move_to(95, -55)
        ctx.curve_to(88, -38, 78, -30, 66, -28)
        ctx.curve_to(78, -40, 85, -48, 95, -55)
        fill_stroke(ctx, belly, lw=2)
    else:
        ctx.move_to(0, -6)
        ctx.curve_to(40, 0, 50, -50, 40, -90)
        rgba(ctx, OUTLINE)
        ctx.set_line_width(16)
        ctx.set_line_cap(1)
        ctx.stroke_preserve()
        rgba(ctx, fur)
        ctx.set_line_width(10)
        ctx.stroke()
    ctx.restore()
    _feet(ctx, fur, spread=18, rx=17, ry=9)
    blob(ctx, 0, -55, 38, 47, fur)
    blob(ctx, 4 * face, -48, 22, 30, belly, outline=False)
    _arms(ctx, pose, -70, 38, fur, length=28, thick=10)
    for sx in (-1, 1):
        ctx.move_to(sx * 12, -160)
        ctx.line_to(sx * 36, -204)
        ctx.line_to(sx * 46, -146)
        ctx.close_path()
        fill_stroke(ctx, fur)
        ctx.move_to(sx * 20, -160)
        ctx.line_to(sx * 35, -190)
        ctx.line_to(sx * 40, -156)
        ctx.close_path()
        rgba(ctx, inner)
        ctx.fill()
    blob(ctx, 0, -132, 46, 40, fur)
    if tail == "fox":
        ctx.move_to(-40, -128)
        ctx.curve_to(-20, -100, 30, -100, 50 * face if face > 0 else 40, -122)
        ctx.curve_to(20, -112, -10, -112, -40, -128)
        rgba(ctx, belly)
        ctx.fill()
    else:
        blob(ctx, 5 * face, -116, 20, 13, belly, outline=False)
    _eyes(ctx, -140, 17, 5.5, pose, face)
    blob(ctx, 5 * face, -124, 6, 4.5, hexc("#3a2a24") if tail == "fox" else hexc("#ff8fa8"), lw=1.5)
    blob(ctx, -30 + 4 * face, -116, 8, 5, BLUSH, outline=False)
    blob(ctx, 30 + 4 * face, -116, 8, 5, BLUSH, outline=False)
    if tail == "cat":
        rgba(ctx, OUTLINE)
        ctx.set_line_width(1.6)
        for sx in (-1, 1):
            for dy in (-4, 3):
                ctx.move_to(5 * face + sx * 14, -120 + dy)
                ctx.line_to(5 * face + sx * 38, -122 + dy * 2)
                ctx.stroke()
    _mouth(ctx, 5 * face, -112, 12, pose)


def fox(ctx, pose, face, palette=None):
    p = palette or {}
    _pointy_animal(ctx, pose, face, hexc(p.get("fur", "#f08a3e")), hexc(p.get("belly", "#fff4e6")),
                   hexc("#5a3527"), "fox")


def cat(ctx, pose, face, palette=None):
    p = palette or {}
    _pointy_animal(ctx, pose, face, hexc(p.get("fur", "#b9b4c4")), hexc(p.get("belly", "#f4f1f8")),
                   hexc("#ffb6c8"), "cat")


CHARACTERS = {
    "bunny": (bunny, 230),
    "bear": (bear, 225),
    "squirrel": (squirrel, 170),
    "duck": (duck, 150),
    "fox": (fox, 210),
    "cat": (cat, 210),
}


# ---------------------------------------------------------------- umbrella
RAINBOW = ["#ff5a5f", "#ff9f40", "#ffd84a", "#5cd65c", "#3fa9f5", "#6a6cf5", "#b06af5"]


def umbrella(ctx, hx, hy, top_y, width, t, open_amt=1.0):
    """Rainbow umbrella whose handle is held at (hx, hy)."""
    sway = math.sin(t * 1.8) * 4
    cx = hx + sway
    rgba(ctx, OUTLINE)
    ctx.set_line_width(5)
    ctx.move_to(hx, hy + 18)
    ctx.line_to(cx, top_y)
    ctx.stroke()
    ctx.arc(hx - 8, hy + 18, 8, 0, math.pi)
    ctx.stroke()
    w = width * (0.25 + 0.75 * open_amt)
    h = width * 0.42
    n = len(RAINBOW)
    for i, col in enumerate(RAINBOW):
        x0 = cx - w / 2 + w * i / n
        x1 = cx - w / 2 + w * (i + 1) / n
        ctx.move_to(cx, top_y - h)
        ctx.curve_to(x0 + (cx - x0) * 0.1, top_y - h * 0.9, x0, top_y - h * 0.3, x0, top_y)
        ctx.curve_to(x0 + (x1 - x0) * 0.3, top_y - 12, x1 - (x1 - x0) * 0.3, top_y - 12, x1, top_y)
        ctx.curve_to(x1, top_y - h * 0.3, x1 + (cx - x1) * 0.1, top_y - h * 0.9, cx, top_y - h)
        ctx.close_path()
        fill_stroke(ctx, hexc(col), lw=2.5)
    blob(ctx, cx, top_y - h - 4, 5, 6, hexc("#ffd84a"), lw=2)


def draw_character(ctx, name, x, y, scale, face, pose, palette=None, umbrella_cfg=None):
    fn, _height = CHARACTERS[name]
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(scale * pose.get("squash_x", 1.0), scale * pose.get("squash_y", 1.0))
    if pose.get("rot"):
        ctx.rotate(pose["rot"])
    # soft shadow
    shadow_lift = pose.get("lift", 0)
    ctx.save()
    ctx.translate(0, -shadow_lift / max(scale, 0.01))
    ctx.restore()
    if face < 0:
        ctx.save()
        ctx.scale(-1, 1)
        fn(ctx, pose, 1, palette)
        hand = pose.get("_hand")
        if hand:
            pose["_hand"] = (-hand[0], hand[1])
        ctx.restore()
    else:
        fn(ctx, pose, 1, palette)
    if umbrella_cfg:
        hx, hy = pose.get("_hand", (30, -120))
        top = umbrella_cfg.get("top", -_height - 50)
        umbrella(ctx, hx, hy, top, umbrella_cfg.get("width", 260), pose["t"], umbrella_cfg.get("open", 1.0))
    ctx.restore()


def shadow(ctx, x, y, rx, lift):
    k = max(0.4, 1 - lift / 120)
    ellipse_path(ctx, x, y + 2, rx * k, rx * 0.18 * k)
    ctx.set_source_rgba(0, 0, 0, 0.16 * k)
    ctx.fill()
