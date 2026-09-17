# brendankellyai.github.io: series hub build specification

Version 1.0, 16 September 2026
Owner: Brendan Kelly
Repository: github.com/BrendanKellyAI/brendankellyai.github.io (public)
Site: https://brendankellyai.github.io (GitHub Pages, no custom domain)
Local build folder: `brendankellyai.github.io/`, alongside `applied-ai-lab/` in the owner's working folder, never inside it
Related repository: github.com/BrendanKellyAI/applied-ai-lab (code only; the two repositories are linked, not combined)

## 1. How to use this document

This specification is the brief for building the series hub with an AI coding tool on a local machine, after the applied-ai-lab harness is complete.

Instructions for the coding tool:

- Work only in the hub repository. Do not add files to, or change, applied-ai-lab. The hub links to it by URL.

- Build in the phase order in section 10. Stop at the end of each phase and report what was built and how it was verified.
- Irish and UK English in all visible text. Code identifiers follow normal conventions.
- No em dashes anywhere in written content, including templates, data, and commit messages.
- Do not write new episode content. The hub only indexes what is already published. Where copy is needed and not supplied, use a clearly marked placeholder and report it.
- Where this document says "verify at build time", check current documentation rather than relying on prior knowledge.

## 2. Purpose

The hub is the episode guide for a LinkedIn series by Brendan Kelly on applied AI, structured like a TV series: 15 seasons of 12 episodes each, interleaving technical and leadership seasons.

LinkedIn shows posts newest first, with no way to group them. The hub puts every episode in order, so a reader, typically a hiring manager or engineering leader, can:

1. See the full season guide and how far the series has progressed
2. Open any season and see its episodes in order
3. Read an episode's summary and decision rule, then open the LinkedIn post, the PDF deck, and any article or code

It is pinned in the LinkedIn Featured section and linked from the S0 series intro deck as the "Episode guide".

Design principles:

- **Index, not blog.** No new content is written for the hub.
- **One entry per episode.** Publishing an episode means adding one data entry and its files.
- **Same brand as the decks.** Recognisably the same identity as the slides.
- **Fast, accessible, private.** Static HTML, no tracking, no third-party requests.
- **Stable addresses.** Episode URLs match repository folder names and deck file names, and never change once published.

## 3. Scope

In scope:

- Static site generator, templates, styles, and data schema
- Home, season guide, season pages, episode pages, and About page
- Atom feed, sitemap, robots file, and social preview metadata
- Validation and link checking in continuous integration
- Deployment to GitHub Pages with GitHub Actions
- Seed data for S0, all 15 seasons, and the 13 Season 1 entries (E0 to E12)

Out of scope:

- Analytics, cookies, comments, search, or any client-side application
- A custom domain
- Writing episode summaries, decision rules, or the About biography (supplied by the owner)

## 4. Technology choices

| Area | Choice | Notes |
|---|---|---|
| Language | Python 3.12 or later | Same stack as applied-ai-lab |
| Environment | uv, with pyproject.toml | |
| Templates | Jinja2 | |
| Data | YAML, validated with pydantic | Build fails on any schema error |
| Build output | Static HTML and CSS in `_site/`, not committed | |
| Deployment | GitHub Actions to GitHub Pages | Verify the current official Pages deployment actions at build time |
| JavaScript | None required | Every page works with JavaScript disabled |
| Fonts | Inter Tight and JetBrains Mono, self-hosted WOFF2 files from Fontsource | SIL Open Font License; include licence files. No Google Fonts requests |
| Tests | pytest with pytest-cov, 85% minimum | Matches applied-ai-lab |
| Linting | ruff | |
| HTML checks | An HTML validator and an internal link checker in CI | Verify suitable tools at build time |

Why not Jekyll: GitHub Pages builds Jekyll natively, but a Python build keeps one toolchain across both repositories, and allows schema validation and content checks to fail the build before anything deploys.

Why self-hosted fonts: loading Google Fonts from Google's servers sends visitor IP addresses to a third party, which raises GDPR concerns for an EU-based site.

## 5. Site structure and URLs

