"""Course helpers made available to every template: progress, the course map, and slides."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment

from hub.graph import course_graph, episode_concepts, season_concepts, season_graph, slide_chapters
from hub.models import Episode
from hub.render import SiteData, episode_position, episode_url_slug, season_progress


def install_course_globals(
    env: Environment, data: SiteData, slides: dict[str, list[Path]] | None = None
) -> None:
    """Register the course helpers. `slides` maps episode URL slugs to rendered slide images."""
    slides = slides or {}

    def slides_for(episode: Episode) -> list[str]:
        slug = episode_url_slug(episode)
        return [f"/static/episodes/{slug}/slides/{image.name}" for image in slides.get(slug, [])]

    env.globals.update(
        course=data,
        episode_position=lambda episode: episode_position(data, episode),
        season_progress=lambda code: season_progress(data, code),
        course_graph=lambda: course_graph(data),
        season_graph=lambda code: season_graph(data, code),
        season_concepts=lambda code: season_concepts(data, code),
        episode_concepts=lambda episode: episode_concepts(data.course_map, episode),
        slides_for=slides_for,
        slide_chapters=lambda episode: slide_chapters(
            data.course_map, episode, len(slides_for(episode))
        ),
    )
