from hub.discovery import entry_timestamp, feed_episodes, feed_updated, sitemap_paths
from hub.loaders import DATA_DIR
from hub.models import Episode
from hub.render import SiteData, load_site_data

SEED_DATA = load_site_data(DATA_DIR)


def _published(code, slug, number, publish_date):
    return Episode.model_validate(
        {
            "code": code,
            "season": "S1",
            "number": number,
            "slug": slug,
            "title": slug,
            "format": "explainer",
            "status": "published",
            "publish_date": publish_date,
            "summary": f"Summary for {slug}.",
            "linkedin_url": "https://www.linkedin.com/posts/example",
            "deck_pdf": f"bk-{code.lower().replace(' ', '-')}-{slug}-v1.pdf",
            "cover_image": "cover.png",
            "og_image": "og.png",
        }
    )


def test_sitemap_paths_covers_home_seasons_and_about_but_not_404():
    paths = sitemap_paths(SEED_DATA)
    assert "/" in paths
    assert "/seasons/" in paths
    assert "/about/" in paths
    assert "/seasons/s1-how-llms-work/" in paths
    assert len(paths) == 3 + 15
    assert "/404.html" not in paths


def test_sitemap_paths_includes_published_episodes():
    published = _published("S1 E2", "tokens", 2, "2026-10-06")
    data = SiteData(
        site=SEED_DATA.site,
        seasons=SEED_DATA.seasons,
        episodes_by_season={"S1": [published]},
        all_episodes=[published],
    )
    paths = sitemap_paths(data)
    assert "/episodes/s1-e2-tokens/" in paths


def test_feed_episodes_orders_newest_first():
    older = _published("S1 E2", "tokens", 2, "2026-10-06")
    newer = _published("S1 E3", "embeddings", 3, "2026-11-01")
    data = SiteData(
        site=SEED_DATA.site,
        seasons=SEED_DATA.seasons,
        episodes_by_season={"S1": [older, newer]},
        all_episodes=[older, newer],
    )
    ordered = feed_episodes(data)
    assert ordered == [newer, older]


def test_feed_updated_uses_latest_publish_date():
    older = _published("S1 E2", "tokens", 2, "2026-10-06")
    newer = _published("S1 E3", "embeddings", 3, "2026-11-01")
    data = SiteData(
        site=SEED_DATA.site,
        seasons=SEED_DATA.seasons,
        episodes_by_season={"S1": [older, newer]},
        all_episodes=[older, newer],
    )
    assert feed_updated(data) == "2026-11-01T00:00:00+00:00"


def test_feed_updated_falls_back_to_today_with_no_published_episodes():
    updated = feed_updated(SEED_DATA)
    assert updated.endswith("T00:00:00+00:00")


def test_entry_timestamp_format():
    episode = _published("S1 E2", "tokens", 2, "2026-10-06")
    assert entry_timestamp(episode) == "2026-10-06T00:00:00+00:00"
