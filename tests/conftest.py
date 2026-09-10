import os

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost/mirror_test")
os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use-in-production")


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
