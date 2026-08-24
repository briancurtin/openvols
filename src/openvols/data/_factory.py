"""Builds a Store for the backend selected by DataSettings."""

from openvols.data import _store, memory


def create_store(settings: _store.DataSettings) -> _store.Store:
    if settings.backend == "memory":
        return memory.MemoryStore()
    if settings.backend == "postgres":
        raise NotImplementedError("The postgres backend is not implemented yet")
    raise ValueError(f"Unknown data backend: {settings.backend!r}")
