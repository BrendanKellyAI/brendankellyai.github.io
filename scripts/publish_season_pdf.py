"""Publish a season's combined PDF (every lesson in one file) and link it from the site.

    uv run python scripts/publish_season_pdf.py S1 "C:/path/to/AppliedAI-Season-1-Combined.pdf"

The PDF is large, so it is not committed to the site. Instead this uploads it to a GitHub
release named season-<n> on this repository (creating the release if needed, replacing the file
if it is already there), then records its download link, page count, and size on the season in
data/seasons.yaml. Commit that change and push to main to show the download on the site.

Needs the GitHub CLI (gh), signed in with permission to create releases.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pypdfium2 as pdfium
import yaml

ROOT = Path(__file__).resolve().parents[1]
SEASONS_FILE = ROOT / "data" / "seasons.yaml"
REPO = "BrendanKellyAI/brendankellyai.github.io"


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=True, capture_output=True, text=True)


def _release_exists(tag: str) -> bool:
    result = subprocess.run(
        ["gh", "release", "view", tag, "--repo", REPO], capture_output=True, text=True
    )
    return result.returncode == 0


def _set_season_fields(code: str, url: str, pages: int, size_mb: float) -> None:
    """Add or replace the pdf_* lines under one season, keeping the file's layout and comments."""
    text = SEASONS_FILE.read_text(encoding="utf-8")
    blocks = re.split(r"(?m)^(?=- code: )", text)
    for index, block in enumerate(blocks):
        if re.match(rf"- code: {re.escape(code)}\s*$", block.splitlines()[0] if block else ""):
            lines = block.rstrip("\n").splitlines()
            lines = [line for line in lines if not line.startswith("  pdf_")]
            lines += [
                f"  pdf_url: {url}",
                f"  pdf_pages: {pages}",
                f"  pdf_size_mb: {size_mb}",
            ]
            blocks[index] = "\n".join(lines) + ("\n\n" if index < len(blocks) - 1 else "\n")
            SEASONS_FILE.write_text("".join(blocks), encoding="utf-8")
            return
    raise SystemExit(f"Season {code} not found in {SEASONS_FILE}")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 1
    code, pdf = argv[0].upper(), Path(argv[1])
    seasons = {s["code"]: s for s in yaml.safe_load(SEASONS_FILE.read_text(encoding="utf-8"))}
    if code not in seasons:
        raise SystemExit(f"Unknown season {code}; expected one of {', '.join(seasons)}")
    if not pdf.is_file():
        raise SystemExit(f"No such file: {pdf}")
    season = seasons[code]

    document = pdfium.PdfDocument(pdf)
    pages = len(document)
    document.close()
    size_mb = round(pdf.stat().st_size / (1024 * 1024), 1)

    number = season["number"]
    tag = f"season-{number}"
    asset = f"applied-ai-season-{number}-{season['slug']}.pdf"
    title = f"Season {number}: {season['title']}, every lesson in one PDF"

    with tempfile.TemporaryDirectory() as folder:
        upload = Path(folder) / asset
        shutil.copy2(pdf, upload)
        if _release_exists(tag):
            _run("gh", "release", "upload", tag, str(upload), "--clobber", "--repo", REPO)
        else:
            notes = (
                f"All {pages} slides of Season {number}, {season['title']}, in one PDF, for "
                "reading the season start to finish. Linked from the season page on "
                "https://brendankellyai.github.io."
            )
            _run(
                "gh", "release", "create", tag, str(upload), "--repo", REPO,
                "--title", title, "--notes", notes, "--latest=false",
            )

    url = f"https://github.com/{REPO}/releases/download/{tag}/{asset}"
    _set_season_fields(code, url, pages, size_mb)
    print(f"Uploaded {asset} ({pages} pages, {size_mb} MB) to release {tag}.")
    print(f"Updated {SEASONS_FILE.relative_to(ROOT)}; commit it and push to main to publish.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
