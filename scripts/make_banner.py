"""Build the homepage banner and the repeating canal strip from the pixel-art logo files.

Usage (needs Pillow):  python scripts/make_banner.py

banner.png: the lettered logo scene, followed by the straight canal below the dam continuing
downstream, which dissolves into the page background with an ordered (Bayer) dither.
canal-tile.png: a seamlessly repeating stretch of that canal, used behind page titles and above the footer.

Everything to the right of the logo is rebuilt from pieces of the unlettered scene (welcome.png),
never mirrored:
- Land above and below the canal: "image quilting". Slices of random width from river-free parts
  of the scene are laid side by side in random order; each overlaps the previous one and joins along
  the path of least visible difference, so trees stay whole and don't fall into a fixed rhythm.
- The canal: the stone banks repeat as they are; the shadow line under the top bank, the ripple
  dashes and the grass tufts on the lower bank are placed at random.
- The sky: flat, with the scene's two clouds placed at irregular spacing.
Output is at 1x pixel scale; the site CSS scales it up with crisp pixels. The random seed is
fixed, so the output only changes if the source art or these settings change.
"""
import random
from pathlib import Path

from PIL import Image

MEDIA = Path(__file__).resolve().parent.parent / "assets" / "media"
SEED = 7
FRAME = 3  # 2px sand + 1px brown border around the logo art
FRAME_COLORS = {(233, 195, 120), (73, 47, 36)}
SKY_ROWS = 25       # clouds sit above this row
# Column ranges of the scene with no river, sand, rock or dam crossing each band; slices come from these.
UPPER_SOURCES = [(199, 250)]
LOWER_SOURCES = [(199, 250)]
RECENT = 3          # a slice can't start within NEAR px of the last RECENT picks
NEAR = 12
CANAL_X = 225       # the dam's spray ends before this column
BLOCKS = (12, 26)   # quilting slice width range, in art pixels
OVERLAP = 6
CHOICES = 12        # pick each slice at random from this many best-fitting candidates
TILE = 900
# The homepage banner's canal dissolves into the page background between these columns past the logo.
FADE = (10, 250)
PAGE_BACKGROUND = (251, 246, 234)  # --paper in assets/css/main.css
WATER = (56, 139, 182)
RIPPLE = (19, 102, 151)
STONE = (115, 116, 113)
# Spacing between clouds (first value is the offset of the first cloud), in art pixels.
BANNER_GAPS = [35, 70, 110, 45, 140, 60, 95, 125, 50, 160, 75, 100, 55, 130, 85, 65, 115, 90, 150, 70]
TILE_GAPS = [20, 90, 60, 130, 40, 110, 75, 95]
CLOUD_LIFT = [0, 2, -1, 1, -2, 1]  # small vertical offsets so clouds don't line up


def interior(path):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    img = img.crop((FRAME, FRAME, w - FRAME, h - FRAME))
    # The frame's rounded corners poke a few pixels into the crop; fill them from inside.
    w, h = img.size
    for cx, cy, dx, dy in ((0, 0, 1, 1), (w - 1, 0, -1, 1), (0, h - 1, 1, -1), (w - 1, h - 1, -1, -1)):
        fill = img.getpixel((cx + 2 * dx, cy + 2 * dy))
        for i in range(2):
            for j in range(2):
                x, y = cx + i * dx, cy + j * dy
                if img.getpixel((x, y)) in FRAME_COLORS:
                    img.putpixel((x, y), fill)
    return img


def canal_rows(scene):
    """First and one-past-last rows of the canal band (stone banks included) at the right edge."""
    x = scene.width - 1
    water = [y for y in range(40, scene.height)
             if (lambda r, g, b: b > r + 40 and b > 150)(*scene.getpixel((x, y)))]
    return min(water) - 3, max(water) + 3


def is_cloud(p):
    return sum(p) > 600


def is_sky(p):
    r, g, b = p
    return b >= 180 and b > r + 20


def is_green(p):
    r, g, b = p
    return g > r + 10 and g > b


# ---------- land: random quilting ----------

def seam(left, right, weights):
    """Lowest-cost vertical path through two overlapping column blocks (lists of rows of pixels).
    Returns (cost, path) where path[r] is the first column taken from `right` in row r."""
    rows, cols = len(left), len(left[0])
    err = [[weights[r] * sum(abs(a - b) for a, b in zip(left[r][i], right[r][i])) for i in range(cols)]
           for r in range(rows)]
    cost = [err[0][:]]
    back = []
    for r in range(1, rows):
        prev, row, links = cost[-1], [], []
        for i in range(cols):
            j = min((j for j in (i - 1, i, i + 1) if 0 <= j < cols), key=lambda j: prev[j])
            row.append(prev[j] + err[r][i])
            links.append(j)
        cost.append(row)
        back.append(links)
    i = min(range(cols), key=lambda i: cost[-1][i])
    total = cost[-1][i]
    path = [i]
    for links in reversed(back):
        i = links[i]
        path.append(i)
    return total, path[::-1]


