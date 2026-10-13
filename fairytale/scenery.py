"""Backgrounds, weather effects and props."""
import math

from draw import TAU, OUTLINE, hexc, lerp_color, blob, ellipse_path, fill_stroke, rgba, rand, smooth

W, H = 1280, 720
GROUND_Y = 560

SKIES = {
    "day": (hexc("#7ec8f5"), hexc("#d8f1ff")),
    "cloudy": (hexc("#8d9bab"), hexc("#c9d2db")),
    "sunset": (hexc("#ff9e7a"), hexc("#ffe0a8")),
    "night": (hexc("#1d2457"), hexc("#4a4f8f")),
}

THEMES = {
    "meadow": {"hill1": "#9fdc7c", "hill2": "#7cc95f", "ground": "#6dbb55"},
    "forest": {"hill1": "#6fb07a", "hill2": "#4f9a63", "ground": "#5aa45a"},
    "riverside": {"hill1": "#a8de86", "hill2": "#86cf6c", "ground": "#79c45f"},
    "snowfield": {"hill1": "#eef4fb", "hill2": "#dfe9f5", "ground": "#f4f8fd"},
}


def sky(ctx, kind_from, kind_to, p):
    a = SKIES[kind_from]
    b = SKIES[kind_to]
    top = lerp_color(a[0], b[0], p)
    bottom = lerp_color(a[1], b[1], p)
    import cairo
    g = cairo.LinearGradient(0, 0, 0, GROUND_Y)
    g.add_color_stop_rgba(0, *top)
    g.add_color_stop_rgba(1, *bottom)
    ctx.rectangle(0, 0, W, H)
    ctx.set_source(g)
    ctx.fill()


def sun(ctx, t, alpha=1.0):
    if alpha <= 0:
        return
    cx, cy = 1100, 120
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(t * 0.15)
    ctx.set_source_rgba(1, 0.85, 0.3, 0.5 * alpha)
    ctx.set_line_width(8)
    ctx.set_line_cap(1)
    for i in range(12):
        a = TAU * i / 12
        ctx.move_to(math.cos(a) * 70, math.sin(a) * 70)
        ctx.line_to(math.cos(a) * 95, math.sin(a) * 95)
        ctx.stroke()
    ctx.restore()
    ellipse_path(ctx, cx, cy, 55, 55)
    ctx.set_source_rgba(1, 0.86, 0.32, alpha)
    ctx.fill()
    ellipse_path(ctx, cx - 15, cy - 15, 18, 18)
    ctx.set_source_rgba(1, 0.95, 0.65, alpha)
    ctx.fill()


def moon_stars(ctx, t, alpha=1.0):
    if alpha <= 0:
        return
    for i in range(70):
        x = rand(i * 3 + 1) * W
        y = rand(i * 7 + 2) * (GROUND_Y - 150)
        tw = 0.5 + 0.5 * math.sin(t * (1.5 + rand(i) * 2) + i)
        r = 1.2 + rand(i * 11) * 2.2
        ellipse_path(ctx, x, y, r, r)
        ctx.set_source_rgba(1, 1, 0.85, alpha * (0.35 + 0.65 * tw))
        ctx.fill()
    ellipse_path(ctx, 1080, 120, 50, 50)
    ctx.set_source_rgba(1, 0.97, 0.8, alpha)
    ctx.fill()
    ellipse_path(ctx, 1102, 105, 44, 44)
    ctx.set_source_rgba(*SKIES["night"][0][:3], alpha)
    ctx.fill()


def cloud(ctx, x, y, s, color):
    for dx, dy, r in ((-50, 10, 35), (-15, -12, 45), (30, -5, 40), (60, 12, 30), (5, 18, 38)):
        ellipse_path(ctx, x + dx * s, y + dy * s, r * s, r * s)
    rgba(ctx, color)
    ctx.fill()


