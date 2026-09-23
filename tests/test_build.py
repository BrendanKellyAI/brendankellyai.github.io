import pytest

from hub.build import build
from hub.loaders import DATA_DIR

SITE_YAML = """\
name: Brendan Kelly
descriptor: Applied AI
description: A series on applied AI.
base_url: https://brendankellyai.github.io
linkedin_profile_url: https://www.linkedin.com/in/brendan-kelly-irl
newsletter_name: Applied AI with Brendan Kelly
newsletter_url: https://example.com/newsletter
lab_repo_url: https://github.com/BrendanKellyAI/applied-ai-lab
about_bio: A short biography.
current_season: S1
launch: false
"""

SEASONS_YAML = """\
- code: S1
  number: 1
  slug: how-llms-work
  title: How LLMs work
  type: technical
  description: What a large language model does.
"""

S0_EPISODE_YAML = """\
code: S0
season: null
number: 0
slug: series-intro
title: "Applied AI: the series"
format: series_intro
status: published
publish_date: 2026-09-20
summary: The introduction to the applied AI series.
linkedin_url: https://www.linkedin.com/posts/example
deck_pdf: bk-s0-series-intro-v1.pdf
cover_image: cover.png
og_image: og.png
"""

S1_E2_EPISODE_YAML = """\
code: "S1 E2"
season: S1
number: 2
slug: tokens
title: Tokens
format: explainer
status: published
publish_date: 2026-10-06
summary: Tokens are the unit behind every cost and latency figure.
decision_rule: Measure cost, latency, and limits in tokens.
linkedin_url: https://www.linkedin.com/posts/example
deck_pdf: bk-s1-e2-tokens-v1.pdf
cover_image: cover.png
og_image: og.png
"""


def _make_episode_static_files(static_dir, episode_dir_name, deck_filename):
    episode_dir = static_dir / "episodes" / episode_dir_name
    episode_dir.mkdir(parents=True)
    (episode_dir / deck_filename).write_bytes(b"%PDF-1.4 fake")
    (episode_dir / "cover.png").write_bytes(b"cover")
    (episode_dir / "og.png").write_bytes(b"og")


@pytest.fixture
def fixture_project(tmp_path):
    data_dir = tmp_path / "data"
    (data_dir / "episodes").mkdir(parents=True)
    (data_dir / "site.yaml").write_text(SITE_YAML, encoding="utf-8")
    (data_dir / "seasons.yaml").write_text(SEASONS_YAML, encoding="utf-8")
    (data_dir / "episodes" / "s0-series-intro.yaml").write_text(S0_EPISODE_YAML, encoding="utf-8")
    (data_dir / "episodes" / "s1-e2-tokens.yaml").write_text(S1_E2_EPISODE_YAML, encoding="utf-8")

    static_dir = tmp_path / "static"
    (static_dir / "css").mkdir(parents=True)
    (static_dir / "css" / "style.css").write_text("body {}", encoding="utf-8")
    (static_dir / "icons").mkdir(parents=True)
    for filename in ("favicon.ico", "favicon.svg", "apple-touch-icon.png"):
        (static_dir / "icons" / filename).write_bytes(b"fake icon")
    (static_dir / "social").mkdir(parents=True)
    (static_dir / "social" / "default-og.png").write_bytes(b"fake og image")
    _make_episode_static_files(static_dir, "s0-series-intro", "bk-s0-series-intro-v1.pdf")
    _make_episode_static_files(static_dir, "s1-e2-tokens", "bk-s1-e2-tokens-v1.pdf")

    return data_dir, static_dir


