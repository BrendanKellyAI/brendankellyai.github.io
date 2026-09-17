"""Cross-entity validation rules for the hub's content data (build spec section 7.4)."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

from hub.loaders import DATA_DIR, STATIC_EPISODES_DIR, load_episodes, load_seasons, load_site
from hub.models import FORMATS_REQUIRING_DECISION_RULE, Episode, EpisodeStatus, Season, SiteSettings

_DASH_CHARS = "—–"
_MAX_PDF_BYTES = 3 * 1024 * 1024
_TO_BE_SUPPLIED = "TO_BE_SUPPLIED"
_WARN_IF_UNSUPPLIED = ("description", "newsletter_url", "about_bio")


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_site(site: SiteSettings, seasons: list[Season], result: ValidationResult) -> None:
    season_codes = {season.code for season in seasons}
    if site.current_season not in season_codes:
        result.errors.append(
            f"site.yaml: current_season {site.current_season!r} does not exist in seasons.yaml"
        )
    for field_name in _WARN_IF_UNSUPPLIED:
        value = getattr(site, field_name)
        if value != _TO_BE_SUPPLIED:
            continue
        if site.launch:
            result.errors.append(f"site.yaml: {field_name} is TO_BE_SUPPLIED but launch is true")
        else:
            result.warnings.append(f"site.yaml: {field_name} is still TO_BE_SUPPLIED")


def _check_identity(
    path: Path, episode: Episode, seen_codes: dict[str, Path], result: ValidationResult
) -> None:
    expected_filename = f"{episode.code_slug}-{episode.slug}.yaml"
    if path.name != expected_filename:
        result.errors.append(
            f"{path}: file name does not match code/slug, expected {expected_filename}"
        )
    if episode.code in seen_codes:
        result.errors.append(
            f"{path}: duplicate episode code {episode.code!r} (also in {seen_codes[episode.code]})"
        )
    else:
        seen_codes[episode.code] = path


def _check_season_and_number(
    path: Path,
    episode: Episode,
    season_codes: set[str],
    numbers_by_season: dict[str, dict[int, Path]],
    result: ValidationResult,
) -> None:
    if episode.code == "S0":
        if episode.season is not None:
            result.errors.append(f"{path}: S0 must not have a season")
        if episode.number != 0:
            result.errors.append(f"{path}: S0 must have number 0")
        return

    if episode.season is None:
        result.errors.append(f"{path}: missing season")
        return
    if episode.season not in season_codes:
        result.errors.append(f"{path}: season {episode.season!r} does not exist in seasons.yaml")
        return

    bucket = numbers_by_season.setdefault(episode.season, {})
    if episode.number in bucket:
        result.errors.append(
            f"{path}: duplicate episode number {episode.number} in season {episode.season} "
            f"(also in {bucket[episode.number]})"
        )
    else:
        bucket[episode.number] = path


def _check_published_requirements(path: Path, episode: Episode, result: ValidationResult) -> None:
    if episode.status != EpisodeStatus.PUBLISHED:
        return

    required = {
        "publish_date": episode.publish_date,
        "summary": episode.summary,
        "linkedin_url": episode.linkedin_url,
        "deck_pdf": episode.deck_pdf,
        "cover_image": episode.cover_image,
        "og_image": episode.og_image,
    }
    for field_name, value in required.items():
        if not value:
            result.errors.append(f"{path}: published episode missing {field_name}")

    if episode.format in FORMATS_REQUIRING_DECISION_RULE and not episode.decision_rule:
        result.errors.append(f"{path}: published {episode.format.value} missing decision_rule")

    if episode.format.value == "field_note":
        if not episode.article_url:
            result.errors.append(f"{path}: published field note missing article_url")
        if not episode.lab_path:
            result.errors.append(f"{path}: published field note missing lab_path")

    if episode.format.value == "playbook":
        if not episode.playbook_slides:
            result.errors.append(f"{path}: published playbook has no playbook_slides")
        for slide in episode.playbook_slides:
            if not slide.alt:
                result.errors.append(f"{path}: playbook slide {slide.file} missing alt text")


def _episode_dir(static_dir: Path, episode: Episode) -> Path:
    return static_dir / f"{episode.code_slug}-{episode.slug}"


def _check_referenced_files(
    path: Path, episode: Episode, static_dir: Path, result: ValidationResult
) -> None:
    episode_dir = _episode_dir(static_dir, episode)

    for field_name in ("deck_pdf", "cover_image", "og_image"):
        filename = getattr(episode, field_name)
        if not filename:
            continue
        file_path = episode_dir / filename
        if not file_path.exists():
            result.errors.append(f"{path}: {field_name} file not found: {file_path}")
        elif field_name == "deck_pdf" and file_path.stat().st_size > _MAX_PDF_BYTES:
            result.errors.append(f"{path}: deck_pdf {filename} is over 3 MB")

    for slide in episode.playbook_slides:
        file_path = episode_dir / slide.file
        if not file_path.exists():
            result.errors.append(f"{path}: playbook slide file not found: {file_path}")


def validate_episodes(
    episodes: dict[Path, Episode],
    seasons: list[Season],
    static_dir: Path,
    result: ValidationResult,
) -> None:
    season_codes = {season.code for season in seasons}
    seen_codes: dict[str, Path] = {}
    numbers_by_season: dict[str, dict[int, Path]] = {}

    for path, episode in episodes.items():
        _check_identity(path, episode, seen_codes, result)
        _check_season_and_number(path, episode, season_codes, numbers_by_season, result)
        _check_published_requirements(path, episode, result)
        _check_referenced_files(path, episode, static_dir, result)


def check_no_dashes_in_files(paths: list[Path], result: ValidationResult) -> None:
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for char in _DASH_CHARS:
            if char in text:
                result.errors.append(f"{path}: contains an em dash or en dash")


def validate_all(
    data_dir: Path = DATA_DIR,
    static_dir: Path = STATIC_EPISODES_DIR,
) -> ValidationResult:
    result = ValidationResult()

    site = load_site(data_dir / "site.yaml")
    seasons = load_seasons(data_dir / "seasons.yaml")
    episodes = load_episodes(data_dir / "episodes")

    validate_site(site, seasons, result)
    validate_episodes(episodes, seasons, static_dir, result)

    data_files = [
        data_dir / "site.yaml",
        data_dir / "seasons.yaml",
        *sorted((data_dir / "episodes").glob("*.yaml")),
    ]
    check_no_dashes_in_files(data_files, result)

    return result


def main() -> int:
    result = validate_all()
    for warning in result.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    if not result.ok:
        for error in result.errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    print("Content data is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
