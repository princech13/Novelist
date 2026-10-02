# UI review and editorial direction

Reviewed and updated 2026-10-02.

## Assessment

The existing interface communicates a book-management dashboard more strongly than a place to read and write. Its strengths are a warm background, serif headings, and existing book/review workflows. The fixed sidebar, compact typography, repeated elevated cards, and small review form dilute that editorial character. A book description was also presented as a “Featured Review,” although it was not a reader review. There was no article-writing surface.

## Implemented direction

- **Identity:** paper white, ink blue, muted sage, and small terracotta accents; expressive serif headings paired with restrained interface text. Decorative books are CSS artwork, not fabricated catalog entries.
- **Navigation:** a responsive masthead with Library, Stories, My journal, Discover, and My reading; a persistent writing action. Semantic search remains accessible in the footer.
- **Library:** a reading-room introduction, understated book displays with typographic fallback covers, clear filter states, and a writing invitation. Book data remains API-backed. Corrected sorting so newest/rating ordering applies even without search text.
- **Journal:** account-backed drafts and published stories, with browser recovery copies and access to legacy local drafts.
- **Writer:** spacious title, subtitle, body, review metadata, word count, reading time, Markdown formatting tools, reading preview, and export. Explicit save/publish/unpublish actions distinguish private work from the public snapshot. Local recovery and revision conflicts protect unsaved work.
- **Rated reviews:** a larger native dialog, readable writing area, native radio inputs for keyboard-operable star ratings, focus containment, Escape dismissal, and pending/error states. The existing rating API and 1,000-character limit remain in place.
- **Accessibility:** labeled inputs and icon actions, keyboard-operable book links, visible focus, skip navigation, reduced-motion support, and mobile layouts. This is not a full accessibility audit.

## Second phase delivered

Public story feeds, reading pages, and author pages now share the editorial system. Authentication, book detail, reading history, discovery, and semantic search have matching typography, spacing, responsive layouts, and honest loading/error/empty states. Discovery describes all-time reader favourites; semantic search presents passages rather than implying generated answers. Book detail retains rated reviews, text editing/indexing, and deletion controls.

The new article API supports owner-only drafts and explicit public snapshots. See [publishing architecture](ARTICLE_PUBLISHING.md) for contracts and persistence decisions. Long-form book reviews remain separate from star-rated catalog reviews.

## Remaining work

Image uploads and a full visual rich-text editor remain future work. The current renderer supports a deliberate Markdown subset, without HTML, images, or links. Local recovery is browser storage, not encrypted storage; clearing browser data removes unsaved copies. Download delivery was not confirmed by the browser's download-event check.

## Verification

All 71 backend tests pass, including article authorization, draft isolation, publishing/unpublishing, validation, typed summaries, and revision conflicts. These tests use fake infrastructure; real Neo4j transaction and Cypher execution remain unverified.

Production TypeScript/Vite build and Oxlint pass. A temporary development harness using the real UI components and an isolated in-memory API adapter was used for desktop/mobile visual review and draft → save → publish → private edit → public snapshot verification. It is removed after review. No production auth bypass or demo data is shipped. Screenshots are in `artifacts/ui-review/`. Keyboard star selection and Escape dismissal were verified during the first phase; this is not a full accessibility audit.