def columns(img, x0, x1, y0, y1):
    return [[img.getpixel((x, y)) for x in range(x0, x1)] for y in range(y0, y1)]


def quilt_band(canvas, scene, y0, y1, start, rng, sources):
    """Fill rows y0..y1 of the canvas from `start` rightwards with randomly chosen, seamed slices."""
    # rows that are pure sky everywhere in the sources don't count toward seam cost
    weights = [0 if all(is_sky(p) or is_cloud(p) for a, b in sources for p in (scene.getpixel((x, y)) for x in range(a, b)))
               else 1 for y in range(y0, y1)]
    heads = {o: columns(scene, o, o + OVERLAP, y0, y1) for a, b in sources for o in range(a, b - OVERLAP)}
    cur, recent = start, []
    while cur < canvas.width:
        x = cur - OVERLAP
        block = rng.randint(*BLOCKS)
        offsets = [o for a, b in sources for o in range(a, b - block + 1)]
        fresh = [o for o in offsets if all(abs(o - r) >= NEAR for r in recent)] or offsets
        existing = columns(canvas, x, x + OVERLAP, y0, y1)
        scored = sorted((seam(existing, heads[o], weights) + (o,) for o in fresh), key=lambda t: t[0])
        _, path, o = rng.choice(scored[:CHOICES])
        for r in range(y1 - y0):
            for i in range(path[r], block):
                if x + i < canvas.width:
                    canvas.putpixel((x + i, y0 + r), scene.getpixel((o + i, y0 + r)))
        cur, recent = x + block, (recent + [o])[-RECENT:]


# ---------- canal: banks repeat, ripples and tufts are scattered ----------

def canal_band(canvas, scene, top, bottom, start, rng):
    w = scene.width
    period = w - CANAL_X
    unit = scene.crop((CANAL_X, top, w, bottom))
    px_unit = unit.load()
    # strip the ripples and tufts from the repeating unit; they get placed at random below
    water_top = next(y for y in range(unit.height) if px_unit[unit.width - 1, y] == WATER) + 2
    for y in range(water_top, unit.height):
        for x in range(unit.width):
            p = px_unit[x, y]
            if y >= unit.height - 1 and is_green(p):
                px_unit[x, y] = STONE
            elif y < unit.height - 1 and (p[2] > 140 and p != WATER or is_green(p)):
                px_unit[x, y] = WATER
    x = start
    while x < canvas.width:
        canvas.paste(unit, (x, top))
        x += period

    px = canvas.load()
    # shadow under the top bank: one continuous line with a few random breaks
    shadow_y = top + water_top - 1
    shadow = scene.getpixel((CANAL_X, shadow_y))
    for x in range(start, canvas.width):
        px[x, shadow_y] = shadow
    x = start + rng.randint(10, 40)
    while x < canvas.width - 5:
        for i in range(rng.randint(2, 5)):
            px[x + i, shadow_y] = WATER
        x += rng.randint(20, 70)

    first, last = top + water_top + 1, bottom - 3
    x = start + rng.randint(2, 10)
    while x < canvas.width - 10:
        length = rng.choice([3, 4, 5, 5, 6, 8])
        y = rng.randint(first, last)
        tick = (x, y - 1) if rng.random() < 0.5 else (x, y + 1)
        for i in range(1, length + 1):
            px[x + i, y] = RIPPLE
        px[tick] = RIPPLE
        x += length + rng.randint(4, 16)

    # the grass tuft growing over the lower bank, taken from the original's right edge
    tuft = [(dx, dy, scene.getpixel((w - 4 + dx, bottom - 4 + dy)))
            for dx in range(4) for dy in range(4) if is_green(scene.getpixel((w - 4 + dx, bottom - 4 + dy)))]
    x = start + rng.randint(5, 30)
    while x < canvas.width - 4:
        for dx, dy, p in tuft:
            px[x + dx, bottom - 4 + dy] = p
        x += rng.randint(14, 55)


# ---------- clouds ----------

def cloud_sprites(scene):
    """Every complete cloud in the original sky, as (image, mask, top_row)."""
    seen, sprites = set(), []
    for y0 in range(SKY_ROWS):
        for x0 in range(scene.width):
            if (x0, y0) in seen or not is_cloud(scene.getpixel((x0, y0))):
                continue
            comp, stack = [], [(x0, y0)]
            seen.add((x0, y0))
            while stack:
                x, y = stack.pop()
                comp.append((x, y))
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if (0 <= nx < scene.width and 0 <= ny < SKY_ROWS and (nx, ny) not in seen
                            and is_cloud(scene.getpixel((nx, ny)))):
                        seen.add((nx, ny))
                        stack.append((nx, ny))
            xs = [p[0] for p in comp]
            if len(comp) < 300 or min(xs) == 0 or max(xs) == scene.width - 1:
                continue  # skip specks and clouds cut off by the image edge
            pts = trim_cloud_bottom(set(comp))
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            box = (min(xs), min(ys), max(xs) + 1, max(ys) + 1)
            mask = Image.new("1", (box[2] - box[0], box[3] - box[1]))
            for x, y in pts:
                mask.putpixel((x - box[0], y - box[1]), 1)
            sprites.append((scene.crop(box), mask, box[1]))
    return sprites


