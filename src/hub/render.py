"""Assemble content data and render it through Jinja2 templates."""

from __future__ import annotations

from dataclasses import dataclass, field

from jinja2 import Environment, FileSystemLoader, select_autoescape

from hub.loaders import DATA_DIR, ROOT, load_episodes, load_seasons, load_site
from hub.models import Episode, EpisodeStatus, Season, SiteSettings

TEMPLATES_DIR = ROOT / "templates"

FORMAT_LABELS = {
    "series_intro": "Series intro",
    "season_intro": "Season intro",
    "explainer": "Explainer",
    "field_note": "Field note",
    "playbook": "Playbook",
    "decision_framework": "Decision framework",
    "recap": "Recap",
}

TO_BE_SUPPLIED = "TO_BE_SUPPLIED"


def episode_url_slug(episode: Episode) -> str:
    return f"{episode.code_slug}-{episode.slug}"


def season_url_slug(season: Season) -> str:
    return f"{season.code.lower()}-{season.slug}"


def format_label(format_value: str) -> str:
    return FORMAT_LABELS[format_value]


def format_date(value) -> str:
    return value.strftime("%d %B %Y").lstrip("0")


@dataclass
class SiteData:
    site: SiteSettings
    seasons: list[Season]
    episodes_by_season: dict[str, list[Episode]] = field(default_factory=dict)
    all_episodes: list[Episode] = field(default_factory=list)

    def episodes_for(self, season_code: str) -> list[Episode]:
        return self.episodes_by_season.get(season_code, [])

    @property
    def published_episodes(self) -> list[Episode]:
        return [ep for ep in self.all_episodes if ep.status == EpisodeStatus.PUBLISHED]

    @property
    def latest_episode(self) -> Episode | None:
        published = self.published_episodes
        if not published:
            return None
        return max(published, key=lambda ep: ep.publish_date)


def load_site_data(data_dir=DATA_DIR) -> SiteData:
    site = load_site(data_dir / "site.yaml")
    seasons = sorted(load_seasons(data_dir / "seasons.yaml"), key=lambda season: season.number)
    episodes = list(load_episodes(data_dir / "episodes").values())

    episodes_by_season: dict[str, list[Episode]] = {}
    for episode in episodes:
        if episode.season is None:
            continue
        episodes_by_season.setdefault(episode.season, []).append(episode)
    for season_episodes in episodes_by_season.values():
        season_episodes.sort(key=lambda ep: ep.number)

    return SiteData(
        site=site, seasons=seasons, episodes_by_season=episodes_by_season, all_episodes=episodes
    )


def make_environment() -> Environment:
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals["episode_url_slug"] = episode_url_slug
    env.globals["season_url_slug"] = season_url_slug
    env.globals["format_label"] = format_label
    env.globals["TO_BE_SUPPLIED"] = TO_BE_SUPPLIED
    env.filters["format_date"] = format_date
    return env


def adjacent(items: list, current) -> tuple:
    """Return (previous, next) neighbours of `current` in `items`, or (None, None)."""
    index = items.index(current)
    previous = items[index - 1] if index > 0 else None
    following = items[index + 1] if index < len(items) - 1 else None
    return previous, following
