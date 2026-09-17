import pytest
from pydantic import ValidationError

from hub.models import Episode, EpisodeFormat, Season, SeasonType, SiteSettings

VALID_SEASON = {
    "code": "S1",
    "number": 1,
    "slug": "how-llms-work",
    "title": "How LLMs work",
    "type": "technical",
    "description": "What a large language model does.",
}

VALID_EPISODE = {
    "code": "S1 E2",
    "season": "S1",
    "number": 2,
    "slug": "tokens",
    "title": "Tokens",
    "format": "explainer",
    "status": "planned",
}

VALID_SITE = {
    "name": "Brendan Kelly",
    "descriptor": "Applied AI",
    "description": "A series on applied AI.",
    "base_url": "https://brendankellyai.github.io",
    "linkedin_profile_url": "https://www.linkedin.com/in/brendan-kelly-irl",
    "newsletter_name": "Applied AI with Brendan Kelly",
    "newsletter_url": "https://example.com/newsletter",
    "lab_repo_url": "https://github.com/BrendanKellyAI/applied-ai-lab",
    "current_season": "S1",
    "launch": False,
}


def test_valid_season_passes():
    season = Season.model_validate(VALID_SEASON)
    assert season.type == SeasonType.TECHNICAL


def test_valid_episode_passes():
    episode = Episode.model_validate(VALID_EPISODE)
    assert episode.format == EpisodeFormat.EXPLAINER
    assert episode.code_slug == "s1-e2"


def test_valid_site_passes():
    site = SiteSettings.model_validate(VALID_SITE)
    assert site.current_season == "S1"


def test_unknown_field_rejected_on_season():
    with pytest.raises(ValidationError):
        Season.model_validate({**VALID_SEASON, "extra_field": "nope"})


def test_unknown_field_rejected_on_episode():
    with pytest.raises(ValidationError):
        Episode.model_validate({**VALID_EPISODE, "extra_field": "nope"})


def test_unknown_field_rejected_on_site():
    with pytest.raises(ValidationError):
        SiteSettings.model_validate({**VALID_SITE, "extra_field": "nope"})


def test_em_dash_rejected():
    with pytest.raises(ValidationError, match="em dash"):
        Season.model_validate({**VALID_SEASON, "title": "How LLMs work — an overview"})


def test_en_dash_rejected():
    with pytest.raises(ValidationError, match="em dash"):
        Episode.model_validate({**VALID_EPISODE, "title": "Tokens 2020–2026"})


def test_em_dash_rejected_in_nested_playbook_slide():
    with pytest.raises(ValidationError, match="em dash"):
        Episode.model_validate(
            {
                **VALID_EPISODE,
                "playbook_slides": [{"file": "slide1.png", "alt": "A slide — with a dash"}],
            }
        )


def test_episode_number_below_range_rejected():
    with pytest.raises(ValidationError, match="0-12"):
        Episode.model_validate({**VALID_EPISODE, "number": -1})


def test_episode_number_above_range_rejected():
    with pytest.raises(ValidationError, match="0-12"):
        Episode.model_validate({**VALID_EPISODE, "number": 13})


def test_summary_over_word_limit_rejected():
    long_summary = " ".join(["word"] * 31) + "."
    with pytest.raises(ValidationError, match="word limit"):
        Episode.model_validate({**VALID_EPISODE, "summary": long_summary})


def test_summary_at_word_limit_passes():
    summary = " ".join(["word"] * 30) + "."
    episode = Episode.model_validate({**VALID_EPISODE, "summary": summary})
    assert episode.summary == summary


def test_summary_multiple_sentences_rejected():
    with pytest.raises(ValidationError, match="single sentence"):
        Episode.model_validate(
            {**VALID_EPISODE, "summary": "Tokens are the unit. Cost follows them."}
        )


def test_summary_without_terminal_punctuation_after_text_rejected():
    with pytest.raises(ValidationError, match="single sentence"):
        Episode.model_validate({**VALID_EPISODE, "summary": "Tokens end mid. sentence oddly"})


def test_deck_filename_valid_pattern_passes():
    episode = Episode.model_validate({**VALID_EPISODE, "deck_pdf": "bk-s1-e2-tokens-v1.pdf"})
    assert episode.deck_pdf == "bk-s1-e2-tokens-v1.pdf"


def test_deck_filename_invalid_pattern_rejected():
    with pytest.raises(ValidationError, match="deck_pdf"):
        Episode.model_validate({**VALID_EPISODE, "deck_pdf": "tokens-deck.pdf"})


def test_deck_filename_wrong_code_rejected():
    with pytest.raises(ValidationError, match="deck_pdf"):
        Episode.model_validate({**VALID_EPISODE, "deck_pdf": "bk-s1-e3-tokens-v1.pdf"})
