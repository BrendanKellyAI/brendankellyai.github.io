"""Generate the favicon set and default social image from the BK monogram (spec 8.3, 9).

One-off asset generation, run manually and the output committed to static/.
Not part of the ongoing build, since these are static brand assets:

    python scripts/generate_brand_assets.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ICONS_DIR = ROOT / "static" / "icons"
SOCIAL_DIR = ROOT / "static" / "social"

NAVY = (11, 31, 58)
GREEN = (184, 224, 74)

FONT_PATH = Path("C:/Windows/Fonts/arialbd.ttf")


def _monogram_square(size: int, border: int) -> Image.Image:
    image = Image.new("RGB", (size, size), NAVY)
    draw = ImageDraw.Draw(image)
    if border:
        inset = border // 2
        box = [inset, inset, size - inset, size - inset]
        draw.rectangle(box, outline=GREEN, width=border)
    font = ImageFont.truetype(str(FONT_PATH), size=int(size * 0.46))
    text = "BK"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((size - text_width) / 2 - bbox[0], (size - text_height) / 2 - bbox[1])
    draw.text(position, text, font=font, fill=GREEN)
    return image


def write_favicon_ico() -> None:
    base = _monogram_square(256, border=0)
    sizes = [(16, 16), (32, 32), (48, 48)]
    base.save(ICONS_DIR / "favicon.ico", sizes=sizes)


def write_apple_touch_icon() -> None:
    image = _monogram_square(180, border=8)
    image.save(ICONS_DIR / "apple-touch-icon.png")


def write_favicon_svg() -> None:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="8" fill="rgb{NAVY}"/>
  <text x="32" y="42" font-family="Arial, sans-serif" font-weight="700" font-size="28"
        text-anchor="middle" fill="rgb{GREEN}">BK</text>
</svg>
"""
    (ICONS_DIR / "favicon.svg").write_text(svg, encoding="utf-8")


def write_default_og_image() -> None:
    width, height = 1200, 627
    image = Image.new("RGB", (width, height), NAVY)
    draw = ImageDraw.Draw(image)

    monogram_size = 220
    monogram = _monogram_square(monogram_size, border=6)
    monogram_x = (width - monogram_size) // 2
    monogram_y = 120
    image.paste(monogram, (monogram_x, monogram_y))

    name_font = ImageFont.truetype(str(FONT_PATH), size=64)
    descriptor_font = ImageFont.truetype(str(FONT_PATH), size=40)

    name = "Brendan Kelly"
    name_bbox = draw.textbbox((0, 0), name, font=name_font)
    name_width = name_bbox[2] - name_bbox[0]
    draw.text(((width - name_width) / 2, 400), name, font=name_font, fill=(255, 255, 255))

    descriptor = "Applied AI"
    descriptor_bbox = draw.textbbox((0, 0), descriptor, font=descriptor_font)
    descriptor_width = descriptor_bbox[2] - descriptor_bbox[0]
    descriptor_position = ((width - descriptor_width) / 2, 480)
    draw.text(descriptor_position, descriptor, font=descriptor_font, fill=(201, 211, 224))

    image.save(SOCIAL_DIR / "default-og.png")


def main() -> None:
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    SOCIAL_DIR.mkdir(parents=True, exist_ok=True)
    write_favicon_ico()
    write_apple_touch_icon()
    write_favicon_svg()
    write_default_og_image()
    print(f"Wrote favicon.ico, apple-touch-icon.png, favicon.svg to {ICONS_DIR}")
    print(f"Wrote default-og.png to {SOCIAL_DIR}")


if __name__ == "__main__":
    main()
