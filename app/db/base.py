"""Single import point for all SQLModel table models.

Alembic's autogenerate needs every model imported somewhere before it inspects
`SQLModel.metadata`, so `alembic/env.py` imports this module rather than the
individual model modules.
"""

from sqlmodel import SQLModel

from app.models.client_profile import ClientProfile  # noqa: F401
from app.models.enhance_job import EnhanceJob  # noqa: F401
from app.models.enhance_usage import EnhanceUsage  # noqa: F401
from app.models.makeup_look import MakeupLook  # noqa: F401
from app.models.shade_item import ShadeItem  # noqa: F401
from app.models.subscription import Subscription  # noqa: F401
from app.models.user import User  # noqa: F401

metadata = SQLModel.metadata
