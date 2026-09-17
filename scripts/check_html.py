"""Validate every rendered HTML page against the W3C Nu Html Checker.

Manual dev tool for Phase 3 verification. Not wired into pytest, since it
needs network access. Run after `uv run python -m hub.build`:

    uv run python scripts/check_html.py
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "_site"
VALIDATOR_URL = "https://validator.w3.org/nu/?out=json"


def validate_file(path: Path) -> list[dict]:
    body = path.read_bytes()
    request = urllib.request.Request(
        VALIDATOR_URL,
        data=body,
        headers={
            "Content-Type": "text/html; charset=utf-8",
            "User-Agent": "brendankellyai-hub-build (html5 validation check)",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))
    return [msg for msg in result.get("messages", []) if msg.get("type") == "error"]


def main() -> int:
    html_files = sorted(SITE_DIR.rglob("*.html"))
    if not html_files:
        print(f"No HTML files found under {SITE_DIR}. Run the build first.", file=sys.stderr)
        return 1

    had_errors = False
    for path in html_files:
        errors = validate_file(path)
        relative = path.relative_to(SITE_DIR)
        if errors:
            had_errors = True
            print(f"FAIL {relative}")
            for error in errors:
                print(f"  line {error.get('lastLine')}: {error.get('message')}")
        else:
            print(f"OK   {relative}")

    return 1 if had_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
