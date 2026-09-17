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

The favicon set and the default social share image are generated once from the BK monogram and
committed to `static/`. Regenerate them (requires Pillow, not a project dependency) with:

```
python scripts/generate_brand_assets.py
```

## Develop

```
uv sync
uv run pytest
uv run ruff check
```

## Deploy

`.github/workflows/deploy.yml` lints, validates the content data, runs the tests, builds the
site, checks internal links, and deploys `_site/` to GitHub Pages on every push to `main`. A
schema error, a broken internal link, or an un-supplied `TO_BE_SUPPLIED` placeholder while
`launch: true` is set in `data/site.yaml` fails the workflow before anything deploys.

This repository's GitHub Pages source must be set to "GitHub Actions" (Settings > Pages) for the
workflow's deploy step to work. It is currently set to deploy from the `main` branch directly.

## Publish an episode

See the publishing workflow in the build specification.

## Licence

Code in this repository is MIT licensed. Decks, articles, and other episode content are not.
