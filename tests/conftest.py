import os
from collections.abc import AsyncGenerator, Generator

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost/mirror_test")
os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use-in-production")

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.db.base import metadata  # noqa: E402
from app.db.session import get_session  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def test_engine():
    return create_async_engine(
        "sqlite+aiosqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )


@pytest.fixture
def session_factory(test_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def _setup_db(test_engine, session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[None, None]:
    """Every test gets a fresh in-memory SQLite schema, with app.db.session.get_session
    overridden to use it — so tests never touch a real Postgres instance."""
    async with test_engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    yield

    app.dependency_overrides.clear()
    await test_engine.dispose()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c
