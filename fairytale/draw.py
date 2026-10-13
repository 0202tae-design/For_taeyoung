"""Cairo drawing helpers shared by characters and scenery.

All drawing happens in a 1280x720 logical canvas; the renderer scales the
context to the real output resolution.
"""
import math

TAU = math.pi * 2
OUTLINE = (0.23, 0.17, 0.14)


def hexc(h, a=1.0):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)) + (a,)


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return tuple(lerp(x, y, t) for x, y in zip(c1, c2))


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def rgba(ctx, c):
    if len(c) == 3:
        ctx.set_source_rgb(*c)
    else:
        ctx.set_source_rgba(*c)


def ellipse_path(ctx, cx, cy, rx, ry, rot=0.0):
    ctx.save()
    ctx.translate(cx, cy)
    if rot:
        ctx.rotate(rot)
    ctx.scale(max(rx, 0.01), max(ry, 0.01))
    ctx.new_sub_path()
    ctx.arc(0, 0, 1, 0, TAU)
    ctx.restore()


def blob(ctx, cx, cy, rx, ry, fill, rot=0.0, outline=True, lw=3.0):
    """Filled ellipse with the cartoon outline."""
    ellipse_path(ctx, cx, cy, rx, ry, rot)
    rgba(ctx, fill)
    if outline:
        ctx.fill_preserve()
        rgba(ctx, OUTLINE)
        ctx.set_line_width(lw)
        ctx.stroke()
    else:
        ctx.fill()


def fill_stroke(ctx, fill, outline=True, lw=3.0):
    rgba(ctx, fill)
    if outline:
        ctx.fill_preserve()
        rgba(ctx, OUTLINE)
        ctx.set_line_width(lw)
        ctx.stroke()
    else:
        ctx.fill()


def rounded_rect(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def rand(seed):
    """Deterministic pseudo random in [0, 1) from an integer seed."""
    x = math.sin(seed * 12.9898 + 78.233) * 43758.5453
    return x - math.floor(x)
