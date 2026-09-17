# brendankellyai.github.io

Episode guide for Applied AI, a LinkedIn series by Brendan Kelly, structured like a TV series:
15 seasons of 12 episodes each, interleaving technical and leadership seasons.

Site: https://brendankellyai.github.io

This repository holds the static site generator and content data for the hub. Episode code
and experiments live in the related repository, [applied-ai-lab](https://github.com/BrendanKellyAI/applied-ai-lab).

## Requirements

- Python 3.12 or later
- [uv](https://docs.astral.sh/uv/)

## Build

```
uv run python -m hub.build
```

Output is written to `_site/` and is not committed.

To check the built pages against the W3C Nu Html Checker (requires network access, so it is not
part of the test suite):

```
uv run python scripts/check_html.py
```

## Develop

```
uv sync
uv run pytest
uv run ruff check
```

## Publish an episode

See the publishing workflow in the build specification.

## Licence

Code in this repository is MIT licensed. Decks, articles, and other episode content are not.
