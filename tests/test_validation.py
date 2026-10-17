from pathlib import Path

from hub.models import Concept, CourseMap, Episode, Season
from hub.validation import (
    MAX_PDF_MB,
    ValidationResult,
    check_no_dashes_in_files,
    main,
    validate_all,
    validate_course_map,
    validate_episodes,
    validate_site,
)

SEASON_S1 = Season.model_validate(
    {
        "code": "S1",
        "number": 1,
        "slug": "how-llms-work",
        "title": "How LLMs work",
        "type": "technical",
        "description": "What a large language model does.",
    }
)


def episode(**overrides) -> Episode:
    base = {
        "code": "S1 E2",
        "season": "S1",
        "number": 2,
        "slug": "tokens",
        "title": "Tokens",
        "format": "explainer",
        "status": "planned",
    }
    return Episode.model_validate({**base, **overrides})


def path_for(ep: Episode) -> Path:
    return Path(f"data/episodes/{ep.code_slug}-{ep.slug}.yaml")


PUBLISHED_REQUIRED_FIELDS = {
    "publish_date": "2026-10-06",
    "summary": "Tokens are the unit behind every cost and latency figure.",
    "deck_pdf": "bk-s1-e2-tokens-v1.pdf",
    "cover_image": "cover.png",
    "og_image": "og.png",
}


def test_seed_data_passes_validation():
    # The real seed data changes as the owner fills in placeholders (site
    # description, about_bio, and so on), so this only checks that it is
    # schema valid and free of hard errors. Warning behaviour for specific
    # TO_BE_SUPPLIED fields is covered by the fixture based tests below,
    # which do not depend on the current state of data/site.yaml.
    result = validate_all()
    assert result.ok, result.errors


def test_duplicate_episode_code_fails():
    ep1 = episode(code="S1 E2", slug="tokens", number=2)
    ep2 = episode(code="S1 E2", slug="tokens-two", number=3)
    episodes = {path_for(ep1): ep1, path_for(ep2): ep2}
    result = ValidationResult()
    validate_episodes(episodes, [SEASON_S1], Path("static/episodes"), result)
    assert any("duplicate episode code" in error for error in result.errors)


def test_unknown_season_fails():
    ep = episode(season="S99")
    result = ValidationResult()
    validate_episodes({path_for(ep): ep}, [SEASON_S1], Path("static/episodes"), result)
    assert any("does not exist in seasons.yaml" in error for error in result.errors)


def test_duplicate_number_in_season_fails():
    ep1 = episode(code="S1 E2", slug="tokens", number=2)
    ep2 = episode(code="S1 E3", slug="tokens-two", number=2)
    episodes = {path_for(ep1): ep1, path_for(ep2): ep2}
    result = ValidationResult()
    validate_episodes(episodes, [SEASON_S1], Path("static/episodes"), result)
    assert any("duplicate episode number" in error for error in result.errors)


def test_s0_with_season_fails():
    ep = episode(code="S0", season="S1", number=0, slug="series-intro", format="series_intro")
    result = ValidationResult()
    validate_episodes({path_for(ep): ep}, [SEASON_S1], Path("static/episodes"), result)
    assert any("S0 must not have a season" in error for error in result.errors)


def test_s0_wrong_number_fails():
    ep = episode(code="S0", season=None, number=1, slug="series-intro", format="series_intro")
    result = ValidationResult()
    validate_episodes({path_for(ep): ep}, [SEASON_S1], Path("static/episodes"), result)
    assert any("S0 must have number 0" in error for error in result.errors)


def test_published_missing_required_fields_fails():
    ep = episode(status="published")
    result = ValidationResult()
    validate_episodes({path_for(ep): ep}, [SEASON_S1], Path("static/episodes"), result)
    for field_name in PUBLISHED_REQUIRED_FIELDS:
        assert any(field_name in error for error in result.errors), field_name


def test_published_format_missing_decision_rule_fails():
    ep = episode(status="published", format="explainer", **PUBLISHED_REQUIRED_FIELDS)
    result = ValidationResult()
    validate_episodes({path_for(ep): ep}, [SEASON_S1], Path("static/episodes"), result)
    assert any("missing decision_rule" in error for error in result.errors)


