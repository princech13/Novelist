# Architectural decision records

Reviewed: 2026-10-02 against the current working tree.

These records document implemented choices retrospectively. ADR-001–007 preserve the identifiers in the previous architecture document. Rationale below describes the fit and tradeoffs visible in this implementation; it is not evidence of a historical team discussion, measured performance, or a formal comparison of alternatives. Open gaps are not endorsed decisions. See the [architecture review](ARCHITECTURE.md) for runtime flows and prioritized findings.

## ADR-001: Organize the backend as a modular monolith

**Status:** Implemented.

**Context and decision:** Books, users, ratings, auth, analytics, recommendations, profile, and semantic search run in one FastAPI application, organized by feature. Services depend on narrow `Protocol` ports; one concrete repository combines feature mixins. Lifespan owns shared infrastructure and dependency factories construct services.

**Rationale and alternatives:** One deployment and one graph make cross-feature queries and local development straightforward. Separate services would require network contracts, data ownership, and distributed failure handling. The repository provides no evidence that those costs are currently needed.

**Consequences:** Features deploy and scale together. Ports support lightweight service tests, but isolation is incomplete: several routers directly use the repository, services reference HTTP/infrastructure helpers, and repository mixins call one another. Extracting a service would require deliberate boundary and data-ownership work.

**Evidence:** [bootstrap](../app/main.py), [DI](../app/core/dependencies.py), [repository composition](../app/infrastructure/neo4j/repository.py), [books router](../app/modules/books/router.py).

## ADR-002: Publish optional, best-effort events through RabbitMQ

**Status:** Implemented; delivery and concurrency limitations remain.

**Context and decision:** Book mutations and rating upserts publish JSON events after persistence to the durable topic exchange `novelist.domain.exchange`. The publisher reuses a connection, sends persistent messages, retries once on AMQP errors, and suppresses a second AMQP failure. `RABBITMQ_ENABLED=false` disables publishing. No consumers or queue bindings are provided here.

**Rationale and alternatives:** Topic routing permits downstream integrations without adding consumers to HTTP handlers. A transactional outbox and a worker could provide durable handoff, but are not implemented. The repository does not establish a measured RabbitMQ-versus-Kafka selection.

**Consequences:** Durable exchange/message flags do not guarantee delivery. There are no publisher confirms, outbox, or atomic database/broker commit; retries can duplicate an event, and failures can lose one. Serialization and non-AMQP exceptions are not covered by the AMQP suppression policy. Publishing still blocks the request, and the shared channel has no concurrency coordination. `user.created` in the old specification is not emitted.

**Evidence:** [publisher](../app/infrastructure/messaging/publisher.py), [book service](../app/modules/books/service.py), [rating service](../app/modules/ratings/service.py).

## ADR-003: Use Neo4j for application records and vectors

**Status:** Implemented; schema provisioning is incomplete.

**Context and decision:** Users, books, refresh tokens, and content chunks share Neo4j. Ratings are relationships with properties. Recommendations and analytics are computed with Cypher; semantic search uses a cosine vector index in the same database. Preferences are serialized into a JSON string property.

**Rationale and alternatives:** Rating traversals directly express shared reading preferences, while keeping vectors with book data avoids a second persistence service. A relational database plus a vector store would introduce another model and synchronization boundary.

**Consequences:** Cypher and vector-index behavior tie persistence to Neo4j. JSON preferences are convenient to store but not modeled for graph queries. `_one`/`_all` open a session per call; multi-call use cases do not share a transaction. Ordinary indexes and uniqueness constraints exist as documentation examples, not executable migrations. Read-before-write checks can race.

**Evidence:** [query helpers](../app/infrastructure/neo4j/base.py), [recommendations](../app/modules/recommendations/repository.py), [users](../app/modules/users/repository.py), [RAG repository](../app/modules/rag/repository.py).

## ADR-004: Use access JWTs with persisted refresh-token revocation

**Status:** Implemented.

**Context and decision:** Bcrypt hashes protect passwords. Signed JWTs distinguish access from refresh tokens. Access authentication is stateless; refresh-token IDs and revocation state live in Neo4j. Defaults are HS256, 60-minute access tokens, and seven-day refresh tokens.

**Rationale and alternatives:** Access validation avoids a database lookup for each authenticated request, while persisted refresh state permits logout to prevent future refreshes. Server-side sessions or per-request user checks would offer different immediate-revocation semantics.

**Consequences:** Logout does not revoke existing access JWTs. Refresh tokens are not rotated; no expiry cleanup job is present. Deleting a user neither invalidates an access JWT nor removes that user's refresh records. Production requires a deliberate secret configuration; a development fallback remains in settings.

