from hub.loaders import load_course_map, load_episodes, load_seasons, load_site
from hub.models import Episode, Season, SiteSettings


def test_load_site_returns_site_settings():
    site = load_site()
    assert isinstance(site, SiteSettings)
    assert site.current_season == "S1"


def test_load_seasons_returns_fifteen_seasons():
    seasons = load_seasons()
    assert len(seasons) == 15
    assert all(isinstance(season, Season) for season in seasons)
    assert [season.code for season in seasons] == [f"S{n}" for n in range(1, 16)]


def test_load_episodes_returns_fourteen_episodes():
    episodes = load_episodes()
    assert len(episodes) == 14
    assert all(isinstance(episode, Episode) for episode in episodes.values())
    codes = {episode.code for episode in episodes.values()}
    assert codes == {"S0", *(f"S1 E{n}" for n in range(13))}


def test_load_course_map_reads_the_real_map():
    course_map = load_course_map()
    assert course_map.sections["rule"] == "Decision rule"
    assert course_map.concepts


def test_load_course_map_is_empty_when_the_file_is_missing(tmp_path):
    course_map = load_course_map(tmp_path / "course-map.yaml")
    assert course_map.sections == {}
    assert course_map.concepts == []