| Page | URL |
|---|---|
| Home | `/` |
| Season guide | `/seasons/` |
| Season page | `/seasons/<season-code>-<slug>/`, for example `/seasons/s1-how-llms-work/` |
| Episode page | `/episodes/<episode-code>-<slug>/`, for example `/episodes/s1-e2-tokens/` |
| Series intro | `/episodes/s0-series-intro/` |
| About | `/about/` |
| Atom feed | `/feed.xml` |
| Sitemap | `/sitemap.xml` |
| Robots | `/robots.txt` |
| Not found | `/404.html` |

URL rules:

- All lowercase, hyphen-separated, with a trailing slash.
- Episode codes in URLs are lowercase without spaces: `s1-e2`.
- Episode slugs match the applied-ai-lab folder names wherever a folder exists, for example `s1-e7-lost-in-the-middle`.
- A published URL never changes. If a title changes, the slug stays.

Confirmed URLs already referenced elsewhere:

- https://brendankellyai.github.io/episodes/s1-e1-one-token-at-a-time/
- https://brendankellyai.github.io/episodes/s1-e2-tokens/

## 6. Pages

### 6.1 Home

- Name and descriptor: "Brendan Kelly" and "Applied AI"
- One-line series description (section 11.1)
- Season guide summary: all 15 seasons as tiles, as in section 6.2
- Latest episode: the most recent published episode, with code, title, summary, and link
- Where to follow: LinkedIn profile, the newsletter "Applied AI with Brendan Kelly", and the applied-ai-lab repository

### 6.2 Season guide

- Heading "The season guide"
- A line explaining the pattern: two technical seasons, then one leadership season that applies them
- 15 tiles in order, each showing the season code and title, linking to the season page
- Technical seasons filled, leadership seasons outlined, the current season in acid green; a legend explains all three
- The note: "The field moves quickly. Seasons and episodes may be added as the series progresses."
- No total duration anywhere

### 6.3 Season page

- Season code, title, type (technical or leadership), and description
- Every episode entry for that season in order, E0 to E12
- Each row: episode code, title, format label, and publish date if published
- Published episodes link to their page. Planned episodes show code and title only, labelled "Coming soon", with no date
- Seasons with no episode entries yet show the description and "Episodes announced at the season intro"
- Previous and next season links

### 6.4 Episode page

Shown only for published episodes. Planned episodes have no page.

- Episode code badge, season label, and title
- Format label: series intro, season intro, explainer, field note, playbook, decision framework, or recap
- Publish date
- One-sentence summary
- The decision rule as text, in the decision rule style (section 8.3), where the episode has one
- Links:
  - LinkedIn post
  - PDF deck, served from the hub
  - For field notes: the LinkedIn article, and the experiment folder in applied-ai-lab
  - For episodes with code, such as S1 E1: the episode folder in applied-ai-lab
- For playbooks: the template walkthrough slides as images, shown in order as a one-page reference, each with alt text supplied in data
- Cover image of the deck
- Deck PDFs are image-only, so they cannot be restyled by mobile reading modes, but they contain no selectable text. The summary and decision rule on this page are therefore the accessible and indexable version of each deck, and must always be present for published episodes.
- Previous and next episode links within the season, and a link back to the season page

### 6.5 About

- Short biography supplied by the owner. Until supplied, a marked placeholder. No confidential employer detail.
- How to follow and contact: LinkedIn profile link only
- A note that code is published under the MIT licence in applied-ai-lab, and that decks and articles are not

### 6.6 Not found

- Branded page with links to the home page and season guide

## 7. Data model

All content lives in `data/`. Adding an episode means adding one entry and its files.

### 7.1 Site settings: `data/site.yaml`

```yaml
name: Brendan Kelly
descriptor: Applied AI
description: TO_BE_SUPPLIED            # see section 11.1 for the proposed line
base_url: https://brendankellyai.github.io
linkedin_profile_url: https://www.linkedin.com/in/brendan-kelly-irl
newsletter_name: Applied AI with Brendan Kelly
newsletter_url: TO_BE_SUPPLIED
lab_repo_url: https://github.com/BrendanKellyAI/applied-ai-lab
current_season: S1
launch: false                         # set to true for the public launch
```