def test_build_writes_every_page_for_seed_data(tmp_path):
    output_dir = tmp_path / "_site"
    build(output_dir=output_dir)

    assert (output_dir / "index.html").exists()
    assert (output_dir / "seasons" / "index.html").exists()
    assert (output_dir / "seasons" / "s1-how-llms-work" / "index.html").exists()
    assert (output_dir / "about" / "index.html").exists()
    assert (output_dir / "404.html").exists()
    assert (output_dir / "static" / "css" / "style.css").exists()
    assert (output_dir / "static" / "fonts" / "inter-tight").is_dir()

    season_dirs = list((output_dir / "seasons").iterdir())
    assert len([p for p in season_dirs if p.is_dir()]) == 15

    assert not (output_dir / "episodes").exists()

    assert (output_dir / "sitemap.xml").exists()
    assert (output_dir / "robots.txt").exists()
    assert (output_dir / "feed.xml").exists()
    assert (output_dir / "favicon.ico").exists()
    assert (output_dir / "favicon.svg").exists()
    assert (output_dir / "apple-touch-icon.png").exists()


def test_build_never_emits_an_empty_href(tmp_path):
    # Regression test: a blank (not TO_BE_SUPPLIED) site.yaml field, such as
    # newsletter_url: "", must not render as <a href="">, which is a broken
    # link. This covers the real seed data as it changes over time.
    output_dir = tmp_path / "_site"
    build(output_dir=output_dir)

    for html_file in output_dir.rglob("*.html"):
        assert 'href=""' not in html_file.read_text(encoding="utf-8"), html_file

    sitemap_xml = (output_dir / "sitemap.xml").read_text(encoding="utf-8")
    assert "https://brendankellyai.github.io/seasons/s1-how-llms-work/" in sitemap_xml
    assert "404" not in sitemap_xml

    robots_txt = (output_dir / "robots.txt").read_text(encoding="utf-8")
    assert "Sitemap: https://brendankellyai.github.io/sitemap.xml" in robots_txt

    feed_xml = (output_dir / "feed.xml").read_text(encoding="utf-8")
    assert "<feed xmlns=" in feed_xml

    about_html = (output_dir / "about" / "index.html").read_text(encoding="utf-8")
    assert '"@type": "Person"' in about_html

    seasons_html = (output_dir / "seasons" / "index.html").read_text(encoding="utf-8")
    assert '"@type": "CreativeWorkSeries"' in seasons_html

    not_found_html = (output_dir / "404.html").read_text(encoding="utf-8")
    assert 'name="robots" content="noindex"' in not_found_html


def test_build_writes_pages_for_published_episodes(fixture_project, tmp_path):
    data_dir, static_dir = fixture_project
    output_dir = tmp_path / "_site"

    build(output_dir=output_dir, data_dir=data_dir, static_source_dir=static_dir)

    s0_page = output_dir / "episodes" / "s0-series-intro" / "index.html"
    s1e2_page = output_dir / "episodes" / "s1-e2-tokens" / "index.html"
    assert s0_page.exists()
    assert s1e2_page.exists()

    home_html = (output_dir / "index.html").read_text(encoding="utf-8")
    assert "Tokens" in home_html

    episode_html = s1e2_page.read_text(encoding="utf-8")
    assert '"@type": "CreativeWork"' in episode_html
    assert 'property="og:type" content="article"' in episode_html

    feed_xml = (output_dir / "feed.xml").read_text(encoding="utf-8")
    assert "Tokens" in feed_xml
    assert "<entry>" in feed_xml

    s1_page_html = (output_dir / "seasons" / "s1-how-llms-work" / "index.html").read_text(
        encoding="utf-8"
    )
    assert "Coming soon" not in s1_page_html
    assert "Tokens" in s1_page_html


def test_build_fails_on_validation_error(tmp_path):
    data_dir = tmp_path / "data"
    (data_dir / "episodes").mkdir(parents=True)
    (data_dir / "site.yaml").write_text(
        SITE_YAML.replace("current_season: S1", "current_season: S99"), encoding="utf-8"
    )
    (data_dir / "seasons.yaml").write_text(SEASONS_YAML, encoding="utf-8")

    static_dir = tmp_path / "static"
    static_dir.mkdir()

    with pytest.raises(SystemExit):
        build(output_dir=tmp_path / "_site", data_dir=data_dir, static_source_dir=static_dir)


def test_data_dir_default_matches_real_project_data():
    assert DATA_DIR.name == "data"