def clouds(ctx, t, darkness, count=5):
    col = lerp_color(hexc("#ffffff", 0.95), hexc("#7d8794", 0.97), darkness)
    n = count + int(darkness * 5)
    for i in range(n):
        speed = 6 + rand(i * 5) * 10
        x = (rand(i * 13) * (W + 400) + t * speed) % (W + 400) - 200
        y = 70 + rand(i * 17) * 170
        s = 0.8 + rand(i * 19) * 0.9 + darkness * 0.4
        cloud(ctx, x, y, s, col)


def hills(ctx, theme, t):
    th = THEMES[theme]
    ctx.move_to(0, 430)
    ctx.curve_to(250, 340, 450, 470, 700, 400)
    ctx.curve_to(900, 345, 1100, 420, W, 380)
    ctx.line_to(W, H)
    ctx.line_to(0, H)
    ctx.close_path()
    rgba(ctx, hexc(th["hill1"]))
    ctx.fill()
    ctx.move_to(0, 500)
    ctx.curve_to(300, 440, 600, 520, 900, 470)
    ctx.curve_to(1050, 445, 1180, 480, W, 470)
    ctx.line_to(W, H)
    ctx.line_to(0, H)
    ctx.close_path()
    rgba(ctx, hexc(th["hill2"]))
    ctx.fill()
    ctx.rectangle(0, GROUND_Y - 20, W, H)
    rgba(ctx, hexc(th["ground"]))
    ctx.fill()


def flowers(ctx, t, n=26, seed=0):
    cols = ["#ff8fb1", "#ffd84a", "#ffffff", "#c79bff", "#ff9f6b"]
    for i in range(n):
        x = rand(seed + i * 3) * W
        y = GROUND_Y + 10 + rand(seed + i * 5) * 140
        s = 0.6 + (y - GROUND_Y) / 220
        sway = math.sin(t * 2 + i) * 3 * s
        ctx.set_line_width(2.5 * s)
        ctx.set_source_rgba(0.25, 0.55, 0.25, 1)
        ctx.move_to(x, y)
        ctx.line_to(x + sway, y - 18 * s)
        ctx.stroke()
        c = hexc(cols[i % len(cols)])
        for k in range(5):
            a = TAU * k / 5 + i
            ellipse_path(ctx, x + sway + math.cos(a) * 6 * s, y - 18 * s + math.sin(a) * 6 * s, 5 * s, 5 * s)
        rgba(ctx, c)
        ctx.fill()
        ellipse_path(ctx, x + sway, y - 18 * s, 3.5 * s, 3.5 * s)
        rgba(ctx, hexc("#ffb02e"))
        ctx.fill()


def grass_tufts(ctx, t, n=40, seed=100, color="#4f9e45"):
    rgba(ctx, hexc(color))
    for i in range(n):
        x = rand(seed + i) * W
        y = GROUND_Y + rand(seed + i * 2) * 150
        s = 0.6 + (y - GROUND_Y) / 200
        sway = math.sin(t * 1.7 + i) * 2
        for k in (-1, 0, 1):
            ctx.move_to(x + k * 5 * s - 3 * s, y)
            ctx.line_to(x + k * 9 * s + sway, y - (12 + 6 * (k == 0)) * s)
            ctx.line_to(x + k * 5 * s + 3 * s, y)
            ctx.close_path()
        ctx.fill()


