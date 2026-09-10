from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal

from pydantic import computed_field, model_validator
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

    # Signs the admin console's session cookie. Falls back to jwt_secret if unset so
    # local dev needs one less env var, but production should set its own distinct
    # value (a leaked mobile-API secret then can't also forge admin sessions).
    admin_session_secret: str | None = None

    r2_account_id: str = ""
    r2_access_key: str = ""
    r2_secret_key: str = ""
    r2_bucket_name: str = ""

    replicate_api_token: str | None = None

    paystack_secret_key: str = ""

    enhance_provider: Literal["local", "hosted"] = "local"

    solo_plan_monthly_cap: int = 100
    studio_plan_monthly_cap: int = 400

    @model_validator(mode="before")
    @classmethod
    def _blank_env_vars_use_defaults(cls, data: Any) -> Any:
        """Treat an empty-string env var as unset so the field's default applies.

        Platforms like Vercel can leave a variable defined but empty for a given
        environment; pydantic-settings only falls back to the default when the
        key is absent entirely, so a blank value would otherwise fail typed
        fields (int, Literal) instead of using the default.
        """
        if not isinstance(data, dict):
            return data
        for name, field in cls.model_fields.items():
            if name in data and data[name] == "" and not field.is_required():
                del data[name]
        return data

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
        """Extra connect args for the async engine (translated from `sslmode`, if present).

        Supabase's "Transaction" pooler (port 6543) is pgbouncer in transaction mode,
        which doesn't support asyncpg's server-side prepared statements -- a connection
        can be handed to a different query between statements, so a statement prepared
        on one backend may not exist on the next. `statement_cache_size=0` disables
        asyncpg's prepared-statement cache so every query runs as a plain (unprepared)
        query instead.
        """
        url = make_url(self.database_url)
        connect_args: dict[str, Any] = {}
        sslmode = url.query.get("sslmode")
        if sslmode in ("require", "verify-ca", "verify-full"):
            connect_args["ssl"] = True
        if url.port == 6543:
            connect_args["statement_cache_size"] = 0
        return connect_args

    @computed_field  # type: ignore[prop-decorator]
    @property
    def admin_session_secret_effective(self) -> str:
        return self.admin_session_secret or self.jwt_secret

    def plan_monthly_cap(self, plan: str) -> int:
        caps = {"solo": self.solo_plan_monthly_cap, "studio": self.studio_plan_monthly_cap}
        try:
            return caps[plan]
        except KeyError as exc:
            raise ValueError(f"Unknown plan: {plan!r}") from exc


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
