"""All settings in one place.

Each setting has a default and can be overridden with an environment variable,
for example when connecting the server:

    claude mcp add expenses -e EXPENSES_WARNING_PERCENT=75 -- uv --directory ... run ...

When the server starts, variables from a .env file in the working directory are
loaded too (see server.main); real environment variables win over the file.
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass


# The Postgres started by docker-compose.yml. Supabase or any other Postgres is
# used by setting EXPENSES_DATABASE_URL.
DEFAULT_DATABASE_URL = "postgresql+psycopg://expenses:expenses@localhost:5432/expenses"
DEFAULT_WARNING_PERCENT = 80
DEFAULT_EXCEEDED_PERCENT = 100
DEFAULT_CURRENCY_SYMBOL = "₪"
DEFAULT_DEV_USER_ID = "local"


@dataclass(frozen=True)
class Settings:
    database_url: str
    """PostgreSQL connection URL. Env: EXPENSES_DATABASE_URL"""

    warning_percent: int
    """Budget usage that triggers a 'warning' alert. Env: EXPENSES_WARNING_PERCENT"""

    exceeded_percent: int
    """Budget usage that triggers an 'exceeded' alert. Env: EXPENSES_EXCEEDED_PERCENT"""

    currency_symbol: str
    """Shown before amounts in alert and error messages. Env: EXPENSES_CURRENCY_SYMBOL"""

    dev_user_id: str
    """The user for local runs without login (stdio). Env: EXPENSES_DEV_USER_ID"""


def load_settings(env: Mapping[str, str] = os.environ) -> Settings:
    """Read settings from environment variables, falling back to the defaults.
    Raises ValueError at startup if a value is invalid."""
    settings = Settings(
        database_url=_database_url(env.get("EXPENSES_DATABASE_URL", DEFAULT_DATABASE_URL)),
        warning_percent=_int(env, "EXPENSES_WARNING_PERCENT", DEFAULT_WARNING_PERCENT),
        exceeded_percent=_int(env, "EXPENSES_EXCEEDED_PERCENT", DEFAULT_EXCEEDED_PERCENT),
        currency_symbol=env.get("EXPENSES_CURRENCY_SYMBOL", DEFAULT_CURRENCY_SYMBOL),
        dev_user_id=env.get("EXPENSES_DEV_USER_ID", DEFAULT_DEV_USER_ID).strip(),
    )
    if not settings.dev_user_id:
        raise ValueError("EXPENSES_DEV_USER_ID must not be empty")
    if not 0 < settings.warning_percent < settings.exceeded_percent:
        raise ValueError(
            "EXPENSES_WARNING_PERCENT must be above 0 and below "
            f"EXPENSES_EXCEEDED_PERCENT, got {settings.warning_percent} "
            f"and {settings.exceeded_percent}"
        )
    return settings


def _int(env: Mapping[str, str], name: str, default: int) -> int:
    raw = env.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        raise ValueError(f"{name} must be a whole number, got {raw!r}") from None


def _database_url(raw: str) -> str:
    """Accept the URL as Supabase and most tools print it (postgresql://...) and
    tell SQLAlchemy to use the psycopg 3 driver."""
    url = raw.strip()
    for prefix in ("postgresql+psycopg://", "postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    # Never echo the URL back: it usually contains the password.
    raise ValueError("EXPENSES_DATABASE_URL must be a PostgreSQL URL (postgresql://...)")
