from __future__ import annotations

from .base import QueryResult


class ArangoDatasource:
    """ArangoDB datasource (AQL).

    Placeholder for step-by-step rollout. Will be wired once Arango connector/settings exist.
    """

    name = "ArangoDB"

    def __init__(self, *args, **kwargs):
        raise NotImplementedError("ArangoDatasource will be implemented once Arango connection settings are added.")

    def test_connection(self) -> None:
        raise NotImplementedError

    def execute(self, query: str) -> QueryResult:
        raise NotImplementedError
