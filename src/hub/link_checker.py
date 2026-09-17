"""Check that every internal link in the built site resolves to a real file (spec phase 5).

External links (LinkedIn, GitHub, and so on) are out of scope: this only checks
links within the site itself, matching the build spec's "internal link checker".
"""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

from hub.build import OUTPUT_DIR

LINK_ATTRS = {
    "a": "href",
    "link": "href",
    "img": "src",
    "script": "src",
}


class _LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_name = LINK_ATTRS.get(tag)
        if attr_name is None:
            return
        for name, value in attrs:
            if name == attr_name and value:
                self.links.append(value)


def extract_links(html: str) -> list[str]:
    parser = _LinkExtractor()
    parser.feed(html)
    return parser.links


def _is_internal(link: str) -> bool:
    if link.startswith("#") or link.startswith("mailto:"):
        return False
    parsed = urlsplit(link)
    return not parsed.scheme and not parsed.netloc and link.startswith("/")


def _resolve(output_dir: Path, link: str) -> Path:
    path = urlsplit(link).path
    if path.endswith("/"):
        return output_dir / path.lstrip("/") / "index.html"
    return output_dir / path.lstrip("/")


def check_links(output_dir: Path = OUTPUT_DIR) -> list[str]:
    broken = []
    for html_file in sorted(output_dir.rglob("*.html")):
        html = html_file.read_text(encoding="utf-8")
        for link in extract_links(html):
            if not _is_internal(link):
                continue
            if not _resolve(output_dir, link).exists():
                broken.append(f"{html_file.relative_to(output_dir)}: broken link {link}")
    return broken


def main(output_dir: Path = OUTPUT_DIR) -> int:
    broken = check_links(output_dir)
    if broken:
        for issue in broken:
            print(f"error: {issue}", file=sys.stderr)
        print(f"{len(broken)} broken internal link(s) found.", file=sys.stderr)
        return 1
    print("No broken internal links found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
