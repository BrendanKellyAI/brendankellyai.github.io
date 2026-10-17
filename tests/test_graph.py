from datetime import date

from hub.graph import (
    course_graph,
    episode_concepts,
    season_concepts,
    season_graph,
    slide_chapters,
)
from hub.models import Concept, CourseMap, Episode, Season, SiteSettings
from hub.render import SiteData

SITE = SiteSettings(
    name="Brendan Kelly",
    descriptor="Applied AI",
    description="A course.",
    base_url="https://example.com",
    linkedin_profile_url="https://example.com/in",
    newsletter_name="News",
    newsletter_url="",
    lab_repo_url="https://example.com/lab",
    about_bio="Bio.",
    current_season="S1",
)


def _season(code: str, number: int) -> Season:
    return Season(
        code=code,
        number=number,
        slug=f"season-{number}",
        title=f"Season {number}",
        type="technical",
        description="A season.",
    )


def _episode(number: int, published: bool, sections: list[str] | None = None) -> Episode:
    return Episode(
        code=f"S1 E{number}",
        season="S1",
        number=number,
        slug=f"lesson-{number}",
        title=f"Lesson {number}",
        format="explainer",
        status="published" if published else "planned",
        publish_date=date(2026, 10, number + 1) if published else None,
        summary="A summary." if published else None,
        slide_sections=sections or [],
    )


def _data(course_map: CourseMap) -> SiteData:
    episodes = [_episode(1, True), _episode(2, False)]
    return SiteData(
        site=SITE,
        seasons=[_season("S1", 1), _season("S2", 2), _season("S3", 3)],
        episodes_by_season={"S1": episodes},
        all_episodes=episodes,
        course_map=course_map,
    )


COURSE_MAP = CourseMap(
    sections={"model": "Mental model", "data": "Data"},
    concepts=[
        Concept(id="tokens", label="Tokens", links=["s1-e1", "S3"]),
        Concept(id="orphan", label="Orphan", links=["s9-e9"]),
        Concept(id="later", label="Later", links=["S2"]),
    ],
    links=[["s1-e1", "s1-e2"], ["s1-e1", "s9-e9"]],
)


def test_course_graph_links_seasons_lessons_and_concepts():
    graph = course_graph(_data(COURSE_MAP))
    ids = {node["id"] for node in graph["nodes"]}

    assert {"S1", "S2", "S3", "s1-e1", "s1-e2", "c-tokens", "c-later"} <= ids
    assert "c-orphan" not in ids, "a concept with no known targets is dropped"
    assert ["S1", "S2"] in graph["links"]
    assert ["S1", "s1-e1"] in graph["links"]
    assert ["s1-e1", "s1-e2"] in graph["links"]
    assert ["s1-e1", "s9-e9"] not in graph["links"], "links to unknown nodes are dropped"


def test_lesson_nodes_only_link_when_published():
    nodes = {node["id"]: node for node in course_graph(_data(COURSE_MAP))["nodes"]}

    assert nodes["s1-e1"]["href"] == "/episodes/s1-e1-lesson-1/"
    assert nodes["s1-e2"]["href"] is None
    assert nodes["s1-e2"]["summary"] is None


def test_season_graph_keeps_its_lessons_their_ideas_and_where_they_lead():
    graph = season_graph(_data(COURSE_MAP), "S1")
    ids = {node["id"] for node in graph["nodes"]}

    assert {"S1", "s1-e1", "s1-e2", "c-tokens", "S2", "S3"} <= ids
    assert "c-later" not in ids, "ideas that touch no lesson in the season are left out"
    assert all(a in ids and b in ids for a, b in graph["links"])


def test_season_and_episode_concepts():
    data = _data(COURSE_MAP)

    assert season_concepts(data, "S1") == ["Tokens"]
    assert episode_concepts(COURSE_MAP, _episode(1, True)) == ["Tokens"]
    assert episode_concepts(COURSE_MAP, _episode(2, False)) == []


def test_slide_chapters_group_consecutive_sections():
    episode = _episode(1, True, ["model", "data", "data", "model"])

    chapters = slide_chapters(COURSE_MAP, episode, 4)

    assert [(c["label"], c["start"], c["count"]) for c in chapters] == [
        ("Mental model", 1, 1),
        ("Data", 2, 2),
        ("Mental model", 4, 1),
    ]


def test_slide_chapters_fall_back_when_sections_are_missing():
    chapters = slide_chapters(COURSE_MAP, _episode(1, True, ["model"]), 3)

    assert [(c["label"], c["start"], c["count"]) for c in chapters] == [
        ("Mental model", 1, 1),
        ("Slides", 2, 2),
    ]
