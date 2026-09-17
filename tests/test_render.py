from datetime import date

from hub.loaders import DATA_DIR
from hub.models import Episode, Season
from hub.render import (
    adjacent,
    episode_url_slug,
    format_date,
    format_label,
    load_site_data,
    make_environment,
    season_url_slug,
)
from hub.structured_data import creative_work_jsonld

SEASON_S1 = Season.model_validate(
    {
        "code": "S1",
        "number": 1,
        "slug": "how-llms-work",
        "title": "How LLMs work",
        "type": "technical",
        "description": "What a large language model does.",
    }
)


def test_episode_url_slug():
    episode = Episode.model_validate(
        {
            "code": "S1 E2",
            "season": "S1",
            "number": 2,
            "slug": "tokens",
            "title": "Tokens",
            "format": "explainer",
        }
    )
    assert episode_url_slug(episode) == "s1-e2-tokens"


def test_season_url_slug():
    assert season_url_slug(SEASON_S1) == "s1-how-llms-work"


def test_format_label():
    assert format_label("field_note") == "Field note"


def test_format_date_strips_leading_zero():
    assert format_date(date(2026, 10, 6)) == "6 October 2026"


def test_adjacent_finds_neighbours():
    items = ["a", "b", "c"]
    assert adjacent(items, "a") == (None, "b")
    assert adjacent(items, "b") == ("a", "c")
    assert adjacent(items, "c") == ("b", None)


def test_load_site_data_groups_episodes_by_season():
    data = load_site_data(DATA_DIR)
    assert len(data.seasons) == 15
    assert len(data.episodes_for("S1")) == 13
    assert data.episodes_for("S2") == []
    assert data.latest_episode is None
    assert data.published_episodes == []


def test_environment_renders_episode_page_for_a_published_episode():
    season = SEASON_S1
    episode = Episode.model_validate(
        {
            "code": "S1 E2",
            "season": "S1",
            "number": 2,
            "slug": "tokens",
            "title": "Tokens",
            "format": "explainer",
            "status": "published",
            "publish_date": "2026-10-06",
            "summary": "Tokens are the unit behind every cost and latency figure.",
            "decision_rule": "Measure cost, latency, and limits in tokens.",
            "linkedin_url": "https://www.linkedin.com/posts/example",
            "deck_pdf": "bk-s1-e2-tokens-v1.pdf",
            "cover_image": "cover.png",
            "og_image": "og.png",
            "lab_path": "episodes/s1-e2-tokens",
        }
    )
    site = load_site_data(DATA_DIR).site
    env = make_environment()
    template = env.get_template("episode.html")
    html = template.render(
        site=site,
        season=season,
        episode=episode,
        previous_episode=None,
        next_episode=None,
        active_nav="seasons",
        social_image_path="/static/episodes/s1-e2-tokens/og.png",
        work_jsonld=creative_work_jsonld(site, episode, season),
    )
    assert "Tokens" in html
    assert "Decision rule" in html
    assert "Measure cost, latency, and limits in tokens." in html
    assert "/static/episodes/s1-e2-tokens/bk-s1-e2-tokens-v1.pdf" in html
    assert "/static/episodes/s1-e2-tokens/cover.png" in html
    assert "episodes/s1-e2-tokens" in html


def test_environment_renders_playbook_slides():
    episode = Episode.model_validate(
        {
            "code": "S1 E3",
            "season": "S1",
            "number": 3,
            "slug": "playbook-example",
            "title": "A playbook",
            "format": "playbook",
            "status": "published",
            "publish_date": "2026-10-06",
            "summary": "A one sentence summary of the playbook.",
            "decision_rule": "Follow the steps in order.",
            "linkedin_url": "https://www.linkedin.com/posts/example",
            "deck_pdf": "bk-s1-e3-playbook-example-v1.pdf",
            "cover_image": "cover.png",
            "og_image": "og.png",
            "playbook_slides": [{"file": "slide1.png", "alt": "Step one of the playbook."}],
        }
    )
    site = load_site_data(DATA_DIR).site
    env = make_environment()
    template = env.get_template("episode.html")
    html = template.render(
        site=site,
        season=SEASON_S1,
        episode=episode,
        previous_episode=None,
        next_episode=None,
        active_nav="seasons",
        social_image_path="/static/episodes/s1-e3-playbook-example/og.png",
        work_jsonld=creative_work_jsonld(site, episode, SEASON_S1),
    )
    assert "Step one of the playbook." in html
    assert "slide1.png" in html


def test_environment_renders_field_note_links():
    episode = Episode.model_validate(
        {
            "code": "S1 E7",
            "season": "S1",
            "number": 7,
            "slug": "lost-in-the-middle",
            "title": "Field note: lost in the middle",
            "format": "field_note",
            "status": "published",
            "publish_date": "2026-11-01",
            "summary": "A one sentence field note summary.",
            "decision_rule": "Trust the middle of long context less than the ends.",
            "linkedin_url": "https://www.linkedin.com/posts/example",
            "deck_pdf": "bk-s1-e7-lost-in-the-middle-v1.pdf",
            "cover_image": "cover.png",
            "og_image": "og.png",
            "article_url": "https://www.linkedin.com/pulse/example",
            "lab_path": "field-notes/s1-e7-lost-in-the-middle",
        }
    )
    site = load_site_data(DATA_DIR).site
    env = make_environment()
    template = env.get_template("episode.html")
    html = template.render(
        site=site,
        season=SEASON_S1,
        episode=episode,
        previous_episode=None,
        next_episode=None,
        active_nav="seasons",
        social_image_path="/static/episodes/s1-e7-lost-in-the-middle/og.png",
        work_jsonld=creative_work_jsonld(site, episode, SEASON_S1),
    )
    assert "LinkedIn article" in html
    assert "Experiment folder in applied-ai-lab" in html


def test_environment_renders_s0_episode_without_season():
    episode = Episode.model_validate(
        {
            "code": "S0",
            "season": None,
            "number": 0,
            "slug": "series-intro",
            "title": "Applied AI: the series",
            "format": "series_intro",
            "status": "published",
            "publish_date": "2026-09-20",
            "summary": "The introduction to the applied AI series.",
            "linkedin_url": "https://www.linkedin.com/posts/example",
            "deck_pdf": "bk-s0-series-intro-v1.pdf",
            "cover_image": "cover.png",
            "og_image": "og.png",
        }
    )
    site = load_site_data(DATA_DIR).site
    env = make_environment()
    template = env.get_template("episode.html")
    html = template.render(
        site=site,
        season=None,
        episode=episode,
        previous_episode=None,
        next_episode=None,
        active_nav="seasons",
        social_image_path="/static/episodes/s0-series-intro/og.png",
        work_jsonld=creative_work_jsonld(site, episode, None),
    )
    assert "Applied AI: the series" in html
    assert "Decision rule" not in html
