"""Render the hub's static site into `_site/` (build spec section 10, phases 3 and 4)."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from hub.discovery import entry_timestamp, feed_episodes, feed_updated, sitemap_paths
from hub.loaders import DATA_DIR, ROOT
from hub.models import EpisodeStatus
from hub.render import (
    SiteData,
    adjacent,
    episode_url_slug,
    load_site_data,
    make_environment,
    season_url_slug,
)
from hub.structured_data import creative_work_jsonld, creative_work_series_jsonld, person_jsonld
from hub.validation import validate_all

OUTPUT_DIR = ROOT / "_site"
STATIC_SOURCE_DIR = ROOT / "static"
DEFAULT_OG_IMAGE_PATH = "/static/social/default-og.png"
FAVICON_FILES = ("favicon.ico", "favicon.svg", "apple-touch-icon.png")


def _write_page(output_dir: Path, url_path: str, html: str) -> None:
    if url_path.endswith("/"):
        target = output_dir / url_path.lstrip("/") / "index.html"
    else:
        target = output_dir / url_path.lstrip("/")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")


def _episode_og_image_path(episode) -> str:
    return f"/static/episodes/{episode_url_slug(episode)}/{episode.og_image}"


def _render_home(env, data: SiteData, output_dir: Path) -> None:
    template = env.get_template("home.html")
    html = template.render(
        site=data.site,
        seasons=data.seasons,
        latest_episode=data.latest_episode,
        active_nav="home",
        canonical_path="/",
        social_image_path=DEFAULT_OG_IMAGE_PATH,
    )
    _write_page(output_dir, "/", html)


def _render_seasons_index(env, data: SiteData, output_dir: Path) -> None:
    template = env.get_template("seasons.html")
    html = template.render(
        site=data.site,
        seasons=data.seasons,
        active_nav="seasons",
        canonical_path="/seasons/",
        social_image_path=DEFAULT_OG_IMAGE_PATH,
        series_jsonld=creative_work_series_jsonld(data.site),
    )
    _write_page(output_dir, "/seasons/", html)


def _render_season_pages(env, data: SiteData, output_dir: Path) -> None:
    template = env.get_template("season.html")
    for season in data.seasons:
        previous_season, next_season = adjacent(data.seasons, season)
        url_path = f"/seasons/{season_url_slug(season)}/"
        html = template.render(
            site=data.site,
            season=season,
            episodes=data.episodes_for(season.code),
            previous_season=previous_season,
            next_season=next_season,
            active_nav="seasons",
            canonical_path=url_path,
            social_image_path=DEFAULT_OG_IMAGE_PATH,
        )
        _write_page(output_dir, url_path, html)


def _render_episode_pages(env, data: SiteData, output_dir: Path) -> None:
    template = env.get_template("episode.html")
    unseasoned = [ep for ep in data.all_episodes if ep.season is None]

    for season in [None, *data.seasons]:
        episodes = data.episodes_for(season.code) if season else unseasoned
        published = [ep for ep in episodes if ep.status == EpisodeStatus.PUBLISHED]
        for episode in published:
            previous_episode, next_episode = adjacent(published, episode)
            url_path = f"/episodes/{episode_url_slug(episode)}/"
            html = template.render(
                site=data.site,
                season=season,
                episode=episode,
                previous_episode=previous_episode,
                next_episode=next_episode,
                active_nav="seasons",
                canonical_path=url_path,
                social_image_path=_episode_og_image_path(episode),
                og_type="article",
                work_jsonld=creative_work_jsonld(data.site, episode, season),
            )
            _write_page(output_dir, url_path, html)


def _render_about(env, data: SiteData, output_dir: Path) -> None:
    template = env.get_template("about.html")
    html = template.render(
        site=data.site,
        active_nav="about",
        canonical_path="/about/",
        social_image_path=DEFAULT_OG_IMAGE_PATH,
        person_jsonld=person_jsonld(data.site),
    )
    _write_page(output_dir, "/about/", html)


def _render_404(env, data: SiteData, output_dir: Path) -> None:
    template = env.get_template("404.html")
    html = template.render(
        site=data.site,
        active_nav=None,
        canonical_path="/404.html",
        social_image_path=DEFAULT_OG_IMAGE_PATH,
    )
    _write_page(output_dir, "/404.html", html)


def _render_sitemap(env, data: SiteData, output_dir: Path) -> None:
    template = env.get_template("sitemap.xml")
    html = template.render(site=data.site, paths=sitemap_paths(data))
    _write_page(output_dir, "/sitemap.xml", html)


def _render_robots(env, data: SiteData, output_dir: Path) -> None:
    template = env.get_template("robots.txt")
    html = template.render(site=data.site)
    _write_page(output_dir, "/robots.txt", html)


def _render_feed(env, data: SiteData, output_dir: Path) -> None:
    template = env.get_template("feed.xml")
    html = template.render(
        site=data.site,
        episodes=feed_episodes(data),
        updated=feed_updated(data),
        entry_timestamp=entry_timestamp,
    )
    _write_page(output_dir, "/feed.xml", html)


def _copy_static(output_dir: Path, static_source_dir: Path) -> None:
    target = output_dir / "static"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(static_source_dir, target)


def _copy_favicons(output_dir: Path, static_source_dir: Path) -> None:
    icons_dir = static_source_dir / "icons"
    for filename in FAVICON_FILES:
        shutil.copy2(icons_dir / filename, output_dir / filename)


def build(
    output_dir: Path = OUTPUT_DIR,
    data_dir: Path = DATA_DIR,
    static_source_dir: Path = STATIC_SOURCE_DIR,
) -> None:
    result = validate_all(data_dir, static_source_dir / "episodes")
    for warning in result.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    if not result.ok:
        for error in result.errors:
            print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    data = load_site_data(data_dir)
    env = make_environment()

    _render_home(env, data, output_dir)
    _render_seasons_index(env, data, output_dir)
    _render_season_pages(env, data, output_dir)
    _render_episode_pages(env, data, output_dir)
    _render_about(env, data, output_dir)
    _render_404(env, data, output_dir)
    _render_sitemap(env, data, output_dir)
    _render_robots(env, data, output_dir)
    _render_feed(env, data, output_dir)
    _copy_static(output_dir, static_source_dir)
    _copy_favicons(output_dir, static_source_dir)


if __name__ == "__main__":
    build()