def test_published_series_intro_does_not_require_decision_rule():
    ep = episode(
        code="S0",
        season=None,
        number=0,
        slug="series-intro",
        format="series_intro",
        status="published",
        publish_date="2026-09-01",
        summary="The introduction to the applied AI series.",
        linkedin_url="https://www.linkedin.com/posts/example",
        deck_pdf="bk-s0-series-intro-v1.pdf",
        cover_image="cover.png",
        og_image="og.png",
    )
    result = ValidationResult()
    validate_episodes({path_for(ep): ep}, [SEASON_S1], Path("static/episodes"), result)
    assert not any("decision_rule" in error for error in result.errors)


def test_published_field_note_missing_lab_path_fails():
    ep = episode(
        format="field_note",
        status="published",
        decision_rule="Trust the middle of long context less than the ends.",
        **PUBLISHED_REQUIRED_FIELDS,
    )
    result = ValidationResult()
    validate_episodes({path_for(ep): ep}, [SEASON_S1], Path("static/episodes"), result)
    assert any("missing lab_path" in error for error in result.errors)
    assert not any("article_url" in error for error in result.errors), "article_url is optional"


def test_published_episode_does_not_need_linkedin_url():
    ep = episode(
        status="published",
        decision_rule="Measure cost, latency, and limits in tokens.",
        **PUBLISHED_REQUIRED_FIELDS,
    )
    result = ValidationResult()
    validate_episodes({path_for(ep): ep}, [SEASON_S1], Path("static/episodes"), result)
    assert not any("linkedin_url" in error for error in result.errors)


def test_published_playbook_missing_slides_fails():
    ep = episode(
        format="playbook",
        status="published",
        decision_rule="Follow the steps in order.",
        **PUBLISHED_REQUIRED_FIELDS,
    )
    result = ValidationResult()
    validate_episodes({path_for(ep): ep}, [SEASON_S1], Path("static/episodes"), result)
    assert any("has no playbook_slides" in error for error in result.errors)


def test_published_playbook_slide_missing_alt_fails():
    ep = episode(
        format="playbook",
        status="published",
        decision_rule="Follow the steps in order.",
        playbook_slides=[{"file": "slide1.png", "alt": ""}],
        **PUBLISHED_REQUIRED_FIELDS,
    )
    result = ValidationResult()
    validate_episodes({path_for(ep): ep}, [SEASON_S1], Path("static/episodes"), result)
    assert any("missing alt text" in error for error in result.errors)


def test_missing_referenced_file_fails(tmp_path):
    ep = episode(status="published", **PUBLISHED_REQUIRED_FIELDS)
    result = ValidationResult()
    validate_episodes({path_for(ep): ep}, [SEASON_S1], tmp_path, result)
    assert any("deck_pdf file not found" in error for error in result.errors)


def test_pdf_over_size_limit_fails(tmp_path):
    ep = episode(status="published", **PUBLISHED_REQUIRED_FIELDS)
    episode_dir = tmp_path / f"{ep.code_slug}-{ep.slug}"
    episode_dir.mkdir(parents=True)
    (episode_dir / ep.deck_pdf).write_bytes(b"0" * (MAX_PDF_MB * 1024 * 1024 + 1))
    (episode_dir / ep.cover_image).write_bytes(b"cover")
    (episode_dir / ep.og_image).write_bytes(b"og")
    result = ValidationResult()
    validate_episodes({path_for(ep): ep}, [SEASON_S1], tmp_path, result)
    assert any(f"over {MAX_PDF_MB} MB" in error for error in result.errors)


def test_referenced_files_within_size_limit_pass(tmp_path):
    ep = episode(
        status="published", decision_rule="Measure in tokens.", **PUBLISHED_REQUIRED_FIELDS
    )
    episode_dir = tmp_path / f"{ep.code_slug}-{ep.slug}"
    episode_dir.mkdir(parents=True)
    (episode_dir / ep.deck_pdf).write_bytes(b"0" * 1024)
    (episode_dir / ep.cover_image).write_bytes(b"cover")
    (episode_dir / ep.og_image).write_bytes(b"og")
    result = ValidationResult()
    validate_episodes({path_for(ep): ep}, [SEASON_S1], tmp_path, result)
    assert result.ok, result.errors


