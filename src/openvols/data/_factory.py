"""Builds a Store for the backend selected by DataSettings."""

from openvols.data import _store, memory, postgres

__all__ = ["create_store"]


def create_store(settings: _store.DataSettings) -> _store.Store:
    if settings.backend == "memory":
        return memory.MemoryStore()

    if settings.backend == "postgres":
        if not settings.postgres_dsn:
            raise ValueError("OPENVOLS_DATA_POSTGRES_DSN is required for the postgres backend")

        return postgres.PostgresStore(settings.postgres_dsn)

    raise ValueError(f"Unknown data backend: {settings.backend!r}")
