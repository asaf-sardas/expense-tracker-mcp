from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import Connection, create_engine, event

# All of the app's tables live in their own schema, not in "public". On
# Supabase, tables in "public" are exposed through the auto-generated Data API;
# a private schema keeps them reachable only through this server.
SCHEMA = "expenses_app"


class Database:
    """Owns the connection pool. The tables are created and changed by Alembic
    migrations (see alembic/), never here: run `uv run alembic upgrade head`."""

    def __init__(self, url: str):
        # pool_pre_ping: check a pooled connection is still alive before using it.
        # Supabase's pooler and Cloud Run both drop idle connections.
        self.engine = create_engine(url, pool_pre_ping=True)

        @event.listens_for(self.engine, "connect")
        def _use_app_schema(dbapi_connection, _record):
            # Unqualified table names (expenses, budgets, users) resolve to SCHEMA.
            # Runs once per new physical connection, so it suits the session pooler.
            with dbapi_connection.cursor() as cur:
                cur.execute(f"SET search_path TO {SCHEMA}")
            dbapi_connection.commit()

    @contextmanager
    def transaction(self) -> Generator[Connection]:
        """One transaction: commits when the block ends, rolls back if it raises,
        and always returns the connection to the pool."""
        with self.engine.begin() as con:
            yield con

    def close(self) -> None:
        self.engine.dispose()
