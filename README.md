# mirrorcentral

Python FastAPI backend for **Mirror**, a Kotlin Android makeup simulation app. This
service backs the Pro/business tier: it accepts a captured photo plus the makeup look
applied to it, runs a higher-quality server-side render (and, later, an AI-assisted
polish pass), and returns the enhanced image. It also owns user accounts, client/look
data, and subscription entitlements.

**Status: phase 1 of 8** — project scaffolding, config loading, database models, the
initial Alembic migration, and a `/health` check. Auth, CRUD, the enhance pipeline,
entitlements, and deployment tooling land in subsequent phases; this README will grow
into full setup/deploy docs at that point.

## Tech stack

- Python 3.12, FastAPI, Pydantic v2, pydantic-settings for config
- SQLAlchemy 2.0 (async) + SQLModel + Alembic for migrations
- Postgres (Neon), read from `DATABASE_URL`
- Redis + arq for the background enhance job queue
- boto3 / Cloudflare R2 for photo storage
- JWT auth, passlib/bcrypt for password hashing
- httpx for outbound calls (AI provider, Paystack)

## Local setup (phase 1)

```
python -m venv .venv
./.venv/Scripts/activate       # Windows
pip install -e ".[dev]"
cp .env.example .env           # then fill in DATABASE_URL and JWT_SECRET at minimum
alembic upgrade head
uvicorn app.main:app --reload
```

Run tests with:

```
pytest
```
