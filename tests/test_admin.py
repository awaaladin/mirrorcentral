from __future__ import annotations

import re
from collections.abc import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import metadata
from app.db.session import get_session
from app.main import app
from app.models.admin_user import AdminUser
from app.models.client_profile import ClientProfile
from app.models.enhance_job import EnhanceJob
from app.models.enhance_usage import EnhanceUsage
from app.models.enums import (
    AccountType,
    AdminRole,
    ClientTag,
    EnhanceJobStatus,
    SubscriptionPlan,
    SubscriptionStatus,
)
from app.models.makeup_look import MakeupLook
from app.models.subscription import Subscription
from app.models.user import User

CSRF_RE = re.compile(r'name="csrf_token" value="([^"]+)"')


@pytest.fixture
def test_engine():
    engine = create_async_engine("sqlite+aiosqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    return engine


@pytest.fixture
def session_factory(test_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def _setup_db(test_engine, session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[None, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    async with session_factory() as session:
        session.add(AdminUser(email="owner@mirror.app", password_hash=hash_password("owner-pass-123"), role=AdminRole.OWNER))
        session.add(AdminUser(email="viewer@mirror.app", password_hash=hash_password("viewer-pass-123"), role=AdminRole.VIEWER))
        await session.commit()

    yield

    app.dependency_overrides.clear()
    await test_engine.dispose()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


def _login(client: TestClient, email: str, password: str) -> None:
    login_page = client.get("/admin/login")
    csrf_token = CSRF_RE.search(login_page.text).group(1)
    response = client.post(
        "/admin/login",
        data={"email": email, "password": password, "csrf_token": csrf_token, "next_path": "/admin/"},
        follow_redirects=False,
    )
    assert response.status_code == 303


def test_dashboard_requires_login(client: TestClient) -> None:
    response = client.get("/admin/", follow_redirects=False)
    assert response.status_code == 303
    assert "/admin/login" in response.headers["location"]


def test_login_and_view_dashboard(client: TestClient) -> None:
    _login(client, "owner@mirror.app", "owner-pass-123")
    response = client.get("/admin/")
    assert response.status_code == 200
    assert "Dashboard" in response.text


def test_wrong_password_shows_error(client: TestClient) -> None:
    login_page = client.get("/admin/login")
    csrf_token = CSRF_RE.search(login_page.text).group(1)
    response = client.post(
        "/admin/login",
        data={"email": "owner@mirror.app", "password": "wrong", "csrf_token": csrf_token, "next_path": "/admin/"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Incorrect email or password" in response.text


def test_shade_crud_by_owner(client: TestClient) -> None:
    _login(client, "owner@mirror.app", "owner-pass-123")

    new_page = client.get("/admin/shades/new")
    csrf_token = CSRF_RE.search(new_page.text).group(1)

    create_response = client.post(
        "/admin/shades/new",
        data={
            "name": "Test Terracotta",
            "hex_color": "#B85C38",
            "category": "lipstick",
            "finish": "matte",
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )
    assert create_response.status_code == 303

    list_response = client.get("/admin/shades")
    assert "Test Terracotta" in list_response.text


def test_viewer_cannot_create_shade(client: TestClient) -> None:
    _login(client, "viewer@mirror.app", "viewer-pass-123")

    response = client.get("/admin/shades/new", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/"


def test_csrf_mismatch_rejected(client: TestClient) -> None:
    _login(client, "owner@mirror.app", "owner-pass-123")

    client.post(
        "/admin/shades/new",
        data={
            "name": "Should Not Save",
            "hex_color": "#000000",
            "category": "lipstick",
            "finish": "matte",
            "csrf_token": "not-the-real-token",
        },
        follow_redirects=True,
    )
    assert "Should Not Save" not in client.get("/admin/shades").text


async def test_full_page_smoke(client: TestClient, session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Every remaining GET page renders without a template error, given real rows."""
    async with session_factory() as session:
        user = User(email="customer@example.com", password_hash="x", account_type=AccountType.BUSINESS)
        session.add(user)
        await session.flush()

        subscription = Subscription(user_id=user.id, plan=SubscriptionPlan.STUDIO, status=SubscriptionStatus.ACTIVE)
        session.add(subscription)

        session.add(EnhanceUsage(user_id=user.id, billing_period="2026-09", render_count=42))

        client_profile = ClientProfile(owner_user_id=user.id, name="Amina T.", tag=ClientTag.CLIENT)
        session.add(client_profile)
        await session.flush()

        look = MakeupLook(client_profile_id=client_profile.id, source_photo_url="https://example.com/a.jpg", layers={"lip_color": "red"})
        session.add(look)
        await session.flush()

        session.add(EnhanceJob(user_id=user.id, look_id=look.id, status=EnhanceJobStatus.FAILED))

        owner = (await session.execute(select(AdminUser).where(AdminUser.email == "owner@mirror.app"))).scalar_one()
        from app.admin.deps import record_audit

        await record_audit(
            session, admin=owner, action="shade.create", target_type="shade_item", target_id="abc", detail={"name": "x"}
        )
        await session.commit()

        user_id, subscription_id, client_id = user.id, subscription.id, client_profile.id

    _login(client, "owner@mirror.app", "owner-pass-123")

    for path in [
        "/admin/",
        "/admin/users",
        f"/admin/users/{user_id}",
        "/admin/subscriptions",
        f"/admin/subscriptions/{subscription_id}/edit",
        "/admin/enhance-jobs",
        "/admin/enhance-jobs?status=failed",
        "/admin/shades",
        "/admin/shades/new",
        "/admin/clients",
        f"/admin/clients/{client_id}",
        "/admin/audit-log",
        "/admin/admins",
    ]:
        response = client.get(path)
        assert response.status_code == 200, f"{path} returned {response.status_code}: {response.text[:500]}"
