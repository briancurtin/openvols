"""Public interface for the Postgres Store backend."""

from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor

from openvols.data.postgres._store import PostgresStore

__all__ = ["PostgresStore"]

AsyncPGInstrumentor().instrument()
