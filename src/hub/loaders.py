"""Load and parse the hub's YAML content data."""

from __future__ import annotations

from pathlib import Path

import yaml

from hub.models import Episode, Season, SiteSettings

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
STATIC_EPISODES_DIR = ROOT / "static" / "episodes"


def _read_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_site(path: Path = DATA_DIR / "site.yaml") -> SiteSettings:
    return SiteSettings.model_validate(_read_yaml(path))


def load_seasons(path: Path = DATA_DIR / "seasons.yaml") -> list[Season]:
    return [Season.model_validate(item) for item in _read_yaml(path)]


def load_episodes(directory: Path = DATA_DIR / "episodes") -> dict[Path, Episode]:
    return {
        episode_path: Episode.model_validate(_read_yaml(episode_path))
        for episode_path in sorted(directory.glob("*.yaml"))
    }
