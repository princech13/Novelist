"""Versioned drafts and explicit published snapshots; writes share one transaction."""
import json
from app.infrastructure.neo4j.base import ConflictError, NotFoundError, now, to_native


class ArticleRepositoryMixin:
    def _ensure_article_schema(self):
        if not getattr(self, "_article_schema_ready", False):
            self._one("CREATE CONSTRAINT article_id_unique IF NOT EXISTS FOR (a:Article) REQUIRE a.articleId IS UNIQUE")
            self._article_schema_ready = True

    @staticmethod
    def _article_out(row, private=False):
        props = to_native(dict(row["a"]))
        content = json.loads(props["draftJson"] if private else props["publishedJson"])
        return {**content, "articleId": props["articleId"], "authorId": props["ownerId"],
                "authorName": row["authorName"], "revision": props["revision"] if private else props["publishedRevision"],
                "published": props.get("publishedJson") is not None,
                "updatedAt": props["updatedAt"] if private else props["publishedAt"],
                "publishedAt": props.get("publishedAt")}

    def save_article(self, article_id: str, user_id: str, payload: dict) -> dict:
        self._ensure_article_schema()
        content = {key: payload[key] for key in ("title", "subtitle", "body", "kind", "book")}
        encoded = json.dumps(content, ensure_ascii=False)

        def write(tx):
            # Matching a live author prevents deleted-account tokens from creating content.
            user = tx.run("MATCH (u:User {userId: $uid}) RETURN u.name AS name", uid=user_id).single()
            if not user:
                raise NotFoundError("Author not found")
            row = tx.run(
                "MERGE (a:Article {articleId: $id}) "
                "ON CREATE SET a.ownerId = $uid, a.revision = 0, a.createdAt = $now "
                "SET a._writeLock = true RETURN a",
                id=article_id, uid=user_id, now=now(),
            ).single()
            # The explicit write lock serializes revision checks, including concurrent creates.
            article = dict(row["a"])
            if article["ownerId"] != user_id:
                raise NotFoundError("Article not found")
            if article["revision"] != payload["revision"]:
                raise ConflictError("This story changed in another session. Reload the server version before saving again.")
            revision = article["revision"] + 1
            props = {"draftJson": encoded, "revision": revision, "updatedAt": now()}
            if payload["action"] == "publish":
                props.update(publishedJson=encoded, publishedAt=now(), publishedRevision=revision)
            elif payload["action"] == "unpublish":
                props.update(publishedJson=None, publishedAt=None, publishedRevision=None)
            row = tx.run(
                "MATCH (a:Article {articleId: $id}) SET a += $props REMOVE a._writeLock "
                "RETURN a, $name AS authorName", id=article_id, props=props, name=user["name"],
            ).single()
            return self._article_out(row, private=True)

        with self.driver.session() as session:
            return session.execute_write(write)

    def get_article(self, article_id: str, owner_id: str | None = None) -> dict:
        row = self._one(
            "MATCH (a:Article {articleId: $id}), (u:User {userId: a.ownerId}) "
            "WHERE ($owner IS NOT NULL AND a.ownerId = $owner) OR ($owner IS NULL AND a.publishedJson IS NOT NULL) "
            "RETURN a, u.name AS authorName", id=article_id, owner=owner_id,
        )
        if not row:
            raise NotFoundError("Article not found")
        return self._article_out(row, private=owner_id is not None)

    def page_articles(self, page: int, size: int, owner_id: str | None = None, author_id: str | None = None):
        match = ("MATCH (a:Article), (u:User {userId: a.ownerId}) "
                 "WHERE (($owner IS NOT NULL AND a.ownerId = $owner) OR ($owner IS NULL AND a.publishedJson IS NOT NULL)) "
                 "AND ($author IS NULL OR a.ownerId = $author) ")
        params = dict(owner=owner_id, author=author_id, skip=page * size, size=size)
        total = self._one(match + "RETURN count(a) AS total", **params)["total"]
        order = "a.updatedAt" if owner_id else "a.publishedAt"
        rows = self._all(match + f"RETURN a, u.name AS authorName ORDER BY {order} DESC, a.articleId SKIP $skip LIMIT $size", **params)
        return [self._article_out(row, private=owner_id is not None) for row in rows], total

    def get_author(self, user_id: str) -> dict:
        row = self._one(
            "MATCH (u:User {userId: $uid}) OPTIONAL MATCH (a:Article {ownerId: $uid}) "
            "WHERE a.publishedJson IS NOT NULL RETURN u.userId AS userId, u.name AS name, count(a) AS publishedCount", uid=user_id,
        )
        if not row:
            raise NotFoundError("Author not found")
        return dict(row)
