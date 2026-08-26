"""
Provides the `store` fixture the conformance suite runs against: once per
test for MemoryStore, and once per test for PostgresStore if one is
reachable (skipped otherwise, so `pytest` still passes without Docker
running -- see docker-compose.yml + yoyo.ini to stand one up locally).
"""

import os

import pytest
import pytest_asyncio

from openvols.data.memory import MemoryStore
from openvols.data.postgres import PostgresStore

POSTGRES_DSN = os.environ.get(
    "OPENVOLS_TEST_POSTGRES_DSN", "postgresql://openvols:openvols@localhost:5432/openvols"
)

# Every table the schema defines -- TRUNCATE ... CASCADE handles the FK
# dependency ordering, so listing them isn't order-sensitive.
_TABLES = (
    "organizations",
    "users",
    "roles",
    "locations",
    "agreements",
    "opportunities",
    "opportunity_agreements",
    "participants",
)


@pytest_asyncio.fixture(params=["memory", "postgres"])
async def store(request):
    if request.param == "memory":
        async with MemoryStore() as memory_store:
            yield memory_store
        return

    postgres_store = PostgresStore(POSTGRES_DSN)
    try:
        await postgres_store.__aenter__()
    except OSError as e:
        pytest.skip(f"Postgres not reachable at {POSTGRES_DSN}: {e}")

    try:
        await postgres_store.pool.execute(f"TRUNCATE {', '.join(_TABLES)} CASCADE")
        yield postgres_store
    finally:
        await postgres_store.__aexit__()