**Evidence:** [security](../app/core/security.py), [auth service](../app/modules/auth/service.py), [token storage](../app/modules/auth/repository.py).

## ADR-005: Separate the React SPA from the JSON API

**Status:** Implemented for local development; production UI deployment is unspecified.

**Context and decision:** React Router handles browser navigation, TanStack Query caches server responses, and Axios centralizes bearer headers and 401 handling. AuthContext stores identity and tokens in `localStorage`. The shared Query client uses 30-second freshness and one retry.

**Rationale and alternatives:** Separating UI and API allows independent frontend builds and reusable HTTP endpoints. Server rendering or cookie-based sessions would require different deployment and authentication contracts.

**Consequences:** Browser tokens are accessible to JavaScript. A 401 clears tokens and redirects; there is no automatic refresh despite refresh-token storage. Client-side route protection is only a UX mechanism. The API base URL is hard-coded; static deployment needs origin configuration and SPA routing support. Logout does not clear the shared Query cache, so user-specific data must be explicitly cleared or scoped to identity.

**Evidence:** [App](../ui/src/App.tsx), [Axios client](../ui/src/api/client.ts), [AuthContext](../ui/src/context/AuthContext.tsx).

## ADR-006: Enforce self-ownership for selected user mutations

**Status:** Implemented; shared-catalog permissions need an explicit product policy.

**Context and decision:** The backend compares the JWT subject with the URL user ID for user update/delete/preferences and rating writes. Current-user endpoints derive the ID from the token. Other business routes require authentication without roles or book ownership.

**Rationale and alternatives:** Subject equality provides a small, explicit rule for personal writes. Role-based catalog administration or per-resource access policies are alternatives if editing should be restricted.

**Consequences:** Every authenticated user can mutate shared books and invoke indexing. Other users' profiles are readable by authenticated users. Authorization at the router boundary does not sanitize response fields: untyped user collection items currently retain password hashes, a review finding requiring correction rather than an intentional policy.

**Evidence:** [require_self](../app/core/security.py), [users router](../app/modules/users/router.py), [ratings router](../app/modules/ratings/router.py), [RAG router](../app/modules/rag/router.py).

## ADR-007: Parse CORS origins from a string setting

**Status:** Implemented.

**Context and decision:** `cors_origins` is a string setting; `cors_origins_list` parses comma-separated values or a JSON array. The code explicitly avoids settings-layer JSON decoding of a list field when the environment contains a bare `*`.

**Rationale and alternatives:** This supports simple environment values while retaining JSON-array input. A JSON-only contract would simplify accepted formats but change the existing configuration interface.

**Consequences:** The default is wildcard origins and the middleware enables credentials. Deployment must supply the intended origins. Parsing does not independently validate the JSON result as a list of origins. Settings are cached per process, so configuration changes require restarting it.

**Evidence:** [settings](../app/core/config.py), [CORS middleware](../app/main.py).

## ADR-008: Run local semantic retrieval explicitly within HTTP requests

**Status:** Implemented; indexing lifecycle has known gaps.

**Context and decision:** Sentence-transformers produces embeddings locally. The default model is `all-MiniLM-L6-v2`, loaded lazily and cached per process. Content is split into overlapping character chunks (defaults 512/64), stored as `BookChunk` nodes, and retrieved with cosine similarity. Indexing is an explicit endpoint; search returns excerpts and scores without generation.

**Rationale and alternatives:** A local model avoids a hosted embedding API dependency and keeps query processing within the application runtime. A worker queue could move indexing cost outside HTTP requests; a separate model service could centralize inference. Neither exists here.

**Consequences:** Model loading and embedding consume request capacity and process memory. The image caches only the default model, so configuring another model may require a download. Model changes require compatible index dimensions and re-embedding; no version migration exists. The process-wide index-ready flag does not wait for database index readiness or track model/database changes. Replacing chunks uses separate delete/insert calls; edits do not reindex automatically and book deletion does not remove chunks.

**Evidence:** [embedding wrapper](../app/modules/rag/embedding_service.py), [RAG service](../app/modules/rag/service.py), [RAG repository](../app/modules/rag/repository.py), [Dockerfile](../Dockerfile).

## ADR-009: Derive ratings, analytics, and recommendations from graph queries

**Status:** Implemented.

**Context and decision:** Rating writes use `MERGE` for a user/book relationship. Analytics aggregate live graph data. Recommendations traverse highly rated shared books (rating at least four), exclude already rated books, and rank by matching path count. Catalog search uses case-insensitive substring matching and offset pagination.

**Rationale and alternatives:** Query-time computation avoids maintaining precomputed aggregates, search projections, or a recommendation-training pipeline. Materialized views or dedicated search could be introduced if measured query costs warrant them.