def tree(ctx, x, y, s, t, seed=0, canopy="#4caf50"):
    ctx.move_to(x - 16 * s, y)
    ctx.curve_to(x - 12 * s, y - 60 * s, x - 14 * s, y - 120 * s, x - 10 * s, y - 150 * s)
    ctx.line_to(x + 10 * s, y - 150 * s)
    ctx.curve_to(x + 14 * s, y - 120 * s, x + 12 * s, y - 60 * s, x + 16 * s, y)
    ctx.close_path()
    fill_stroke(ctx, hexc("#8b5a3c"), lw=3)
    sway = math.sin(t * 1.2 + seed) * 3 * s
    base = hexc(canopy)
    for dx, dy, r in ((-55, -170, 55), (50, -175, 55), (0, -225, 65), (-35, -250, 45), (40, -250, 45)):
        blob(ctx, x + dx * s + sway, y + dy * s, r * s, r * s, base, lw=3)
    for dx, dy, r in ((-20, -235, 18), (35, -195, 14), (-45, -185, 12)):
        ellipse_path(ctx, x + dx * s + sway, y + dy * s, r * s, r * s)
        ctx.set_source_rgba(1, 1, 1, 0.18)
        ctx.fill()


def back_forest(ctx):
    rgba(ctx, hexc("#5d9e6a"))
    for i in range(14):
        x = i * 100 + rand(i) * 40 - 20
        h = 140 + rand(i * 3) * 80
        ctx.move_to(x - 60, GROUND_Y - 30)
        ctx.line_to(x, GROUND_Y - 30 - h)
        ctx.line_to(x + 60, GROUND_Y - 30)
        ctx.close_path()
    ctx.fill()


def mushrooms(ctx):
    for i, (x, y, s) in enumerate(((180, 610, 1.0), (1150, 640, 1.2), (960, 600, 0.8))):
        blob(ctx, x, y - 12 * s, 8 * s, 14 * s, hexc("#fff4e0"), lw=2)
        ctx.arc(x, y - 22 * s, 22 * s, math.pi, TAU)
        ctx.close_path()
        fill_stroke(ctx, hexc("#ff5a5f"), lw=2.5)
        for dx in (-10, 4, 12):
            ellipse_path(ctx, x + dx * s, y - 32 * s + abs(dx) * 0.5 * s, 3.5 * s, 3.5 * s)
            ctx.set_source_rgb(1, 1, 1)
            ctx.fill()


def river(ctx, t):
    ctx.move_to(0, 520)
    ctx.curve_to(400, 505, 800, 535, W, 512)
    ctx.line_to(W, 572)
    ctx.curve_to(800, 590, 400, 562, 0, 580)
    ctx.close_path()
    rgba(ctx, hexc("#5bb8f0"))
    ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.55)
    ctx.set_line_width(3)
    ctx.set_line_cap(1)
    for i in range(16):
        x = (rand(i * 7) * W + t * 30) % W
        y = 528 + rand(i * 9) * 40
        ctx.move_to(x, y)
        ctx.line_to(x + 30, y)
        ctx.stroke()
    for i, x in enumerate((90, 140, 1180, 1220, 1240)):
        sway = math.sin(t * 1.5 + i) * 4
        ctx.set_source_rgba(0.3, 0.55, 0.3, 1)
        ctx.set_line_width(4)
        ctx.move_to(x, 585)
        ctx.line_to(x + sway, 500)
        ctx.stroke()
        blob(ctx, x + sway, 500, 6, 18, hexc("#8b5a3c"), lw=2)


