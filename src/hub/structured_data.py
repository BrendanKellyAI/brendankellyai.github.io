"""JSON-LD structured data (build spec section 9): Person, CreativeWorkSeries, CreativeWork."""

from __future__ import annotations

from hub.models import Episode, Season, SiteSettings
from hub.render import episode_url_slug


def _absolute(site: SiteSettings, path: str) -> str:
    return site.base_url.rstrip("/") + path


def person_jsonld(site: SiteSettings) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": site.name,
        "url": _absolute(site, "/about/"),
        "sameAs": [site.linkedin_profile_url],
    }


def creative_work_series_jsonld(site: SiteSettings) -> dict:
    data = {
        "@context": "https://schema.org",
        "@type": "CreativeWorkSeries",
        "name": f"{site.name}: {site.descriptor}",
        "url": _absolute(site, "/seasons/"),
        "author": {"@type": "Person", "name": site.name},
    }
    if site.description != "TO_BE_SUPPLIED":
        data["description"] = site.description
    return data


def creative_work_jsonld(site: SiteSettings, episode: Episode, season: Season | None) -> dict:
    data = {
        "@context": "https://schema.org",
        "@type": "CreativeWork",
        "name": episode.title,
        "description": episode.summary,
        "url": _absolute(site, f"/episodes/{episode_url_slug(episode)}/"),
        "datePublished": episode.publish_date.isoformat(),
        "author": {"@type": "Person", "name": site.name},
        "image": _absolute(
            site, f"/static/episodes/{episode_url_slug(episode)}/{episode.og_image}"
        ),
        "isPartOf": {
            "@type": "CreativeWorkSeries",
            "name": season.title if season else site.descriptor,
            "url": _absolute(site, "/seasons/"),
        },
    }
    return data
