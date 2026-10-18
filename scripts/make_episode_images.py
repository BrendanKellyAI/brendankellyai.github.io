"""Make an episode's cover.png and og.png from the first slide of its deck.

    uv run python scripts/make_episode_images.py static/episodes/<folder>/<deck>.pdf

cover.png is the first slide at 1080 by 1350. og.png is the 1200 by 627 link preview, laid out
like the existing ones: the deck's green band on top, its title block in the middle, and its
footer at the bottom. All three pieces are cut from the rendered slide, so the lettering is the
deck's own. Both files are written next to the PDF.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image

COVER_WIDTH = 1080
OG_SIZE = (1200, 627)
OG_BAND_HEIGHT = 100  # the green band on existing og images
OG_FOOTER_RULE_Y = 530  # where the footer rule sits on existing og images
OG_SIDE_MARGIN = 64
BLOCK_GAP = 24  # rows of plain background that separate two blocks of content
BAND_PADDING = 8  # green kept above and below the monogram in the og band
EDGE_ROWS = 6  # rows at the top and bottom of the slide's band that are never content


def _render_first_slide(pdf_path: Path, width: int) -> Image.Image:
    pdf = pdfium.PdfDocument(pdf_path)
    try:
        page = pdf[0]
        return page.render(scale=width / page.get_width()).to_pil().convert("RGB")
    finally:
        pdf.close()


def _differs(pixel: tuple[int, int, int], background: tuple[int, int, int]) -> bool:
    return sum(abs(a - b) for a, b in zip(pixel, background, strict=True)) > 60


def _content_rows(image: Image.Image, background: tuple[int, int, int]) -> list[bool]:
    """For each row, whether anything other than the slide background is drawn on it."""
    width, height = image.size
    pixels = image.load()
    rows = []
    for y in range(height):
        rows.append(any(_differs(pixels[x, y], background) for x in range(0, width, 2)))
    return rows


def _blocks(rows: list[bool], start: int, end: int) -> list[tuple[int, int]]:
    """Runs of content rows between start and end, merging runs closer than BLOCK_GAP."""
    blocks: list[list[int]] = []
    for y in range(start, end):
        if not rows[y]:
            continue
        if blocks and y - blocks[-1][1] <= BLOCK_GAP:
            blocks[-1][1] = y
        else:
            blocks.append([y, y])
    return [(top, bottom + 1) for top, bottom in blocks]


def _paste_band(og: Image.Image, slide: Image.Image, band_bottom: int) -> None:
    """Rebuild the green band at og height from the slide's own band elements.

    The episode code (left) and the BK monogram (right) are cut out separately, shrunk only
    if taller than the og band allows, and placed at their original left and right margins.
    Decks draw the monogram at slightly different sizes, so a fixed strip would clip it.
    """
    width = slide.width
    green = slide.getpixel((5, 5))
    og.paste(Image.new("RGB", (og.width, OG_BAND_HEIGHT), green), (0, 0))
    pixels = slide.load()
    # Skip the band's edge rows, where anti-aliasing against the slide below looks like content.
    inner = range(EDGE_ROWS, band_bottom - EDGE_ROWS)
    columns = [any(_differs(pixels[x, y], green) for y in inner[::2]) for x in range(width)]
    for left, right in _blocks(columns, 0, width):
        rows = [y for y in inner if any(_differs(pixels[x, y], green) for x in range(left, right))]
        element = slide.crop((left, rows[0], right, rows[-1] + 1))
        room = OG_BAND_HEIGHT - 2 * BAND_PADDING
        if element.height > room:
            scale = room / element.height
            element = element.resize((max(1, int(element.width * scale)), room), Image.LANCZOS)
        x = left if left < width // 2 else right - element.width
        og.paste(element, (x, (OG_BAND_HEIGHT - element.height) // 2))


def make_og(slide: Image.Image) -> Image.Image:
    width, height = slide.size
    background = slide.getpixel((5, height // 2))  # the left margin is always plain slide
    rows = _content_rows(slide, background)

    band_bottom = next(y for y in range(height) if not _differs(slide.getpixel((5, y)), background))
    content = _blocks(rows, band_bottom, height)
    footer_top = content[-2][0]  # the footer rule, then the name line
    title_top, title_bottom = content[0][0], content[-3][1]

    og = Image.new("RGB", OG_SIZE, background)
    _paste_band(og, slide, band_bottom)

    footer = slide.crop((0, footer_top, width, content[-1][1] + 8))
    og.paste(footer, (0, OG_FOOTER_RULE_Y))

    title = slide.crop((0, title_top, width, title_bottom))
    room = OG_FOOTER_RULE_Y - OG_BAND_HEIGHT - 2 * BLOCK_GAP
    if title.height > room:
        scale = room / title.height
        title = title.resize((int(width * scale), room), Image.LANCZOS)
        # Keep the left edge aligned with the band and footer text after shrinking.
        left = int(OG_SIDE_MARGIN * (1 - scale))
    else:
        left = 0
    top = OG_BAND_HEIGHT + (OG_FOOTER_RULE_Y - OG_BAND_HEIGHT - title.height) // 2
    og.paste(title, (left, top))
    return og


def main(pdf_paths: list[str]) -> int:
    if not pdf_paths:
        print(__doc__)
        return 1
    for name in pdf_paths:
        pdf_path = Path(name)
        cover = _render_first_slide(pdf_path, COVER_WIDTH)
        cover.save(pdf_path.parent / "cover.png", optimize=True)
        og = make_og(_render_first_slide(pdf_path, OG_SIZE[0]))
        og.save(pdf_path.parent / "og.png", optimize=True)
        print(f"wrote cover.png and og.png in {pdf_path.parent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