The build warns, but does not fail, when a value is `TO_BE_SUPPLIED`. Once `launch` is `true`, the deploy workflow fails if any remain (section 10, Phase 5).

### 7.2 Seasons: `data/seasons.yaml`

```yaml
- code: S1
  number: 1
  slug: how-llms-work
  title: How LLMs work
  type: technical            # technical or leadership
  description: What a large language model does, from tokens and attention to hallucination and reasoning.
```

### 7.3 Episodes: `data/episodes/<episode-code>-<slug>.yaml`

One file per episode.

```yaml
code: S1 E2
season: S1
number: 2
slug: tokens
title: Tokens
format: explainer             # series_intro, season_intro, explainer, field_note, playbook, decision_framework, recap
status: published             # planned or published
publish_date: 2026-10-06      # example; required when published
summary: Tokens, not words, are the unit behind every cost, latency, and context limit in a large language model.
decision_rule: Measure cost, latency, and limits in tokens, using the tokeniser of the model you will run.
linkedin_url: https://www.linkedin.com/...
deck_pdf: bk-s1-e2-tokens-v1.pdf   # versioned; a new version gets a new file name
cover_image: cover.png
og_image: og.png
lab_path: null                # for example episodes/s1-e1-one-token-at-a-time
article_url: null             # field notes only
playbook_slides: []           # playbooks only: list of { file, alt }
```

Episode files (deck, cover, social image, playbook slides) live in `static/episodes/<episode-code>-<slug>/` and are copied to the episode URL.

### 7.4 Validation rules

The build fails if any rule is broken:

- Every field matches the schema; unknown fields are rejected.
- Episode codes are unique, and the file name, code, and slug agree.
- Every episode's season exists; episode numbers are 0 to 12 and unique within a season. S0 is the only exception, with number 0 and no season page.
- Published episodes have a publish date, summary, LinkedIn URL, deck PDF, cover image, and social image.
- Published explainers, field notes, playbooks, and decision frameworks have a decision rule. Series intros, season intros, and recaps do not require one.
- Field notes have an article URL and a lab path. Playbooks have at least one playbook slide with alt text.
- Every referenced file exists; PDFs are under 3 MB.
- Deck file names match `bk-<episode-code>-<slug>-v<number>.pdf`, for example `bk-s1-e2-tokens-v1.pdf`. When a new version is published, the old PDF is removed from the episode folder, so only the current version is served and a stale cached copy can never be linked.
- `current_season` exists.
- No em dash (U+2014) or en dash (U+2013) appears in any data file or template.
- Summaries are one sentence and under 30 words.

## 8. Design system

The hub follows the Brendan Kelly brand system, version 1.6. Where this section and the brand board differ, report it rather than choosing.

### 8.1 Colour tokens

| Token | Value | Use |
|---|---|---|
| navy | #0B1F3A | Page background |
| panel | #12294A | Cards, rows, raised areas |
| hair | #1D3A63 | Dividers |
| green | #B8E04A | Accent: badges, borders, rules, focus rings, current season |
| white | #FFFFFF | Headings |
| mist | #C9D3E0 | Body text |
| slate | #8193AD | Secondary text, borders, metadata |

Rules:

- Acid green is an accent only: never body text or large fills. Text on green is always navy.
- One green focal element per page section, and every green highlight is explained where it could be ambiguous.
- No gradients, shadows, or background images.
- The site uses the navy theme in both light and dark system settings, so it matches the decks.
- All text meets WCAG 2.2 AA contrast. Mist on navy is 10.9:1 and slate on navy is 5.3:1.

### 8.2 Typography

- Inter Tight for all text, weights 400, 500, and 700. JetBrains Mono 400 for code only.
- Base size 18px on mobile, 19px on desktop, line height 1.6. Headings in 700 with slight negative tracking.
- Sentence case everywhere. No all caps, no italics for emphasis.
- Fallback stacks: system-ui, Helvetica, Arial for Inter Tight; ui-monospace, Menlo, Consolas for JetBrains Mono.

