"""Persistence operations for users."""
import json
from typing import Any
from uuid import uuid4

from app.infrastructure.neo4j.base import ConflictError, NotFoundError, node, now, to_native


class UserRepositoryMixin:
    @staticmethod
    def _user_properties(payload: dict[str, Any]) -> dict[str, Any]:
        fields = {"name": payload.get("name"), "email": payload.get("email"), "age": payload.get("age")}
        password_hash = payload.get("passwordHash") or payload.get("password_hash")
        if password_hash is not None:
            fields["passwordHash"] = password_hash
        if payload.get("preferences") is not None:
            fields["preferencesJson"] = json.dumps(payload["preferences"], separators=(",", ":"))
        return {key: value for key, value in fields.items() if value is not None}

    @staticmethod
    def _user_out(user: dict[str, Any], ratings: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        preferences = user.pop("preferencesJson", None)
        if preferences:
            user["preferences"] = json.loads(preferences)
        if ratings is not None:
            user["ratedBooks"] = ratings
        return user

    def create_user(self, payload: dict[str, Any]) -> dict[str, Any]:
        props = self._user_properties(payload)
        email = props.get("email")
        if email and self._one("MATCH (u:User) WHERE toLower(u.email) = toLower($email) RETURN u", email=email):
            raise ConflictError(f"User already exists with identifier: {email}")
        props.update(userId=str(uuid4()), createdAt=now(), updatedAt=now())
        return self._user_out(node(self._one("CREATE (u:User) SET u = $props RETURN u AS entity", props=props)), [])

    def find_user_by_email(self, email: str) -> dict[str, Any] | None:
        record = self._one("MATCH (u:User {email: $email}) RETURN u AS entity", email=email)
        return self._user_out(node(record), []) if record else None

    def get_user(self, user_id: str) -> dict[str, Any]:
        record = self._one("MATCH (u:User {userId: $user_id}) RETURN u AS entity", user_id=user_id)
        if not record:
            raise NotFoundError(f"User not found with id: {user_id}")
        ratings = []
        for row in self._all("MATCH (u:User {userId: $user_id})-[r:RATED]->(b:Book) RETURN r, b", user_id=user_id):
            relation = to_native(dict(row["r"]))
            book = to_native(dict(row["b"]))
            ratings.append({"book": book, "rating": relation["rating"], "review": relation.get("review"), "timestamp": relation.get("timestamp"), "helpfulCount": relation.get("helpful", 0)})
        return self._user_out(node(record), ratings)

    def update_user(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.get_user(user_id)
        props = self._user_properties(payload)
        if "email" in props:
            duplicate = self._one("MATCH (u:User) WHERE toLower(u.email) = toLower($email) AND u.userId <> $user_id RETURN u", email=props["email"], user_id=user_id)
            if duplicate:
                raise ConflictError(f"User already exists with identifier: {props['email']}")
        props["updatedAt"] = now()
        self._one("MATCH (u:User {userId: $user_id}) SET u += $props RETURN u", user_id=user_id, props=props)
        return self.get_user(user_id)

    def delete_user(self, user_id: str) -> None:
        self.get_user(user_id)
        self._one("MATCH (u:User {userId: $user_id}) DETACH DELETE u", user_id=user_id)

    def page_users(self, page: int, size: int, query: str | None = None) -> tuple[list[dict[str, Any]], int]:
        where = "WHERE ($search_query IS NULL OR toLower(u.name) CONTAINS toLower($search_query))"
        params = {"search_query": query, "skip": page * size, "size": size}
        total = self._one(f"MATCH (u:User) {where} RETURN count(u) AS total", **params)["total"]
        rows = self._all(f"MATCH (u:User) {where} RETURN u AS entity ORDER BY u.name SKIP $skip LIMIT $size", **params)
        return [self._user_out(node(row), []) for row in rows], total
