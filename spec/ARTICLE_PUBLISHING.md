# Article publishing

Implemented 2026-10-02. The articles feature follows the existing router → service → repository port/mixin architecture.

## State and ownership

Each `Article` node stores an owner ID, JSON draft content, increasing revision, creation/update timestamps, and an optional published JSON snapshot with its own revision/date. A private save increments the revision without changing the public snapshot. Publish copies submitted content into both draft and public snapshot. Unpublish removes the snapshot while retaining the submitted private draft. There is no revision history or article deletion endpoint yet.

Owner reads and all writes require bearer authentication. The owner is derived from the token, never the request body. A write verifies the author still exists; another owner's article is reported as missing. Public routes return only published content. Author responses project only ID, name, and published count. Article collection response models omit body and revision.

## API

All routes use `/api/v1`:

| Method and path | Contract |
| --- | --- |
| GET `/articles` | Public, paginated published summaries; optional `authorId` |
| GET `/articles/{articleId}` | Public published snapshot or 404 |
| GET `/authors/{userId}` | Safe public author projection |
| GET `/me/articles` | Authenticated caller's draft/published summaries |
| GET `/me/articles/{articleId}` | Caller-owned current draft |
| PUT `/articles/{articleId}` | Save with `revision` and `action`: `save`, `publish`, or `unpublish` |

Article IDs are UUIDs chosen by the client. Creation uses revision 0; successful writes return the next revision. Stale writes return 409 without replacing saved content. Title/subtitle/body/book limits are 200/500/100000/300 characters; kind is `Article` or `Book review`. Publishing requires a nonblank title and body. Pagination is zero-based, size 1–100. Validation errors follow the existing 400 convention.

## Persistence and concurrency

The repository lazily installs `article_id_unique` before its first write. The Neo4j application principal therefore needs constraint-creation permission, or this should be moved to a deployment migration. This is a feature-specific safeguard, not a migration system for the older entities.

Writes run in one managed Neo4j transaction. MERGE plus the unique ID constraint handles competing creates; an explicit node write acquires the lock before ownership/revision checks. Failed checks roll back. Content update and snapshot publication commit together. No article events or vector indexing are emitted.

JSON snapshots keep content fields consistent and simplify publishing, at the cost of querying individual content fields in Cypher. List queries currently retrieve snapshots before response filtering; larger datasets may warrant separate summary properties. Count and page queries are separate and may observe concurrent changes.

## Browser behavior

The journal lists server drafts and recoverable local work. Legacy local drafts are retained and can be opened in the new writer. Edits create account/article-scoped browser recovery copies; successful server saves clear those copies. Server saving is explicit. A revision conflict preserves the editor text and asks the writer to reload the server version. This is conflict detection, not collaborative merging.

The reading renderer constructs React text nodes for paragraphs, headings, quotations, lists, bold, and italic. It does not inject HTML. Full rich text, media storage/uploads, links, moderation, and revision-history UI remain future work.

## Verification boundary

API tests cover owner isolation, publication state transitions, stale revisions, validation, public author filtering, and summaries. Repository tests cover snapshot selection and conflict ordering with fake transactions. Browser checks use an isolated API adapter. Live Neo4j constraint creation, concurrent writes, and deployed end-to-end behavior still need adapter-level verification.
