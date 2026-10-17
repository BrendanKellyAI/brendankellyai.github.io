# brendankellyai.github.io

Applied AI, a course by Brendan Kelly: short visual lessons on how AI works in production and
how to lead it, in 15 seasons that interleave technical and leadership topics. Each lesson's
deck plays on the site slide by slide, and a course map shows how lessons and ideas connect.

Site: https://brendankellyai.github.io

This repository holds the static site generator and content data for the course site. Episode code
and experiments live in the related repository, [applied-ai-lab](https://github.com/BrendanKellyAI/applied-ai-lab).

## Requirements

- Python 3.12 or later
- [uv](https://docs.astral.sh/uv/)

## Build

```
uv run python -m hub.build
```

Output is written to `_site/` and is not committed. To preview it locally:

```
python -m http.server 8000 -d _site
```

Slide images are rendered from each deck PDF during the build and cached in `.cache/slides/`
(not committed). Deck file names carry a version, so a new version renders fresh and an unchanged
deck is never rendered twice. The first build takes about 40 seconds; later builds take a few.

To check the built pages against the W3C Nu Html Checker (requires network access, so it is not
part of the test suite):

```
uv run python scripts/check_html.py
```

The favicon set and the default social share image are generated once from the BK monogram and
committed to `static/`. Regenerate them with:

```
uv run python scripts/generate_brand_assets.py
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

Every episode already has a file in `data/episodes/`, with `status: planned`. To publish one:

1. Add the files to `static/episodes/<code>-<slug>/`, for example `static/episodes/s1-e4-attention/`:
   - the deck, named `bk-<code>-<slug>-v<number>.pdf` (for example `bk-s1-e4-attention-v1.pdf`)
   - `cover.png`, the first slide, used on lesson cards
   - `og.png`, the 1200 by 627 link preview image
2. In the episode's YAML file, set `status: published` and fill in `publish_date`, `summary`
   (one sentence, 30 words at most), `decision_rule`, `linkedin_url`, `deck_pdf`,
   `cover_image`, `og_image`, and `lab_path`.
3. Optional: add `slide_sections`, one tag per slide, to name the chapters in the lesson
   player. The tags are listed under `sections` in `data/course-map.yaml`:

   ```yaml
   slide_sections: [cover, why, model, concepts, concepts, data, data, eng, breaks, eng, eng, practice, leaders, rule, map]
   ```

   Without it, the player still works and shows a single "Slides" chapter.
4. Optional: link the episode into the course map by adding its code (for example `s1-e4`) to
   the `links` of a concept in `data/course-map.yaml`.
5. Run `uv run python -m hub.validation`, then `uv run python -m hub.build` and preview it.
6. Push to `main`. The workflow builds and deploys the site.

To fix a deck after publishing, add the corrected PDF with the next version number, point
`deck_pdf` at it, and delete the old file.

## Licence

Code in this repository is MIT licensed. Decks, articles, and other episode content are not.