### 8.3 Components

- **Episode badge:** navy text on a green block, for example "S1 E2", matching the deck covers.
- **Monogram:** "BK" square, green on navy, used as the favicon source.
- **Season tile:** filled panel for technical, 2px mist outline for leadership, green fill with navy text for the current season.
- **Episode row:** panel background with a slate left border, containing badge, title, format label, and date or "Coming soon".
- **Decision rule:** panel background, green left border, green "Decision rule" label, statement in white at heading weight.
- **Link list:** plain rows with visible underlined links; external links marked with visually hidden text "(opens LinkedIn)" or similar, not icons alone.

### 8.4 Layout and accessibility

- Mobile first, single column up to 720px, maximum content width 1080px.
- Semantic landmarks: header, nav, main, footer. One h1 per page.
- Keyboard focus visible on every interactive element, using a green focus ring.
- A skip to content link.
- Images have meaningful alt text; decorative images have empty alt.
- `prefers-reduced-motion` respected, though no motion is planned.
- Target: Lighthouse accessibility, best practices, and SEO scores of 95 or above on home, a season page, and an episode page.

## 9. Metadata and discovery

- Every page has a unique title, meta description, and canonical URL.
- Open Graph and Twitter card tags on every page. Episode pages use the episode's `og_image`; other pages use a site-wide image.
- Social images are 1200 by 627 pixels, the size LinkedIn uses for link previews. Verify at build time. The content side supplies these images.
- JSON-LD structured data: `Person` on About, `CreativeWorkSeries` on the season guide, `CreativeWork` on episode pages. Verify appropriate types at build time.
- Atom feed of published episodes, newest first, with title, summary, decision rule, and link.
- `sitemap.xml` lists every page; `robots.txt` allows all and links to the sitemap.
- Favicon set generated from the BK monogram.

## 10. Build phases

Each phase ends with a stop, a short report, and review before the next phase.

| Phase | Build | Verification |
|---|---|---|
| 1. Skeleton | Install uv if missing; pyproject.toml, ruff, pytest with pytest-cov, .gitignore, README outline; self-hosted fonts with licence files | `uv run pytest` and `uv run ruff check` pass; coverage gate at 85% |
| 2. Data | Pydantic schema, loaders, and every validation rule in section 7.4; seed data from section 11 | Tests prove each rule fails on a bad example and passes on the seed data |
| 3. Templates | Base layout, components, and every page in section 6; CSS from section 8 | Local preview renders all pages; HTML validator passes; no JavaScript required |
| 4. Discovery | Metadata, structured data, feed, sitemap, robots, favicons, 404 | Feed and sitemap validate; every page has title, description, canonical, and social tags |
| 5. Deploy | GitHub Actions workflow: validate, test, build, check internal links, deploy to Pages; placeholder check blocks deploy when `launch: true` is set in `site.yaml` | A push to main deploys; a broken link or schema error fails the workflow before deploy |
| 6. Review | Lighthouse runs on three page types; manual keyboard and screen reader pass on home and one episode page | Scores of 95 or above; issues fixed or reported |

## 11. Seed data

### 11.1 Proposed site description

"A series on applied AI, structured like a TV series: technical seasons on how AI works in production, and leadership seasons on how to decide, organise, and govern it."

For owner approval.

### 11.2 Seasons