def test_current_season_missing_fails():
    from hub.models import SiteSettings

    site = SiteSettings.model_validate(
        {
            "name": "Brendan Kelly",
            "descriptor": "Applied AI",
            "description": "A series on applied AI.",
            "base_url": "https://brendankellyai.github.io",
            "linkedin_profile_url": "https://www.linkedin.com/in/brendan-kelly-irl",
            "newsletter_name": "Applied AI with Brendan Kelly",
            "newsletter_url": "https://example.com/newsletter",
            "lab_repo_url": "https://github.com/BrendanKellyAI/applied-ai-lab",
            "about_bio": "A short biography.",
            "current_season": "S99",
            "launch": False,
        }
    )
    result = ValidationResult()
    validate_site(site, [SEASON_S1], result)
    assert any("does not exist in seasons.yaml" in error for error in result.errors)


def test_launch_true_with_unsupplied_field_fails():
    from hub.models import SiteSettings

    site = SiteSettings.model_validate(
        {
            "name": "Brendan Kelly",
            "descriptor": "Applied AI",
            "description": "TO_BE_SUPPLIED",
            "base_url": "https://brendankellyai.github.io",
            "linkedin_profile_url": "https://www.linkedin.com/in/brendan-kelly-irl",
            "newsletter_name": "Applied AI with Brendan Kelly",
            "newsletter_url": "https://example.com/newsletter",
            "lab_repo_url": "https://github.com/BrendanKellyAI/applied-ai-lab",
            "about_bio": "A short biography.",
            "current_season": "S1",
            "launch": True,
        }
    )
    result = ValidationResult()
    validate_site(site, [SEASON_S1], result)
    assert any("launch is true" in error for error in result.errors)


def test_dash_in_data_file_fails(tmp_path):
    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text("title: A season — with a dash\n", encoding="utf-8")
    result = ValidationResult()
    check_no_dashes_in_files([bad_file], result)
    assert any("em dash or en dash" in error for error in result.errors)


def test_clean_file_has_no_dash_errors(tmp_path):
    good_file = tmp_path / "good.yaml"
    good_file.write_text("title: A season without any dash\n", encoding="utf-8")
    result = ValidationResult()
    check_no_dashes_in_files([good_file], result)
    assert result.ok


def test_filename_mismatch_fails():
    ep = episode(code="S1 E2", slug="tokens")
    wrong_path = Path("data/episodes/wrong-name.yaml")
    result = ValidationResult()
    validate_episodes({wrong_path: ep}, [SEASON_S1], Path("static/episodes"), result)
    assert any("file name does not match" in error for error in result.errors)


def test_main_returns_zero_for_the_real_seed_data(capsys):
    assert main() == 0
    assert "Content data is valid." in capsys.readouterr().out


def test_main_returns_one_when_validation_fails(monkeypatch, capsys):
    failing_result = ValidationResult(errors=["something is wrong"])
    monkeypatch.setattr("hub.validation.validate_all", lambda: failing_result)
    assert main() == 1
    assert "something is wrong" in capsys.readouterr().err


def test_course_map_with_valid_links_and_sections_passes():
    ep = episode(slide_sections=["model", "data"])
    course_map = CourseMap(
        sections={"model": "Mental model", "data": "Data"},
        concepts=[Concept(id="tokens", label="Tokens", links=["s1-e2", "S1"])],
        links=[["s1-e2", "S1"]],
    )
    result = ValidationResult()

    validate_course_map(course_map, {path_for(ep): ep}, [SEASON_S1], result)

    assert result.ok, result.errors


def test_course_map_rejects_unknown_targets_bad_links_and_unknown_sections():
    ep = episode(slide_sections=["model", "typo"])
    course_map = CourseMap(
        sections={"model": "Mental model"},
        concepts=[Concept(id="tokens", label="Tokens", links=["s1-e9"])],
        links=[["s1-e2", "S7"], ["s1-e2"]],
    )
    result = ValidationResult()

    validate_course_map(course_map, {path_for(ep): ep}, [SEASON_S1], result)

    assert any("concept 'tokens' links to unknown 's1-e9'" in e for e in result.errors)
    assert any("names unknown 'S7'" in e for e in result.errors)
    assert any("must name exactly two items" in e for e in result.errors)
    assert any("slide_sections uses tags not in course-map.yaml" in e for e in result.errors)