**Consequences:** Work grows with graph size and traversal fan-out. Recommendation scores count paths rather than distinct people and have no cold-start fallback. “Trending” has no time window; genre popularity counts catalog books, not reader activity. Count and page queries are separate and can observe different concurrent states. No performance benchmark establishes a scaling limit.

**Evidence:** [ratings](../app/modules/ratings/repository.py), [analytics](../app/modules/analytics/repository.py), [recommendations](../app/modules/recommendations/repository.py), [books](../app/modules/books/repository.py).

## ADR-010: Share validation and pagination conventions across the API

**Status:** Implemented with exceptions.

**Context and decision:** Pydantic API models alias snake_case fields to camelCase and accept Python field names. Collection routes share zero-based page envelopes. Validation errors map to 400 and repository exceptions to 404/409.

**Rationale and alternatives:** Shared helpers reduce duplicated request and response conventions. Fully typed generic page models and a single error schema would give stronger contracts than the current partial standardization.

**Consequences:** `PageOut.content` is untyped, so it bypasses entity output filtering. Auth token responses keep snake_case. HTTP exceptions use a different error envelope from custom handlers. Frontend TypeScript contracts are handwritten rather than generated from OpenAPI and can drift from runtime responses.

**Evidence:** [schemas](../app/modules/shared/schemas.py), [pagination](../app/core/pagination.py), [handlers](../app/main.py), [UI types](../ui/src/api/types.ts).

## ADR-011: Provide a Compose deployment with basic operational visibility

**Status:** Implemented configuration; deployment behavior not verified in this review.

**Context and decision:** Compose assembles the API and infrastructure. A non-root Python image bundles the default embedding model. HTTP metrics, structured logs, a Neo4j health probe, and IP-based rate limits are built into the API. Startup tolerates unavailable Neo4j.

**Rationale and alternatives:** A single local stack reduces setup work. A deployment platform, shared rate-limit store, distributed tracing, and managed dependencies would add operational capabilities but are not configured here.

**Consequences:** UI hosting is separate. Health does not cover all features; Compose still waits for RabbitMQ. The API healthcheck relies on `wget` without installing it in the image. Rate limits and model/index flags are process-local. Backend dependencies use version ranges without a lockfile, while the UI includes a package lock. The repository does not provide a complete production operations configuration.

**Evidence:** [Compose](../docker-compose.yml), [Dockerfile](../Dockerfile), [metrics config](../prometheus.yml), [limiter](../app/core/limiter.py), [logging](../app/core/logging.py), [requirements](../requirements.txt).

## ADR-012: Isolate application tests with replaceable dependencies

**Status:** Implemented; real-adapter verification is a gap.

**Context and decision:** Service tests use stubs and publisher spies. API tests override FastAPI dependencies with fake repositories/publishers, and RAG endpoint tests mock its service.

**Rationale and alternatives:** This makes route contracts and orchestration testable without Neo4j, RabbitMQ, or model downloads. Container-backed integration and browser tests would exercise different failure modes.

**Consequences:** The suites named integration/coverage do not validate real database queries, response behavior with actual stored fields, broker concurrency/delivery, or vector indexing. Their success cannot establish deployment readiness. Add adapter-level coverage when addressing the review's integrity, serialization, messaging, and indexing findings.

**Evidence:** [unit tests](../tests/unit/test_services.py), [API integration suite](../tests/test_api_integration.py), [API coverage suite](../tests/test_api_coverage.py).


## ADR-013: Separate editable drafts from explicit published snapshots

**Status:** Implemented; live Neo4j verification pending.

**Context and decision:** Writers need to revise a story privately after publishing it. Store draft and published JSON snapshots on one owner-scoped Article node. Save, publish, and unpublish run in one transaction with a revision check and node lock. A unique article ID constraint protects concurrent creation. Public routes expose only published snapshots and typed safe author/summary projections.

**Rationale and alternatives:** Separate snapshots make the publication boundary explicit without introducing version-history tables or a publishing queue. A single mutable body would expose unfinished edits. A full revision log and collaborative editor would add capabilities beyond this phase.

**Consequences:** Private saves do not change public content. Stale writes fail with 409; the browser retains recovery text but does not merge edits. Constraint setup currently requires schema permission on the first write. Full rich text, image storage, moderation, and revision history remain future work. Local recovery is supplementary browser storage; explicit save persists the account draft.

**Evidence:** [publishing contract and limitations](ARTICLE_PUBLISHING.md), [article repository](../app/modules/articles/repository.py), [writer](../ui/src/pages/JournalPage.tsx), [contract tests](../tests/test_articles.py).
