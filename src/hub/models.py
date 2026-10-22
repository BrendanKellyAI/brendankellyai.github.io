"""Pydantic schema for the hub's content data (build spec section 7)."""

from __future__ import annotations

import re
from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, model_validator

_DASH_CHARS = "—–"
_SUMMARY_MAX_WORDS = 30
# Seasons were planned at 12 episodes; Season 2 runs to 16. The cap only catches typos.
MAX_EPISODE_NUMBER = 20
_SENTENCE_END = (".", "!", "?")
_SENTENCE_BREAK = re.compile(r"[.!?](?=\s|$)")


class SeasonType(StrEnum):
    TECHNICAL = "technical"
    LEADERSHIP = "leadership"


class EpisodeFormat(StrEnum):
    SERIES_INTRO = "series_intro"
    SEASON_INTRO = "season_intro"
    EXPLAINER = "explainer"
    FIELD_NOTE = "field_note"
    PLAYBOOK = "playbook"
    DECISION_FRAMEWORK = "decision_framework"
    RECAP = "recap"


class EpisodeStatus(StrEnum):
    PLANNED = "planned"
    PUBLISHED = "published"


FORMATS_REQUIRING_DECISION_RULE = frozenset(
    {
        EpisodeFormat.EXPLAINER,
        EpisodeFormat.FIELD_NOTE,
        EpisodeFormat.PLAYBOOK,
        EpisodeFormat.DECISION_FRAMEWORK,
    }
)


def _check_no_dashes(value: str, field_name: str) -> None:
    for char in _DASH_CHARS:
        if char in value:
            raise ValueError(f"{field_name} contains an em dash or en dash: {value!r}")


class NoDashModel(BaseModel):
    """Base model that rejects em dashes and en dashes in every string field."""

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _no_dashes(self) -> NoDashModel:
        for field_name, value in self.__dict__.items():
            if isinstance(value, str):
                _check_no_dashes(value, field_name)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        _check_no_dashes(item, field_name)
        return self


class PlaybookSlide(NoDashModel):
    file: str
    alt: str


class SiteSettings(NoDashModel):
    name: str
    descriptor: str
    description: str
    base_url: str
    linkedin_profile_url: str
    newsletter_name: str
    newsletter_url: str
    lab_repo_url: str
    about_bio: str
    current_season: str
    launch: bool = False
    # Google Analytics measurement ID, such as G-ABC123. Empty means no analytics at all.
    # When set, GA loads only after a visitor accepts the consent banner.
    analytics_id: str = ""
    # Privacy notice (/privacy/): how long analytics data is kept, as set in Google Analytics,
    # and when the notice last changed. Privacy requests go to linkedin_profile_url.
    analytics_retention: str = "2 months"
    privacy_updated: date | None = None

    @model_validator(mode="after")
    def _check_analytics_id(self) -> SiteSettings:
        if self.analytics_id and not re.fullmatch(r"G-[A-Z0-9]{4,20}", self.analytics_id):
            raise ValueError(f"analytics_id {self.analytics_id!r} is not a GA4 ID like G-ABC123")
        return self


class Season(NoDashModel):
    code: str
    number: int
    slug: str
    title: str
    type: SeasonType
    description: str
    # The whole season in one PDF, hosted on a GitHub release (see scripts/publish_season_pdf.py).
    pdf_url: str | None = None
    pdf_pages: int | None = None
    pdf_size_mb: float | None = None

    @model_validator(mode="after")
    def _check_pdf(self) -> Season:
        fields = (self.pdf_url, self.pdf_pages, self.pdf_size_mb)
        if any(value is not None for value in fields) and None in fields:
            raise ValueError(f"{self.code}: set pdf_url, pdf_pages, and pdf_size_mb together")
        if self.pdf_url and not self.pdf_url.startswith("https://"):
            raise ValueError(f"{self.code}: pdf_url must be an https:// link")
        return self


class Episode(NoDashModel):
    code: str
    season: str | None = None
    number: int
    slug: str
    title: str
    format: EpisodeFormat
    status: EpisodeStatus = EpisodeStatus.PLANNED
    publish_date: date | None = None
    summary: str | None = None
    decision_rule: str | None = None
    linkedin_url: str | None = None
    deck_pdf: str | None = None
    cover_image: str | None = None
    og_image: str | None = None
    lab_path: str | None = None
    article_url: str | None = None
    playbook_slides: list[PlaybookSlide] = []
    slide_sections: list[str] = []

    @property
    def code_slug(self) -> str:
        """The lowercase, hyphen-separated form of `code` used in file names and URLs."""
        return self.code.lower().replace(" ", "-")

    @model_validator(mode="after")
    def _check_number_range(self) -> Episode:
        if not 0 <= self.number <= MAX_EPISODE_NUMBER:
            raise ValueError(f"episode number {self.number} is outside 0-{MAX_EPISODE_NUMBER}")
        return self

    @model_validator(mode="after")
    def _check_summary(self) -> Episode:
        if self.summary is None:
            return self
        summary = self.summary.strip()
        word_count = len(summary.split())
        if word_count > _SUMMARY_MAX_WORDS:
            raise ValueError(
                f"summary has {word_count} words, over the {_SUMMARY_MAX_WORDS} word limit"
            )
        # A mark only ends a sentence when followed by a space or the end, so "9.2" is not one.
        terminal_count = len(_SENTENCE_BREAK.findall(summary))
        if terminal_count > 1 or (terminal_count == 1 and not summary.endswith(_SENTENCE_END)):
            raise ValueError(f"summary is not a single sentence: {summary!r}")
        return self

    @model_validator(mode="after")
    def _check_deck_filename(self) -> Episode:
        if self.deck_pdf is None:
            return self
        pattern = re.compile(rf"^bk-{re.escape(self.code_slug)}-{re.escape(self.slug)}-v\d+\.pdf$")
        if not pattern.match(self.deck_pdf):
            raise ValueError(
                f"deck_pdf {self.deck_pdf!r} does not match "
                f"bk-{self.code_slug}-{self.slug}-v<number>.pdf"
            )
        return self


class Concept(NoDashModel):
    """An idea on the course map, linked to episodes (by code slug) and seasons (by code)."""

    id: str
    label: str
    links: list[str]


class CourseMap(NoDashModel):
    """Slide section names, and the concepts and cross-links drawn on the course map."""

    sections: dict[str, str] = {}
    concepts: list[Concept] = []
    links: list[list[str]] = []
