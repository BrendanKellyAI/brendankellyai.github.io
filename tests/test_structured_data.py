from hub.loaders import DATA_DIR
from hub.models import Episode, Season, SiteSettings
from hub.render import load_site_data
from hub.structured_data import creative_work_jsonld, creative_work_series_jsonld, person_jsonld

SITE = load_site_data(DATA_DIR).site

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

PUBLISHED_EPISODE = Episode.model_validate(
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
        "linkedin_url": "https://www.linkedin.com/posts/example",
        "deck_pdf": "bk-s1-e2-tokens-v1.pdf",
        "cover_image": "cover.png",
        "og_image": "og.png",
    }
)


def test_person_jsonld_shape():
    data = person_jsonld(SITE)
    assert data["@type"] == "Person"
    assert data["name"] == SITE.name
    assert data["url"] == f"{SITE.base_url}/about/"
    assert data["sameAs"] == [SITE.linkedin_profile_url]


def test_creative_work_series_jsonld_omits_unsupplied_description():
    site = SiteSettings.model_validate({**SITE.model_dump(), "description": "TO_BE_SUPPLIED"})
    data = creative_work_series_jsonld(site)
    assert data["@type"] == "CreativeWorkSeries"
    assert "description" not in data


def test_creative_work_series_jsonld_includes_supplied_description():
    site = SiteSettings.model_validate({**SITE.model_dump(), "description": "A real description."})
    data = creative_work_series_jsonld(site)
    assert data["description"] == "A real description."


def test_creative_work_jsonld_for_published_episode():
    data = creative_work_jsonld(SITE, PUBLISHED_EPISODE, SEASON_S1)
    assert data["@type"] == "CreativeWork"
    assert data["name"] == "Tokens"
    assert data["datePublished"] == "2026-10-06"
    assert data["image"] == f"{SITE.base_url}/static/episodes/s1-e2-tokens/og.png"
    assert data["isPartOf"]["name"] == "How LLMs work"


def test_creative_work_jsonld_without_season_uses_descriptor():
    data = creative_work_jsonld(SITE, PUBLISHED_EPISODE, None)
    assert data["isPartOf"]["name"] == SITE.descriptor
