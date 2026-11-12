"""Runs migrations against EXPENSES_DATABASE_URL.

The URL comes from the environment, or from .env in the working directory, the
same way the server gets it. Tests pass a URL explicitly through
config.attributes["database_url"] instead.
"""

from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from alembic import context
from mcp_server.expenses_tracker.config import load_settings
from mcp_server.expenses_tracker.db import SCHEMA

config = context.config
if config.config_file_name is not None and config.attributes.get("configure_logger", True):
    fileConfig(config.config_file_name)


def database_url() -> str:
    if "database_url" in config.attributes:
        return config.attributes["database_url"]
    load_dotenv(override=False)
    return load_settings().database_url


def run_migrations_online() -> None:
    engine = create_engine(database_url())
    with engine.connect() as connection:
        # Alembic keeps its own version table inside our schema, so the schema
        # must exist before Alembic looks for that table.
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"))
        connection.commit()

        context.configure(
            connection=connection,
            version_table_schema=SCHEMA,
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    raise SystemExit("Offline (--sql) migrations are not supported; run against a database.")
run_migrations_online()