| Code | Slug | Title | Type | Description |
|---|---|---|---|---|
| S1 | how-llms-work | How LLMs work | technical | What a large language model does, from tokens and attention to hallucination and reasoning. |
| S2 | retrieval-and-rag | Retrieval and RAG | technical | Grounding models in your own data with embeddings, search, chunking, reranking, and retrieval-augmented generation (RAG). |
| S3 | ai-strategy | AI strategy and use case selection | leadership | Choosing where AI earns its place, building the business case, and knowing when not to use it. |
| S4 | adapting-models | Adapting models | technical | Prompting, structured output, fine-tuning, quantisation, and choosing the right model for the task. |
| S5 | agent-fundamentals | Agent fundamentals | technical | How agents plan, use tools, and remember, including common design patterns and the Model Context Protocol (MCP). |
| S6 | ai-economics | AI economics | leadership | Build versus buy, managed versus self-hosted, lock-in, and the unit economics of AI features. |
| S7 | data-for-ai | Data for AI | technical | Ingestion, document parsing, structured data, and the data quality every AI system depends on. |
| S8 | evaluation | Evaluation | technical | Proving AI systems work, with golden sets, model-based judging, trajectory evaluation, and regression gates. |
| S9 | ai-teams | Building AI teams and operating models | leadership | Team structures, hiring, skills, and how AI teams work with the rest of the organisation. |
| S10 | reliability-and-traceability | Agents in production: reliability and traceability | technical | Tracing, failure modes, retries, and keeping humans in the loop. |
| S11 | security | Agents in production: security | technical | Prompt injection, guardrails, tool permissions, and limiting the blast radius. |
| S12 | delivery-and-adoption | Delivery, adoption, and change | leadership | Moving from pilot to production, aligning stakeholders, and getting AI adopted. |
| S13 | performance-and-cost | Agents in production: performance and cost | technical | Latency budgets, caching, inference optimisation, and token economics. |
| S14 | resilience | Agents in production: resilience | technical | What happens when an agent gets it wrong, and how to recover. |
| S15 | governance | Governance and the regulated EU enterprise | leadership | The EU AI Act, data sovereignty, audit trails, and responsible AI in regulated industries. |

Season descriptions are for owner approval.

### 11.3 Episodes

All start with `status: planned`. The owner publishes each by adding its date, LinkedIn URL, and files.

| Code | Slug | Title | Format | Lab path |
|---|---|---|---|---|
| S0 | series-intro | Applied AI: the series | series_intro | |
| S1 E0 | season-intro | Season 1: How LLMs work | season_intro | |
| S1 E1 | one-token-at-a-time | One token at a time | explainer | episodes/s1-e1-one-token-at-a-time |
| S1 E2 | tokens | Tokens | explainer | |
| S1 E3 | embeddings | Embeddings | explainer | |
| S1 E4 | attention | Attention | explainer | |
| S1 E5 | the-transformer | The transformer | explainer | |
| S1 E6 | context-windows | Context windows | explainer | |
| S1 E7 | lost-in-the-middle | Field note: lost in the middle | field_note | field-notes/s1-e7-lost-in-the-middle |
| S1 E8 | sampling | Sampling | explainer | |
| S1 E9 | hallucination | Hallucination | explainer | |
| S1 E10 | reasoning-vs-standard | Field note: reasoning versus standard | field_note | field-notes/s1-e10-reasoning-vs-standard |
| S1 E11 | when-is-reasoning-worth-the-cost | When is a reasoning model worth the cost? | decision_framework | |
| S1 E12 | recap | Season 1 recap | recap | |

Summaries and decision rules for S0, S1 E1, and S1 E2 are already written in their decks and captions, and can be supplied at publication.

## 12. Publishing workflow

For each episode, after its LinkedIn post is live:

1. Copy the deck PDF, cover image, and social image into the episode's `static/episodes/` folder. If replacing a deck, remove the previous version and update `deck_pdf` to the new versioned file name.
2. In the episode's data file, set `status: published`, the publish date, the LinkedIn URL, and confirm the summary and decision rule.
3. Update `current_season` in `site.yaml` when a new season starts.
4. Commit and push. The workflow validates, builds, checks links, and deploys.

The LinkedIn URL exists only after posting, so the hub is updated on the same day, shortly after each post goes live.

## 13. Decisions for the owner

- Approve or edit the site description and the 15 season descriptions
- Newsletter URL, once the newsletter is created (LinkedIn profile URL supplied: https://www.linkedin.com/in/brendan-kelly-irl)
- About biography
- Whether season intros and recaps keep those names, or use TV terms such as trailer and season finale (this affects format labels only)
- Launch timing: the hub must be live, with S0 published, before the S0 post goes out