def background(ctx, scene, t, p):
    """Draw the scene's world. p is the scene progress 0..1."""
    sky_from = scene.get("sky", "day")
    sky_to = scene.get("sky_to", sky_from)
    sp = smooth(p * 1.6) if sky_to != sky_from else 0.0
    sky(ctx, sky_from, sky_to, sp)

    def weight(kind):
        return (1 - sp) * (sky_from == kind) + sp * (sky_to == kind)

    moon_stars(ctx, t, weight("night"))
    sun(ctx, t, weight("day") + weight("sunset"))
    darkness = weight("cloudy")
    clouds(ctx, t, darkness, count=2 if weight("night") > 0.5 else 5)
    if scene.get("rainbow"):
        rainbow(ctx, smooth((p - 0.1) * 2.5))

    bg = scene.get("bg", "meadow")
    theme = bg if bg in THEMES else "meadow"
    if bg == "forest":
        hills(ctx, theme, t)
        back_forest(ctx)
        ctx.rectangle(0, GROUND_Y - 20, W, H)
        rgba(ctx, hexc(THEMES[theme]["ground"]))
        ctx.fill()
        for i, (x, s) in enumerate(((90, 1.15), (330, 0.95), (1000, 1.05), (1210, 1.25))):
            tree(ctx, x, GROUND_Y + 10, s, t, seed=i, canopy="#3f9a4f" if i % 2 else "#4caf50")
        grass_tufts(ctx, t, color="#468f3f")
        mushrooms(ctx)
    elif bg == "riverside":
        hills(ctx, theme, t)
        tree(ctx, 1100, GROUND_Y - 10, 0.9, t, seed=3)
        river(ctx, t)
        grass_tufts(ctx, t, n=25)
    elif bg == "snowfield":
        hills(ctx, theme, t)
        for i, (x, s) in enumerate(((120, 1.0), (1150, 1.1))):
            tree(ctx, x, GROUND_Y + 10, s, t, seed=i, canopy="#e8f0fa")
    else:
        hills(ctx, theme, t)
        tree(ctx, 140, GROUND_Y - 5, 0.85, t, seed=7)
        grass_tufts(ctx, t)
        flowers(ctx, t)

    night = weight("night")
    if night > 0:
        ctx.rectangle(0, 0, W, H)
        ctx.set_source_rgba(0.08, 0.1, 0.3, 0.38 * night)
        ctx.fill()
    if darkness > 0:
        ctx.rectangle(0, 0, W, H)
        ctx.set_source_rgba(0.2, 0.25, 0.35, 0.18 * darkness)
        ctx.fill()


def rainbow(ctx, a):
    if a <= 0:
        return
    cols = ["#ff5a5f", "#ff9f40", "#ffd84a", "#5cd65c", "#3fa9f5", "#6a6cf5", "#b06af5"]
    ctx.set_line_width(22)
    for i, c in enumerate(cols):
        r = 520 - i * 22
        ctx.arc(640, 620, r, math.pi, TAU)
        rgba(ctx, hexc(c, 0.75 * a))
        ctx.stroke()


def weather(ctx, scene, t, p):
    kind = scene.get("weather", "none")
    ramp = scene.get("weather_ramp")  # [start, end] in progress units
    amt = 1.0
    if ramp:
        a, b = ramp
        amt = smooth((p - a) / max(b - a, 1e-3)) if b > a else 1 - smooth((p - b) / max(a - b, 1e-3))
    if kind == "rain" and amt > 0:
        ctx.set_line_cap(1)
        ctx.set_line_width(2.5)
        n = int(220 * amt)
        for i in range(n):
            speed = 700 + rand(i * 3) * 300
            x = rand(i * 7) * (W + 200) - 100
            y = (rand(i * 11) * H + t * speed) % (H + 60) - 40
            x += (y / H) * -60
            ctx.set_source_rgba(0.75, 0.88, 1, 0.65)
            ctx.move_to(x, y)
            ctx.line_to(x - 7, y + 22)
            ctx.stroke()
        ctx.set_line_width(2)
        for i in range(int(14 * amt)):
            period = 1.2 + rand(i) * 0.8
            ph = ((t + rand(i * 5) * period) % period) / period
            x = rand(i * 13 + 1) * W
            y = GROUND_Y + 15 + rand(i * 17) * 140
            ellipse_path(ctx, x, y, 6 + ph * 26, (6 + ph * 26) * 0.3)
            ctx.set_source_rgba(1, 1, 1, 0.6 * (1 - ph))
            ctx.stroke()
    elif kind == "snow" and amt > 0:
        for i in range(int(120 * amt)):
            speed = 40 + rand(i * 3) * 50
            x = rand(i * 7) * W + math.sin(t + i) * 20
            y = (rand(i * 11) * H + t * speed) % (H + 20) - 10
            r = 2 + rand(i * 5) * 3
            ellipse_path(ctx, x, y, r, r)
            ctx.set_source_rgba(1, 1, 1, 0.9)
            ctx.fill()
    elif kind == "sparkle" and amt > 0:
        for i in range(40):
            x = rand(i * 7 + 3) * W
            y = rand(i * 9 + 4) * (H - 200)
            tw = max(0.0, math.sin(t * 3 + i * 1.7))
            star(ctx, x, y, 6 + 6 * tw, hexc("#fff5b0", amt * tw))


