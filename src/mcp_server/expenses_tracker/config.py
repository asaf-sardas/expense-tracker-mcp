"""All settings in one place.

Each setting has a default and can be overridden with an environment variable,
for example when connecting the server:

    claude mcp add expenses -e EXPENSES_WARNING_PERCENT=75 -- uv --directory ... run ...
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    db_path: Path
    """SQLite database file. Env: EXPENSES_DB"""

    warning_percent: int
    """Budget usage that triggers a 'warning' alert. Env: EXPENSES_WARNING_PERCENT"""

    exceeded_percent: int
    """Budget usage that triggers an 'exceeded' alert. Env: EXPENSES_EXCEEDED_PERCENT"""

    currency_symbol: str
    """Shown before amounts in alert and error messages. Env: EXPENSES_CURRENCY_SYMBOL"""


def load_settings(env: Mapping[str, str] = os.environ) -> Settings:
    """Read settings from environment variables, falling back to the defaults.
    Raises ValueError at startup if a value is invalid."""
    settings = Settings(
        db_path=Path(env.get("EXPENSES_DB", Path.home() / "expenses.db")).expanduser(),
        warning_percent=_int(env, "EXPENSES_WARNING_PERCENT", 80),
        exceeded_percent=_int(env, "EXPENSES_EXCEEDED_PERCENT", 100),
        currency_symbol=env.get("EXPENSES_CURRENCY_SYMBOL", "₪"),
    )
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


settings = load_settings()
