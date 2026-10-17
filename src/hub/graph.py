"""The course map (seasons, lessons, and the ideas that link them) and slide chapters."""

from __future__ import annotations

from hub.models import CourseMap, Episode, EpisodeFormat, EpisodeStatus
from hub.render import SiteData, episode_url_slug, season_url_slug

CONCEPT_PREFIX = "c-"
DEFAULT_SECTION_LABEL = "Slides"


def _lesson_node(episode: Episode) -> dict:
    live = episode.status == EpisodeStatus.PUBLISHED
    # Intro titles repeat the season name, which crowds the map; the hover card keeps it.
    is_intro = episode.format == EpisodeFormat.SEASON_INTRO
    return {
        "id": episode.code_slug,
        "kind": "lesson",
        "code": episode.code,
        "label": "Season intro" if is_intro else episode.title,
        "title": episode.title,
        "live": live,
        "summary": episode.summary if live else None,
        "href": f"/episodes/{episode_url_slug(episode)}/" if live else None,
        "slug": episode_url_slug(episode),
    }


def _season_node(season, current_code: str, published: int, total: int) -> dict:
    return {
        "id": season.code,
        "kind": "season",
        "code": season.code,
        "label": season.title,
        "type": season.type.value,
        "current": season.code == current_code,
        "summary": season.description,
        "progress": [published, total],
        "href": f"/seasons/{season_url_slug(season)}/",
    }


def course_graph(data: SiteData) -> dict:
    """Seasons form a backbone, lessons hang off their season, concepts tie lessons together."""
    nodes: list[dict] = []
    links: list[list[str]] = []
    previous_season = None
    for season in data.seasons:
        episodes = data.episodes_for(season.code)
        published = sum(ep.status == EpisodeStatus.PUBLISHED for ep in episodes)
        nodes.append(_season_node(season, data.site.current_season, published, len(episodes)))
        if previous_season:
            links.append([previous_season.code, season.code])
        previous_season = season
        for index, episode in enumerate(episodes):
            nodes.append(_lesson_node(episode))
            parent = season.code if index == 0 else episodes[index - 1].code_slug
            links.append([parent, episode.code_slug])

    known = {node["id"] for node in nodes}
    for concept in data.course_map.concepts:
        targets = [target for target in concept.links if target in known]
        if not targets:
            continue
        concept_id = f"{CONCEPT_PREFIX}{concept.id}"
        nodes.append({"id": concept_id, "kind": "concept", "label": concept.label})
        links.extend([concept_id, target] for target in targets)
    links.extend(
        list(pair) for pair in data.course_map.links if len(pair) == 2 and set(pair) <= known
    )
    return {"nodes": nodes, "links": links}


def season_graph(data: SiteData, season_code: str) -> dict:
    """One season's lessons, the ideas they touch, and the other seasons those ideas lead to."""
    full = course_graph(data)
    by_id = {node["id"]: node for node in full["nodes"]}
    lesson_ids = {ep.code_slug for ep in data.episodes_for(season_code)}
    keep = {season_code} | lesson_ids
    for a, b in full["links"]:
        for here, other in ((a, b), (b, a)):
            if here in lesson_ids and other.startswith(CONCEPT_PREFIX):
                keep.add(other)
    keep |= {
        other
        for a, b in full["links"]
        for here, other in ((a, b), (b, a))
        if here in keep and by_id[other]["kind"] == "season"
    }
    return {
        "nodes": [node for node in full["nodes"] if node["id"] in keep],
        "links": [[a, b] for a, b in full["links"] if a in keep and b in keep],
    }


def season_concepts(data: SiteData, season_code: str) -> list[str]:
    """Labels of the ideas a season's lessons cover, in course-map order."""
    graph = season_graph(data, season_code)
    return [node["label"] for node in graph["nodes"] if node["kind"] == "concept"]


def episode_concepts(course_map: CourseMap, episode: Episode) -> list[str]:
    """Labels of the ideas the course map links to one episode."""
    return [
        concept.label for concept in course_map.concepts if episode.code_slug in concept.links
    ]


def slide_chapters(course_map: CourseMap, episode: Episode, slide_count: int) -> list[dict]:
    """Group consecutive slides that share a section tag into named chapters.

    Slides beyond the tags listed in `slide_sections` fall into a generic "Slides" chapter,
    so an episode published without tags still gets a working player.
    """
    chapters: list[dict] = []
    for index in range(slide_count):
        tag = episode.slide_sections[index] if index < len(episode.slide_sections) else ""
        if chapters and chapters[-1]["tag"] == tag:
            chapters[-1] = {**chapters[-1], "count": chapters[-1]["count"] + 1}
        else:
            label = course_map.sections.get(tag, DEFAULT_SECTION_LABEL)
            chapters.append({"tag": tag, "label": label, "start": index + 1, "count": 1})
    return chapters
