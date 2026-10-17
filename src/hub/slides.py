"""Render each published deck PDF into slide images for the on-site lesson player.

Images are cached by PDF file name. Deck names carry a version (bk-s1-e2-tokens-v4.pdf), so a
new deck version is a new name and is rendered fresh; an unchanged deck is never re-rendered.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pypdfium2 as pdfium

from hub.loaders import ROOT

CACHE_DIR = ROOT / ".cache" / "slides"
SLIDE_WIDTH_PX = 1080
WEBP_QUALITY = 82
_DONE_MARKER = ".complete"


def render_slides(pdf_path: Path, cache_dir: Path = CACHE_DIR) -> list[Path]:
    """Slide images for one deck, rendered into the cache on first use, in page order."""
    target = cache_dir / pdf_path.stem
    marker = target / _DONE_MARKER
    if marker.exists():
        return sorted(target.glob("*.webp"))

    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    pdf = pdfium.PdfDocument(pdf_path)
    try:
        for index in range(len(pdf)):
            page = pdf[index]
            scale = SLIDE_WIDTH_PX / page.get_width()
            image = page.render(scale=scale).to_pil()
            image.save(target / f"{index + 1:02d}.webp", "WEBP", quality=WEBP_QUALITY)
            page.close()
    finally:
        pdf.close()
    marker.write_text("ok", encoding="utf-8")
    return sorted(target.glob("*.webp"))


def copy_slides(images: list[Path], output_dir: Path) -> None:
    """Copy rendered slide images into the built site."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for image in images:
        shutil.copy2(image, output_dir / image.name)
