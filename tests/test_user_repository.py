from sqlalchemy import text

from mcp_server.expenses_tracker.repository.UserRepository import UserRepository


def users(db):
    with db.transaction() as con:
        return [tuple(r) for r in con.execute(text("SELECT id, email FROM users"))]


def test_ensure_user_creates_the_row(db):
    assert UserRepository(db).ensure_user("alice", "alice@example.com") == "alice"
    assert users(db) == [("alice", "alice@example.com")]


def test_ensure_user_twice_keeps_one_row(db):
    repo = UserRepository(db)
    repo.ensure_user("alice", "alice@example.com")
    repo.ensure_user("alice", "other@example.com")
    assert users(db) == [("alice", "alice@example.com")]