def trim_cloud_bottom(pts):
    """Drop thin wisps below a cloud (e.g. a mountain's snowcap that touches it)."""
    widths = {}
    for _, y in pts:
        widths[y] = widths.get(y, 0) + 1
    widest = max(widths.values())
    last = max(widths)
    while widths[last] < widest // 4:
        last -= 1
    pts = {(x, y) for x, y in pts if y <= last}
    return {(x, y) for x, y in pts if y < last or (x, y - 1) in pts}


def place_clouds(strip, scene, gaps):
    """Repaint the sky flat, then place the scene's clouds at irregular spacing."""
    sky_colors = {}
    for y in range(SKY_ROWS):
        edge = scene.getpixel((scene.width - 1, y))  # match the logo's right edge exactly
        if is_sky(edge) and not is_cloud(edge):
            sky_colors[y] = edge
        else:
            row = [scene.getpixel((x, y)) for x in range(scene.width)]
            sky_colors[y] = max(set(p for p in row if is_sky(p) and not is_cloud(p)), key=row.count)
    px = strip.load()
    for y in range(SKY_ROWS):
        for x in range(strip.width):
            if is_sky(px[x, y]) or is_cloud(px[x, y]):
                px[x, y] = sky_colors[y]
    sprites = cloud_sprites(scene)
    x = gaps[0]
    for i, gap in enumerate(gaps[1:] + gaps[:1]):
        cloud, mask, cy = sprites[i % len(sprites)]
        if x + cloud.width > strip.width:
            break
        top = max(0, cy - CLOUD_LIFT[i % len(CLOUD_LIFT)])
        for dy in range(cloud.height):
            for dx in range(cloud.width):
                # draw only over sky so treetops stay in front
                if mask.getpixel((dx, dy)) and top + dy < SKY_ROWS and is_sky(px[x + dx, top + dy]):
                    px[x + dx, top + dy] = cloud.getpixel((dx, dy))
        x += cloud.width + gap


# ---------- assembly ----------

def extend(logo, scene, width, rng):
    """The logo followed by `width` pixels of canal (clouds not yet placed)."""
    w, h = scene.size
    top, bottom = canal_rows(scene)
    canvas = Image.new("RGB", (w + width, h))
    canvas.paste(logo, (0, 0))
    quilt_band(canvas, scene, 0, top, w, rng, UPPER_SOURCES)
    canal_band(canvas, scene, top, bottom, w, rng)
    quilt_band(canvas, scene, bottom, h, w, rng, LOWER_SOURCES)
    # the first seam overlaps the logo's right edge: keep its lettering and sky exactly as drawn
    for x in range(w - OVERLAP, w):
        for y in range(h):
            p = logo.getpixel((x, y))
            if p != scene.getpixel((x, y)) or is_sky(p) or is_cloud(p):
                canvas.putpixel((x, y), p)
    return canvas


def loop(strip, start, width):
    """Cut strip[start:start+width] and seam its end into what preceded `start`, so it repeats cleanly."""
    end = start + width
    out = strip.crop((start, 0, end, strip.height))
    weights = [0 if y < SKY_ROWS else 1 for y in range(strip.height)]
    _, path = seam(columns(strip, end - OVERLAP, end, 0, strip.height),
                   columns(strip, start - OVERLAP, start, 0, strip.height), weights)
    for y in range(strip.height):
        for i in range(path[y], OVERLAP):
            out.putpixel((width - OVERLAP + i, y), strip.getpixel((start - OVERLAP + i, y)))
    return out


BAYER = [[0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
         [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
         [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
         [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21]]


def dither_fade(img, start, end, color):
    """Ordered-dither fade into a flat colour between columns start and end; crops at end."""
    px = img.load()
    for x in range(start, end):
        level = (x - start) / (end - start) * 64
        for y in range(img.height):
            if BAYER[y % 8][x % 8] < level:
                px[x, y] = color
    return img.crop((0, 0, end, img.height))


def main():
    logo = interior(MEDIA / "digitalrivers.png")
    scene = interior(MEDIA / "welcome.png")
    w = scene.width

    banner = extend(logo, scene, FADE[1], random.Random(SEED))
    canal = banner.crop((w, 0, banner.width, banner.height))
    place_clouds(canal, scene, BANNER_GAPS)
    banner.paste(canal, (w, 0))
    banner = dither_fade(banner, w + FADE[0], w + FADE[1], PAGE_BACKGROUND)
    banner.save(MEDIA / "banner.png", optimize=True)
    print(f"banner.png {banner.size}")

    strip = extend(logo, scene, TILE + 200, random.Random(SEED + 1))
    tile = loop(strip, w + 100, TILE)
    place_clouds(tile, scene, TILE_GAPS)
    tile.save(MEDIA / "canal-tile.png", optimize=True)
    print(f"canal-tile.png {tile.size}")


if __name__ == "__main__":
    main()
