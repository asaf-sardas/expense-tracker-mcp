import pytest

from mcp_server.expenses_tracker.config import load_settings


def test_defaults_when_nothing_is_set():
    settings = load_settings({})
    assert settings.database_url == (
        "postgresql+psycopg://expenses:expenses@localhost:5432/expenses"
    )
    assert settings.warning_percent == 80
    assert settings.exceeded_percent == 100
    assert settings.currency_symbol == "₪"


def test_environment_overrides_defaults():
    settings = load_settings(
        {
            "EXPENSES_DATABASE_URL": "postgresql+psycopg://u:p@db.example:5432/x",
            "EXPENSES_WARNING_PERCENT": "70",
            "EXPENSES_EXCEEDED_PERCENT": "90",
            "EXPENSES_CURRENCY_SYMBOL": "$",
        }
    )
    assert settings.database_url == "postgresql+psycopg://u:p@db.example:5432/x"
    assert (settings.warning_percent, settings.exceeded_percent) == (70, 90)
    assert settings.currency_symbol == "$"


@pytest.mark.parametrize("prefix", ["postgresql://", "postgres://"])
def test_plain_postgres_urls_get_the_psycopg_driver(prefix):
    # Supabase and most tools print URLs without a driver.
    settings = load_settings({"EXPENSES_DATABASE_URL": f"{prefix}u:p@host:5432/db"})
    assert settings.database_url == "postgresql+psycopg://u:p@host:5432/db"


def test_non_postgres_url_is_rejected_without_echoing_it():
    with pytest.raises(ValueError, match="must be a PostgreSQL URL") as error:
        load_settings({"EXPENSES_DATABASE_URL": "sqlite:///secret-password.db"})
    assert "secret-password" not in str(error.value)


def test_non_number_percent_is_rejected():
    with pytest.raises(ValueError, match="EXPENSES_WARNING_PERCENT must be a whole number"):
        load_settings({"EXPENSES_WARNING_PERCENT": "eighty"})


@pytest.mark.parametrize(
    "warning, exceeded",
    [("100", "100"), ("90", "80"), ("0", "100"), ("-10", "100")],
    ids=["equal", "warning-above-exceeded", "zero", "negative"],
)
def test_warning_must_be_above_zero_and_below_exceeded(warning, exceeded):
    with pytest.raises(ValueError, match="must be above 0 and below"):
        load_settings(
            {
                "EXPENSES_WARNING_PERCENT": warning,
                "EXPENSES_EXCEEDED_PERCENT": exceeded,
            }
        )


def test_dev_user_defaults_to_local_and_can_be_overridden():
    assert load_settings({}).dev_user_id == "local"
    assert load_settings({"EXPENSES_DEV_USER_ID": "asaf"}).dev_user_id == "asaf"


@pytest.mark.parametrize("value", ["", "   "])
def test_empty_dev_user_is_rejected(value):
    with pytest.raises(ValueError, match="EXPENSES_DEV_USER_ID must not be empty"):
        load_settings({"EXPENSES_DEV_USER_ID": value})