def star(ctx, x, y, r, color, outline=False):
    ctx.move_to(x, y - r)
    for k in range(1, 10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        ctx.line_to(x + math.cos(a) * rr, y + math.sin(a) * rr)
    ctx.close_path()
    if outline:
        fill_stroke(ctx, color, lw=2.5)
    else:
        rgba(ctx, color)
        ctx.fill()


# ---------------------------------------------------------------- props
def prop(ctx, kind, x, y, s, t):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    if kind == "leaf":
        ctx.rotate(math.sin(t * 2) * 0.05 - 0.15)
        ctx.move_to(-80, 0)
        ctx.curve_to(-60, -55, 60, -55, 80, 0)
        ctx.curve_to(40, 18, -40, 18, -80, 0)
        fill_stroke(ctx, hexc("#6cc24a"))
        ctx.move_to(-75, 0)
        ctx.line_to(75, 0)
        rgba(ctx, OUTLINE)
        ctx.set_line_width(2)
        ctx.stroke()
        ctx.move_to(0, 5)
        ctx.line_to(4, 120)
        ctx.set_line_width(4)
        ctx.stroke()
    elif kind == "gift":
        ctx.rectangle(-40, -70, 80, 70)
        fill_stroke(ctx, hexc("#ff7aa2"))
        ctx.rectangle(-8, -70, 16, 70)
        fill_stroke(ctx, hexc("#ffd84a"), lw=2)
        for sx in (-1, 1):
            blob(ctx, sx * 16, -80, 16, 10, hexc("#ffd84a"), rot=sx * 0.4, lw=2)
    elif kind == "puddle":
        ellipse_path(ctx, 0, 0, 90, 18)
        rgba(ctx, hexc("#8fd0f5", 0.9))
        ctx.fill()
    elif kind == "apple":
        blob(ctx, 0, -20, 22, 20, hexc("#ff4d4d"))
        blob(ctx, 8, -44, 9, 5, hexc("#5cd65c"), rot=-0.5, lw=2)
    elif kind == "star":
        star(ctx, 0, 0, 30 + 3 * math.sin(t * 4), hexc("#ffd84a"), outline=True)
    elif kind == "flower":
        flowers_one(ctx, t)
    elif kind == "house":
        ctx.rectangle(-90, -120, 180, 120)
        fill_stroke(ctx, hexc("#ffe2b8"))
        ctx.move_to(-110, -115)
        ctx.line_to(0, -200)
        ctx.line_to(110, -115)
        ctx.close_path()
        fill_stroke(ctx, hexc("#e8645a"))
        ctx.rectangle(-25, -70, 50, 70)
        fill_stroke(ctx, hexc("#a8754f"))
        ctx.rectangle(40, -95, 34, 30)
        fill_stroke(ctx, hexc("#9fdcff"))
    ctx.restore()


def flowers_one(ctx, t):
    ctx.set_line_width(4)
    ctx.set_source_rgba(0.25, 0.55, 0.25, 1)
    ctx.move_to(0, 0)
    ctx.line_to(math.sin(t * 2) * 4, -50)
    ctx.stroke()
    for k in range(6):
        a = TAU * k / 6
        blob(ctx, math.cos(a) * 13, -50 + math.sin(a) * 13, 10, 10, hexc("#ff8fb1"), lw=2)
    blob(ctx, 0, -50, 9, 9, hexc("#ffd84a"), lw=2)
