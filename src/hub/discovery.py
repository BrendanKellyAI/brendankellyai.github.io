"""Assemble data for the feed, sitemap, and robots output (build spec section 9, phase 4)."""

from __future__ import annotations

from datetime import UTC, date
from datetime import datetime as _datetime

from hub.models import Episode
from hub.render import SiteData, episode_url_slug, season_url_slug


def sitemap_paths(data: SiteData) -> list[str]:
    """Every indexable page. The 404 page is excluded, since it is marked noindex."""
    paths = ["/", "/seasons/", "/about/"]
    paths += [f"/seasons/{season_url_slug(season)}/" for season in data.seasons]
    paths += [f"/episodes/{episode_url_slug(episode)}/" for episode in data.published_episodes]
    return paths


def feed_episodes(data: SiteData) -> list[Episode]:
    """Published episodes, newest first."""
    return sorted(data.published_episodes, key=lambda ep: ep.publish_date, reverse=True)


def feed_updated(data: SiteData) -> str:
    episodes = feed_episodes(data)
    day = episodes[0].publish_date if episodes else date.today()
    return _datetime(day.year, day.month, day.day, tzinfo=UTC).isoformat()


def entry_timestamp(episode: Episode) -> str:
    day = episode.publish_date
    return _datetime(day.year, day.month, day.day, tzinfo=UTC).isoformat()
