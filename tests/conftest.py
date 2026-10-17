"""Shared test helpers."""

from pathlib import Path

from PIL import Image


def write_pdf(path: Path, pages: int = 2) -> None:
    """Write a small, real PDF with `pages` blank pages, so slide rendering can open it."""
    images = [Image.new("RGB", (80, 100), (11, 31, 58)) for _ in range(pages)]
    images[0].save(path, "PDF", save_all=True, append_images=images[1:])
