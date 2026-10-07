"""Remove white background and export navbar logo + favicon PNGs."""
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "images" / "logo and favicon.jpeg"
OUT_LOGO = ROOT / "images" / "academic-edge-logo.png"
OUT_FAVICON = ROOT / "images" / "favicon.png"
OUT_FAVICON_32 = ROOT / "images" / "favicon-32.png"


def is_background(r: int, g: int, b: int) -> bool:
    # Tolerant of JPEG compression; keeps interior whites (pen nib) enclosed by color.
    return r >= 232 and g >= 232 and b >= 232 and max(r, g, b) - min(r, g, b) <= 28


def remove_white_background(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    w, h = rgba.size
    pixels = rgba.load()
    bg = [[False] * w for _ in range(h)]

    q: deque[tuple[int, int]] = deque()
    for x in range(w):
        for y in (0, h - 1):
            if is_background(*pixels[x, y][:3]):
                bg[y][x] = True
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if not bg[y][x] and is_background(*pixels[x, y][:3]):
                bg[y][x] = True
                q.append((x, y))

    while q:
        x, y = q.popleft()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < w and 0 <= ny < h and not bg[ny][nx]:
                if is_background(*pixels[nx, ny][:3]):
                    bg[ny][nx] = True
                    q.append((nx, ny))

    for y in range(h):
        for x in range(w):
            if bg[y][x]:
                pixels[x, y] = (255, 255, 255, 0)

    return rgba


def trim_alpha(img: Image.Image, pad: int = 8) -> Image.Image:
    bbox = img.getbbox()
    if not bbox:
        return img
    left, top, right, bottom = bbox
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(img.width, right + pad)
    bottom = min(img.height, bottom + pad)
    return img.crop((left, top, right, bottom))


def make_favicon(logo: Image.Image, canvas_size: int = 512, icon_fill: float = 0.62) -> Image.Image:
    w, h = logo.size
    # Icon sits above the wordmark; use upper portion of trimmed art.
    icon_h = int(h * 0.56)
    icon = logo.crop((0, 0, w, icon_h))
    ibox = icon.getbbox()
    if ibox:
        icon = icon.crop(ibox)

    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    inset = max(0, int(canvas_size * 0.02))
    draw = ImageDraw.Draw(canvas)
    draw.ellipse(
        (inset, inset, canvas_size - inset - 1, canvas_size - inset - 1),
        fill=(255, 255, 255, 255),
    )

    target = int((canvas_size - 2 * inset) * icon_fill)
    iw, ih = icon.size
    scale = target / max(iw, ih)
    new_w = max(1, int(iw * scale))
    new_h = max(1, int(ih * scale))
    icon = icon.resize((new_w, new_h), Image.Resampling.LANCZOS)

    ox = (canvas_size - new_w) // 2
    oy = (canvas_size - new_h) // 2
    canvas.paste(icon, (ox, oy), icon)
    return canvas


def main() -> None:
    src = Image.open(SRC)
    logo = trim_alpha(remove_white_background(src), pad=10)
    logo.save(OUT_LOGO, "PNG", optimize=True)

    favicon = make_favicon(logo)
    favicon.save(OUT_FAVICON, "PNG", optimize=True)
    make_favicon(logo, canvas_size=32, icon_fill=0.62).save(OUT_FAVICON_32, "PNG", optimize=True)
    print(f"Wrote {OUT_LOGO.name}, {OUT_FAVICON.name}, {OUT_FAVICON_32.name}")


if __name__ == "__main__":
    main()
