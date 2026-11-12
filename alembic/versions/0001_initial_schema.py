"""Initial schema: users, expenses and budgets, each row owned by a user.

Revision ID: 0001
Revises:
Create Date: 2026-11-09
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from mcp_server.expenses_tracker.db import SCHEMA

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = ("users", "expenses", "budgets")


def upgrade() -> None:
    # id is the login's subject: "local" for the dev user, later the OAuth
    # (Supabase auth) user id. TEXT, so both fit.
    op.create_table(
        "users",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("email", sa.Text),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema=SCHEMA,
    )

    op.create_table(
        "expenses",
        sa.Column("id", sa.BigInteger, sa.Identity(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Text,
            sa.ForeignKey(f"{SCHEMA}.users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Money as whole agorot: exact, no float rounding.
        sa.Column("amount_agorot", sa.BigInteger, nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("category", sa.Text, nullable=False),
        sa.Column("expense_date", sa.Date, nullable=False),
        sa.CheckConstraint("amount_agorot > 0", name="expenses_amount_positive"),
        schema=SCHEMA,
    )
    # Every expense query filters by user, then by a date range.
    op.create_index(
        "idx_expenses_user_date", "expenses", ["user_id", "expense_date"], schema=SCHEMA
    )

    op.create_table(
        "budgets",
        sa.Column(
            "user_id",
            sa.Text,
            sa.ForeignKey(f"{SCHEMA}.users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("category", sa.Text, primary_key=True),
        sa.Column("amount_agorot", sa.BigInteger, nullable=False),
        sa.CheckConstraint("amount_agorot > 0", name="budgets_amount_positive"),
        schema=SCHEMA,
    )

    # Defense in depth for Supabase: with RLS on and no policies, the public
    # "anon" and "authenticated" API roles can read nothing even if this schema
    # is ever exposed. The server connects as the table owner, which bypasses RLS.
    for table in TABLES:
        op.execute(f"ALTER TABLE {SCHEMA}.{table} ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    for table in reversed(TABLES):
        op.drop_table(table, schema=SCHEMA)
