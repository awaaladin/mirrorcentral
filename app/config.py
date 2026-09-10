from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    """Application configuration, loaded entirely from environment variables.

    See .env.example for the full list of variables and what each one is for.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"

    # Postgres (Neon). Plain "postgresql://" / "postgres://" URLs are accepted and
    # rewritten to use the asyncpg driver; see `database_url_async`.
    database_url: str

    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    r2_account_id: str = ""
    r2_access_key: str = ""
    r2_secret_key: str = ""
    r2_bucket_name: str = ""

    replicate_api_token: str | None = None

    paystack_secret_key: str = ""

    enhance_provider: Literal["local", "hosted"] = "local"

    solo_plan_monthly_cap: int = 100
    studio_plan_monthly_cap: int = 400

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url_async(self) -> str:
        """`database_url` normalized to the asyncpg driver for SQLAlchemy's async engine.

        Uses SQLAlchemy's own URL parser (rather than urllib) so it round-trips
        driver-specific quirks correctly, e.g. sqlite's triple-slash relative paths.

        asyncpg doesn't understand libpq's `sslmode` query parameter, so a Neon-style
        `...?sslmode=require` URL has it stripped here; `database_connect_args` carries
        the equivalent SSL requirement instead.
        """
        url = make_url(self.database_url)
        if url.drivername in ("postgres", "postgresql"):
            url = url.set(drivername="postgresql+asyncpg")
        if "sslmode" in url.query:
            url = url.set(query={k: v for k, v in url.query.items() if k != "sslmode"})
        return url.render_as_string(hide_password=False)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_connect_args(self) -> dict[str, Any]:
        """Extra connect args for the async engine (translated from `sslmode`, if present)."""
        sslmode = make_url(self.database_url).query.get("sslmode")
        if sslmode in ("require", "verify-ca", "verify-full"):
            return {"ssl": True}
        return {}

    def plan_monthly_cap(self, plan: str) -> int:
        caps = {"solo": self.solo_plan_monthly_cap, "studio": self.studio_plan_monthly_cap}
        try:
            return caps[plan]
        except KeyError as exc:
            raise ValueError(f"Unknown plan: {plan!r}") from exc


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
